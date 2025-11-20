from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import Literal
from enum import Enum

from corrector.application.database import get_session
from corrector.application.database.tables import User, Document
from corrector.application.http_api.controllers.document import DocumentBase, DocumentDTO
from corrector.application.http_api.controllers.mistake import MistakeDTO
from corrector.application.http_api.controllers.status import StatusResponse
from corrector.application.http_api.controllers.auth import get_password_hash


# Импортируем функции из того же файла (если они в одном файле)
# Если функции в том же файле, они уже доступны

router = APIRouter(
    prefix="/users", 
    tags=["users"]
)
SessionDep = Annotated[Session, Depends(get_session)]


class UserDTO(BaseModel):
    first_name: str = Field(description="Имя пользователя", max_length=255)
    user_name: str = Field(description="Логин", max_length=255)

class UserDb(BaseModel):
    id: int | None = Field(description="Идентификатор", default=None)
    first_name: str = Field(description="Имя пользователя", max_length=255)
    surname_name: str = Field(description="Фамилия пользователя", max_length=255)
    patronomic_name: str = Field(description="Отчество пользователя (при наличии)", max_length=255)
    user_name: str = Field(description="Логин", max_length=255)
    tg_username: str = Field(description="Telegram:", max_length=255)
    is_tg_subscribed: bool = Field(False, description="Подписка на канал")
    is_admin: bool = Field(False, description="Админка")
    theme: Literal["dark", "light"] = Field(description="Тема приложения")
    notification_push: bool = Field(False, description="Уведомления в браузере")

class UserCreate(BaseModel):
    first_name: str = Field(description="Имя пользователя", max_length=255)
    surname_name: str | None = Field(None, description="Фамилия пользователя", max_length=255)
    patronomic_name: str | None = Field(None, description="Отчество пользователя (при наличии)", max_length=255)
    user_name: str = Field(description="Логин", max_length=255)
    password: str = Field(description="Пароль", max_length=255)
    tg_username: str | None = Field(None, description="Telegram username", max_length=255)
    theme: Literal["dark", "light"] = Field("light", description="Тема приложения")
    notification_push: bool = Field(False, description="Уведомления в браузере")

class UserUpdate(BaseModel):
    first_name: str | None = Field(None, description="Имя пользователя", max_length=255)
    surname_name: str | None = Field(None, description="Фамилия пользователя", max_length=255)
    patronomic_name: str | None = Field(None, description="Отчество пользователя (при наличии)", max_length=255)
    password: str | None = Field(None, description="Пароль", max_length=255)
    user_name: str | None = Field(None, description="Логин", max_length=255)
    tg_username: str | None = Field(None, description="Telegram username", max_length=255)
    theme: Literal["dark", "light"] | None = Field(None, description="Тема приложения")
    notification_push: bool | None = Field(None, description="Уведомления в браузере")

# ИСПРАВЛЕННЫЕ ЭНДПОИНТЫ С ХЭШИРОВАНИЕМ ПАРОЛЕЙ

@router.post(path="", response_model=UserDb)
async def create_user(user_data: UserCreate, session: SessionDep):
    """Запрос: создание нового пользователя"""
    # Проверка существования пользователя с таким логином
    existing_user = session.scalar(select(User).where(User.user_name == user_data.user_name))
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    
    # Проверка существования пользователя с таким Telegram username
    if user_data.tg_username:
        existing_tg = session.scalar(select(User).where(User.tg_username == user_data.tg_username))
        if existing_tg:
            raise HTTPException(status_code=400, detail="Пользователь с таким Telegram username уже существует")
    
    # ХЭШИРОВАНИЕ ПАРОЛЯ ПЕРЕД СОХРАНЕНИЕМ
    hashed_password = get_password_hash(user_data.password)
    
    # Создание пользователя с хэшированным паролем
    user = User(
        first_name=user_data.first_name,
        surname_name=user_data.surname_name,
        patronomic_name=user_data.patronomic_name,
        user_name=user_data.user_name,
        password=hashed_password,  # Используем хэшированный пароль
        tg_username=user_data.tg_username,
        theme=user_data.theme,
        notification_push=user_data.notification_push
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.put(path="/{user_id}", response_model=UserDb)
async def update_user(user_id: int, user_data: UserUpdate, session: SessionDep):
    """Запрос: обновление данных пользователя"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверка уникальности логина, если изменяется
    if user_data.user_name and user_data.user_name != user.user_name:
        existing_user = session.scalar(select(User).where(User.user_name == user_data.user_name))
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    
    # Проверка уникальности Telegram username, если изменяется
    if user_data.tg_username and user_data.tg_username != user.tg_username:
        existing_tg = session.scalar(select(User).where(User.tg_username == user_data.tg_username))
        if existing_tg:
            raise HTTPException(status_code=400, detail="Пользователь с таким Telegram username уже существует")
    
    # Получаем данные для обновления
    update_data = user_data.model_dump(exclude_unset=True)
    
    # ЕСЛИ ПЕРЕДАН ПАРОЛЬ - ХЭШИРУЕМ ЕГО
    if 'password' in update_data and update_data['password']:
        update_data['password'] = get_password_hash(update_data['password'])
    
    # Обновляем поля
    for field, value in update_data.items():
        setattr(user, field, value)
    
    session.commit()
    session.refresh(user)
    return user

# Остальные ваши эндпоинты остаются без изменений
@router.get(path="", response_model=list[UserDb])
async def get_users(session: SessionDep):
    """Запрос: получение списка пользователей"""
    return session.scalars(select(User)).all()

@router.get(path="/{user_id}", response_model=UserDb)
async def get_user(user_id: int, session: SessionDep):
    """Запрос: получение пользователя по ID"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.delete("/{user_id}")
async def delete_user(user_id: int, session: SessionDep):
    """Запрос: удаление пользователя"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    session.delete(user)
    session.commit()
    
    return {"message": "Пользователь успешно удален"}

@router.get("/{user_id}/documents", response_model=list[DocumentBase])
async def get_user_documents(user_id: int, session: SessionDep):
    """Запрос: получение всех документов пользователя"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    documents = session.scalars(select(Document).where(Document.user_id == user_id)).all()
    return documents

@router.get("/username/{username}", response_model=UserDb)
async def get_user_by_username(username: str, session: SessionDep):
    """Запрос: получение пользователя по логину"""
    user = session.scalar(select(User).where(User.user_name == username))
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.get("/{user_id}/documents/status", response_model=list[DocumentBase])
async def get_user_documents_status(user_id: int, session: SessionDep):
    """Запрос: получение всех документов пользователя с их статусами"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    documents = session.scalars(select(Document).where(Document.user_id == user_id)).all()
    if not documents:
        raise HTTPException(status_code=404, detail="Документы не найдены")
    
    return documents