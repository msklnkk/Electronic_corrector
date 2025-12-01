from typing import Annotated
from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy import select

from project.infrastructure.postgres.database import database
from project.infrastructure.postgres.models import Users
from project.resource.auth import verify_password, get_password_hash
from project.schemas.auth import Token, AuthCredential
from project.core.config import settings

auth_routes = APIRouter()
logger = logging.getLogger(__name__)


@auth_routes.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    description="Регистрация нового пользователя"
)
async def register(user: AuthCredential) -> Token:
    logger.debug(f"Попытка регистрации нового пользователя: {user.login}")
    async with database.session() as session:
        # Проверка email
        exists_email = await session.scalar(select(Users).where(Users.email == user.login))
        if exists_email:
            raise HTTPException(409, "Пользователь с такой почтой уже существует")

        # Проверка tg_username
        if user.tg_username:
            exists_tg = await session.scalar(
                select(Users).where(Users.tg_username == user.tg_username)
            )
            if exists_tg:
                raise HTTPException(409, "Этот Telegram username уже занят")

        # Создаем нового пользователя
        db_user = Users(
            first_name=user.first_name,
            surname_name=user.surname_name,
            patronomic_name=user.patronomic_name,
            email=user.login,
            username=user.login,
            password=get_password_hash(user.password),
            tg_username=user.tg_username,  # None ок
            role="user",
            is_admin=False,
            is_tg_subscribed=False,
            theme="light",
            is_push_enabled=False,
        )
        session.add(db_user)
        await session.flush()
        await session.refresh(db_user)

        # Генерируем токен
        token_data = {"sub": db_user.email}
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data.update({"exp": expire})
        access_token = jwt.encode(
            claims=token_data,
            key=settings.SECRET_AUTH_KEY.get_secret_value(),
            algorithm=settings.AUTH_ALGORITHM,
        )

        logger.info(f"Успешно зарегистрирован новый пользователь: {db_user.email}")
        return Token(access_token=access_token, token_type="bearer")


@auth_routes.post(
    "/token",
    response_model=Token,
    description="Авторизация пользователя"
)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    async with database.session() as session:
        result = await session.execute(select(Users).where(Users.email == form_data.username))
        user = result.scalars().first()

        if not user or not verify_password(form_data.password, user.password):
            logger.warning(f"Неудачная попытка входа: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Генерируем токен
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + access_token_expires
        token_data = {"sub": user.email, "exp": expire}
        access_token = jwt.encode(
            claims=token_data,
            key=settings.SECRET_AUTH_KEY.get_secret_value(),
            algorithm=settings.AUTH_ALGORITHM,
        )
        logger.info(f"Пользователь вошел в систему: {user.email}")
        return Token(access_token=access_token, token_type="bearer")
