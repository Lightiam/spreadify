from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
from ..models import User, Stream, StreamSchedule
from ..auth import get_current_user
from ..database import db
from datetime import datetime, timedelta
import asyncio

router = APIRouter(prefix="/schedules", tags=["schedules"])

async def send_stream_reminder(stream_id: str):
    """Background task to send stream reminder"""
    stream = await db.get_stream(stream_id)
    if not stream or not stream.schedule:
        return
        
    # Wait until 15 minutes before stream
    wait_time = (stream.schedule.start_time - datetime.utcnow() - timedelta(minutes=15)).total_seconds()
    if wait_time > 0:
        await asyncio.sleep(wait_time)
        
    # Update reminder status
    stream.schedule.reminder_sent = True
    await db.update_stream(stream_id, {"schedule": stream.schedule})

@router.post("/{stream_id}")
async def schedule_stream(
    stream_id: str,
    schedule: StreamSchedule,
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
            detail="You don't have permission to schedule this stream"
        )
    
    # Validate schedule time
    if schedule.start_time < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Cannot schedule stream in the past"
        )
    
    # Update stream schedule
    stream.schedule = schedule
    await db.update_stream(stream_id, {"schedule": schedule})
    
    # Schedule reminder
    background_tasks.add_task(send_stream_reminder, stream_id)
    
    return schedule

@router.get("/{stream_id}")
async def get_stream_schedule(
    stream_id: str,
    current_user: User = Depends(get_current_user)
):
    stream = await db.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    return stream.schedule

@router.delete("/{stream_id}")
async def delete_stream_schedule(
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
            detail="You don't have permission to modify this stream"
        )
    
    stream.schedule = None
    await db.update_stream(stream_id, {"schedule": None})
    return {"status": "success"}
