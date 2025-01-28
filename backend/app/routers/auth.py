from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, RedirectResponse
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from ..schemas.auth import Token, TokenData, UserBase
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config
from starlette.requests import Request

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth2 configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configure Google OAuth - use environment variables directly
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
JWT_SECRET = os.environ.get('JWT_SECRET')

print("\nAuth Router - Environment variables:")
print(f"GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID}")
print(f"GOOGLE_CLIENT_SECRET: {GOOGLE_CLIENT_SECRET}")
print(f"JWT_SECRET: {JWT_SECRET}")

# Initialize OAuth configuration
oauth = OAuth()

# Get environment-specific configuration
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
PUBLIC_URL = os.getenv('PUBLIC_URL', 'https://stream-live-app-tunnel-x1l3blok.devinapps.com')
OAUTH_REDIRECT_URL = os.getenv('OAUTH_REDIRECT_URL', f"{PUBLIC_URL}/auth/callback")

oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'
    }
)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv('JWT_SECRET'), algorithm=ALGORITHM)
    return encoded_jwt

@router.get("/login/google")
async def login_google(request: Request):
    try:
        # Use public URL for callback
        callback_url = OAUTH_REDIRECT_URL
        print(f"Using callback URL: {callback_url}")
        
        # Initialize the OAuth flow
        redirect_uri = await oauth.google.authorize_redirect(
            request,
            callback_url,
            scope="openid email profile"
        )
        return redirect_uri
    except Exception as e:
        print(f"Google login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Google login: {str(e)}"
        )

@router.get("/callback")
async def auth_callback(request: Request):
    try:
        # Get the token from Google
        token = await oauth.google.authorize_access_token(request)
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get token from Google"
            )
            
        # Get user info from ID token
        user = await oauth.google.parse_id_token(request, token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info from Google"
            )
        
        # Create our application's access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user["sub"],
                "email": user["email"],
                "name": user.get("name"),
                "picture": user.get("picture")
            },
            expires_delta=access_token_expires
        )
        
        # Create response with user info and token
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        
        # Create redirect response
        redirect_url = f"{frontend_url}/login?code={access_token}"
        response = RedirectResponse(url=redirect_url)
        
        # Set secure cookie with token
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600  # 1 hour
        )
        
        return response
        
    except OAuthError as e:
        print(f"OAuth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth authentication failed: {str(e)}"
        )
    except Exception as e:
        print(f"Auth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to server error"
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserBase:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=[ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, sub=payload.get("sub"))
    except JWTError:
        raise credentials_exception
    return UserBase(email=token_data.email)

@router.get("/me", response_model=UserBase)
async def get_current_user_info(current_user: UserBase = Depends(get_current_user)):
    return current_user

@router.get("/test-token")
async def get_test_token():
    """Generate a test token for WebSocket testing."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": "test-user",
            "email": "test@example.com",
            "name": "Test User"
        },
        expires_delta=access_token_expires
    )
    return access_token
