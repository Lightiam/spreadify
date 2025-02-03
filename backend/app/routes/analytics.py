from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from ..db.models import Stream, Channel, ChatMessage
from ..db.database import get_db
from datetime import datetime, timedelta
from pydantic import BaseModel

class StreamMetrics(BaseModel):
    total_viewers: int = 0
    peak_viewers: int = 0
    average_viewers: int = 0
    chat_messages: int = 0
    super_chats: int = 0
    donations: float = 0
    subscriptions_gained: int = 0
    platform_stats: Dict[str, Dict[str, int]] = {}
    engagement_rate: float = 0
    duration: float = 0
    likes: int = 0
    shares: int = 0

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/stream/{stream_id}/metrics", response_model=StreamMetrics)
async def get_stream_metrics(
    stream_id: str,
    db: Session = Depends(get_db)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    channel = db.query(Channel).filter(Channel.id == stream.channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    chat_messages = db.query(ChatMessage).filter(ChatMessage.stream_id == stream_id).all()
    platform_stats = stream.platform_stats
    
    total_viewers = sum(
        stats.get("viewers", 0)
        for stats in platform_stats.values()
    )
    
    metrics = StreamMetrics(
        total_viewers=total_viewers,
        peak_viewers=max(
            (stats.get("peak_viewers", 0)
            for stats in platform_stats.values()),
            default=0
        ),
        average_viewers=total_viewers // len(platform_stats) if platform_stats else 0,
        chat_messages=len(chat_messages),
        super_chats=sum(
            1 for msg in chat_messages
            if msg.get("type") == "super_chat"
        ),
        donations=sum(
            payment.get("amount", 0)
            for payment in getattr(stream, "payments", [])
            if payment.get("type") in ["donation", "super_chat"]
        ),
        platform_stats=platform_stats,
        duration=(stream.ended_at - stream.started_at).total_seconds() if stream.ended_at and stream.started_at else 0,
        likes=sum(
            stats.get("likes", 0)
            for stats in platform_stats.values()
        ),
        shares=sum(
            stats.get("shares", 0)
            for stats in platform_stats.values()
        )
    )
    
    if metrics.total_viewers > 0:
        metrics.engagement_rate = (
            metrics.chat_messages / metrics.total_viewers
        ) * 100
    
    return metrics

@router.get("/channel/{channel_id}/analytics")
async def get_channel_analytics(
    channel_id: str,
    days: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    start_date = datetime.utcnow() - timedelta(days=days if days is not None else 30)
    streams = db.query(Stream).filter(
        Stream.channel_id == channel_id,
        Stream.created_at >= start_date
    ).all()
    
    total_watch_time = sum(
        (stream.ended_at - stream.started_at).total_seconds()
        for stream in streams
        if stream.started_at and stream.ended_at
    )
    
    total_earnings = sum(
        payment.get("amount", 0)
        for stream in streams
        for payment in getattr(stream, "payments", [])
    )
    
    subscribers = []  # Simplified: no subscribers in anonymous mode
    
    return {
        "total_streams": len(streams),
        "total_watch_time": total_watch_time,
        "total_earnings": total_earnings,
        "subscriber_count": len(subscribers),
        "average_viewers": sum(
            stream.viewer_count for stream in streams
        ) // len(streams) if streams else 0,
        "total_chat_messages": sum(
            db.query(ChatMessage).filter(ChatMessage.stream_id == stream.id).count()
            for stream in streams
        ),
        "streams": [
            {
                "id": stream.id,
                "title": stream.title,
                "metrics": await get_stream_metrics(stream.id)
            }
            for stream in streams
        ]
    }

@router.get("/channel/{channel_id}/earnings")
async def get_channel_earnings(
    channel_id: str,
    days: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    start_date = datetime.utcnow() - timedelta(days=days if days is not None else 30)
    streams = db.query(Stream).filter(
        Stream.channel_id == channel_id,
        Stream.created_at >= start_date
    ).all()
    
    earnings = {
        "donations": 0,
        "super_chats": 0,
        "subscriptions": 0,
        "total": 0
    }
    
    for stream in streams:
        for payment in getattr(stream, "payments", []):
            amount = payment.get("amount", 0)
            payment_type = payment.get("type")
            if payment_type in earnings:
                earnings[payment_type] += amount
                earnings["total"] += amount
    
    history = []
    current_date = start_date
    while current_date <= datetime.utcnow():
        day_earnings = {
            "date": current_date.date().isoformat(),
            "amount": sum(
                payment.get("amount", 0)
                for stream in streams
                for payment in getattr(stream, "payments", [])
                if datetime.fromisoformat(payment.get("created_at")).date() == current_date.date()
            )
        }
        history.append(day_earnings)
        current_date += timedelta(days=1)
    
    return {
        "summary": earnings,
        "history": history,
        "top_donors": [
            {
                "user_id": payment.get("user_id"),
                "amount": payment.get("amount"),
                "type": payment.get("type")
            }
            for stream in streams
            for payment in sorted(
                getattr(stream, "payments", []),
                key=lambda x: x.get("amount", 0),
                reverse=True
            )[:10]
        ]
    }
