from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class StreamBase(BaseModel):
    title: str
    description: Optional[str] = None
    platforms: List[str]

class StreamCreate(StreamBase):
    pass

class Stream(StreamBase):
    id: str
    user_id: str
    status: str
    created_at: datetime
    rtmp_url: Optional[str] = None
    stream_key: Optional[str] = None

    class Config:
        from_attributes = True
