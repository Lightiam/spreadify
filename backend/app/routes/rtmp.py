from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Optional
from ..models import User, Stream
from ..auth import get_current_user
from ..database import db
import asyncio
import uuid
import os
from datetime import datetime

router = APIRouter(prefix="/rtmp", tags=["rtmp"])

active_streams: Dict[str, Dict] = {}

@router.post("/connect")
async def rtmp_connect(
    stream_key: str,
    current_user: User = Depends(get_current_user)
):
    stream = await db.get_stream_by_key(stream_key)
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid stream key"
        )
    
    channel = await db.get_channel(stream.channel_id)
    if not channel or channel.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to stream on this channel"
        )
    
    if stream.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stream is not in scheduled state"
        )
    
    stream_id = str(uuid.uuid4())
    active_streams[stream_id] = {
        "stream_key": stream_key,
        "user_id": current_user.id,
        "started_at": datetime.utcnow(),
        "viewer_count": 0
    }
    
    await db.update_stream(stream.id, {
        "status": "live",
        "started_at": datetime.utcnow()
    })
    
    return {
        "stream_id": stream_id,
        "rtmp_url": f"rtmp://{os.getenv('PUBLIC_URL')}/live/{stream_id}"
    }

@router.post("/disconnect/{stream_id}")
async def rtmp_disconnect(
    stream_id: str,
    current_user: User = Depends(get_current_user)
):
    if stream_id not in active_streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    stream_data = active_streams[stream_id]
    if stream_data["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to end this stream"
        )
    
    stream = await db.get_stream_by_key(stream_data["stream_key"])
    if stream:
        await db.update_stream(stream.id, {
            "status": "ended",
            "ended_at": datetime.utcnow()
        })
    
    del active_streams[stream_id]
    return {"status": "success"}

@router.get("/active")
async def get_active_streams(current_user: User = Depends(get_current_user)):
    user_streams = {
        stream_id: data
        for stream_id, data in active_streams.items()
        if data["user_id"] == current_user.id
    }
    return user_streams

@router.post("/{stream_id}/viewer")
async def update_viewer_count(
    stream_id: str,
    viewer_count: int,
    current_user: User = Depends(get_current_user)
):
    if stream_id not in active_streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    stream_data = active_streams[stream_id]
    if stream_data["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this stream"
        )
    
    active_streams[stream_id]["viewer_count"] = max(0, viewer_count)
    
    stream = await db.get_stream_by_key(stream_data["stream_key"])
    if stream:
        await db.update_stream(stream.id, {"viewer_count": max(0, viewer_count)})
    
    return {"status": "success"}
