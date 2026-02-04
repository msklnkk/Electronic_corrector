import asyncio
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from project.gost_checker.checker import GOSTDocumentChecker
from project.infrastructure.postgres.repository.gost_check_repo import AsyncGostCheckRepository
from project.infrastructure.postgres.models import Documents, Status

class GostCheckService:
    def __init__(self, db: AsyncSession):  # Добавляем аннотацию типа
        self.db: AsyncSession = db
        self.checker = GOSTDocumentChecker(rules_file="/app/src/project/gost_checker/manual_rules.json")
        self.repository = AsyncGostCheckRepository(db)

    async def start_gost_check(self, document_id: int) -> int:
        """Запустить проверку ГОСТ для документа"""
        # Создаем запись о проверке
        check = await self.repository.create_gost_check(document_id)
        
        # Обновляем статус документа на "Анализируется"
        await self._update_document_status(document_id, "Анализируется")
        
        # Запускаем асинхронную проверку
        asyncio.create_task(self._process_gost_check(document_id, check.check_id))
        
        return check.check_id
    
    async def _process_gost_check(self, document_id: int, check_id: int):
        """Асинхронная обработка проверки ГОСТ"""
        try:
            # Получаем документ
            result = await self.db.execute(
                select(Documents).where(Documents.document_id == document_id)
            )
            document = result.scalars().first()
            if not document:
                return
            
            # Запускаем проверку
            report = await self.checker.check_document(document.filepath, document_id=str(document_id))

            # Адаптируем результат под старый формат (временно, чтобы не ломать БД)
            is_compliant = report.passed_checks == report.total_checks
            score = float(report.passed_checks) / max(1, float(report.total_checks)) * 100

            result_data = {
                'is_compliant': report.passed_checks == report.total_checks,
                'errors': [r.message for r in report.get_failed_results()],
                'warnings': [r.message for r in report.get_warning_issues()],
                'score': score
            }

            # Сохраняем результат
            await self.repository.update_check_result(check_id, result_data)
            await self.repository.save_check_details(check_id, result_data)
            await self.repository.create_mistakes(document_id, result_data['errors'], result_data['warnings'])
            
            # Обновляем статус документа
            new_status = "Идеален" if result['is_compliant'] else "Отправлен на доработку"
            await self._update_document_status(document_id, new_status)
            
        except Exception as e:
            # В случае ошибки ставим статус ошибки
            await self._update_document_status(document_id, "Ошибка")
            print(f"Ошибка при проверке ГОСТ документа {document_id}: {str(e)}")
    
    async def _update_document_status(self, document_id: int, status_name: str):
        """Обновить статус документа"""
        result = await self.db.execute(
            select(Status).where(Status.status_name == status_name)
        )

        status = result.scalars().first()
        if not status:
            # Создаем статус если не существует
            status = Status(status_name=status_name)
            self.db.add(status)
            await self.db.commit()
            await self.db.refresh(status)
        
        result = await self.db.execute(
            select(Documents).where(Documents.document_id == document_id)
        )
        document = result.scalars().first()
        if document:
            document.status_id = status.status_id
            await self.db.commit()

    async def get_check_result(self, check_id: int) -> Dict[str, Any]:
        """Получить результат проверки"""
        check = await self.repository.get_check_by_id(check_id)
        if not check:
            return {}

        # Получаем score из check или из документа
        score = getattr(check, 'score', None)
        if score is None:
            # Получаем из документа
            result = await self.db.execute(
                select(Documents).where(Documents.document_id == check.document_id)
            )
            document = result.scalars().first()
            if document and document.score is not None:
                score = float(document.score)
            else:
                score = 0.0
        else:
            score = float(score)

        # Преобразуем результат в нормальные типы Python
        return {
            'check_id': int(check.check_id),
            'document_id': int(check.document_id),
            'status': str(check.result),
            'checked_at': check.checked_at.isoformat() if check.checked_at else None,
            'score': score,  # float, безопасно для React
            'errors': [],  # можно потом добавить реальные ошибки
            'warnings': []  # можно потом добавить реальные предупреждения
        }
