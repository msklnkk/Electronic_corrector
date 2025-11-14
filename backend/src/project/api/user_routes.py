from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select, update, insert, delete
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from project.core.exceptions import UserAlreadyExists, UserNameAlreadyExists, UserNotFound
from project.resource.auth import get_password_hash
from project.schemas.user import UserCreate, UserSchema


from project.infrastructure.postgres.session import get_session
from project.api.depends import database, user_repo, get_current_user, check_for_admin_access


user_routes = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

# class UserDb(BaseModel):
#     """Пользователь"""
#     id: int | None = Field(description="Идентификатор", default=None)
#     first_name: str = Field(description="Имя")
#     surname_name: str = Field(description="Фамилия")
#     patronomic_name: str = Field(description="Отчество")
#     user_name: str = Field(description="Логин")
#     password: str = Field(description="Пароль")
#     role: str = Field(description="Роль")
#     is_admin: bool = Field(description="Админ", default=False)
    
@user_routes.get(
    "/all_users",
    response_model=list[UserSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_all_users() -> list[UserSchema]:
    async with database.session() as session:
        all_users = await user_repo.get_all_users(session=session)

    return all_users

@user_routes.post(
    "/add_user",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED
)
async def add_user(
    user_dto: UserCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> UserSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            user_dto.password = get_password_hash(password=user_dto.password)
            new_user = await user_repo.create_user(session=session, user=user_dto)
    except UserAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)
    except UserNameAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return new_user

@user_routes.put(
    "/update_user/{user_id}",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: int,
    user_dto: UserCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> UserSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            user_dto.password = get_password_hash(password=user_dto.password)
            updated_user = await user_repo.update_user(
                session=session,
                user_id=user_id,
                user=user_dto,
            )
    except UserNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)

    return updated_user

@user_routes.delete(
    "/delete_user/{user_id}",
    status_code = status.HTTP_204_NO_CONTENT
)
async def delete_user(
        user_id: int,
        current_user: UserSchema = Depends(get_current_user),
) -> None:
    """Запрос: удалить пользователя"""
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            user = await user_repo.delete_user(session=session, user_id=user_id)
    except UserNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)

    return user