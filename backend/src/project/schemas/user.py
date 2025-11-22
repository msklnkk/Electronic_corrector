from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    first_name: str
    surname_name: str
    patronomic_name: str
    username: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = "user"
    is_admin: bool = False
    tg_username: str | None = None
    is_tg_subscribed: bool = False
    theme: str = "light"
    is_push_enabled: bool = False

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    surname_name: Optional[str] = None
    patronomic_name: Optional[str] = None

    email: Optional[EmailStr] = None
    user_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6)

    role: Optional[str] = None
    is_admin: Optional[bool] = None

    tg_username: Optional[str] = None
    is_tg_subscribed: Optional[bool] = None

    theme: Optional[str] = None
    is_push_enabled: Optional[bool] = None

class UserSchema(UserBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)