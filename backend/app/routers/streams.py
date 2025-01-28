from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict
import uuid
from datetime import datetime
from ..schemas.stream import Stream, StreamCreate
from ..schemas.auth import UserBase
from .auth import get_current_user

router = APIRouter(prefix="/streams", tags=["streams"])

# In-memory storage for streams and connections
streams: Dict[str, Stream] = {}
connections: Dict[str, List[WebSocket]] = {}

@router.post("/", response_model=Stream)
async def create_stream(
    stream: StreamCreate,
    current_user: UserBase = Depends(get_current_user)
):
    stream_id = str(uuid.uuid4())
    new_stream = Stream(
        id=stream_id,
        user_id=current_user.email,
        status="created",
        created_at=datetime.utcnow(),
        **stream.dict()
    )
    streams[stream_id] = new_stream
    return new_stream

@router.get("/", response_model=List[Stream])
async def list_streams(current_user: UserBase = Depends(get_current_user)):
    return [
        stream for stream in streams.values()
        if stream.user_id == current_user.email
    ]

@router.get("/{stream_id}", response_model=Stream)
async def get_stream(
    stream_id: str,
    current_user: UserBase = Depends(get_current_user)
):
    if stream_id not in streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    stream = streams[stream_id]
    if stream.user_id != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized")
    return stream

@router.websocket("/{stream_id}/ws")
async def websocket_endpoint(websocket: WebSocket, stream_id: str):
    await websocket.accept()
    if stream_id not in connections:
        connections[stream_id] = []
    connections[stream_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast the message to all connected clients
            for connection in connections[stream_id]:
                if connection != websocket:
                    await connection.send_json(data)
    except WebSocketDisconnect:
        connections[stream_id].remove(websocket)
        if not connections[stream_id]:
            del connections[stream_id]
