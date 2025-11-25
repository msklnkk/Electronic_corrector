from typing import Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, true
from sqlalchemy.exc import IntegrityError, InterfaceError
from project.schemas.mistake_type import MistakeTypeCreate, MistakeTypeSchema
from project.infrastructure.postgres.models import MistakeType
from project.core.exceptions import MistakeTypeNotFound, MistakeTypeAlreadyExists


class MistakeTypeRepository:
    _collection: Type[MistakeType] = MistakeType

    async def check_connection(self, session: AsyncSession) -> bool:
        query = select(true())
        try:
            return await session.scalar(query)
        except (Exception, InterfaceError):
            return False

    async def get_all_mistake_types(self, session: AsyncSession) -> list[MistakeTypeSchema]:
        query = select(self._collection)
        mistake_types = await session.scalars(query)
        return [MistakeTypeSchema.model_validate(obj=mt) for mt in mistake_types.all()]

    async def get_mistake_type_by_id(self, session: AsyncSession, mistake_type_id: int) -> MistakeTypeSchema:
        query = select(self._collection).where(self._collection.mistake_type_id == mistake_type_id)
        mistake_type = await session.scalar(query)
        if not mistake_type:
            raise MistakeTypeNotFound(_id=mistake_type_id)
        return MistakeTypeSchema.model_validate(obj=mistake_type)

    async def get_mistake_type_by_name(self, session: AsyncSession, mistake_type_name: str) -> MistakeType | None:
        query = select(self._collection).where(self._collection.mistake_type_name == mistake_type_name)
        return await session.scalar(query)

    async def create_mistake_type(self, session: AsyncSession, mistake_type: MistakeTypeCreate) -> MistakeTypeSchema:
        # Проверяем уникальность mistake_type_name
        exists = await self.get_mistake_type_by_name(session, mistake_type_name=mistake_type.mistake_type_name)
        if exists:
            raise MistakeTypeAlreadyExists(name=mistake_type.mistake_type_name)
        query = (
            insert(self._collection)
            .values(mistake_type.model_dump())
            .returning(self._collection)
        )
        try:
            created_mistake_type = await session.scalar(query)
        except IntegrityError:
            raise MistakeTypeAlreadyExists(name=mistake_type.mistake_type_name)
        return MistakeTypeSchema.model_validate(obj=created_mistake_type)

    async def update_mistake_type(self, session: AsyncSession, mistake_type_id: int,
                                  mistake_type: MistakeTypeCreate) -> MistakeTypeSchema:
        # Проверяем существование типа ошибки
        existing_mistake_type = await session.scalar(
            select(self._collection).where(self._collection.mistake_type_id == mistake_type_id)
        )
        if not existing_mistake_type:
            raise MistakeTypeNotFound(_id=mistake_type_id)
        # Проверяем уникальность mistake_type_name при обновлении
        if mistake_type.mistake_type_name != existing_mistake_type.mistake_type_name:
            exists = await self.get_mistake_type_by_name(session, mistake_type.mistake_type_name)
            if exists:
                raise MistakeTypeAlreadyExists(name=mistake_type.mistake_type_name)
        query = (
            update(self._collection)
            .where(self._collection.mistake_type_id == mistake_type_id)
            .values(mistake_type.model_dump())
            .returning(self._collection)
        )
        updated_mistake_type = await session.scalar(query)
        return MistakeTypeSchema.model_validate(obj=updated_mistake_type)

    async def delete_mistake_type(self, session: AsyncSession, mistake_type_id: int) -> None:
        query = delete(self._collection).where(self._collection.mistake_type_id == mistake_type_id)
        result = await session.execute(query)
        if not result.rowcount:
            raise MistakeTypeNotFound(_id=mistake_type_id)