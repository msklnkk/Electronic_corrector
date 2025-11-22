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
    filename: Optional[str]
    filepath: Optional[str]
    doc_type: Optional[str]
    is_example: Optional[bool]
    size: Optional[Decimal]
    status_id: Optional[int]
    report_pdf_path: Optional[str]
    score: Optional[Decimal]
    analysis_time: Optional[Decimal]
    upload_datetime: Optional[datetime]

class DocumentCreate(DocumentBase):
    pass


class DocumentSchema(DocumentBase):
    document_id: int

    model_config = ConfigDict(from_attributes=True)
