from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables before anything else
env_path = Path(__file__).resolve().parent.parent / '.env'
print(f"Looking for .env at: {env_path}")
print(f"File exists: {env_path.exists()}")

if not env_path.exists():
    raise FileNotFoundError(f".env file not found at {env_path}")

# Read and set environment variables directly
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')
            except ValueError:
                continue

# Debug environment variables
print("\nEnvironment variables after loading:")
print(f"GOOGLE_CLIENT_ID: {os.environ.get('GOOGLE_CLIENT_ID')}")
print(f"GOOGLE_CLIENT_SECRET: {os.environ.get('GOOGLE_CLIENT_SECRET')}")
print(f"JWT_SECRET: {os.environ.get('JWT_SECRET')}")
print(f"FRONTEND_URL: {os.environ.get('FRONTEND_URL')}")

# Import routers after environment variables are loaded
from .routers import auth, streams, webrtc, stripe

# Initialize FastAPI app with configuration
app = FastAPI(
    title="Spreadify AI",
    description="A multi-platform live streaming and recording platform",
    version="1.0.0"
)

# Get frontend URLs from environment
FRONTEND_URLS = json.loads(os.environ.get("CORS_ORIGINS", '["http://localhost:5173", "http://localhost:3000"]'))
if isinstance(FRONTEND_URLS, str):
    FRONTEND_URLS = [FRONTEND_URLS]

# Ensure all required URLs are included
required_urls = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://stream-live-app-tunnel-x1l3blok.devinapps.com",
    "https://stream-live-app-xabl732t.devinapps.com"
]

for url in required_urls:
    if url not in FRONTEND_URLS:
        FRONTEND_URLS.append(url)

print("\nConfigured CORS Origins:", FRONTEND_URLS)

# Add session middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class WebSocketUpgradeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "upgrade" in request.headers.get("connection", "").lower():
            return await call_next(request)
        response = await call_next(request)
        return response

app.add_middleware(WebSocketUpgradeMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("JWT_SECRET"),
    same_site='lax',  # Allow cross-site cookies for OAuth
    https_only=False  # Set to True in production
)

# Configure CORS middleware with frontend URLs and WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=[*FRONTEND_URLS, "https://accounts.google.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Cookie",
        "Set-Cookie",
        # WebSocket headers
        "Sec-WebSocket-Extensions",
        "Sec-WebSocket-Key",
        "Sec-WebSocket-Version",
        "Sec-WebSocket-Protocol",
        "Sec-WebSocket-Accept",
        "Upgrade",
        "Connection",
        # Additional headers for WebSocket auth
        "X-Token",
        "Authorization",
    ],
    expose_headers=[
        "Content-Type",
        "Authorization",
        "Location",
        "Set-Cookie",
        # WebSocket headers
        "Sec-WebSocket-Accept",
        "Sec-WebSocket-Protocol",
        "Upgrade",
        "Connection",
        # Additional headers for WebSocket auth
        "X-Token",
        "Authorization",
    ],
    allow_origin_regex=r"https://accounts\.google\.com.*",
    max_age=3600,
)

# Load environment variables
load_dotenv()

# Include routers
app.include_router(auth.router)
app.include_router(streams.router)
app.include_router(webrtc.router)
app.include_router(stripe.router)

# Verify environment variables after router initialization
required_env_vars = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "JWT_SECRET",
    "FRONTEND_URL",
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print("Warning: Missing environment variables:", ', '.join(missing_vars))
    print("Current environment:")
    for var in required_env_vars:
        print(f"{var}: {'Set' if os.getenv(var) else 'Not set'}")

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
