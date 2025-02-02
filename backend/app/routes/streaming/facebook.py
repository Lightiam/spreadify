from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, cast

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session
from ...db.database import get_db
from ...db.init_mock_data import MOCK_USER_ID
from ...db.models import SocialAccount, Stream

router = APIRouter(prefix="/streaming/facebook", tags=["streaming"])

async def get_facebook_token(db: Session, user_id: str) -> str:
    social_account = db.query(SocialAccount).filter(
        SocialAccount.user_id == user_id,
        SocialAccount.provider == "facebook"
    ).first()
    
    if not social_account:
        raise HTTPException(status_code=400, detail="Facebook account not connected")
        
    return str(social_account.access_token)

@router.post("/start")
async def start_facebook_stream(
    stream_id: str,
    db: Session = Depends(get_db)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    try:
        access_token = await get_facebook_token(db, "anonymous")
    except Exception as e:
        logger.error(f"Failed to get Facebook token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authenticate with Facebook"
        )
    
    async with httpx.AsyncClient() as client:
        # Create Facebook Live video
        response = await client.post(
            "https://graph.facebook.com/v18.0/me/live_videos",
            params=cast(Dict[str, str], {"access_token": access_token}),
            json={
                "title": stream.title,
                "description": stream.description,
                "status": "LIVE_NOW"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to create Facebook Live video")
            
        live_video = response.json()
        
        return {
            "stream_id": live_video["id"],
            "stream_url": live_video["stream_url"],
            "secure_stream_url": live_video["secure_stream_url"],
            "stream_key": live_video.get("stream_key")
        }

@router.post("/stop/{live_video_id}")
async def stop_facebook_stream(
    live_video_id: str,
    db: Session = Depends(get_db)
):
    access_token = await get_facebook_token(db, "anonymous")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.facebook.com/v18.0/{live_video_id}",
            params=cast(Dict[str, str], {
                "access_token": access_token,
                "end_live_video": "true"
            })
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to stop Facebook stream")
            
        return {"status": "success"}
