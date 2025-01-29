from pydantic import BaseModel, EmailStr

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

class UserCreate(UserBase):
    pass

class UserUpdate(UserBase):
    pass

class User(UserBase):
    id: str
    is_active: bool = True
    is_verified: bool = False

    class Config:
        from_attributes = True
