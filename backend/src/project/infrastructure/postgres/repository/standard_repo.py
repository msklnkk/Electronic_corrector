from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, true
from sqlalchemy.exc import IntegrityError, InterfaceError

from project.infrastructure.postgres.models import Standart
from project.schemas.standart import StandardCreate, StandardSchema
from project.core.exceptions import StandardNotFound, StandardAlreadyExists


class StandardRepository:
    _collection: Type[Standart] = Standart

    async def check_connection(self, session: AsyncSession) -> bool:
        query = select(true())
        try:
            return await session.scalar(query)
        except (Exception, InterfaceError):
            return False

    async def get_standard_by_id(self, session: AsyncSession, standart_id: int) -> StandardSchema:
        query = select(self._collection).where(self._collection.standart_id == standart_id)
        standard = await session.scalar(query)
        if not standard:
            raise StandardNotFound(_id=standart_id)
        return StandardSchema.model_validate(obj=standard)

    async def get_all_standards(self, session: AsyncSession) -> list[StandardSchema]:
        query = select(self._collection)
        standards = await session.scalars(query)
        return [StandardSchema.model_validate(obj=std) for std in standards.all()]

    async def get_standard_by_name_version(
        self,
        session: AsyncSession,
        name: str,
        version: str | None
    ) -> Standart | None:
        """Проверка уникальности стандарта name+version"""
        query = select(self._collection).where(
            self._collection.name == name,
            self._collection.version == version
        )
        return await session.scalar(query)

    async def create_standard(self, session: AsyncSession, standard: StandardCreate) -> StandardSchema:
        # Проверяем уникальность name+version
        exists = await self.get_standard_by_name_version(
            session,
            standard.name,
            standard.version,
        )
        if exists:
            raise StandardAlreadyExists(name=standard.name, version=standard.version)

        query = (
            insert(self._collection)
            .values(standard.model_dump())
            .returning(self._collection)
        )
        try:
            created_standard = await session.scalar(query)
            await session.flush()
        except IntegrityError:
            raise StandardAlreadyExists(name=standard.name, version=standard.version)

        return StandardSchema.model_validate(obj=created_standard)

    async def update_standard(
        self,
        session: AsyncSession,
        standart_id: int,
        standard: StandardCreate
    ) -> StandardSchema:

        existing = await session.scalar(
            select(self._collection).where(self._collection.standart_id == standart_id)
        )
        if not existing:
            raise StandardNotFound(_id=standart_id)

        # Проверяем уникальность name+version (если меняются)
        if (
            (standard.name != existing.name) or
            (standard.version != existing.version)
        ):
            exists = await self.get_standard_by_name_version(
                session,
                standard.name,
                standard.version
            )
            if exists:
                raise StandardAlreadyExists(name=standard.name, version=standard.version)

        query = (
            update(self._collection)
            .where(self._collection.standart_id == standart_id)
            .values(standard.model_dump())
            .returning(self._collection)
        )

        updated_standard = await session.scalar(query)
        return StandardSchema.model_validate(obj=updated_standard)

    async def delete_standard(self, session: AsyncSession, standart_id: int) -> None:
        query = delete(self._collection).where(self._collection.standart_id == standart_id)
        result = await session.execute(query)

        if not result.rowcount:
            raise StandardNotFound(_id=standart_id)
