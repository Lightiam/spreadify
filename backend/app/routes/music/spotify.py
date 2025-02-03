from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import os
from datetime import datetime, timedelta

from ...db.database import get_db
from ...db.models import SocialAccount
from ...db.init_mock_data import MOCK_USER_ID
import urllib.parse

router = APIRouter(prefix="/music/spotify", tags=["music"])

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = (os.getenv("PUBLIC_URL") or "") + "/auth/callback/spotify"

async def get_spotify_token(refresh_token: str = None) -> dict:
    async with httpx.AsyncClient() as client:
        if refresh_token:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            }
        else:
            data = {
                "grant_type": "client_credentials",
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            }
            
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data=data
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get Spotify token")
        return response.json()

@router.get("/auth-url")
async def get_spotify_auth_url():
    if not SPOTIFY_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Spotify is not configured")
        
    scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": scope
    }
    
    return {
        "url": f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}"
    }

@router.get("/callback")
async def spotify_callback(
    code: str,
    db: Session = Depends(get_db)
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Spotify token")
            
        token_data = response.json()
        
        # Store the tokens in the user's social accounts
        social_account = db.query(SocialAccount).filter(
            SocialAccount.user_id == MOCK_USER_ID,
            SocialAccount.provider == "spotify"
        ).first()
        
        if not social_account:
            social_account = SocialAccount(
                user_id=MOCK_USER_ID,
                provider="spotify",
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            )
            db.add(social_account)
        else:
            social_account.access_token = token_data["access_token"]
            social_account.refresh_token = token_data["refresh_token"]
            social_account.expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            
        db.commit()
        return {"status": "success"}

@router.get("/now-playing")
async def get_now_playing(
    db: Session = Depends(get_db)
):
    social_account = db.query(SocialAccount).filter(
        SocialAccount.user_id == MOCK_USER_ID,
        SocialAccount.provider == "spotify"
    ).first()
    
    if not social_account:
        raise HTTPException(status_code=400, detail="Spotify not connected")
        
    if social_account.expires_at <= datetime.utcnow():
        token_data = await get_spotify_token(social_account.refresh_token)
        social_account.access_token = token_data["access_token"]
        social_account.expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        db.commit()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers={"Authorization": f"Bearer {social_account.access_token}"}
        )
        
        if response.status_code == 204:
            return None
        elif response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get current track")
            
        return response.json()

@router.post("/play")
async def play_track(
    track_uri: str,
    db: Session = Depends(get_db)
):
    social_account = db.query(SocialAccount).filter(
        SocialAccount.user_id == MOCK_USER_ID,
        SocialAccount.provider == "spotify"
    ).first()
    
    if not social_account:
        raise HTTPException(status_code=400, detail="Spotify not connected")
        
    if social_account.expires_at <= datetime.utcnow():
        token_data = await get_spotify_token(social_account.refresh_token)
        social_account.access_token = token_data["access_token"]
        social_account.expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        db.commit()
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            "https://api.spotify.com/v1/me/player/play",
            headers={"Authorization": f"Bearer {social_account.access_token}"},
            json={"uris": [track_uri]}
        )
        
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="Failed to play track")
            
        return {"status": "success"}
