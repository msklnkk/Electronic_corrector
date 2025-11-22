from datetime import date

from pydantic import BaseModel, Field, ConfigDict


class ReviewBase(BaseModel):
    user_id: int
    rating: int = Field(ge=1, le=5)
    review_text: str | None = None
    created_at: date


class ReviewCreate(ReviewBase):
    pass


class ReviewSchema(ReviewBase):
    review_id: int

    model_config = ConfigDict(from_attributes=True)
