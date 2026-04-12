from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentStatusEvent(BaseModel):
    document_id: int
    status: str
    message: str
    created_at: datetime
    error: Optional[str] = None


class GenerateReportTask(BaseModel):
    document_id: int
    report_type: str = "json"
    created_at: datetime