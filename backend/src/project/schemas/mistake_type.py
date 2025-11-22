from pydantic import BaseModel, ConfigDict


class MistakeTypeBase(BaseModel):
    mistake_type_name: str


class MistakeTypeCreate(MistakeTypeBase):
    pass


class MistakeTypeSchema(MistakeTypeBase):
    mistake_type_id: int

    model_config = ConfigDict(from_attributes=True)
