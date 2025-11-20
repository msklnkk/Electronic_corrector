from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Literal

from corrector.application.database import get_session
from corrector.application.database.tables import Status

router = APIRouter(
    prefix="/statuses", 
    tags=["statuses"]
    )

SessionDep = Annotated[Session, Depends(get_session)]

class StatusResponse(BaseModel):
    status_name: Literal[
        "Загружен",
        "Анализируется",
        "Проверен",
        "Отправлен на доработку",
        "Идеален"
    ] = Field(description="Наименование статуса")

class StatusDb(BaseModel):
    """Статус"""
    id: int | None = Field(description="Идентификатор", default=None)
    
    status_name: Literal[
        "Загружен",
        "Анализируется",
        "Проверен",
        "Отправлен на доработку",
        "Идеален"
    ] = Field(description="Наименование статуса")



@router.get(path="", response_model=list[StatusDb])
async def get_statuses(session: SessionDep):
    """Запрос: получение списка статусов"""
    statuses = session.scalars(select(Status)).all()
    return statuses

@router.get("/{status_id}")
async def get_status_name_by_id(status_id: int, session: SessionDep):
    """Запрос: получение наименования статуса по ID"""
    status_obj = session.get(Status, status_id)
    if not status_obj:
        raise HTTPException(404, f"Статус {status_id} не найден")
    return {"status_name": status_obj.status_name}

@router.get("/documents/status/{status_id}")
async def get_documents_by_status(status_id: int, session: SessionDep):
    """Запрос: получение всех документов с определённым статусом"""
    status = session.get(Status, status_id)
    if not status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не найден")
    documents = status.documents
    return documents


