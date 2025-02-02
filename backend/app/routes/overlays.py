from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models import User, Stream, StreamOverlay
from ..auth import get_current_user
from ..database import db
import uuid

router = APIRouter(prefix="/overlays", tags=["overlays"])

@router.post("/{stream_id}")
async def create_overlay(
    stream_id: str,
    overlay: StreamOverlay,
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
            detail="You don't have permission to modify this stream"
        )
    
    overlay.id = str(uuid.uuid4())
    if not hasattr(stream, "overlays"):
        stream.overlays = []
    stream.overlays.append(overlay)
    
    await db.update_stream(stream_id, {"overlays": stream.overlays})
    return overlay

@router.put("/{stream_id}/{overlay_id}")
async def update_overlay(
    stream_id: str,
    overlay_id: str,
    overlay_update: StreamOverlay,
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
            detail="You don't have permission to modify this stream"
        )
    
    for i, overlay in enumerate(stream.overlays):
        if overlay.id == overlay_id:
            overlay_update.id = overlay_id
            stream.overlays[i] = overlay_update
            await db.update_stream(stream_id, {"overlays": stream.overlays})
            return overlay_update
            
    raise HTTPException(status_code=404, detail="Overlay not found")

@router.delete("/{stream_id}/{overlay_id}")
async def delete_overlay(
    stream_id: str,
    overlay_id: str,
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
            detail="You don't have permission to modify this stream"
        )
    
    stream.overlays = [o for o in stream.overlays if o.id != overlay_id]
    await db.update_stream(stream_id, {"overlays": stream.overlays})
    return {"status": "success"}
