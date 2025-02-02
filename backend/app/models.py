from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
import re

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    
    @validator("username")
    def validate_username(cls, v):
        if not re.match("^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator("password")
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

class User(UserBase):
    id: str
    created_at: datetime
    is_active: bool = True
    password: Optional[str] = None
    blocked_users: List[str] = []
    is_moderator: bool = False

class ChannelBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    profile_picture_url: Optional[str] = None
    
    @validator("name")
    def validate_channel_name(cls, v):
        if not re.match("^[a-zA-Z0-9 _-]+$", v):
            raise ValueError("Channel name can only contain letters, numbers, spaces, underscores, and hyphens")
        return v

class ChannelCreate(ChannelBase):
    owner_id: str

class ChannelSettings(BaseModel):
    monetization_enabled: bool = False
    subscription_price: Optional[int] = Field(None, ge=100)  # Minimum $1 in cents
    subscription_benefits: List[str] = Field(default_factory=list)
    minimum_donation: Optional[int] = Field(None, ge=100)  # Minimum $1 in cents
    minimum_super_chat: Optional[int] = Field(None, ge=100)  # Minimum $1 in cents
    
    @validator("subscription_benefits")
    def validate_benefits(cls, v):
        if len(v) > 10:
            raise ValueError("Maximum 10 subscription benefits allowed")
        if any(len(benefit) > 100 for benefit in v):
            raise ValueError("Benefit description cannot exceed 100 characters")
        return v

class Channel(ChannelBase):
    id: str
    owner_id: str
    created_at: datetime
    settings: ChannelSettings = ChannelSettings(
        subscription_price=100,  # Default $1
        minimum_donation=100,    # Default $1
        minimum_super_chat=100   # Default $1
    )

class StreamOverlay(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., pattern="^(image|text|alert)$")
    content: str = Field(..., max_length=5000)
    position_x: int = Field(0, ge=0, le=1920)  # Max 1080p width
    position_y: int = Field(0, ge=0, le=1080)  # Max 1080p height
    width: int = Field(100, ge=10, le=1920)
    height: int = Field(100, ge=10, le=1080)
    style: dict = Field(default_factory=dict)
    
    @validator("style")
    def validate_style(cls, v):
        allowed_keys = {"color", "fontSize", "fontFamily", "backgroundColor", "opacity", "borderRadius"}
        invalid_keys = set(v.keys()) - allowed_keys
        if invalid_keys:
            raise ValueError(f"Invalid style properties: {', '.join(invalid_keys)}")
        return v

class StreamSchedule(BaseModel):
    start_time: datetime
    duration: Optional[int] = Field(None, ge=15, le=720)  # 15 min to 12 hours
    recurring: bool = False
    recurring_days: List[int] = Field(default_factory=list)  # 0-6 for Monday-Sunday
    reminder_sent: bool = False
    
    @validator("start_time")
    def validate_start_time(cls, v):
        if v < datetime.utcnow():
            raise ValueError("Start time cannot be in the past")
        return v
        
    @validator("recurring_days")
    def validate_recurring_days(cls, v):
        if not all(0 <= day <= 6 for day in v):
            raise ValueError("Recurring days must be between 0 and 6 (Monday to Sunday)")
        return v

class StreamBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    scheduled_for: Optional[datetime] = None
    platforms: List[str] = Field(default_factory=list)
    schedule: Optional[StreamSchedule] = None
    overlays: List[StreamOverlay] = Field(default_factory=list)
    
    @validator("scheduled_for")
    def validate_schedule_time(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("Stream cannot be scheduled in the past")
        return v
        
    @validator("platforms")
    def validate_platforms(cls, v):
        valid_platforms = {"youtube", "facebook", "twitch", "linkedin"}
        invalid_platforms = set(v) - valid_platforms
        if invalid_platforms:
            raise ValueError(f"Invalid platforms: {', '.join(invalid_platforms)}")
        return v

class StreamCreate(StreamBase):
    channel_id: str
    
    def generate_stream_key(self) -> str:
        return secrets.token_urlsafe(32)

class Stream(StreamBase):
    id: str
    channel_id: str
    status: str = Field("scheduled", pattern="^(scheduled|live|ended)$")
    stream_key: str
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    viewer_count: int = Field(0, ge=0)
    chat_enabled: bool = True
    platform_stats: dict = Field(default_factory=dict)
    payments: List[dict] = Field(default_factory=list)
    
    @validator("ended_at")
    def validate_end_time(cls, v, values):
        if v and values.get("started_at") and v < values["started_at"]:
            raise ValueError("End time cannot be before start time")
        return v
