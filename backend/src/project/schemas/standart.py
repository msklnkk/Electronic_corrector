from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StandardBase(BaseModel):
    name: str
    version: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    is_custom: bool = False


class StandardCreate(StandardBase):
    pass


class StandardSchema(StandardBase):
    standart_id: int

    model_config = ConfigDict(from_attributes=True)
