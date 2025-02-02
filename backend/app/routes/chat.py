from fastapi import APIRouter, WebSocket, Depends, HTTPException, status, WebSocketDisconnect
from typing import List, Dict, Optional, Tuple
from ..models import User
from ..auth import get_current_user
from ..database import db
from datetime import datetime, timedelta
import json
import re
import asyncio
from pydantic import BaseModel

# Rate limiting settings
RATE_LIMIT = 3  # messages
RATE_WINDOW = 5  # seconds

# Store message timestamps for rate limiting
message_timestamps: Dict[str, List[datetime]] = {}

class ChatCommand(BaseModel):
    name: str
    response: str

chat_commands: Dict[str, ChatCommand] = {
    "!help": ChatCommand(name="!help", response="Available commands: !help, !uptime"),
    "!uptime": ChatCommand(name="!uptime", response="Stream uptime: {uptime}")
}

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory storage for active chat connections
chat_connections: Dict[str, List[Tuple[WebSocket, str]]] = {}

def is_spam(message: str) -> bool:
    # Simple spam detection
    spam_patterns = [
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
        r'(.)\1{4,}',  # Repeated characters
        r'[A-Z]{5,}'  # ALL CAPS
    ]
    return any(re.search(pattern, message) for pattern in spam_patterns)

@router.websocket("/ws/{stream_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    stream_id: str,
    current_user: User = Depends(get_current_user)
):
    await websocket.accept()
    
    if stream_id not in chat_connections:
        chat_connections[stream_id] = []
    chat_connections[stream_id].append((websocket, current_user.id))
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Rate limiting check
            now = datetime.utcnow()
            if current_user.id not in message_timestamps:
                message_timestamps[current_user.id] = []
            
            # Remove old timestamps
            message_timestamps[current_user.id] = [
                ts for ts in message_timestamps[current_user.id]
                if now - ts < timedelta(seconds=RATE_WINDOW)
            ]
            
            if len(message_timestamps[current_user.id]) >= RATE_LIMIT:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Rate limit exceeded. Please wait {RATE_WINDOW} seconds."
                }))
                continue
            
            message_timestamps[current_user.id].append(now)
            msg_content = message.get("message", "")
            
            # Check if message is spam
            if is_spam(msg_content):
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Your message was flagged as spam"
                }))
                continue
            
            # Handle chat commands
            if msg_content.startswith("!"):
                command = msg_content.split()[0]
                if command in chat_commands:
                    stream = await db.get_stream(stream_id)
                    if command == "!uptime" and stream and stream.started_at:
                        uptime = datetime.utcnow() - stream.started_at
                        response = chat_commands[command].response.format(
                            uptime=str(uptime).split(".")[0]
                        )
                    else:
                        response = chat_commands[command].response
                    
                    await websocket.send_text(json.dumps({
                        "type": "command",
                        "message": response
                    }))
                    continue
            
            # Create chat message
            chat_message = {
                "type": "chat",
                "user_id": current_user.id,
                "username": current_user.username,
                "message": message.get("message", ""),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store message
            await db.store_chat_message(stream_id, chat_message)
            
            # Broadcast to non-blocked clients
            for connection, user_id in chat_connections[stream_id]:
                if not await db.is_user_blocked(user_id, current_user.id):
                    await connection.send_text(json.dumps(chat_message))
    except WebSocketDisconnect:
        if stream_id in chat_connections:
            chat_connections[stream_id].remove((websocket, current_user.id))
            if not chat_connections[stream_id]:
                del chat_connections[stream_id]
            
            # Notify other users
            for conn, _ in chat_connections.get(stream_id, []):
                try:
                    await conn.send_text(json.dumps({
                        "type": "system",
                        "message": f"{current_user.username} left the chat"
                    }))
                except:
                    pass
    except Exception as e:
        if stream_id in chat_connections:
            chat_connections[stream_id].remove((websocket, current_user.id))
            if not chat_connections[stream_id]:
                del chat_connections[stream_id]
        print(f"Chat error: {str(e)}")

@router.post("/commands")
async def create_chat_command(
    command: ChatCommand,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only moderators can create chat commands"
        )
    
    if not command.name.startswith("!"):
        command.name = "!" + command.name
        
    chat_commands[command.name] = command
    return command

@router.delete("/commands/{command_name}")
async def delete_chat_command(
    command_name: str,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only moderators can delete chat commands"
        )
        
    if not command_name.startswith("!"):
        command_name = "!" + command_name
        
    if command_name in chat_commands:
        del chat_commands[command_name]
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Command not found")

@router.post("/{stream_id}/block")
async def block_user(
    stream_id: str,
    blocked_user_id: str,
    current_user: User = Depends(get_current_user)
):
    stream = await db.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Block user
    await db.block_user(current_user.id, blocked_user_id)
    return {"status": "success"}

@router.post("/{stream_id}/unblock")
async def unblock_user(
    stream_id: str,
    blocked_user_id: str,
    current_user: User = Depends(get_current_user)
):
    stream = await db.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Unblock user
    await db.unblock_user(current_user.id, blocked_user_id)
    return {"status": "success"}
