from typing import Type
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, true
from sqlalchemy.exc import IntegrityError, InterfaceError
from sqlalchemy.orm import joinedload

from project.schemas.check import CheckCreate, CheckSchema
from project.infrastructure.postgres.models import Check
from project.core.exceptions import CheckNotFound, CheckAlreadyExists


class CheckRepository:
    _collection: Type[Check] = Check

    async def check_connection(self, session: AsyncSession) -> bool:
        query = select(true())
        try:
            return await session.scalar(query)
        except (Exception, InterfaceError):
            return False

    async def get_all_checks(self, session: AsyncSession) -> list[CheckSchema]:
        query = select(self._collection)
        checks = await session.scalars(query)
        return [CheckSchema.model_validate(obj=check) for check in checks.all()]

    async def get_check_by_id(self, session: AsyncSession, check_id: int) -> CheckSchema:
        query = select(self._collection).where(self._collection.check_id == check_id)
        check = await session.scalar(query)
        if not check:
            raise CheckNotFound(_id=check_id)
        return CheckSchema.model_validate(obj=check)

    async def get_checks_by_document_id(self, session: AsyncSession, document_id: int) -> Sequence[Check]:
        query = select(self._collection).where(self._collection.document_id == document_id)
        checks = await session.scalars(query)
        return checks.all()

    async def get_checks_by_standart_id(self, session: AsyncSession, standart_id: int) -> Sequence[Check]:
        query = select(self._collection).where(self._collection.standart_id == standart_id)
        checks = await session.scalars(query)
        return checks.all()

    async def create_check(self, session: AsyncSession, check: CheckCreate) -> CheckSchema:
        # Проверяем уникальность комбинации document_id и standart_id
        existing_checks = await self.get_checks_by_document_id(session, document_id=check.document_id)
        if any(c.standart_id == check.standart_id for c in existing_checks):
            raise CheckAlreadyExists(document_id=check.document_id, standart_id=check.standart_id)
        query = (
            insert(self._collection)
            .values(check.model_dump())
            .returning(self._collection)
        )
        try:
            created_check = await session.scalar(query)
        except IntegrityError:
            raise CheckAlreadyExists(document_id=check.document_id, standart_id=check.standart_id)
        return CheckSchema.model_validate(obj=created_check)

    async def update_check(self, session: AsyncSession, check_id: int, check: CheckCreate) -> CheckSchema:
        # Проверяем существование проверки
        existing_check = await session.scalar(
            select(self._collection).where(self._collection.check_id == check_id)
        )
        if not existing_check:
            raise CheckNotFound(_id=check_id)
        # Проверяем уникальность комбинации document_id и standart_id при обновлении
        if check.document_id != existing_check.document_id or check.standart_id != existing_check.standart_id:
            existing_checks = await self.get_checks_by_document_id(session, document_id=check.document_id)
            if any(c.standart_id == check.standart_id for c in existing_checks):
                raise CheckAlreadyExists(document_id=check.document_id, standart_id=check.standart_id)
        query = (
            update(self._collection)
            .where(self._collection.check_id == check_id)
            .values(check.model_dump())
            .returning(self._collection)
        )
        updated_check = await session.scalar(query)
        return CheckSchema.model_validate(obj=updated_check)

    async def delete_check(self, session: AsyncSession, check_id: int) -> None:
        query = delete(self._collection).where(self._collection.check_id == check_id)
        result = await session.execute(query)
        if not result.rowcount:
            raise CheckNotFound(_id=check_id)

    async def get_checks_by_user_id(self, session: AsyncSession, user_id: int) -> list[CheckSchema]:
        query = (
            select(self._collection)
            .join(self._collection.document)
            .where(self._collection.document.has(user_id=user_id))
            .options(joinedload(self._collection.document))
        )
        checks = await session.scalars(query)
        return [CheckSchema.model_validate(obj=check) for check in checks.all()]
