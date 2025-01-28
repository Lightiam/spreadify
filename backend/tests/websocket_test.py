import asyncio
import websockets
import json
import jwt
import os
from datetime import datetime, timedelta, UTC

# Create a test token
def create_test_token():
    """Create a test JWT token for WebSocket authentication."""
    payload = {
        "sub": "test-user",
        "email": "test@example.com",
        "exp": datetime.now(UTC) + timedelta(minutes=15)
    }
    jwt_secret = os.getenv("JWT_SECRET", "spreadify_secret_key_change_in_production")
    print(f"Using JWT secret: {jwt_secret}")
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    print(f"Generated token: {token}")
    return token

async def test_websocket_connection():
    """Test WebSocket connection with authentication."""
    token = create_test_token()
    uri = f"ws://localhost:8000/webrtc/signal/test-room?token={token}"
    print(f"Connecting to WebSocket server at {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Wait for connection success message
            response = await websocket.recv()
            print(f"Received initial response: {response}")
            
            # Send a test message
            message = {
                "type": "test",
                "from": "test-client",
                "data": "Hello, WebSocket server!"
            }
            print(f"Sending test message: {message}")
            await websocket.send(json.dumps(message))
            print("Sent test message")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("Timeout waiting for server response")
                return
            
            # Keep connection open briefly to ensure proper cleanup
            await asyncio.sleep(1)
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Failed to connect: {e}")
        if hasattr(e, 'headers'):
            print(f"Response headers: {e.headers}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"WebSocket connection closed: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
