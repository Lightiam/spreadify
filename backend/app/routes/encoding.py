from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Stream
from ..db.init_mock_data import MOCK_USER_ID
import asyncio
import json
from pydantic import BaseModel

router = APIRouter(prefix="/encoding", tags=["encoding"])

class VideoProfile(BaseModel):
    width: int
    height: int
    bitrate: int  # in kbps
    fps: int = 30

# Define standard video profiles
VIDEO_PROFILES = {
    "1080p": VideoProfile(width=1920, height=1080, bitrate=6000),
    "720p": VideoProfile(width=1280, height=720, bitrate=4000),
    "480p": VideoProfile(width=854, height=480, bitrate=2000),
    "360p": VideoProfile(width=640, height=360, bitrate=1000)
}

async def transcode_stream(stream_id: str, profile: VideoProfile):
    """Background task to transcode stream to different quality"""
    stream = await db.get_stream(stream_id)
    if not stream:
        return
        
    try:
        from ..services.video_processor import VideoProcessor
        processor = VideoProcessor()
        
        qualities = [{
            "height": profile.height,
            "bitrate": profile.bitrate
        }]
        
        rtmp_url = f"rtmp://{os.getenv('PUBLIC_URL')}/live/{stream_id}"
        stream_url = await processor.process_stream(rtmp_url, stream_id, "hls", qualities)
        
        if not hasattr(stream, "transcoding_status"):
            stream.transcoding_status = {}
        
        profile_key = f"{profile.height}p"
        stream.transcoding_status[profile_key] = {
            "status": "completed",
            "url": stream_url,
            "profile": profile.dict()
        }
        
        await db.update_stream(stream_id, {"transcoding_status": stream.transcoding_status})
    except Exception as e:
        print(f"Transcoding error for stream {stream_id}: {str(e)}")

@router.post("/{stream_id}/transcode")
async def start_transcoding(
    stream_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    profiles: List[str] = ["720p", "480p", "360p"]  # Default profiles
):
    stream = await db.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Verify channel ownership
    channel = await db.get_channel(stream.channel_id)
    if not channel or channel.owner_id != MOCK_USER_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to transcode this stream"
        )
    
    # Start transcoding tasks for each profile
    for profile_name in profiles:
        if profile_name not in VIDEO_PROFILES:
            continue
        background_tasks.add_task(
            transcode_stream,
            stream_id,
            VIDEO_PROFILES[profile_name]
        )
    
    return {"status": "transcoding_started", "profiles": profiles}

@router.get("/{stream_id}/status")
async def get_transcoding_status(
    stream_id: str,
    db: Session = Depends(get_db)
):
    stream = await db.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    return getattr(stream, "transcoding_status", {})
