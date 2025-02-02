from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.orm import Session
import httpx
from datetime import datetime, timedelta
import os

from ..db.database import get_db
from ..db.models import SocialAccount
from ..db.init_mock_data import MOCK_USER_ID

router = APIRouter(prefix="/auth/social", tags=["social"])

FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")
TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")

async def verify_facebook_token(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.facebook.com/v18.0/me",
            params={
                "fields": "id,email,name",
                "access_token": access_token
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Facebook token")
        return response.json()

async def verify_twitter_token(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.twitter.com/2/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Twitter token")
        return response.json()

@router.post("/facebook")
async def facebook_login(
    access_token: str,
    db: Session = Depends(get_db)
) -> dict:
    user_data = await verify_facebook_token(access_token)
    
    social_account = db.query(SocialAccount).filter(
        SocialAccount.provider == "facebook",
        SocialAccount.provider_user_id == user_data["id"]
    ).first()
    
    if not social_account:
        user = User(
            email=user_data.get("email"),
            username=f"fb_{user_data['id']}",
            is_active=True
        )
        db.add(user)
        db.flush()
        
        social_account = SocialAccount(
            user_id=MOCK_USER_ID,
            provider="facebook",
            provider_user_id=user_data["id"],
            access_token=access_token,
            expires_at=datetime.utcnow() + timedelta(days=60)
        )
        db.add(social_account)
        db.commit()
    else:
        social_account.access_token = access_token
        social_account.expires_at = datetime.utcnow() + timedelta(days=60)
        db.commit()
    
    access_token = create_access_token(data={"sub": str(social_account.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/twitter")
async def twitter_login(
    access_token: str,
    db: Session = Depends(get_db)
) -> dict:
    user_data = await verify_twitter_token(access_token)
    
    social_account = db.query(SocialAccount).filter(
        SocialAccount.provider == "twitter",
        SocialAccount.provider_user_id == user_data["data"]["id"]
    ).first()
    
    if not social_account:
        user = User(
            username=f"tw_{user_data['data']['id']}",
            is_active=True
        )
        db.add(user)
        db.flush()
        
        social_account = SocialAccount(
            user_id=MOCK_USER_ID,
            provider="twitter",
            provider_user_id=user_data["data"]["id"],
            access_token=access_token
        )
        db.add(social_account)
        db.commit()
    else:
        social_account.access_token = access_token
        db.commit()
    
    access_token = create_access_token(data={"sub": str(social_account.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/facebook/url")
def facebook_login_url() -> dict:
    if not FACEBOOK_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Facebook authentication not configured")
    
    redirect_uri = f"{os.getenv('PUBLIC_URL')}/auth/callback/facebook"
    url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={FACEBOOK_CLIENT_ID}&redirect_uri={redirect_uri}&scope=email,public_profile"
    return {"url": url}

@router.get("/twitter/url")
def twitter_login_url() -> dict:
    if not TWITTER_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Twitter authentication not configured")
    
    redirect_uri = f"{os.getenv('PUBLIC_URL')}/auth/callback/twitter"
    url = f"https://twitter.com/i/oauth2/authorize?client_id={TWITTER_CLIENT_ID}&redirect_uri={redirect_uri}&scope=tweet.read%20users.read&response_type=code"
    return {"url": url}

@router.get("/callback/facebook")
async def facebook_callback(
    code: str,
    db: Session = Depends(get_db)
) -> dict:
    if not FACEBOOK_CLIENT_ID or not FACEBOOK_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Facebook authentication not configured")
    
    redirect_uri = f"{os.getenv('PUBLIC_URL')}/auth/callback/facebook"
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "client_id": FACEBOOK_CLIENT_ID,
                "client_secret": FACEBOOK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Facebook access token")
        
        token_data = token_response.json()
        return await facebook_login(token_data["access_token"], db)

@router.get("/callback/twitter")
async def twitter_callback(
    code: str,
    db: Session = Depends(get_db)
) -> dict:
    if not TWITTER_CLIENT_ID or not TWITTER_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Twitter authentication not configured")
    
    redirect_uri = f"{os.getenv('PUBLIC_URL')}/auth/callback/twitter"
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://api.twitter.com/2/oauth2/token",
            data={
                "code": code,
                "grant_type": "authorization_code",
                "client_id": TWITTER_CLIENT_ID,
                "client_secret": TWITTER_CLIENT_SECRET,
                "redirect_uri": redirect_uri
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Twitter access token")
        
        token_data = token_response.json()
        return await twitter_login(token_data["access_token"], db)
