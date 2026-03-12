from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedRule(BaseModel):
    section: Optional[str] = None
    title: str
    text: str
    page: int
    category: str
    confidence: float = Field(ge=0.0, le=1.0)


class BertRulesResponse(BaseModel):
    filename: str
    pages: int
    rules_count: int
    rules: List[ExtractedRule]