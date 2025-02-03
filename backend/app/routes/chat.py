from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import json
import re
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
    stream_id: str
):
    await websocket.accept()
    
    if stream_id not in chat_connections:
        chat_connections[stream_id] = []
    chat_connections[stream_id].append((websocket, "anonymous"))
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Rate limiting check
            now = datetime.utcnow()
            user_id = "anonymous"
            if user_id not in message_timestamps:
                message_timestamps[user_id] = []
            
            # Remove old timestamps
            message_timestamps[user_id] = [
                ts for ts in message_timestamps[user_id]
                if now - ts < timedelta(seconds=RATE_WINDOW)
            ]
            
            if len(message_timestamps[user_id]) >= RATE_LIMIT:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Rate limit exceeded. Please wait {RATE_WINDOW} seconds."
                }))
                continue
            
            message_timestamps[user_id].append(now)
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
                "user_id": "anonymous",
                "username": "Anonymous User",
                "message": message.get("message", ""),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # No message storage in simplified version
            
            # Broadcast to non-blocked clients
            for connection, _ in chat_connections[stream_id]:
                await connection.send_text(json.dumps(chat_message))
    except WebSocketDisconnect:
        if stream_id in chat_connections:
            chat_connections[stream_id].remove((websocket, "anonymous"))
            if not chat_connections[stream_id]:
                del chat_connections[stream_id]
    except Exception as e:
        if stream_id in chat_connections:
            chat_connections[stream_id].remove((websocket, "anonymous"))
            if not chat_connections[stream_id]:
                del chat_connections[stream_id]

@router.post("/commands")
async def create_chat_command(command: ChatCommand):
    if not command.name.startswith("!"):
        command.name = "!" + command.name
    chat_commands[command.name] = command
    return command

@router.delete("/commands/{command_name}")
async def delete_chat_command(command_name: str):
    if not command_name.startswith("!"):
        command_name = "!" + command_name
    if command_name in chat_commands:
        del chat_commands[command_name]
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Command not found")
