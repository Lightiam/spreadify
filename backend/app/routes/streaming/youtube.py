from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from ...db import get_db
from ...auth import get_current_user
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
        
    if social_account.expires_at <= datetime.utcnow():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "refresh_token": social_account.refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to refresh YouTube token")
                
            token_data = response.json()
            social_account.access_token = token_data["access_token"]
            social_account.expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            db.commit()
            
    return social_account.access_token

@router.post("/start")
async def start_youtube_stream(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    if stream.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    access_token = await get_youtube_token(db, current_user.id)
    
    # Create YouTube broadcast
    async with httpx.AsyncClient() as client:
        broadcast_response = await client.post(
            "https://www.googleapis.com/youtube/v3/liveBroadcasts",
            headers=cast(Dict[str, str], {"Authorization": f"Bearer {access_token}"}),
            json={
                "snippet": {
                    "title": stream.title,
                    "description": stream.description,
                    "scheduledStartTime": stream.scheduled_for.isoformat() if stream.scheduled_for else None
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
            headers=cast(Dict[str, str], {"Authorization": f"Bearer {access_token}"}),
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
            headers=cast(Dict[str, str], {"Authorization": f"Bearer {access_token}"}),
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    access_token = await get_youtube_token(db, current_user.id)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition",
            headers=cast(Dict[str, str], {"Authorization": f"Bearer {access_token}"}),
            params={
                "id": broadcast_id,
                "broadcastStatus": "complete",
                "part": "id,status"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to stop YouTube stream")
            
        return {"status": "success"}
