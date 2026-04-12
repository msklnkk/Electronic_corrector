from typing import List, Optional
from pydantic import BaseModel


class ExtractedRule(BaseModel):
    section: Optional[str] = None
    title: str
    text: str
    page: int
    category: str
    confidence: float


class BertRulesResponse(BaseModel):
    filename: str
    pages: int
    rules_count: int
    rules: List[ExtractedRule]