from pydantic import BaseModel, Field
class AuthCredential(BaseModel):
    login: str
    password: str
    first_name: str
    surname_name: str
    patronomic_name: str
class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    username: str | None = Field(default=None)