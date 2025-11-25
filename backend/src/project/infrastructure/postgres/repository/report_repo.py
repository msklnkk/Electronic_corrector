from typing import Type, List
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, true
from sqlalchemy.exc import IntegrityError, InterfaceError
from project.schemas.reports import ReportCreate, ReportSchema
from project.infrastructure.postgres.models import Reports
from project.core.exceptions import ReportNotFound, ReportAlreadyExists
from project.infrastructure.postgres.models import Reports, Check, Documents


class ReportRepository:
    _collection: Type[Reports] = Reports

    async def check_connection(self, session: AsyncSession) -> bool:
        query = select(true())
        try:
            return await session.scalar(query)
        except (Exception, InterfaceError):
            return False

    async def get_all_reports(self, session: AsyncSession) -> List[ReportSchema]:
        query = select(self._collection)
        reports = await session.scalars(query)
        return [ReportSchema.model_validate(obj=report) for report in reports.all()]

    async def get_report_by_id(self, session: AsyncSession, report_id: int) -> ReportSchema:
        query = select(self._collection).where(self._collection.report_id == report_id)
        report = await session.scalar(query)
        if not report:
            raise ReportNotFound(_id=report_id)
        return ReportSchema.model_validate(obj=report)

    async def get_reports_by_check_id(self, session: AsyncSession, check_id: int) -> Sequence[Reports]:
        query = select(self._collection).where(self._collection.check_id == check_id)
        reports = await session.scalars(query)
        return reports.all()

    async def create_report(self, session: AsyncSession, report: ReportCreate) -> ReportSchema:
        query = (
            insert(self._collection)
            .values(report.model_dump())
            .returning(self._collection)
        )
        try:
            created_report = await session.scalar(query)
        except IntegrityError:
            raise ReportAlreadyExists(check_id=report.check_id)
        return ReportSchema.model_validate(obj=created_report)

    async def update_report(self, session: AsyncSession, report_id: int, report: ReportCreate) -> ReportSchema:
        # Проверяем существование отчета
        existing_report = await session.scalar(
            select(self._collection).where(self._collection.report_id == report_id)
        )
        if not existing_report:
            raise ReportNotFound(_id=report_id)
        # Если меняем check_id, catch IntegrityError на уровне БД
        query = (
            update(self._collection)
            .where(self._collection.report_id == report_id)
            .values(report.model_dump())
            .returning(self._collection)
        )
        updated_report = await session.scalar(query)
        return ReportSchema.model_validate(obj=updated_report)

    async def delete_report(self, session: AsyncSession, report_id: int) -> None:
        query = delete(self._collection).where(self._collection.report_id == report_id)
        result = await session.execute(query)
        if not result.rowcount:
            raise ReportNotFound(_id=report_id)

    async def get_reports_by_user(self, session: AsyncSession, user_id: int) -> List[ReportSchema]:
        """
        Возвращает все отчёты, относящиеся к документам конкретного пользователя.
        JOIN: reports → checks → documents
        """
        query = (
            select(self._collection)
            .join(Check, Check.check_id == Reports.check_id)
            .join(Documents, Documents.document_id == Check.document_id)
            .where(Documents.user_id == user_id)
        )

        reports = await session.scalars(query)
        return [ReportSchema.model_validate(obj=report) for report in reports.all()]
