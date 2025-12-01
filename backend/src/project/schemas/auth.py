from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class AuthCredential(BaseModel):
    login: EmailStr = Field(..., description="Email (используется как логин и username)")
    password: str = Field(..., min_length=6, description="Пароль")
    first_name: str = Field(..., min_length=2, description="Имя")
    surname_name: str = Field(..., min_length=2, description="Фамилия")
    patronomic_name: Optional[str] = Field(None, description="Отчество (необязательно)")
    tg_username: Optional[str] = Field(None, description="Telegram username без @ (необязательно)")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = Field(default=None)