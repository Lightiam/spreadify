from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, cast

logger = logging.getLogger(__name__)

from ...db import get_db
from ...auth import get_current_user
from ...db.models import SocialAccount, Stream

router = APIRouter(prefix="/streaming/twitch", tags=["streaming"])

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

async def get_twitch_token(db: Session, user_id: str) -> str:
    social_account = db.query(SocialAccount).filter(
        SocialAccount.user_id == user_id,
        SocialAccount.provider == "twitch"
    ).first()
    
    if not social_account:
        raise HTTPException(status_code=400, detail="Twitch account not connected")
        
    if social_account.expires_at <= datetime.utcnow():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": TWITCH_CLIENT_ID,
                    "client_secret": TWITCH_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": social_account.refresh_token
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to refresh Twitch token")
                
            token_data = response.json()
            social_account.access_token = token_data["access_token"]
            social_account.refresh_token = token_data["refresh_token"]
            social_account.expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            db.commit()
            
    return social_account.access_token

@router.post("/start")
async def start_twitch_stream(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    if stream.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    access_token = await get_twitch_token(db, current_user.id)
    
    async with httpx.AsyncClient() as client:
        # Get user channel info
        headers = cast(Dict[str, str], {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }) if TWITCH_CLIENT_ID else {}
        
        user_response = await client.get(
            "https://api.twitch.tv/helix/users",
            headers=headers
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Twitch user info")
            
        user_data = user_response.json()["data"][0]
        
        # Update stream info
        stream_response = await client.patch(
            f"https://api.twitch.tv/helix/channels?broadcaster_id={user_data['id']}",
            headers=headers,
            json={
                "title": stream.title,
                "game_id": "0",
                "broadcaster_language": "en"
            }
        )
        
        if stream_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to update Twitch stream info")
        
        # Get stream key
        key_response = await client.get(
            "https://api.twitch.tv/helix/streams/key",
            headers=headers
        )
        
        if key_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Twitch stream key")
            
        stream_key = key_response.json()["data"][0]["stream_key"]
        
        return {
            "stream_url": "rtmp://live.twitch.tv/app/",
            "stream_key": stream_key
        }

@router.post("/stop")
async def stop_twitch_stream(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    access_token = await get_twitch_token(db, current_user.id)
    
    async with httpx.AsyncClient() as client:
        headers = cast(Dict[str, str], {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }) if TWITCH_CLIENT_ID else {}
        
        response = await client.delete(
            "https://api.twitch.tv/helix/streams",
            headers=headers
        )
        
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="Failed to stop Twitch stream")
            
        return {"status": "success"}
