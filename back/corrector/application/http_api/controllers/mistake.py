from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Literal, List, Optional

from corrector.application.database import get_session
from corrector.application.database.tables import Mistake

router = APIRouter(
    prefix="/mistakes", 
    tags=["mistakes"]
    )

SessionDep = Annotated[Session, Depends(get_session)]
    
class MistakeDb(BaseModel):
    """Ошибочки""" 
    id: int | None = Field(description="Идентификатор", default=None)
    mistake_type_id: int | None = Field(description="Связь с Mistake_Type", default=None)
    description: str = Field(description="Описание ошибки", max_length=255)
    critical_status: Literal["Критично","Замечание"] = Field(description="Статус важности")
    document_id: int | None = Field(description="Связь с Mistake_Type", default=None)
    
class MistakeResponse(BaseModel):
    id: int
    description: str

@router.post(path="",status_code=status.HTTP_204_NO_CONTENT)
async def create_mistake(body: MistakeDb, session: SessionDep):
    """Запрос: создание новой ошибки"""
    new_mistake = Mistake(
        mistake_type_id=body.mistake_type_id,
        description=body.description,
        critical_status=body.critical_status,
        document_id=body.document_id
    )
    session.add(new_mistake)
    session.commit()
    return None

@router.get(path="", response_model=list[MistakeDb])
async def get_mistakes(session: SessionDep):
    """Запрос: получение всех ошибок"""
    return session.scalars(select(Mistake)).all()

@router.get(path="", response_model=list[MistakeDb])
async def get_mistakes_by_document(document_id: int, session: SessionDep):
    """Запрос: получение всех ошибок для определенного документа"""
    document = session.get(document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")
    
    return document.mistakes

@router.delete(path="", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mistake(mistake_id: int, session: SessionDep):
    """Запрос: удаление ошибки"""
    mistake = session.get(Mistake, mistake_id)
    if not mistake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ошибка не найдена")
    
    session.delete(mistake)
    session.commit()
    return None


class MistakeDTO(BaseModel):
    id: int | None = Field(description="Идентификатор", default=None)
    description: str = Field(description="Описание ошибки", max_length=255)
    critical_status: Literal["Критично","Замечание"] = Field(description="Статус важности")