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
        document = None  # Инициализируем заранее
        try:
            document_stmt = select(Documents).where(Documents.document_id == document_id)
            # Получаем документ
            result = await self.db.execute(document_stmt)
            document = result.scalars().first()
            if not document:
                raise ValueError("Документ не найден")

            # Передаём filename для отчёта и логирования
            report = await self.checker.check_document(
                file_path=document.filepath,
                document_id=str(document_id),
                original_filename=document.filename
            )

            # Подготавливаем данные для сохранения (полный отчёт!)
            report_dict = report.to_dict()
            # Добавляем filename явно
            report_dict['filename'] = document.filename

            # Адаптируем результат под старый формат (временно, чтобы не ломать БД)
            is_compliant = report.passed_checks == report.total_checks
            score = float(report.passed_checks) / max(1, report.total_checks) * 100 if report.total_checks > 0 else 0.0

            result_data = {
                'is_compliant': is_compliant,
                'score': score,
                'report': report_dict
            }

            # Сохраняем полный JSON отчёт
            await self.repository.update_check_result(check_id, result_data)

            # Сохраняем ошибки/предупреждения как отдельные записи
            errors = [r.message for r in report.get_failed_results() if r.severity == RuleSeverity.CRITICAL]
            warnings = [r.message for r in report.get_warning_issues()]
            await self.repository.create_mistakes(document_id, errors, warnings)

            # Статус
            new_status = "Идеален" if is_compliant else "Отправлен на доработку"
            await self._update_document_status(document_id, new_status)

        except Exception as e:
            print(f"Ошибка при проверке ГОСТ документа {document_id}: {str(e)}")
            # Фикс: дефолтный result_data в случае ошибки
            result_data = {
                'is_compliant': False,
                'score': 0.0,
                'report': {
                    'results': [{'message': f'Системная ошибка: {str(e)}', 'severity': 'critical'}],
                    'total_checks': 1,
                    'passed_checks': 0,
                    'filename': document.filename if document else "unknown"
                }
            }
            await self.repository.update_check_result(check_id, result_data)
            errors = [str(e)]
            warnings = []
            await self.repository.create_mistakes(document_id, errors, warnings)
            await self._update_document_status(document_id, "Ошибка")

    async def _update_document_status(self, document_id: int, status_name: str):
        """Обновить статус документа"""
        status_stmt = select(Status).where(Status.status_name == status_name)
        result = await self.db.execute(status_stmt)
        status_obj = result.scalars().first()

        if not status_obj:
            status_obj = Status(status_name=status_name)
            self.db.add(status_obj)
            await self.db.commit()
            await self.db.refresh(status_obj)

        doc_stmt = select(Documents).where(Documents.document_id == document_id)
        result = await self.db.execute(doc_stmt)
        document = result.scalars().first()
        if document:
            document.status_id = status_obj.status_id
            await self.db.commit()

    async def get_check_result(self, check_id: int) -> Dict[str, Any]:
        """Получить результат проверки"""
        check = await self.repository.get_check_by_id(check_id)
        if not check:
            return {}

        # Получаем score из check или из документа
        doc_stmt = select(Documents).where(Documents.document_id == check.document_id)
        result = await self.db.execute(doc_stmt)
        document = result.scalars().first()

        filename = document.filename if document else "unknown"

        result_data = {}
        report = {}
        errors = []
        warnings = []

        # Парсим полный отчёт из check.result (теперь JSON)
        try:
            if check.result:
                result_data = json.loads(check.result)
            else:
                result_data = {}  # Пустой, если result None
            report = result_data.get('report', {})
            errors = [r['message'] for r in report.get('results', []) if
                      not r['is_passed'] and r['severity'] == 'critical']
            warnings = [r['message'] for r in report.get('results', []) if
                        not r['is_passed'] and r['severity'] == 'warning']
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга результата проверки {check_id}: {str(e)}")
            # Можно добавить дефолтный отчёт или ошибку
            errors = ["Ошибка чтения отчёта из БД"]
            warnings = []

        score = result_data.get('score', 0.0)
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