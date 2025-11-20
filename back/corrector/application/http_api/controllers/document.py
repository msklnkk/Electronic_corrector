from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import date, time
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import Literal, List, Optional

from corrector.application.database import get_session
from corrector.application.database.tables import Document, Status, Mistake, User
from corrector.application.http_api.controllers.mistake import MistakeDTO
from corrector.application.http_api.controllers.status import StatusResponse

router = APIRouter(
    prefix="/documents", 
    tags=["documents"]
)

SessionDep = Annotated[Session, Depends(get_session)]

# Кастомный тип для Decimal без ограничений
class AnyDecimal(Decimal):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.any_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x) if x is not None else None
            )
        )

    @classmethod
    def validate(cls, value):
        if isinstance(value, Decimal):
            return value
        elif isinstance(value, (int, float, str)):
            return Decimal(str(value))
        else:
            raise ValueError("Invalid decimal value")

class DocumentFullInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    file_name: str = Field(description="Имя файла")
    user_name: str = Field(description="Имя пользователя")
    status: StatusResponse = Field(description="Статус документа")
    mistakes: List[MistakeDTO] = Field(description="Ошибки документа")
    upload_date: date = Field(description="Дата загрузки")
    upload_time: time = Field(description="Время загрузки")
    score: float = Field(description="Оценка документа")

class DocumentBase(BaseModel):
    file_name: str = Field(description="Имя файла", max_length=255)
    status: StatusResponse

class DocumentDb(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: int | None = Field(description="Идентификатор", default=None)
    file_name: str = Field(description="Имя файла", max_length=255)
    upload_date: date = Field(description="Дата загрузки")
    upload_time: time = Field(description="Время загрузки")
    size: AnyDecimal = Field(description="Размер в МБ")
    report_pdf_path: str = Field(description="Путь к отчёту")
    score: AnyDecimal = Field(description="Оценка")
    analysis_time: AnyDecimal = Field(description="Время анализа")
    user_id: int = Field(description="ID пользователя")
    status_id: int = Field(description="ID статуса")

class DocumentCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    file_name: str = Field(description="Имя файла", max_length=255)
    upload_date: date = Field(description="Дата загрузки")
    upload_time: time = Field(description="Время загрузки")
    size: AnyDecimal = Field(description="Размер в МБ")
    report_pdf_path: str = Field(description="Путь к отчёту")
    score: AnyDecimal = Field(description="Оценка")
    analysis_time: AnyDecimal = Field(description="Время анализа")
    user_id: int = Field(description="ID пользователя")
    status_id: int = Field(description="ID статуса")

class DocumentUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    file_name: str | None = Field(None, description="Имя файла", max_length=255)
    upload_date: date | None = Field(None, description="Дата загрузки")
    upload_time: time | None = Field(None, description="Время загрузки")
    size: AnyDecimal | None = Field(None, description="Размер в МБ")
    report_pdf_path: str | None = Field(None, description="Путь к отчёту")
    score: AnyDecimal | None = Field(None, description="Оценка")
    analysis_time: AnyDecimal | None = Field(None, description="Время анализа")
    user_id: int | None = Field(None, description="ID пользователя")
    status_id: int | None = Field(None, description="ID статуса")

class DocumentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    
    id: int = Field(description="Идентификатор")
    file_name: str = Field(description="Имя файла", max_length=255)
    status: StatusResponse
    mistakes: List[MistakeDTO] = []
    user_id: int = Field(description="ID пользователя")
    upload_date: date = Field(description="Дата загрузки")
    upload_time: time = Field(description="Время загрузки")
    size: AnyDecimal = Field(description="Размер в МБ")
    score: AnyDecimal = Field(description="Оценка")
    analysis_time: AnyDecimal = Field(description="Время анализа")
    report_pdf_path: str = Field(description="Путь к отчёту")

class DocumentWithUser(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: int = Field(description="Идентификатор")
    file_name: str = Field(description="Имя файла", max_length=255)
    upload_date: date = Field(description="Дата загрузки")
    upload_time: time = Field(description="Время загрузки")
    size: AnyDecimal = Field(description="Размер в МБ")
    score: AnyDecimal = Field(description="Оценка")
    analysis_time: AnyDecimal = Field(description="Время анализа")
    user_id: int = Field(description="ID пользователя")
    user_name: str = Field(description="Имя пользователя")
    status_name: str = Field(description="Название статуса")

class DocumentDbSimple(BaseModel):
    id: int | None = Field(description="Идентификатор", default=None)
    file_name: str = Field(description="Имя файла", max_length=255)
    upload_date: date = Field(description="Дата загрузки")
    upload_time: time = Field(description="Время загрузки")
    size: float = Field(description="Размер в МБ")
    report_pdf_path: str = Field(description="Путь к отчёту")
    score: float = Field(description="Оценка")
    analysis_time: float = Field(description="Время анализа")
    user_id: int = Field(description="ID пользователя")
    status_id: int = Field(description="ID статуса")

@router.get("", response_model=list[DocumentDbSimple])
async def get_documents(session: SessionDep):
    """Запрос: получение списка документов"""
    documents = session.scalars(select(Document)).all()
    return documents

@router.get("/{document_id}", response_model=DocumentDTO)
async def get_document_by_id(document_id: int, session: SessionDep):
    """Запрос: получение документа с его статусом и ошибками"""
    document = session.execute(
        select(Document)
        .options(joinedload(Document.status), joinedload(Document.mistakes))
        .filter(Document.id == document_id)
    ).scalar()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Документ не найден"
        )
    
    return document

@router.post("", response_model=DocumentDbSimple)
async def create_document(document_data: DocumentCreate, session: SessionDep):
    """Запрос: создание нового документа"""
    user = session.get(User, document_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    status_obj = session.get(Status, document_data.status_id)
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статус не найден"
        )
    existing_document = session.scalar(
        select(Document).where(Document.file_name == document_data.file_name)
    )
    if existing_document:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Документ с таким именем файла уже существует"
        )
    new_document = Document(
        file_name=document_data.file_name,
        upload_date=document_data.upload_date,
        upload_time=document_data.upload_time,
        size=document_data.size,
        report_pdf_path=document_data.report_pdf_path,
        score=document_data.score,
        analysis_time=document_data.analysis_time,
        user_id=document_data.user_id,
        status_id=document_data.status_id
    )
    
    session.add(new_document)
    session.commit()
    session.refresh(new_document)
    
    return new_document

@router.put("/{document_id}", response_model=DocumentDbSimple)
async def update_document(document_id: int, document_data: DocumentUpdate, session: SessionDep):
    """Запрос: обновление документа"""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Документ не найден"
        )
    if document_data.file_name and document_data.file_name != document.file_name:
        existing_document = session.scalar(
            select(Document).where(Document.file_name == document_data.file_name)
        )
        if existing_document:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Документ с таким именем файла уже существует"
            )
    if document_data.user_id and document_data.user_id != document.user_id:
        user = session.get(User, document_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
    if document_data.status_id and document_data.status_id != document.status_id:
        status_obj = session.get(Status, document_data.status_id)
        if not status_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Статус не найден"
            )
    update_data = document_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    session.commit()
    session.refresh(document)
    
    return document

@router.delete("/{document_id}")
async def delete_document(document_id: int, session: SessionDep):
    """Запрос: удаление документа"""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Документ не найден"
        )
    
    session.delete(document)
    session.commit()
    
    return {"message": "Документ успешно удален"}

@router.get("/user/{user_id}", response_model=list[DocumentDbSimple])
async def get_user_documents(user_id: int, session: SessionDep):
    """Запрос: получение всех документов пользователя"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    documents = session.scalars(
        select(Document).where(Document.user_id == user_id)
    ).all()
    
    return documents

@router.get("/status/{status_id}", response_model=list[DocumentDbSimple])
async def get_documents_by_status(status_id: int, session: SessionDep):
    """Запрос: получение документов по статусу"""
    status_obj = session.get(Status, status_id)
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статус не найден"
        )
    
    documents = session.scalars(
        select(Document).where(Document.status_id == status_id)
    ).all()
    
    return documents


@router.get("mistakes", response_model=list[MistakeDTO])
async def get_document_mistakes(document_id: int, session: SessionDep):
    """Запрос: получение ошибок документа"""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Документ не найден"
        )
    
    mistakes = session.scalars(
        select(Mistake).where(Mistake.document_id == document_id)
    ).all()
    
    return mistakes

@router.get("full-info-optimized", response_model=DocumentFullInfo)
async def get_document_full_info_optimized(document_id: int, session: SessionDep):
    """Запрос: получение полной информации о документе (оптимизированная версия)"""
    result = session.execute(
        select(
            Document.file_name,
            User.first_name.label('user_name'),
            Status,
            Document.upload_date,
            Document.upload_time,
            Document.score
        )
        .join(User, Document.user_id == User.id)
        .join(Status, Document.status_id == Status.id)
        .filter(Document.id == document_id)
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Документ не найден"
        )
    mistakes = session.scalars(
        select(Mistake)
        .where(Mistake.document_id == document_id)
    ).all()
    
    return {
        "file_name": result.file_name,
        "user_name": result.user_name,
        "status": result.Status,
        "mistakes": mistakes,
        "upload_date": result.upload_date,
        "upload_time": result.upload_time,
        "score": float(result.score) if result.score else 0.0
    }
