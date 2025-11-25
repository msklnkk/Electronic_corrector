from typing import Type, List
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, true
from sqlalchemy.exc import IntegrityError, InterfaceError
from project.schemas.mistake import MistakeCreate, MistakeSchema
from project.infrastructure.postgres.models import Mistake
from project.core.exceptions import MistakeNotFound, MistakeAlreadyExists


class MistakeRepository:
    _collection: Type[Mistake] = Mistake

    async def check_connection(self, session: AsyncSession) -> bool:
        query = select(true())
        try:
            return await session.scalar(query)
        except (Exception, InterfaceError):
            return False

    async def get_all_mistakes(self, session: AsyncSession) -> List[MistakeSchema]:
        query = select(self._collection)
        mistakes = await session.scalars(query)
        return [MistakeSchema.model_validate(obj=mistake) for mistake in mistakes.all()]

    async def get_mistake_by_id(self, session: AsyncSession, mistake_id: int) -> MistakeSchema:
        query = select(self._collection).where(self._collection.mistake_id == mistake_id)
        mistake = await session.scalar(query)
        if not mistake:
            raise MistakeNotFound(_id=mistake_id)
        return MistakeSchema.model_validate(obj=mistake)

    async def get_mistakes_by_document_id(self, session: AsyncSession, document_id: int) -> Sequence[Mistake]:
        # Проверка существования ошибок по document_id
        query = select(self._collection).where(self._collection.document_id == document_id)
        mistakes = await session.scalars(query)
        return mistakes.all()

    async def get_mistakes_by_mistake_type_id(self, session: AsyncSession, mistake_type_id: int) -> Sequence[Mistake]:
        # Проверка существования ошибок по mistake_type_id
        query = select(self._collection).where(self._collection.mistake_type_id == mistake_type_id)
        mistakes = await session.scalars(query)
        return mistakes.all()

    async def create_mistake(self, session: AsyncSession, mistake: MistakeCreate) -> MistakeSchema:
        # Проверяем уникальность комбинации document_id и mistake_type_id (если указан)
        if mistake.mistake_type_id is not None:
            existing_mistakes = await self.get_mistakes_by_document_id(session, document_id=mistake.document_id)
            if any(m.mistake_type_id == mistake.mistake_type_id for m in existing_mistakes):
                raise MistakeAlreadyExists(document_id=mistake.document_id, mistake_type_id=mistake.mistake_type_id)
        query = (
            insert(self._collection)
            .values(mistake.model_dump())
            .returning(self._collection)
        )
        try:
            created_mistake = await session.scalar(query)
        except IntegrityError:
            raise MistakeAlreadyExists(document_id=mistake.document_id, mistake_type_id=mistake.mistake_type_id)
        return MistakeSchema.model_validate(obj=created_mistake)

    async def update_mistake(self, session: AsyncSession, mistake_id: int, mistake: MistakeCreate) -> MistakeSchema:
        # Проверяем существование ошибки
        existing_mistake = await session.scalar(
            select(self._collection).where(self._collection.mistake_id == mistake_id)
        )
        if not existing_mistake:
            raise MistakeNotFound(_id=mistake_id)
        # Проверяем уникальность комбинации document_id и mistake_type_id при обновлении (если указан)
        if (mistake.document_id != existing_mistake.document_id or
            mistake.mistake_type_id != existing_mistake.mistake_type_id) and mistake.mistake_type_id is not None:
            existing_mistakes = await self.get_mistakes_by_document_id(session, document_id=mistake.document_id)
            if any(m.mistake_type_id == mistake.mistake_type_id for m in existing_mistakes):
                raise MistakeAlreadyExists(document_id=mistake.document_id, mistake_type_id=mistake.mistake_type_id)
        query = (
            update(self._collection)
            .where(self._collection.mistake_id == mistake_id)
            .values(mistake.model_dump())
            .returning(self._collection)
        )
        updated_mistake = await session.scalar(query)
        return MistakeSchema.model_validate(obj=updated_mistake)

    async def delete_mistake(self, session: AsyncSession, mistake_id: int) -> None:
        query = delete(self._collection).where(self._collection.mistake_id == mistake_id)
        result = await session.execute(query)
        if not result.rowcount:
            raise MistakeNotFound(_id=mistake_id)