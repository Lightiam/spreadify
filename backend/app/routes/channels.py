from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List
from ..models import Channel, ChannelCreate, User, ChannelSettings
from ..auth import get_current_user
from ..database import db
import uuid
from datetime import datetime
import os
import aiofiles

router = APIRouter(prefix="/channels", tags=["channels"])

@router.post("", response_model=Channel)
async def create_channel(
    channel_data: ChannelCreate,
    current_user: User = Depends(get_current_user)
):
    # Check if user already has maximum allowed channels (e.g., 5)
    user_channels = await db.get_user_channels(current_user.id)
    if len(user_channels) >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum number of channels reached"
        )
    
    channel = Channel(
        id=str(uuid.uuid4()),
        name=channel_data.name,
        description=channel_data.description,
        profile_picture_url=channel_data.profile_picture_url,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        settings=ChannelSettings()  # Default settings
    )
    return await db.create_channel(channel)

@router.get("/me", response_model=List[Channel])
async def get_my_channels(current_user: User = Depends(get_current_user)):
    return await db.get_user_channels(current_user.id)

@router.get("/{channel_id}", response_model=Channel)
async def get_channel(channel_id: str):
    channel = await db.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.put("/{channel_id}/settings")
async def update_channel_settings(
    channel_id: str,
    settings: ChannelSettings,
    current_user: User = Depends(get_current_user)
):
    channel = await db.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if channel.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this channel")
    
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
    
    await db.update_channel(channel_id, {"settings": settings})
    return {"status": "success"}

@router.post("/{channel_id}/profile-picture")
async def upload_profile_picture(
    channel_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    channel = await db.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if channel.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this channel")
    
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
    await db.update_channel(channel_id, {"profile_picture_url": profile_picture_url})
    
    return {"profile_picture_url": profile_picture_url}

@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: str,
    current_user: User = Depends(get_current_user)
):
    channel = await db.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if channel.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this channel")
    
    await db.delete_channel(channel_id)
    return {"message": "Channel deleted successfully"}
