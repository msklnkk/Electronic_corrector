from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportBase(BaseModel):
    check_id: int
    report_json: str | None = None
    created_at: datetime | None = None


class ReportCreate(ReportBase):
    pass


class ReportSchema(ReportBase):
    report_id: int

    model_config = ConfigDict(from_attributes=True)
