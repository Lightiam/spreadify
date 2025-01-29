from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, RedirectResponse
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
import logging
from urllib.parse import urlparse, quote
from ..schemas.auth import Token, TokenData, UserBase, UserCreate, UserUpdate
from ..crud import user as crud
from ..database import get_db
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config
from starlette.requests import Request

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
PUBLIC_URL = os.getenv('PUBLIC_URL', 'https://stream-live-app-xabl732t.devinapps.com')
OAUTH_REDIRECT_URL = os.getenv('OAUTH_REDIRECT_URL', f"{PUBLIC_URL}/auth/callback")

# Configure allowed JavaScript origins and OAuth settings
ALLOWED_ORIGINS = [
    'https://stream-live-app-xabl732t.devinapps.com',
    'http://localhost:5173',
    'http://localhost:3000'
]

# Configure OAuth client
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'consent',  # Always show consent screen
        'access_type': 'offline',  # Request refresh token
    },
    authorize_params={
        'include_granted_scopes': 'true',  # Include previously granted scopes
        'response_type': 'code',  # Request authorization code
    }
)

# OAuth configuration is now handled above

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
async def login_google(request: Request, state: str = Query(None)):
    """Initialize Google OAuth flow."""
    try:
        logger.info(f"Starting Google OAuth flow with callback URL: {OAUTH_REDIRECT_URL}")
        
        # Validate state parameter
        if not state:
            logger.error("Missing state parameter")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing state parameter"
            )
            
        # Store state in session for verification
        request.session['oauth_state'] = state
        
        # Initialize the OAuth flow with proper configuration
        redirect_uri = await oauth.google.authorize_redirect(
            request,
            OAUTH_REDIRECT_URL,
            access_type='offline',  # Request refresh token
            prompt='consent',  # Force consent screen
            include_granted_scopes='true',  # Include previously granted scopes
            state=state  # Include state parameter for CSRF protection
        )
        
        logger.info("Successfully initialized Google OAuth redirect")
        return redirect_uri
        
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        # Redirect to frontend with error
        error_message = quote(str(e))
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=oauth_failed&message={error_message}",
            status_code=status.HTTP_302_FOUND
        )

@router.get("/callback")
async def auth_callback(request: Request, state: str = Query(None), error: str = Query(None), error_description: str = Query(None)):
    """Handle the OAuth callback from Google."""
    try:
        # Check for OAuth error response
        if error:
            error_msg = error_description or error
            logger.error(f"OAuth error: {error_msg}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error={quote(error)}&message={quote(error_msg)}",
                status_code=status.HTTP_302_FOUND
            )

        # Verify state parameter for CSRF protection
        stored_state = request.session.get('oauth_state')
        if not state or not stored_state or state != stored_state:
            logger.error("State parameter mismatch or missing")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=invalid_state&message={quote('Invalid state parameter')}",
                status_code=status.HTTP_302_FOUND
            )
        
        # Clear state from session
        request.session.pop('oauth_state', None)
        
        try:
            # Get the token from Google
            token = await oauth.google.authorize_access_token(request)
            if not token:
                raise ValueError("Failed to get token from Google")

            # Get user info from ID token
            user = await oauth.google.parse_id_token(request, token)
            if not user:
                raise ValueError("Failed to get user info from Google")

            # Verify email is verified (Google security requirement)
            if not user.get('email_verified'):
                raise ValueError("Email not verified with Google")
        except Exception as e:
            logger.error(f"OAuth token/user error: {str(e)}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=auth_failed&message={quote(str(e))}",
                status_code=status.HTTP_302_FOUND
            )

        # Create our application's access token with all necessary user info
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user["sub"],
                "email": user["email"],
                "name": user.get("name", ""),
                "picture": user.get("picture", ""),
                "email_verified": user["email_verified"]
            },
            expires_delta=access_token_expires
        )

        # Create response with user info and token
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        redirect_url = f"{frontend_url}/studio?token={access_token}"
        response = RedirectResponse(url=redirect_url)

        # Set secure cookie with token
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600,  # 1 hour
            domain=urlparse(frontend_url).netloc
        )

        return response

    except OAuthError as e:
        error_message = quote(str(e))
        logger.error(f"OAuth error: {error_message}")
        return RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed&message={error_message}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        error_message = quote("Authentication failed")
        logger.error(f"Auth callback error: {str(e)}")
        return RedirectResponse(
            url=f"{frontend_url}/login?error=server_error&message={error_message}",
            status_code=status.HTTP_302_FOUND
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
