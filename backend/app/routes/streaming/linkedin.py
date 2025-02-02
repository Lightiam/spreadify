from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import os
from datetime import datetime

from ...db import get_db
from ...auth import get_current_user
from ...db.models import SocialAccount, Stream

router = APIRouter(prefix="/streaming/linkedin", tags=["streaming"])

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")

async def get_linkedin_token(db: Session, user_id: str) -> str:
    social_account = db.query(SocialAccount).filter(
        SocialAccount.user_id == user_id,
        SocialAccount.provider == "linkedin"
    ).first()
    
    if not social_account:
        raise HTTPException(status_code=400, detail="LinkedIn account not connected")
        
    return social_account.access_token

@router.post("/start")
async def start_linkedin_stream(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    if stream.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    access_token = await get_linkedin_token(db, current_user.id)
    
    async with httpx.AsyncClient() as client:
        # Get user profile
        profile_response = await client.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if profile_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get LinkedIn profile")
            
        profile = profile_response.json()
        
        # Create live stream
        stream_response = await client.post(
            "https://api.linkedin.com/v2/livestreams",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "title": stream.title,
                "description": stream.description,
                "visibility": "PUBLIC"
            }
        )
        
        if stream_response.status_code != 201:
            raise HTTPException(status_code=400, detail="Failed to create LinkedIn stream")
            
        stream_data = stream_response.json()
        
        return {
            "stream_id": stream_data["id"],
            "stream_url": stream_data["rtmpUrl"],
            "stream_key": stream_data["streamKey"]
        }

@router.post("/stop/{stream_id}")
async def stop_linkedin_stream(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    access_token = await get_linkedin_token(db, current_user.id)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.linkedin.com/v2/livestreams/{stream_id}/end",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=400, detail="Failed to stop LinkedIn stream")
            
        return {"status": "success"}
