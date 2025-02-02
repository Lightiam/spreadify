from fastapi import APIRouter, HTTPException, status, Depends, Form, Request
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import update
from ..db.models import Stream, Overlay
from ..db.database import get_db
from ..services.video_processor import VideoProcessor
import asyncio
import uuid
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def forward_stream(stream_id: str, rtmp_url: str, stream_key: str):
    """Forward RTMP stream to another platform"""
    input_url = f"rtmp://localhost:1935/live/{stream_id}"
    output_url = f"{rtmp_url}/{stream_key}"
    
    ffmpeg_command = [
        "ffmpeg",
        "-i", input_url,
        "-c", "copy",
        "-f", "flv",
        output_url
    ]
    
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    return process

video_processor = VideoProcessor()
router = APIRouter(prefix="/rtmp", tags=["rtmp"])
active_streams: Dict[str, Dict] = {}

from fastapi import Form

from pydantic import BaseModel

class StreamKeyRequest(BaseModel):
    stream_key: str

@router.post("/connect")
async def rtmp_connect(
    request: Request,
    stream_key_request: StreamKeyRequest,
    db: Session = Depends(get_db)
):
    if not stream_key_request.stream_key:
        raise HTTPException(status_code=400, detail="Stream key is required")
        
    stream = db.query(Stream).filter(Stream.stream_key == stream_key_request.stream_key).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    if stream.status != "scheduled":
        raise HTTPException(status_code=400, detail="Stream is not scheduled")
    
    # Get active overlays for the stream
    overlays = db.query(Overlay).filter(
        Overlay.stream_id == stream.id,
        Overlay.active == True
    ).all()
    
    # Start HLS stream with multiple quality variants
    rtmp_url = f"rtmp://localhost:1935/live/{stream_key_request.stream_key}"
    hls_url = await video_processor.process_stream(
        input_url=rtmp_url,
        stream_id=stream_key_request.stream_key,
        overlays=[{
            "path": overlay.path,
            "position_x": overlay.position_x,
            "position_y": overlay.position_y,
            "scale": overlay.scale
        } for overlay in overlays],
        format="hls"
    )
    
    # Start platform-specific streams if platforms are configured
    platform_streams = {}
    if stream.platforms:
        platform_list = stream.platforms.split(",")
        for platform in platform_list:
            try:
                platform_result = None
                if platform == "youtube":
                    from .streaming.youtube import start_youtube_stream
                    platform_result = await start_youtube_stream(str(stream.id), db)
                    if "broadcast_id" in platform_result:
                        platform_streams["youtube_broadcast_id"] = platform_result["broadcast_id"]
                elif platform == "twitch":
                    from .streaming.twitch import start_twitch_stream
                    platform_result = await start_twitch_stream(str(stream.id), db)
                elif platform == "facebook":
                    from .streaming.facebook import start_facebook_stream
                    platform_result = await start_facebook_stream(str(stream.id), db)
                    if "stream_id" in platform_result:
                        platform_streams["facebook_live_id"] = platform_result["stream_id"]
                
                if platform_result:
                    logger.info(f"Successfully started {platform} stream for stream ID: {stream.id}")
                    rtmp_url = platform_result.get("stream_url") or platform_result.get("rtmp_url")
                    stream_key = platform_result.get("stream_key")
                    
                    if rtmp_url and stream_key:
                        platform_streams[platform] = {
                            "rtmp_url": rtmp_url,
                            "stream_key": stream_key
                        }
                        # Start forwarding stream to this platform
                        forward_process = await forward_stream(
                            stream_key_request.stream_key,
                            rtmp_url,
                            stream_key
                        )
                        if forward_process:
                            logger.info(f"Successfully started forwarding to {platform}")
                            platform_streams[platform]["process"] = forward_process
                        else:
                            logger.error(f"Failed to start forwarding to {platform}")
                    else:
                        logger.error(f"Missing RTMP URL or stream key for {platform}")
            except Exception as e:
                logger.error(f"Failed to start {platform} stream: {str(e)}", exc_info=True)
    
    active_streams[stream_key_request.stream_key] = {
        "id": stream.id,
        "started_at": datetime.utcnow(),
        "viewer_count": 0,
        "hls_url": hls_url,
        "overlays": [{
            "id": str(overlay.id),
            "path": overlay.path,
            "position_x": overlay.position_x,
            "position_y": overlay.position_y,
            "scale": overlay.scale
        } for overlay in overlays],
        "qualities": video_processor.quality_presets,
        "platforms": platform_list if stream.platforms else [],
        "platform_streams": platform_streams,
        **{k: v for k, v in platform_streams.items() if k in ["youtube_broadcast_id", "facebook_live_id"]}
    }
    
    db.execute(
        update(Stream)
        .where(Stream.id == stream.id)
        .values(
            status="live",
            started_at=datetime.utcnow()
        )
    )
    db.commit()
    
    return {
        "stream_key": stream_key_request.stream_key,
        "rtmp_url": f"{os.getenv('RTMP_SERVER_URL')}/{stream_key_request.stream_key}",
        "hls_url": f"{os.getenv('HLS_SERVER_URL')}/{stream_key_request.stream_key}/master.m3u8",
        "platforms": platform_list if stream.platforms else []
    }

@router.post("/disconnect")
async def rtmp_disconnect(
    request: Request,
    stream_key: str,
    db: Session = Depends(get_db)
):
    if stream_key not in active_streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    stream = db.query(Stream).filter(Stream.stream_key == stream_key).first()
    if stream:
        try:
            # Stop platform-specific streams
            if stream.platforms:
                platform_list = stream.platforms.split(",")
                for platform in platform_list:
                    try:
                        # Kill forwarding process if it exists
                        if platform in active_streams[stream_key].get("platform_streams", {}):
                            process = active_streams[stream_key]["platform_streams"][platform].get("process")
                            if process:
                                try:
                                    process.terminate()
                                    await process.wait()
                                except Exception as e:
                                    logger.error(f"Error terminating {platform} forward process: {str(e)}")
                        
                        # Stop platform-specific stream
                        if platform == "youtube" and "youtube_broadcast_id" in active_streams[stream_key]:
                            from .streaming.youtube import stop_youtube_stream
                            await stop_youtube_stream(active_streams[stream_key]["youtube_broadcast_id"], db)
                        elif platform == "twitch":
                            from .streaming.twitch import stop_twitch_stream
                            await stop_twitch_stream(db)
                        elif platform == "facebook" and "facebook_live_id" in active_streams[stream_key]:
                            from .streaming.facebook import stop_facebook_stream
                            await stop_facebook_stream(active_streams[stream_key]["facebook_live_id"], db)
                    except Exception as e:
                        logger.error(f"Failed to stop {platform} stream: {str(e)}", exc_info=True)
        except Exception as e:
            logger.error(f"Error during platform cleanup: {str(e)}", exc_info=True)
        
        db.execute(
            update(Stream)
            .where(Stream.id == stream.id)
            .values(
                status="ended",
                ended_at=datetime.utcnow()
            )
        )
        db.commit()
    
    try:
        # Clean up stream files
        await video_processor.cleanup_stream(stream_key)
    except Exception as e:
        logger.error(f"Error cleaning up stream files: {str(e)}", exc_info=True)
    
    del active_streams[stream_key]
    return {"status": "success"}

@router.get("/active")
async def get_active_streams():
    return active_streams

from datetime import datetime
from pydantic import BaseModel

class ViewerCount(BaseModel):
    count: int

@router.post("/{stream_key}/viewer")
async def update_viewer_count(
    request: Request,
    stream_key: str,
    viewer_count: ViewerCount,
    db: Session = Depends(get_db)
):
    if stream_key not in active_streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    if stream_key not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Check if stream exists
    stream = db.query(Stream).filter(Stream.stream_key == stream_key).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    active_streams[stream_key]["viewer_count"] = max(0, viewer_count.count)
    
    stream = db.query(Stream).filter(Stream.stream_key == stream_key).first()
    if stream:
        db.execute(
            update(Stream)
            .where(Stream.id == stream.id)
            .values(viewer_count=max(0, viewer_count.count))
        )
        db.commit()
    
    return {"status": "success"}
