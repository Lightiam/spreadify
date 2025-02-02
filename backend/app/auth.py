from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from .models import User
from passlib.context import CryptContext
from .database import db
import os
import httpx
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth configurations
FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")
TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
OAUTH_REDIRECT_URL = os.getenv("OAUTH_REDIRECT_URL")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured"
        )
    encoded_jwt = jwt.encode(to_encode, jwt_secret, algorithm="HS256")
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)



async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT secret not configured"
            )
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        user_id = str(payload.get("sub"))
        if not user_id:
            raise credentials_exception
        user = await db.get_user(user_id)
        if not user:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

async def verify_facebook_token(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.facebook.com/me",
            params={
                "fields": "id,email,name",
                "access_token": access_token
            }
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Facebook token"
            )
        return response.json()

async def verify_twitter_token(oauth_token: str, oauth_verifier: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.twitter.com/oauth/access_token",
            params={
                "oauth_token": oauth_token,
                "oauth_verifier": oauth_verifier
            }
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Twitter token"
            )
        
        params = dict(x.split("=") for x in response.text.split("&"))
        
        headers = {
            "Authorization": f"Bearer {params['oauth_token']}"
        }
        response = await client.get(
            "https://api.twitter.com/2/users/me",
            headers=headers,
            params={"user.fields": "id,name,username,email"}
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get Twitter user info"
            )
        return response.json()

@router.post("/facebook")
async def facebook_auth(access_token: str):
    user_info = await verify_facebook_token(access_token)
    
    user = await db.get_user_by_email(user_info["email"])
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=user_info["email"],
            username=user_info["name"].replace(" ", "_").lower(),
            created_at=datetime.utcnow()
        )
        await db.create_user(user)
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(days=7)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/twitter")
async def twitter_auth(oauth_token: str, oauth_verifier: str):
    user_info = await verify_twitter_token(oauth_token, oauth_verifier)
    
    user = await db.get_user_by_email(user_info["data"]["email"])
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=user_info["data"]["email"],
            username=user_info["data"]["username"],
            created_at=datetime.utcnow()
        )
        await db.create_user(user)
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(days=7)
    )
    return {"access_token": access_token, "token_type": "bearer"}
