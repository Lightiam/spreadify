from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Dict, Set, Optional
from sqlalchemy.orm import Session
from ..db.models import Stream, Channel
from ..db.database import get_db
import json
import asyncio
from datetime import datetime

router = APIRouter(prefix="/signaling", tags=["signaling"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.stream_peers: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, stream_id: str, peer_id: str):
        await websocket.accept()
        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = {}
            self.stream_peers[stream_id] = set()
        self.active_connections[stream_id][peer_id] = websocket
        self.stream_peers[stream_id].add(peer_id)
        
    async def disconnect(self, stream_id: str, peer_id: str):
        if stream_id in self.active_connections and peer_id in self.active_connections[stream_id]:
            del self.active_connections[stream_id][peer_id]
            self.stream_peers[stream_id].remove(peer_id)
            if not self.active_connections[stream_id]:
                del self.active_connections[stream_id]
                del self.stream_peers[stream_id]
                
    async def broadcast_message(self, stream_id: str, message: dict, exclude_peer: Optional[str] = None):
        if stream_id in self.active_connections:
            for peer_id, connection in self.active_connections[stream_id].items():
                if peer_id != exclude_peer:
                    try:
                        await connection.send_json(message)
                    except:
                        await self.disconnect(stream_id, peer_id)

manager = ConnectionManager()

@router.websocket("/{stream_id}/{peer_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    stream_id: str,
    peer_id: str,
    db: Session = Depends(get_db)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    try:
        await manager.connect(websocket, stream_id, peer_id)
        await manager.broadcast_message(
            stream_id,
            {
                "type": "peer_joined",
                "peer_id": peer_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_peer=peer_id
        )
        
        try:
            while True:
                message = await websocket.receive_json()
                if message.get("type") in ["offer", "answer", "ice-candidate"]:
                    await manager.broadcast_message(
                        stream_id,
                        {
                            **message,
                            "peer_id": peer_id,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        exclude_peer=peer_id
                    )
        except WebSocketDisconnect:
            await manager.disconnect(stream_id, peer_id)
            await manager.broadcast_message(
                stream_id,
                {
                    "type": "peer_left",
                    "peer_id": peer_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        await manager.disconnect(stream_id, peer_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@router.get("/{stream_id}/peers")
async def get_peers(
    stream_id: str,
    db: Session = Depends(get_db)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    channel = db.query(Channel).filter(Channel.id == stream.channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    return {
        "peers": list(manager.stream_peers.get(stream_id, set())),
        "timestamp": datetime.utcnow().isoformat()
    }
