from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, BackgroundTasks
from typing import List, Dict
from ..models import Stream, StreamCreate, User
from ..auth import get_current_user
from ..database import db
import logging

logger = logging.getLogger(__name__)
import uuid
from datetime import datetime
import json
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaRelay
from pydantic import BaseModel
import asyncio

class PlatformUpdate(BaseModel):
    platforms: List[str]

router = APIRouter(prefix="/streams", tags=["streams"])

# In-memory storage for WebRTC connections
peer_connections = {}
relay = MediaRelay()

@router.post("", response_model=Stream)
async def create_stream(
    stream_data: StreamCreate,
    current_user: User = Depends(get_current_user)
):
    # Verify channel ownership
    channel = await db.get_channel(stream_data.channel_id)
    if not channel or channel.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create streams for this channel"
        )
    
    stream = Stream(
        id=str(uuid.uuid4()),
        title=stream_data.title,
        description=stream_data.description,
        channel_id=stream_data.channel_id,
        stream_key=stream_data.generate_stream_key(),
        created_at=datetime.utcnow(),
        platforms=stream_data.platforms,
        scheduled_for=stream_data.scheduled_for,
        platform_stats={
            platform: {"viewers": 0, "likes": 0, "shares": 0}
            for platform in stream_data.platforms
        }
    )
    return await db.create_stream(stream)

@router.get("/{stream_id}", response_model=Stream)
async def get_stream(stream_id: str):
    stream = await db.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    return stream

from typing import List

@router.post("/{stream_id}/platforms")
async def update_stream_platforms(
    stream_id: str,
    platform_data: PlatformUpdate,
    current_user: User = Depends(get_current_user)
):
    stream = await db.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Update stream platforms
    stream.platforms = platform_data.platforms
    stream.platform_stats = {
        platform: {"viewers": 0, "likes": 0, "shares": 0}
        for platform in platform_data.platforms
    }
    return await db.update_stream(stream_id, {
        "platforms": platform_data.platforms,
        "platform_stats": stream.platform_stats
    })

@router.post("/{stream_id}/start")
async def start_stream(
    stream_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    stream = await db.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Verify channel ownership
    channel = await db.get_channel(stream.channel_id)
    if not channel or channel.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to start this stream"
        )
    
    if stream.status == "live":
        raise HTTPException(
            status_code=400,
            detail="Stream is already live"
        )
    
    # Update stream status
    stream.status = "live"
    stream.started_at = datetime.utcnow()
    await db.update_stream(stream_id, {
        "status": stream.status,
        "started_at": stream.started_at
    })
    
    # Start platform-specific streaming in background
    platform_streams = await start_platform_streams(stream)
    
    # Update stream with platform-specific information
    await db.update_stream(stream_id, {
        "platform_streams": platform_streams
    })
    
    return {
        "status": "success",
        "stream": stream,
        "platform_streams": platform_streams
    }

@router.post("/{stream_id}/end")
async def end_stream(
    stream_id: str,
    current_user: User = Depends(get_current_user)
):
    stream = await db.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Verify channel ownership
    channel = await db.get_channel(stream.channel_id)
    if not channel or channel.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to end this stream"
        )
    
    if stream.status != "live":
        raise HTTPException(
            status_code=400,
            detail="Stream is not live"
        )
    
    # Stop platform-specific streams
    if stream.platforms:
        platform_list = stream.platforms.split(",")
        for platform in platform_list:
            try:
                if platform == "youtube" and stream.platform_streams.get("youtube_broadcast_id"):
                    from .streaming.youtube import stop_youtube_stream
                    await stop_youtube_stream(stream.platform_streams["youtube_broadcast_id"], db, current_user)
                elif platform == "twitch":
                    from .streaming.twitch import stop_twitch_stream
                    await stop_twitch_stream(db, current_user)
                elif platform == "facebook" and stream.platform_streams.get("facebook_live_id"):
                    from .streaming.facebook import stop_facebook_stream
                    await stop_facebook_stream(stream.platform_streams["facebook_live_id"], db, current_user)
            except Exception as e:
                logger.error(f"Failed to stop {platform} stream: {str(e)}", exc_info=True)
    
    # Update stream status
    stream.status = "ended"
    stream.ended_at = datetime.utcnow()
    await db.update_stream(stream_id, {
        "status": stream.status,
        "ended_at": stream.ended_at,
        "platform_streams": {}  # Clear platform streams data
    })
    
    return {"status": "success", "stream": stream}

async def start_platform_streams(stream: Stream):
    """Start streaming to each configured platform"""
    platform_streams = {}
    
    for platform in stream.platforms:
        try:
            platform_result = None
            if platform == "youtube":
                from .streaming.youtube import start_youtube_stream
                platform_result = await start_youtube_stream(str(stream.id), db, current_user)
                if platform_result and "broadcast_id" in platform_result:
                    platform_streams["youtube_broadcast_id"] = platform_result["broadcast_id"]
            elif platform == "twitch":
                from .streaming.twitch import start_twitch_stream
                platform_result = await start_twitch_stream(str(stream.id), db, current_user)
            elif platform == "facebook":
                from .streaming.facebook import start_facebook_stream
                platform_result = await start_facebook_stream(str(stream.id), db, current_user)
                if platform_result and "stream_id" in platform_result:
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
                else:
                    logger.error(f"Missing RTMP URL or stream key for {platform}")
        except Exception as e:
            logger.error(f"Failed to start {platform} stream: {str(e)}", exc_info=True)
            
    return platform_streams

@router.websocket("/ws/{stream_id}")
async def websocket_endpoint(websocket: WebSocket, stream_id: str):
    await websocket.accept()
    
    try:
        # Create a new RTCPeerConnection for this stream
        pc = RTCPeerConnection()
        peer_connections[stream_id] = pc

        @pc.on("track")
        async def on_track(track: MediaStreamTrack):
            if track.kind == "video":
                # Relay the video track
                relay_track = relay.relay(track)
                for pc in peer_connections.values():
                    pc.addTrack(relay_track)
            elif track.kind == "audio":
                # Relay the audio track
                relay_track = relay.relay(track)
                for pc in peer_connections.values():
                    pc.addTrack(relay_track)

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "offer":
                offer = RTCSessionDescription(
                    sdp=message["sdp"],
                    type=message["type"]
                )
                await pc.setRemoteDescription(offer)
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                
                response = {
                    "type": "answer",
                    "sdp": pc.localDescription.sdp
                }
                await websocket.send_text(json.dumps(response))

    except Exception as e:
        if stream_id in peer_connections:
            await peer_connections[stream_id].close()
            del peer_connections[stream_id]
    
    finally:
        if stream_id in peer_connections:
            await peer_connections[stream_id].close()
            del peer_connections[stream_id]
