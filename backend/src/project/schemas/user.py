from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = "user"
    is_admin: bool = False

class UserCreate(UserBase):
    pass

class UserSchema(UserBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)