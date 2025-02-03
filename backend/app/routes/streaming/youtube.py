from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from ...db.database import get_db
from ...db.init_mock_data import MOCK_USER_ID
from ...db.models import SocialAccount, Stream

router = APIRouter(prefix="/streaming/youtube", tags=["streaming"])

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

async def get_youtube_token(db: Session, user_id: str) -> str:
    social_account = db.query(SocialAccount).filter(
        SocialAccount.user_id == user_id,
        SocialAccount.provider == "youtube"
    ).first()
    
    if not social_account:
        raise HTTPException(status_code=400, detail="YouTube account not connected")
        
    expires_at = getattr(social_account, 'expires_at', None)
    if expires_at and isinstance(expires_at, datetime) and expires_at <= datetime.utcnow():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "refresh_token": str(social_account.refresh_token),
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to refresh YouTube token")
                
            token_data = response.json()
            db.execute(
                update(SocialAccount)
                .where(SocialAccount.id == social_account.id)
                .values(
                    access_token=token_data["access_token"],
                    expires_at=datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
                )
            )
            db.commit()
            return token_data["access_token"]
            
    return str(social_account.access_token)

@router.post("/start")
async def start_youtube_stream(
    stream_id: str,
    db: Session = Depends(get_db)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    access_token = await get_youtube_token(db, "anonymous")
    
    # Create YouTube broadcast
    async with httpx.AsyncClient() as client:
        broadcast_response = await client.post(
            "https://www.googleapis.com/youtube/v3/liveBroadcasts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "snippet": {
                    "title": str(stream.title) if stream.title else "",
                    "description": str(stream.description) if stream.description else "",
                    "scheduledStartTime": stream.scheduled_for.isoformat() if getattr(stream, 'scheduled_for', None) and isinstance(stream.scheduled_for, datetime) else None
                },
                "status": {
                    "privacyStatus": "public"
                }
            }
        )
        
        if broadcast_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to create YouTube broadcast")
            
        broadcast_data = broadcast_response.json()
        
        # Create YouTube stream
        stream_response = await client.post(
            "https://www.googleapis.com/youtube/v3/liveStreams",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "snippet": {
                    "title": stream.title
                },
                "cdn": {
                    "frameRate": "variable",
                    "ingestionType": "rtmp",
                    "resolution": "variable"
                }
            }
        )
        
        if stream_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to create YouTube stream")
            
        stream_data = stream_response.json()
        
        # Bind broadcast and stream
        bind_response = await client.post(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "id": broadcast_data["id"],
                "streamId": stream_data["id"],
                "part": "id,contentDetails"
            }
        )
        
        if bind_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to bind YouTube broadcast and stream")
        
        return {
            "broadcast_id": broadcast_data["id"],
            "stream_id": stream_data["id"],
            "stream_url": stream_data["cdn"]["ingestionInfo"]["ingestionAddress"],
            "stream_key": stream_data["cdn"]["ingestionInfo"]["streamName"]
        }

@router.post("/stop/{broadcast_id}")
async def stop_youtube_stream(
    broadcast_id: str,
    db: Session = Depends(get_db)
):
    access_token = await get_youtube_token(db, "anonymous")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "id": broadcast_id,
                "broadcastStatus": "complete",
                "part": "id,status"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to stop YouTube stream")
            
        return {"status": "success"}
