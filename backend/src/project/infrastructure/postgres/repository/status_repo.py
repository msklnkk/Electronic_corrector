from typing import Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, true
from sqlalchemy.exc import IntegrityError, InterfaceError
from project.schemas.status import StatusCreate, StatusSchema
from project.infrastructure.postgres.models import Status
from project.core.exceptions import StatusNotFound, StatusAlreadyExists


class StatusRepository:
    _collection: Type[Status] = Status

    async def check_connection(self, session: AsyncSession) -> bool:
        query = select(true())
        try:
            return await session.scalar(query)
        except (Exception, InterfaceError):
            return False

    async def get_all_statuses(self, session: AsyncSession) -> list[StatusSchema]:
        query = select(self._collection)
        statuses = await session.scalars(query)
        return [StatusSchema.model_validate(obj=status) for status in statuses.all()]

    async def get_status_by_id(self, session: AsyncSession, status_id: int) -> StatusSchema:
        query = select(self._collection).where(self._collection.status_id == status_id)
        status = await session.scalar(query)
        if not status:
            raise StatusNotFound(_id=status_id)
        return StatusSchema.model_validate(obj=status)

    async def get_status_by_name(self, session: AsyncSession, status_name: str) -> Status | None:
        query = select(self._collection).where(self._collection.status_name == status_name)
        return await session.scalar(query)

    async def create_status(self, session: AsyncSession, status: StatusCreate) -> StatusSchema:
        # Проверяем уникальность status_name
        exists = await self.get_status_by_name(session, status_name=status.status_name)
        if exists:
            raise StatusAlreadyExists(name=status.status_name)
        query = (
            insert(self._collection)
            .values(status.model_dump())
            .returning(self._collection)
        )
        try:
            created_status = await session.scalar(query)
        except IntegrityError:
            raise StatusAlreadyExists(name=status.status_name)
        return StatusSchema.model_validate(obj=created_status)

    async def update_status(self, session: AsyncSession, status_id: int, status: StatusCreate) -> StatusSchema:
        # Проверяем существование статуса
        existing_status = await session.scalar(
            select(self._collection).where(self._collection.status_id == status_id)
        )
        if not existing_status:
            raise StatusNotFound(_id=status_id)
        # Проверяем уникальность status_name при обновлении
        if status.status_name != existing_status.status_name:
            exists = await self.get_status_by_name(session, status.status_name)
            if exists:
                raise StatusAlreadyExists(name=status.status_name)
        query = (
            update(self._collection)
            .where(self._collection.status_id == status_id)
            .values(status.model_dump())
            .returning(self._collection)
        )
        updated_status = await session.scalar(query)
        return StatusSchema.model_validate(obj=updated_status)

    async def delete_status(self, session: AsyncSession, status_id: int) -> None:
        query = delete(self._collection).where(self._collection.status_id == status_id)
        result = await session.execute(query)
        if not result.rowcount:
            raise StatusNotFound(_id=status_id)