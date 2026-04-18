# backend/src/project/core/gost_service.py
import asyncio
import json
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from project.grpc.client import GostCheckerClient
from project.infrastructure.postgres.repository.gost_check_repo import AsyncGostCheckRepository
from project.infrastructure.postgres.models import Check, Documents, Standart, Status


class GostCheckService:
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db
        self.repository = AsyncGostCheckRepository(db)
        # Создаём клиент gRPC при инициализации сервиса
        self.grpc_client = GostCheckerClient(target="grpc_checker:50051")

    async def start_gost_check(self, document_id: int, standart_id: int | None = None) -> int:
        # Запустить проверку ГОСТ для документа
        check = await self.repository.create_gost_check(document_id, standart_id=standart_id)
        await self._update_document_status(document_id, "Анализируется")
        asyncio.create_task(self._process_gost_check(document_id, check.check_id))
        return check.check_id

    async def _process_gost_check(self, document_id: int, check_id: int):
        # Асинхронная обработка проверки ГОСТ через gRPC
        document = None
        try:
            # Получаем информацию о документе из БД
            result = await self.db.execute(
                select(Documents).where(Documents.document_id == document_id)
            )
            document = result.scalars().first()
            if not document:
                raise ValueError("Документ не найден")

            check_row = await self.db.execute(select(Check).where(Check.check_id == check_id))
            check = check_row.scalars().first()
            if not check:
                raise ValueError("Запись проверки не найдена")

            stand_res = await self.db.execute(
                select(Standart).where(Standart.standart_id == check.standart_id)
            )
            standart = stand_res.scalars().first()
            if not standart:
                raise ValueError("Выбранный ГОСТ не найден")
            if not standart.rules_file:
                raise ValueError(
                    "Для выбранного ГОСТ не настроен файл правил. Выберите другой ГОСТ или обратитесь к администратору."
                )
            rules_file = standart.rules_file

            # Читаем файл в память
            with open(document.filepath, "rb") as f:
                file_content = f.read()

            # ВЫЗОВ gRPC СЕРВИСА
            grpc_response = await self.grpc_client.check_document(
                file_content=file_content,
                file_name=document.filename,
                document_id=str(document_id),
                rules_file=rules_file,
            )

            if not grpc_response.success:
                raise Exception(f"gRPC проверка не удалась: {grpc_response.summary_report}")

            # Преобразуем ответ gRPC
            if grpc_response.summary_report:
                try:
                    report_dict = json.loads(grpc_response.summary_report)
                except (json.JSONDecodeError, TypeError):
                    report_dict = {}
            else:
                report_dict = {}

            report_dict['filename'] = document.filename

            passed = float(report_dict.get('passed_checks', 0))
            total = float(report_dict.get('total_checks', 1)) or 1.0
            raw_score = (passed / total) * 100
            score = int(round(raw_score))

            is_compliant = passed == total

            result_data = {
                'is_compliant': is_compliant,
                'score': score,
                'report': report_dict
            }

            # Сохраняем результат в БД
            await self.repository.update_check_result(check_id, result_data)

            # Сохраняем ошибки и предупреждения
            errors = [
                m.description for m in grpc_response.mistakes
                if m.severity.lower() == "critical"
            ]
            warnings = [
                m.description for m in grpc_response.mistakes
                if m.severity.lower() == "warning"
            ]
            await self.repository.create_mistakes(document_id, errors, warnings)

            new_status = "Идеален" if is_compliant else "Отправлен на доработку"
            await self._update_document_status(document_id, new_status)

        except Exception as e:
            print(f"Ошибка при проверке ГОСТ документа {document_id}: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

            # Дефолтный результат при ошибке
            result_data = {
                'is_compliant': False,
                'score': 0,
                'report': {
                    'results': [],
                    'total_checks': 1,
                    'passed_checks': 0,
                    'filename': document.filename if document else "unknown"
                }
            }
            await self.repository.update_check_result(check_id, result_data)
            await self.repository.create_mistakes(document_id,  [f"Системная ошибка: {str(e)}"], [])
            await self._update_document_status(document_id, "Ошибка")

        finally:
            # Закрываем соединение
            await self.grpc_client.close()

    async def _update_document_status(self, document_id: int, status_name: str):
        # Обновление статуса документа
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
        # Получение результата проверки
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
        is_analyzing = False    # флаг что проверка еще идет

        try:
            if check.result:
                result_data = json.loads(check.result)

            # Проверяем, что проверка еще идет
            if result_data.get('status') == 'analyzing':
                is_analyzing = True
                return {
                    'check_id': int(check.check_id),
                    'document_id': int(check.document_id),
                    'filename': filename,
                    'status': 'Анализируется',
                    'score': '0',
                    'is_compliant': False,
                    'checked_at': check.checked_at.isoformat() if check.checked_at else None,
                    'errors': [],
                    'warnings': [],
                    'details': {},
                    'total_checks': 0,
                    'passed_checks': 0
                }

            report = result_data.get('report', {})
            passed = float(report.get('passed_checks', 0))
            total = float(report.get('total_checks', 0))

            mistakes = await self.repository.get_mistakes(check.document_id)

            if mistakes:
                errors = [m.description for m in mistakes if m.critical_status == "high"]
                warnings = [m.description for m in mistakes if m.critical_status == "low"]
            else:
                # Fallback: берем из report если mistakes пустые
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

        except (json.JSONDecodeError, TypeError) as e:
            print(f"Ошибка парсинга результата проверки {check_id}: {str(e)}")
            errors = ["Ошибка чтения отчёта из БД"]

        score = int(result_data.get('score', 0))
        is_compliant = result_data.get('is_compliant', False)

        return {
            'check_id': int(check.check_id),
            'document_id': int(check.document_id),
            'filename': filename,
            'status': "Идеален" if is_compliant else "Требует доработки",
            'score': str(score),
            'is_compliant': is_compliant,
            'checked_at': check.checked_at.isoformat() if check.checked_at else None,
            'errors': errors,
            'warnings': warnings,
            'details': report,
            'total_checks': int(report.get('total_checks', 0)),
            'passed_checks': int(report.get('passed_checks', 0))
        }