from pydantic import BaseModel, HttpUrl
from datetime import datetime

class SocialChannelCreate(BaseModel):
    platform: str
    link: HttpUrl

class SocialChannelRead(BaseModel):
    id: str
    platform: str
    link: str
    created_at: datetime

    class Config:
        from_attributes = True
