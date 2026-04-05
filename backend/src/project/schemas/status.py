# backend/src/project/schemas/status.py
from pydantic import BaseModel, ConfigDict


class StatusBase(BaseModel):
    status_name: str


class StatusCreate(StatusBase):
    pass


class StatusSchema(StatusBase):
    status_id: int

    model_config = ConfigDict(from_attributes=True)
