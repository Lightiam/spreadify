from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Depends
from typing import Dict, Set, Optional
import json
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
import asyncio
import os
from jose import jwt
from jose.exceptions import JWTError
from ..dependencies import get_current_user
from ..schemas.auth import UserBase, TokenData

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure debug logging for this module

router = APIRouter(prefix="/webrtc", tags=["webrtc"])

# Store peer connections and their associated room IDs
peer_connections: Dict[str, RTCPeerConnection] = {}
peer_to_room: Dict[str, str] = {}
# Store room connections
rooms: Dict[str, Set[WebSocket]] = {}

async def cleanup_peer_connection(peer_id: str):
    """Clean up peer connection and associated resources."""
    if peer_id in peer_connections:
        logger.info(f"Cleaning up peer connection for {peer_id}")
        pc = peer_connections[peer_id]
        await pc.close()
        del peer_connections[peer_id]
        if peer_id in peer_to_room:
            del peer_to_room[peer_id]

async def get_token_data(token: str) -> Optional[TokenData]:
    """Validate JWT token and return token data."""
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
            
        jwt_secret = os.environ.get("JWT_SECRET", "spreadify_secret_key_change_in_production")
        if not jwt_secret:
            logger.error("JWT_SECRET not configured")
            return None
            
        logger.debug(f"Attempting to decode token with secret: {jwt_secret[:4]}...")
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        logger.debug(f"Token payload: {payload}")
        
        # Ensure required fields are present
        if not payload.get('email'):
            logger.error("Token payload missing required 'email' field")
            return None
            
        return TokenData(**payload)
    except (JWTError, ValueError) as e:
        logger.error(f"Token validation error for token '{token[:10]}...': {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        return None

@router.websocket("/signal/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for WebRTC signaling."""
    try:
        # Get token from various sources
        token = None
        
        # 1. Try Authorization header
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            logger.debug(f"Token from Authorization header: {token[:10] if token else None}")
        
        # 2. Try query parameters
        if not token:
            token = websocket.query_params.get("token")
            logger.debug(f"Token from query params: {token[:10] if token else None}")
        
        # 3. Try cookie
        if not token:
            cookies = websocket.headers.get("cookie", "")
            logger.debug(f"Cookies header: {cookies}")
            token = next(
                (c.split("=")[1] for c in cookies.split("; ") if c.startswith("token=")),
                None
            ) if cookies else None
            logger.debug(f"Token from cookies: {token[:10] if token else None}")
            
        if not token:
            logger.error("No authentication token provided")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        logger.debug("Token found from one of the sources")

        # Verify JWT token
        token_data = await get_token_data(token)
        if not token_data or not token_data.email:
            logger.error("Invalid token or missing email")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        logger.info(f"Authenticated user {token_data.email} connecting to room {room_id}")

        # Accept WebSocket connection
        logger.debug("Attempting to accept WebSocket connection...")
        try:
            await websocket.accept()
            logger.info(f"WebSocket connection accepted for room {room_id}")
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {str(e)}")
            raise
        
        if room_id not in rooms:
            rooms[room_id] = set()
        rooms[room_id].add(websocket)
        
        # Send initial connection success message
        try:
            await websocket.send_json({
                "type": "connection-success",
                "from": "server",
                "data": "WebSocket connection established"
            })
            logger.info(f"Sent connection success message to room {room_id}")
        except Exception as e:
            logger.error(f"Failed to send connection success message: {e}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        # Add websocket to room
        if room_id not in rooms:
            rooms[room_id] = set()
        rooms[room_id].add(websocket)
        logger.info(f"Added websocket to room {room_id}")

        try:
            while True:
                try:
                    # Wait for messages with a timeout
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    data = json.loads(message)
                    peer_id = data.get("from")
                    
                    if not peer_id:
                        logger.error("Missing peer ID in message")
                        continue
                    
                    logger.info(f"Received {data['type']} message from {peer_id}")
                    
                    if data["type"] == "test":
                        logger.info(f"Received test message from {peer_id}: {data}")
                        # Echo the test message back
                        response = {
                            "type": "test-response",
                            "from": "server",
                            "to": peer_id,
                            "data": "Server received your test message"
                        }
                        await websocket.send_json(response)
                        logger.info(f"Sent test response to {peer_id}")
                        
                    elif data["type"] == "offer":
                        # Cleanup any existing peer connection
                        await cleanup_peer_connection(peer_id)
                        
                        # Create new peer connection with ICE servers from config
                        ice_servers = json.loads(os.environ.get("ICE_SERVERS", '[{"urls":["stun:stun.l.google.com:19302"]}]'))
                        pc = RTCPeerConnection(configuration={"iceServers": ice_servers})
                        peer_connections[peer_id] = pc
                        peer_to_room[peer_id] = room_id
                        
                        # Set the remote description
                        await pc.setRemoteDescription(
                            RTCSessionDescription(sdp=data["sdp"], type=data["type"])
                        )
                        
                        # Create and send answer
                        answer = await pc.createAnswer()
                        await pc.setLocalDescription(answer)
                        
                        response = {
                            "type": "answer",
                            "sdp": pc.localDescription.sdp,
                            "to": peer_id
                        }
                        await websocket.send_json(response)
                        logger.info(f"Sent answer to {peer_id}")
                    
                    elif data["type"] == "ice-candidate":
                        if peer_id in peer_connections:
                            pc = peer_connections[peer_id]
                            candidate = RTCIceCandidate(
                                sdpMid=data["candidate"].get("sdpMid"),
                                sdpMLineIndex=data["candidate"].get("sdpMLineIndex"),
                                candidate=data["candidate"].get("candidate")
                            )
                            await pc.addIceCandidate(candidate)
                            logger.info(f"Added ICE candidate for {peer_id}")
                        else:
                            logger.warning(f"No peer connection found for {peer_id}")
                    
                    # Broadcast to all other clients in the room
                    if room_id in rooms:
                        for client in list(rooms[room_id]):  # Create a copy of the set to iterate
                            if client != websocket and client.client_state.state != WebSocketState.DISCONNECTED:
                                try:
                                    await client.send_text(message)
                                    logger.debug(f"Broadcasted message to peer in room {room_id}")
                                except Exception as e:
                                    logger.warning(f"Failed to broadcast to client in room {room_id}: {e}")
                                    if client in rooms[room_id]:
                                        rooms[room_id].remove(client)
                
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    try:
                        await websocket.send_json({"type": "ping"})
                        logger.debug(f"Sent ping to keep connection alive in room {room_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send ping, closing connection: {e}")
                        break
                
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON message: {e}")
                    continue
                
                except Exception as e:
                    if "disconnect message has been received" in str(e):
                        logger.info(f"Client disconnected from room {room_id}")
                        break
                    logger.error(f"Error processing message: {e}")
                    continue
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for room {room_id}")
        
        finally:
            # Cleanup room
            if room_id in rooms and websocket in rooms[room_id]:
                rooms[room_id].remove(websocket)
                if not rooms[room_id]:
                    del rooms[room_id]
                logger.info(f"Removed websocket from room {room_id}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for room {room_id}")
        if room_id in rooms:
            rooms[room_id].remove(websocket)
            if not rooms[room_id]:
                del rooms[room_id]
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        # Cleanup all peer connections in the room
        peer_ids_to_cleanup = [
            peer_id for peer_id, room in peer_to_room.items()
            if room == room_id
        ]
        for peer_id in peer_ids_to_cleanup:
            await cleanup_peer_connection(peer_id)
