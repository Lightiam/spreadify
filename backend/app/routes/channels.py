from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List
from sqlalchemy.orm import Session
from ..db.models import Channel as DBChannel, ChannelSettings as DBChannelSettings
from ..db.database import get_db
from pydantic import BaseModel
import uuid
from datetime import datetime
import os
import aiofiles

class ChannelSettings(BaseModel):
    monetization_enabled: bool = False
    subscription_price: int | None = None
    minimum_donation: int | None = None
    
    class Config:
        from_attributes = True

class Channel(BaseModel):
    id: str
    name: str
    description: str | None = None
    profile_picture_url: str | None = None
    owner_id: str
    created_at: datetime
    settings: ChannelSettings | None = None
    
    class Config:
        from_attributes = True

class ChannelCreate(BaseModel):
    name: str
    description: str | None = None
    profile_picture_url: str | None = None

router = APIRouter(prefix="/channels", tags=["channels"])

@router.post("", response_model=Channel)
async def create_channel(
    channel_data: ChannelCreate,
    db: Session = Depends(get_db)
):
    # No channel limit in simplified version
    
    channel = DBChannel(
        id=str(uuid.uuid4()),
        name=channel_data.name,
        description=channel_data.description,
        profile_picture_url=channel_data.profile_picture_url,
        owner_id="anonymous",
        created_at=datetime.utcnow(),
        settings=DBChannelSettings()  # Default settings
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel

@router.get("/me", response_model=List[Channel])
async def get_my_channels(db: Session = Depends(get_db)):
    return db.query(Channel).all()

@router.get("/{channel_id}", response_model=Channel)
async def get_channel(channel_id: str, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.put("/{channel_id}/settings")
async def update_channel_settings(
    channel_id: str,
    settings: ChannelSettings,
    db: Session = Depends(get_db)
):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    # Anyone can update channel settings in simplified version
    
    # Validate monetization settings
    if settings.monetization_enabled:
        if settings.subscription_price and settings.subscription_price < 100:  # Minimum $1
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription price must be at least $1"
            )
        if settings.minimum_donation and settings.minimum_donation < 100:  # Minimum $1
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum donation must be at least $1"
            )
    
    db.query(Channel).filter(Channel.id == channel_id).update({"settings": settings})
    db.commit()
    return {"status": "success"}

@router.post("/{channel_id}/profile-picture")
async def upload_profile_picture(
    channel_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    # Anyone can update profile picture in simplified version
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a name"
        )
    
    # Validate file size (max 5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )
    
    # Reset file position after reading
    await file.seek(0)
    
    upload_dir = os.path.join("uploads", "profile_pictures")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Get file extension and validate it
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif"}
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension must be one of: {', '.join(allowed_extensions)}"
        )
    
    file_name = f"{channel_id}{file_ext}"
    file_path = os.path.join(upload_dir, file_name)
    
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    profile_picture_url = f"/uploads/profile_pictures/{file_name}"
    db.query(Channel).filter(Channel.id == channel_id).update({"profile_picture_url": profile_picture_url})
    db.commit()
    
    return {"profile_picture_url": profile_picture_url}

@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: str,
    db: Session = Depends(get_db)
):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    # Anyone can delete channels in simplified version
    
    db.delete(channel)
    db.commit()
    return {"message": "Channel deleted successfully"}
