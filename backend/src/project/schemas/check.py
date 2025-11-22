from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CheckBase(BaseModel):
    document_id: int
    standart_id: int
    checked_at: datetime | None = None
    result: str | None = None    # success / warnings / failed
    report_path: str | None = None


class CheckCreate(CheckBase):
    pass


class CheckSchema(CheckBase):
    check_id: int

    model_config = ConfigDict(from_attributes=True)
