from typing import Type

from sqlalchemy import select, insert, update, delete, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import InterfaceError

from project.schemas.documents import DocumentCreate, DocumentSchema, DocumentUpdate
from project.infrastructure.postgres.models import Documents
from project.core.exceptions import DocumentNotFound


class DocumentRepository:
    _collection: Type[Documents] = Documents

    async def check_connection(self, session: AsyncSession) -> bool:
        query = select(true())
        try:
            return await session.scalar(query)
        except (Exception, InterfaceError):
            return False

    async def get_document_by_id(self, session: AsyncSession, document_id: int) -> DocumentSchema:
        query = select(self._collection).where(self._collection.document_id == document_id)
        document = await session.scalar(query)
        if not document:
            raise DocumentNotFound(_id=document_id)
        return DocumentSchema.model_validate(obj=document)

    async def get_all_documents(self, session: AsyncSession) -> list[DocumentSchema]:
        query = select(self._collection)
        result = await session.scalars(query)
        return [DocumentSchema.model_validate(obj=doc) for doc in result.all()]

    async def get_documents_by_user(self, session: AsyncSession, user_id: int) -> list[DocumentSchema]:
        query = select(self._collection).where(self._collection.user_id == user_id)
        result = await session.scalars(query)
        return [DocumentSchema.model_validate(obj=doc) for doc in result.all()]

    async def get_documents_by_status(self, session: AsyncSession, status_id: int) -> list[DocumentSchema]:
        query = select(self._collection).where(self._collection.status_id == status_id)
        result = await session.scalars(query)
        return [DocumentSchema.model_validate(obj=doc) for doc in result.all()]

    async def get_document_mistakes(self, session: AsyncSession, document_id: int) -> list[dict]:
        document = await self.get_document_by_id(session, document_id)
        # Предположим, что есть поле mistakes — список словарей
        return getattr(document, "mistakes", [])

    async def get_document_full_info(self, session: AsyncSession, document_id: int) -> DocumentSchema:
        document = await self.get_document_by_id(session, document_id)
        # Предположим, что full_info собирается из документа
        return document

    async def create_document(self, session: AsyncSession, document: DocumentCreate) -> DocumentSchema:
        query = (
            insert(self._collection)
            .values(document.model_dump())
            .returning(self._collection)
        )
        created = await session.scalar(query)
        await session.flush()
        return DocumentSchema.model_validate(obj=created)

    async def update_document(self, session: AsyncSession, document_id: int, document: DocumentUpdate) -> DocumentSchema:
        existing = await session.scalar(
            select(self._collection).where(self._collection.document_id == document_id)
        )
        if not existing:
            raise DocumentNotFound(_id=document_id)

        # Частичное обновление — берём только установленные поля
        update_data = document.model_dump(exclude_unset=True)

        query = (
            update(self._collection)
            .where(self._collection.document_id == document_id)
            .values(**update_data)
            .returning(self._collection)
        )

        updated = await session.scalar(query)
        return DocumentSchema.model_validate(obj=updated)

    async def delete_document(self, session: AsyncSession, document_id: int) -> None:
        query = delete(self._collection).where(self._collection.document_id == document_id)
        result = await session.execute(query)

        if not result.rowcount:
            raise DocumentNotFound(_id=document_id)
