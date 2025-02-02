from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import os
import jwt
from datetime import datetime, timedelta

from ...db import get_db
from ...auth import get_current_user

router = APIRouter(prefix="/music/apple", tags=["music"])

APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID")
APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY")

async def get_developer_token() -> str:
    if not all([APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY]):
        raise HTTPException(status_code=500, detail="Apple Music is not configured")
        
    now = datetime.utcnow()
    exp = now + timedelta(hours=24)
    
    token = jwt.encode(
        {
            "iss": APPLE_TEAM_ID,
            "iat": now,
            "exp": exp,
        },
        APPLE_PRIVATE_KEY,
        algorithm="ES256",
        headers={
            "kid": APPLE_KEY_ID,
        }
    )
    
    return token

@router.get("/now-playing")
async def get_now_playing(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    social_account = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id,
        SocialAccount.provider == "apple_music"
    ).first()
    
    if not social_account:
        raise HTTPException(status_code=400, detail="Apple Music not connected")
    
    developer_token = await get_developer_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.music.apple.com/v1/me/player/now-playing",
            headers={
                "Authorization": f"Bearer {developer_token}",
                "Music-User-Token": social_account.access_token
            }
        )
        
        if response.status_code == 204:
            return None
        elif response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get current track")
            
        return response.json()

@router.post("/play")
async def play_track(
    track_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    social_account = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id,
        SocialAccount.provider == "apple_music"
    ).first()
    
    if not social_account:
        raise HTTPException(status_code=400, detail="Apple Music not connected")
    
    developer_token = await get_developer_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.music.apple.com/v1/me/player/play",
            headers={
                "Authorization": f"Bearer {developer_token}",
                "Music-User-Token": social_account.access_token
            },
            json={
                "data": {
                    "id": track_id,
                    "type": "songs"
                }
            }
        )
        
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="Failed to play track")
            
        return {"status": "success"}
