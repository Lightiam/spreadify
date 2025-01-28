from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    sub: str | None = None

class UserBase(BaseModel):
    email: str
    name: str | None = None
    picture: str | None = None
