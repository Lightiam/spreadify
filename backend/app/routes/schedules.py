from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Stream, Channel
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
from uuid import UUID, uuid4

router = APIRouter(prefix="/schedules", tags=["schedules"])

class StreamSchedule(BaseModel):
    start_time: datetime
    duration: int  # Duration in minutes
    title: str
    description: str | None = None

async def send_stream_reminder(stream_id: str, db: Session):
    """Background task to send stream reminder"""
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream or not stream.scheduled_for:
        return
        
    # Wait until 15 minutes before stream
    wait_time = (stream.scheduled_for - datetime.utcnow() - timedelta(minutes=15)).total_seconds()
    if wait_time > 0:
        await asyncio.sleep(wait_time)
        
    # Update reminder status
    db.query(Stream).filter(Stream.id == stream_id).update({"reminder_sent": True})
    db.commit()

@router.post("/{stream_id}")
async def schedule_stream(
    stream_id: str,
    schedule: StreamSchedule,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        # Validate schedule time (ensure both are UTC aware)
        current_time = datetime.utcnow().replace(tzinfo=None)
        start_time = schedule.start_time.replace(tzinfo=None)
        if start_time < current_time:
            raise HTTPException(
                status_code=400,
                detail="Cannot schedule stream in the past"
            )

        stream = db.query(Stream).filter(Stream.id == stream_id).first()
        if not stream:
            # Get or create default channel
            channel = db.query(Channel).filter(Channel.owner_id == "anonymous").first()
            if not channel:
                channel = Channel(
                    name="Default Channel",
                    description="Default streaming channel",
                    owner_id="anonymous"
                )
                db.add(channel)
                db.commit()
                db.refresh(channel)
            
            stream = Stream(
                id=stream_id,
                stream_key=str(uuid4()),
                title=schedule.title,
                description=schedule.description,
                status="scheduled",
                scheduled_for=schedule.start_time,
                duration=schedule.duration,
                channel_id=channel.id,
                owner_id="anonymous"
            )
            db.add(stream)
        else:
            # Update existing stream
            db.query(Stream).filter(Stream.id == stream_id).update({
                "scheduled_for": schedule.start_time,
                "title": schedule.title,
                "description": schedule.description,
                "duration": schedule.duration,
                "status": "scheduled"
            })
        
        db.commit()
        db.refresh(stream)
        
        # Schedule reminder
        background_tasks.add_task(send_stream_reminder, stream_id, db)
        
        return {
            "id": str(stream.id),
            "title": stream.title,
            "description": stream.description,
            "scheduled_for": stream.scheduled_for.isoformat(),
            "duration": stream.duration,
            "status": stream.status,
            "stream_key": stream.stream_key
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{stream_id}")
async def get_stream_schedule(
    stream_id: str,
    db: Session = Depends(get_db)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    if not stream.scheduled_for:
        return None
    
    return {
        "id": str(stream.id),
        "title": stream.title,
        "description": stream.description,
        "scheduled_for": stream.scheduled_for,
        "duration": stream.duration,
        "status": stream.status
    }

@router.delete("/{stream_id}")
async def delete_stream_schedule(
    stream_id: str,
    db: Session = Depends(get_db)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Verify channel exists
    channel = db.query(Channel).filter(Channel.id == stream.channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    db.query(Stream).filter(Stream.id == stream_id).update({
        "scheduled_for": None,
        "duration": None,
        "status": "created"
    })
    db.commit()
    
    return {"status": "success"}
