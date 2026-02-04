from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any, Type
from datetime import datetime

from project.infrastructure.postgres.models import Check, Documents, Status, Standart, Mistake, MistakeType

class AsyncGostCheckRepository:
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def create_gost_check(self, document_id: int) -> Check:
        """Создать проверку ГОСТ для документа"""
        gost_standard = await self.get_or_create_gost_standard()

        check = Check(
            document_id=document_id,
            standart_id=gost_standard.standart_id,
            checked_at=datetime.now(),
            result="analyzing"
        )

        self.db.add(check)
        await self.db.commit()
        await self.db.refresh(check)
        return check

    async def get_or_create_gost_standard(self) -> Standart:
        result = await self.db.execute(
            select(Standart).where(Standart.name == "ГОСТ для курсовых работ")
        )
        standard = result.scalars().first()
        if not standard:
            standard = Standart(
                name="ГОСТ для курсовых работ",
                version="1.0",
                description="Автоматическая проверка курсовых работ на соответствие ГОСТ",
                is_custom=False
            )
            self.db.add(standard)
            await self.db.commit()
            await self.db.refresh(standard)
        return standard

    async def update_check_result(self, check_id: int, result: Dict[str, Any]) -> Check:
        res = await self.db.execute(select(Check).where(Check.check_id == check_id))
        check = res.scalars().first()
        if not check:
            raise ValueError(f"Check {check_id} не найден")

        check.result = "perfect" if result.get('is_compliant') else 'needs_revision'
        check.checked_at = datetime.now()

        # Обновляем документ
        doc_res = await self.db.execute(select(Documents).where(Documents.document_id == check.document_id))
        document = doc_res.scalars().first()
        if document:
            document.score = float(result.get('score', 0))
            # Обновляем статус документа
            new_status_name = "Идеален" if result.get('is_compliant') else "Отправлен на доработку"
            status_res = await self.db.execute(select(Status).where(Status.status_name == new_status_name))
            new_status = status_res.scalars().first()
            if new_status:
                document.status_id = new_status.status_id

        await self.db.commit()
        await self.db.refresh(check)
        return check

    async def save_check_details(self, check_id: int, result: Dict[str, Any]):
        # Пока просто пропустим
        pass

    async def create_mistakes(self, document_id: int, errors: List[str], warnings: List[str]):
        # Ошибки
        error_type_res = await self.db.execute(
            select(MistakeType).where(MistakeType.mistake_type_name == "Ошибка ГОСТ")
        )
        error_type = error_type_res.scalars().first()
        if not error_type:
            error_type = MistakeType(mistake_type_name="Ошибка ГОСТ")
            self.db.add(error_type)
            await self.db.commit()
            await self.db.refresh(error_type)

        # Предупреждения
        warning_type_res = await self.db.execute(
            select(MistakeType).where(MistakeType.mistake_type_name == "Предупреждение ГОСТ")
        )
        warning_type = warning_type_res.scalars().first()
        if not warning_type:
            warning_type = MistakeType(mistake_type_name="Предупреждение ГОСТ")
            self.db.add(warning_type)
            await self.db.commit()
            await self.db.refresh(warning_type)

        for error in errors:
            mistake = Mistake(
                document_id=document_id,
                mistake_type_id=error_type.mistake_type_id,
                description=error,
                critical_status="high"
            )
            self.db.add(mistake)

        for warning in warnings:
            mistake = Mistake(
                document_id=document_id,
                mistake_type_id=warning_type.mistake_type_id,
                description=warning,
                critical_status="low"
            )
            self.db.add(mistake)

        await self.db.commit()

    async def get_check_by_id(self, check_id: int) -> Optional[Check]:
        res = await self.db.execute(select(Check).where(Check.check_id == check_id))
        return res.scalars().first()

    async def get_document_checks(self, document_id: int) -> List[Check]:
        res = await self.db.execute(select(Check).where(Check.document_id == document_id))
        return res.scalars().all()
