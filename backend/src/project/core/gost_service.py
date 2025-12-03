import asyncio
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from project.resource.gost_checker import GostChecker
from project.infrastructure.postgres.repository.gost_check_repo import GostCheckRepository
from project.infrastructure.postgres.models import Documents, Status

class GostCheckService:
    def __init__(self, db: Session):  # Добавляем аннотацию типа
        self.db = db
        self.checker = GostChecker()
        self.repository = GostCheckRepository(db)
    
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
            document = self.db.query(Documents).filter(Documents.document_id == document_id).first()
            if not document:
                return
            
            # Запускаем проверку
            result = await self.checker.check_document(document.filepath, document.filename)
            
            # Сохраняем результат
            await self.repository.update_check_result(check_id, result)
            await self.repository.save_check_details(check_id, result)
            await self.repository.create_mistakes(document_id, result['errors'], result['warnings'])
            
            # Обновляем статус документа
            new_status = "Идеален" if result['is_compliant'] else "Отправлен на доработку"
            await self._update_document_status(document_id, new_status)
            
        except Exception as e:
            # В случае ошибки ставим статус ошибки
            await self._update_document_status(document_id, "Ошибка")
            print(f"Ошибка при проверке ГОСТ документа {document_id}: {str(e)}")
    
    async def _update_document_status(self, document_id: int, status_name: str):
        """Обновить статус документа"""
        status = self.db.query(Status).filter(Status.status_name == status_name).first()
        if not status:
            # Создаем статус если не существует
            status = Status(status_name=status_name)
            self.db.add(status)
            self.db.commit()
            self.db.refresh(status)
        
        document = self.db.query(Documents).filter(Documents.document_id == document_id).first()
        if document:
            document.status_id = status.status_id
            self.db.commit()
    
    async def get_check_result(self, check_id: int) -> Dict[str, Any]:
        """Получить результат проверки"""
        check = await self.repository.get_check_by_id(check_id)
        if not check:
            return {}
        
        return {
            'check_id': check.check_id,
            'document_id': check.document_id,
            'status': check.result,
            'checked_at': check.checked_at
        }