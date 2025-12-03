from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from project.infrastructure.postgres.models import Check, Documents, Status, Standart, Mistake, MistakeType

class GostCheckRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_gost_check(self, document_id: int) -> Check:
        """Создать проверку ГОСТ для документа"""
        # Получаем или создаем стандарт ГОСТ
        gost_standard = await self.get_or_create_gost_standard()
        
        # Создаем запись о проверке
        check = Check(
            document_id=document_id,
            standart_id=gost_standard.standart_id,
            checked_at=datetime.now(),
            result="analyzing"
        )
        
        self.db.add(check)
        self.db.commit()
        self.db.refresh(check)
        return check
    
    async def get_or_create_gost_standard(self) -> Standart:
        """Получить или создать стандарт ГОСТ"""
        standard = self.db.query(Standart).filter(Standart.name == "ГОСТ для курсовых работ").first()
        
        if not standard:
            standard = Standart(
                name="ГОСТ для курсовых работ",
                version="1.0",
                description="Автоматическая проверка курсовых работ на соответствие ГОСТ",
                is_custom=False
            )
            self.db.add(standard)
            self.db.commit()
            self.db.refresh(standard)
        
        return standard
    
    async def update_check_result(self, check_id: int, result: Dict[str, Any]) -> Check:
        """Обновить результат проверки"""
        check = self.db.query(Check).filter(Check.check_id == check_id).first()
        
        if check:
            check.result = "perfect" if result['is_compliant'] else 'needs_revision'
            check.checked_at = datetime.now()
            
            # Обновляем документ
            document = self.db.query(Documents).filter(Documents.document_id == check.document_id).first()
            if document:
                document.score = result['score']
                
                # Обновляем статус документа
                new_status_name = "Идеален" if result['is_compliant'] else "Отправлен на доработку"
                new_status = self.db.query(Status).filter(Status.status_name == new_status_name).first()
                
                if new_status:
                    document.status_id = new_status.status_id
            
            self.db.commit()
            self.db.refresh(check)
        
        return check
    
    async def save_check_details(self, check_id: int, result: Dict[str, Any]):
        """Сохранить детали проверки в отчет"""
        # Здесь можно сохранить детальный отчет в таблицу Reports
        # Пока просто пропустим
        pass
    
    async def create_mistakes(self, document_id: int, errors: List[str], warnings: List[str]):
        """Создать записи об ошибках и предупреждениях"""
        # Создаем тип ошибки если не существует
        error_type = self.db.query(MistakeType).filter(MistakeType.mistake_type_name == "Ошибка ГОСТ").first()
        if not error_type:
            error_type = MistakeType(mistake_type_name="Ошибка ГОСТ")
            self.db.add(error_type)
            self.db.commit()
            self.db.refresh(error_type)
        
        # Создаем тип предупреждения если не существует
        warning_type = self.db.query(MistakeType).filter(MistakeType.mistake_type_name == "Предупреждение ГОСТ").first()
        if not warning_type:
            warning_type = MistakeType(mistake_type_name="Предупреждение ГОСТ")
            self.db.add(warning_type)
            self.db.commit()
            self.db.refresh(warning_type)
        
        # Создаем ошибки
        for error in errors:
            mistake = Mistake(
                document_id=document_id,
                mistake_type_id=error_type.mistake_type_id,
                description=error,
                critical_status="high"
            )
            self.db.add(mistake)
        
        # Создаем предупреждения
        for warning in warnings:
            mistake = Mistake(
                document_id=document_id,
                mistake_type_id=warning_type.mistake_type_id,
                description=warning,
                critical_status="low"
            )
            self.db.add(mistake)
        
        self.db.commit()
    
    async def get_check_by_id(self, check_id: int) -> Optional[Check]:
        """Получить проверку по ID"""
        return self.db.query(Check).filter(Check.check_id == check_id).first()
    
    async def get_document_checks(self, document_id: int) -> List[Check]:
        """Получить все проверки документа"""
        return self.db.query(Check).filter(Check.document_id == document_id).all()