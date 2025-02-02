from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from ..db.models import Stream, Overlay, Channel
from ..db.database import get_db
from pydantic import BaseModel
from uuid import UUID, uuid4
import os
import aiofiles
import subprocess
from pathlib import Path
from fastapi.responses import FileResponse

class OverlayBase(BaseModel):
    position_x: int
    position_y: int
    scale: int

class OverlayUpdate(BaseModel):
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    scale: Optional[int] = None
    active: Optional[bool] = None

class OverlayResponse(BaseModel):
    id: UUID
    stream_id: UUID
    path: str
    position_x: int
    position_y: int
    scale: int
    active: bool = True
    
    class Config:
        from_attributes = True

router = APIRouter(prefix="/overlays", tags=["overlays"])

UPLOAD_DIR = Path("uploads/overlays")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/system/check")
async def check_ffmpeg():
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "status": "ok",
            "ffmpeg_version": result.stdout.split('\n')[0],
            "overlay_support": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FFmpeg not properly configured: {str(e)}"
        )

@router.post("/{stream_id}", response_model=OverlayResponse)
async def create_overlay(
    stream_id: UUID,
    position_x: int = Form(...),
    position_y: int = Form(...),
    scale: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
        
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["png", "jpg", "jpeg", "gif"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Supported types: PNG, JPG, JPEG, GIF"
        )
    
    # Generate unique filename
    file_id = uuid4()
    file_path = UPLOAD_DIR / f"{file_id}.{file_ext}"
    
    try:
        # Save file
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
        
        # Create overlay record
        overlay = Overlay(
            id=uuid4(),
            stream_id=stream_id,
            path=str(file_path.relative_to(UPLOAD_DIR)),
            position_x=position_x,
            position_y=position_y,
            scale=scale,
            active=True
        )
        
        db.add(overlay)
        db.commit()
        db.refresh(overlay)
        return overlay
        
    except Exception as e:
        # Clean up the file if database operation fails
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create overlay: {str(e)}"
        )

@router.patch("/{overlay_id}", response_model=OverlayResponse)
async def update_overlay(
    overlay_id: UUID,
    update_data: OverlayUpdate,
    db: Session = Depends(get_db)
):
    overlay = db.query(Overlay).filter(Overlay.id == overlay_id).first()
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")
    
    stream = db.query(Stream).filter(Stream.id == overlay.stream_id).first()
    channel = db.query(Channel).filter(Channel.id == stream.channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    if update_data.position_x is not None:
        overlay.position_x = update_data.position_x
    if update_data.position_y is not None:
        overlay.position_y = update_data.position_y
    if update_data.scale is not None:
        overlay.scale = update_data.scale
    if update_data.active is not None:
        overlay.active = update_data.active
    
    db.commit()
    db.refresh(overlay)
    
    return overlay

@router.delete("/{overlay_id}")
async def delete_overlay(
    overlay_id: UUID,
    db: Session = Depends(get_db)
):
    overlay = db.query(Overlay).filter(Overlay.id == overlay_id).first()
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")
    
    stream = db.query(Stream).filter(Stream.id == overlay.stream_id).first()
    channel = db.query(Channel).filter(Channel.id == stream.channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    file_path = UPLOAD_DIR / overlay.path
    try:
        file_path.unlink(missing_ok=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete overlay file: {str(e)}"
        )
    
    db.delete(overlay)
    db.commit()
    
    return {"status": "success"}

@router.get("/{stream_id}", response_model=List[OverlayResponse])
async def get_overlays(
    stream_id: UUID,
    db: Session = Depends(get_db)
):
    overlays = db.query(Overlay).filter(
        Overlay.stream_id == stream_id,
        Overlay.active == True
    ).all()
    return overlays

@router.get("/file/{filename}")
async def get_overlay_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overlay file not found"
        )
    
    # Determine media type based on file extension
    ext = filename.lower().split('.')[-1]
    media_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif'
    }
    media_type = media_types.get(ext, 'application/octet-stream')
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename
    )
