from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class GostCheckRequest(BaseModel):
    document_id: int

class GostCheckResponse(BaseModel):
    check_id: int
    document_id: int
    status: str
    score: Decimal
    is_compliant: bool
    total_errors: int
    total_warnings: int
    checked_at: datetime

class GostCheckResult(BaseModel):
    check_id: int
    document_id: int
    is_compliant: bool
    score: Decimal
    status: str
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]
    checked_at: datetime
    filename: Optional[str]

class GostCheckStatus(BaseModel):
    document_id: int
    status: str
    progress: int
    estimated_time_remaining: Optional[int] = None