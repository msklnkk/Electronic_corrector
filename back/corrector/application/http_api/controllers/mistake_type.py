from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Literal, List, Optional

from corrector.application.database import get_session
from corrector.application.database.tables import MistakeType

router = APIRouter(
    prefix="/mistake_types", 
    tags=["mistake_types"]
    )

SessionDep = Annotated[Session, Depends(get_session)]
    
class MistakeTypeDb(BaseModel):
    """Типы ошибок"""
    id: int | None = Field(description="Идентификатор", default=None)
    mistake_type_name:Literal[
        "Шрифт", 
       "Отступы",
       "Структура",
       "Подписи иллюстраций",
       "Таблицы",
       "Ссылки",
       "Нумерация",
       "Абзацы",
       "Заголовки",
       "Формулы",
       "Списки",
       "Колонтитулы",
       "Приложения",
       "Титульный лист",
       "Общий формат"
        ] = Field(description="Наименование типа ошибки")
    
@router.get(path="", response_model=list[MistakeTypeDb])
async def get_mistake_types(session: SessionDep):
    """Запрос: получение всех типов ошибок"""
    mistake_types = session.query(MistakeType).all()
    return mistake_types

@router.get("/{mistake_type_id}")
async def get_mistake_type_by_id(mistake_type_id: int, session: SessionDep):
    """Запрос: получение типа ошибки по ID"""
    mistake_type = session.get(MistakeType, mistake_type_id)
    if not mistake_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MistakeType not found")
    return {"mistake_type_name": mistake_type.mistake_type_name}
 
 