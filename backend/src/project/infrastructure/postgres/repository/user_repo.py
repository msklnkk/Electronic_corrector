from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, true
from sqlalchemy.exc import IntegrityError, InterfaceError

from project.schemas.user import UserCreate, UserSchema
from project.infrastructure.postgres.models import Users
from project.core.exceptions import UserNotFound, UserAlreadyExists, UserNameAlreadyExists, UserTelegramAlreadyExists


class UserRepository:
    _collection: Type[Users] = Users

    async def check_connection(self, session: AsyncSession) -> bool:
        query = select(true())
        try:
            return await session.scalar(query)
        except (Exception, InterfaceError):
            return False

    async def get_user_by_email(self, session: AsyncSession, email: str) -> UserSchema:
        query = (select(self._collection).where(self._collection.email == email))
        user = await session.scalar(query)
        if not user:
            raise UserNotFound(_id=email)
        return UserSchema.model_validate(obj=user)

    async def get_all_users(self,session: AsyncSession) -> list[UserSchema]:
        query = select(self._collection)
        users = await session.scalars(query)
        return [UserSchema.model_validate(obj=user) for user in users.all()]

    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> UserSchema:
        query = (select(self._collection).where(self._collection.user_id == user_id))
        user = await session.scalar(query)
        if not user:
            raise UserNotFound(_id=user_id)
        return UserSchema.model_validate(obj=user)

    async def get_user_by_login(self, session: AsyncSession, user_name: str) -> UserSchema | None:
        """Проверка существования пользователя по логину"""
        query = select(self._collection).where(self._collection.username == user_name)
        return await session.scalar(query)

    async def get_user_by_tg_username(self, session: AsyncSession, tg_username: str) -> Users | None:
        """Проверка существования по Telegram username"""
        query = select(self._collection).where(self._collection.tg_username == tg_username)
        return await session.scalar(query)

    async def create_user(self, session: AsyncSession, user: UserCreate) -> UserSchema:
        # Проверяем логин на уникальность
        exists_login = await self.get_user_by_login(session, user_name=user.user_name)
        if exists_login:
            raise UserNameAlreadyExists(login=user.user_name)

        if user.tg_username:
            exists_tg = await self.get_user_by_tg_username(session, user.tg_username)
            if exists_tg:
                raise UserTelegramAlreadyExists(tg_username=user.tg_username)

        query = (
            insert(self._collection)
            .values(user.model_dump())
            .returning(self._collection)
        )
        try:
            created_user = await session.scalar(query)
            await session.flush()
        except IntegrityError:
            raise UserAlreadyExists(mail=user.mail)

        return UserSchema.model_validate(obj=created_user)

    async def update_user(self, session: AsyncSession, user_id: int, user: UserCreate) -> UserSchema:
        # Проверяем существование пользователя
        existing_user = await session.scalar(
            select(self._collection).where(self._collection.user_id == user_id)
        )
        if not existing_user:
            raise UserNotFound(_id=user_id)

        # Проверяем уникальность логина при обновлении
        if user.user_name and user.user_name != existing_user.username:
            exists_login = await self.get_user_by_login(session, user.user_name)
            if exists_login:
                raise UserNameAlreadyExists(login=user.user_name)

        # Проверяем уникальность Telegram username
        if user.tg_username and user.tg_username != existing_user.tg_username:
            exists_tg = await self.get_user_by_tg_username(session, user.tg_username)
            if exists_tg:
                raise UserTelegramAlreadyExists(tg_username=user.tg_username)

        query = (
            update(self._collection)
            .where(self._collection.user_id == user_id)
            .values(user.model_dump())
            .returning(self._collection)
        )

        updated_user = await session.scalar(query)
        return UserSchema.model_validate(obj=updated_user)

    async def delete_user(self, session: AsyncSession, user_id: int) -> None:
        query = delete(self._collection).where(self._collection.user_id == user_id)
        result = await session.execute(query)
        if not result.rowcount:
            raise UserNotFound(_id=user_id)