from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from ..models import UserCreate, User
from ..auth import (
    create_access_token,
    get_current_user,
    verify_password,
    get_password_hash
)
from ..database import db
import uuid
import os
import httpx

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        username=user_data.username,
        password=get_password_hash(user_data.password),
        created_at=datetime.utcnow()
    )
    user = await db.create_user(user)
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=30)
    )
    
    return {"token": access_token, "user": user}



@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
