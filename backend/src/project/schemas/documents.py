from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DocumentBase(BaseModel):
    user_id: int
    filename: str
    filepath: str
    upload_datetime: datetime
    doc_type: str
    is_example: bool = False
    size: Decimal
    status_id: int
    report_pdf_path: str
    score: Decimal
    analysis_time: Decimal

class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    filepath: Optional[str] = None
    doc_type: Optional[str] = None
    is_example: Optional[bool] = None
    size: Optional[Decimal] = None
    status_id: Optional[int] = None
    report_pdf_path: Optional[str] = None
    score: Optional[Decimal] = None
    analysis_time: Optional[Decimal] = None
    upload_datetime: Optional[datetime] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentSchema(DocumentBase):
    document_id: int
    model_config = ConfigDict(from_attributes=True)

# Новые схемы для загрузки файлов
class FileUploadResponse(BaseModel):
    filename: str
    saved_filename: str
    file_path: str
    file_size: int
    content_type: Optional[str] = None
    document_id: Optional[int] = None
    message: str

class FileInfo(BaseModel):
    filename: str
    size: int
    upload_time: float
    document_id: int

    model_config = ConfigDict(from_attributes=True)