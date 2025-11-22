from pydantic import BaseModel, ConfigDict


class MistakeBase(BaseModel):
    mistake_type_id: int | None = None
    description: str
    critical_status: str
    document_id: int


class MistakeCreate(MistakeBase):
    pass


class MistakeSchema(MistakeBase):
    mistake_id: int

    model_config = ConfigDict(from_attributes=True)
