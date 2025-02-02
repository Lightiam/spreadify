from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from .routes import auth, rtmp, schedules, overlays
from .db import init_db

load_dotenv()

app = FastAPI(
    title="Spreadify API",
    description="Backend API for Spreadify streaming platform",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    init_db()

# Configure CORS with environment variables
cors_origins = os.getenv("CORS_ORIGINS")
if cors_origins:
    try:
        origins = eval(cors_origins)  # Safely evaluate the string list
    except:
        origins = ["*"]  # Fallback to all origins if parsing fails
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rtmp.router)
app.include_router(schedules.router)
app.include_router(overlays.router)

# Mount static files for uploads
os.makedirs("uploads/profile_pictures", exist_ok=True)
os.makedirs("uploads/streams", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {
        "status": "ok",
        "environment": os.getenv("ENV", "development"),
        "version": "1.0.0"
    }
