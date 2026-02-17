import asyncio
import json
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from project.gost_checker import RuleSeverity
from project.gost_checker.checker import GOSTDocumentChecker
from project.infrastructure.postgres.repository.gost_check_repo import AsyncGostCheckRepository
from project.infrastructure.postgres.models import Documents, Status


class GostCheckService:
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db
        self.checker = GOSTDocumentChecker(
            rules_file="/app/src/project/gost_checker/manual_rules.json"
        )
        self.repository = AsyncGostCheckRepository(db)

    async def start_gost_check(self, document_id: int) -> int:
        """Запустить проверку ГОСТ для документа"""
        check = await self.repository.create_gost_check(document_id)
        await self._update_document_status(document_id, "Анализируется")
        asyncio.create_task(self._process_gost_check(document_id, check.check_id))
        return check.check_id

    async def _process_gost_check(self, document_id: int, check_id: int):
        """Асинхронная обработка проверки ГОСТ"""
        document = None
        try:
            result = await self.db.execute(
                select(Documents).where(Documents.document_id == document_id)
            )
            document = result.scalars().first()
            if not document:
                raise ValueError("Документ не найден")

            report = await self.checker.check_document(
                file_path=document.filepath,
                document_id=str(document_id),
                original_filename=document.filename
            )

            # Получаем отчёт и приводим все числовые поля к float/int
            report_dict = report.to_dict()
            report_dict['filename'] = document.filename
            report_dict['passed_checks'] = float(report_dict.get('passed_checks', 0))
            report_dict['total_checks'] = float(report_dict.get('total_checks', 0))

            passed = report_dict['passed_checks']
            total = report_dict['total_checks'] if report_dict['total_checks'] != 0 else 1.0
            raw_score = (passed / total) * 100
            score = int(round(raw_score))

            is_compliant = passed == total

            result_data = {
                'is_compliant': is_compliant,
                'score': score,
                'report': report_dict
            }

            # Сохраняем JSON отчёт и обновляем score в документе
            await self.repository.update_check_result(check_id, result_data)

            # Сохраняем ошибки и предупреждения
            errors = [
                r.message for r in report.get_failed_results()
                if r.severity == RuleSeverity.CRITICAL
            ]
            warnings = [r.message for r in report.get_warning_issues()]
            await self.repository.create_mistakes(document_id, errors, warnings)

            new_status = "Идеален" if is_compliant else "Отправлен на доработку"
            await self._update_document_status(document_id, new_status)

        except Exception as e:
            print(f"Ошибка при проверке ГОСТ документа {document_id}: {str(e)}")
            # Дефолтный результат при ошибке
            result_data = {
                'is_compliant': False,
                'score': 0,
                'report': {
                    'results': [{'message': f'Системная ошибка: {str(e)}', 'severity': 'critical'}],
                    'total_checks': 1,
                    'passed_checks': 0,
                    'filename': document.filename if document else "unknown"
                }
            }
            await self.repository.update_check_result(check_id, result_data)
            await self.repository.create_mistakes(document_id, [str(e)], [])
            await self._update_document_status(document_id, "Ошибка")

    async def _update_document_status(self, document_id: int, status_name: str):
        result = await self.db.execute(select(Status).where(Status.status_name == status_name))
        status_obj = result.scalars().first()
        if not status_obj:
            status_obj = Status(status_name=status_name)
            self.db.add(status_obj)
            await self.db.commit()
            await self.db.refresh(status_obj)

        result = await self.db.execute(select(Documents).where(Documents.document_id == document_id))
        document = result.scalars().first()
        if document:
            document.status_id = status_obj.status_id
            await self.db.commit()

    async def get_check_result(self, check_id: int) -> Dict[str, Any]:
        check = await self.repository.get_check_by_id(check_id)
        if not check:
            return {}

        result = await self.db.execute(select(Documents).where(Documents.document_id == check.document_id))
        document = result.scalars().first()
        filename = document.filename if document else "unknown"

        result_data = {}
        report = {}
        errors = []
        warnings = []

        try:
            if check.result:
                result_data = json.loads(check.result)
            report = result_data.get('report', {})
            # Приводим все числовые поля к float/int
            report['passed_checks'] = float(report.get('passed_checks', 0))
            report['total_checks'] = float(report.get('total_checks', 0))
            errors = [
                r.get('message', 'Неизвестная ошибка')
                for r in report.get('results', [])
                if r.get('severity') == 'critical'
            ]
            warnings = [
                r.get('message', 'Неизвестное замечание')
                for r in report.get('results', [])
                if r.get('severity') == 'warning'
            ]
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга результата проверки {check_id}: {str(e)}")
            errors = ["Ошибка чтения отчёта из БД"]

        score = result_data.get('score', 0)
        if document and document.score is not None:
            score = float(document.score)

        return {
            'check_id': int(check.check_id),
            'document_id': int(check.document_id),
            'filename': filename,
            'status': "Идеален" if result_data.get('is_compliant') else "Требует доработки",
            'score': score,
            'checked_at': check.checked_at.isoformat() if check.checked_at else None,
            'errors': errors,
            'warnings': warnings,
            'is_compliant': result_data.get('is_compliant', False),
            'total_checks': report.get('total_checks', 0),
            'passed_checks': report.get('passed_checks', 0)
        }
