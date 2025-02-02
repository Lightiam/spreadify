from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, BackgroundTasks
from typing import List
from ..models import Stream, StreamCreate, User
from ..auth import get_current_user
from ..database import db
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
    background_tasks.add_task(start_platform_streams, stream)
    
    return {"status": "success", "stream": stream}

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
    
    # Update stream status
    stream.status = "ended"
    stream.ended_at = datetime.utcnow()
    await db.update_stream(stream_id, {
        "status": stream.status,
        "ended_at": stream.ended_at
    })
    
    return {"status": "success", "stream": stream}

async def start_platform_streams(stream: Stream):
    """Start streaming to each configured platform"""
    for platform in stream.platforms:
        try:
            # Here we would implement platform-specific streaming logic
            # For example, using the YouTube API, Facebook Live API, etc.
            await asyncio.sleep(0)  # Placeholder for actual implementation
        except Exception as e:
            print(f"Error streaming to {platform}: {str(e)}")

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
