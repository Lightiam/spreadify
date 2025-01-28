import base64
import os

def generate_websocket_key():
    """Generate a valid WebSocket key (16 random bytes, base64 encoded)."""
    random_bytes = os.urandom(16)
    websocket_key = base64.b64encode(random_bytes).decode()
    print(websocket_key)

if __name__ == "__main__":
    generate_websocket_key()
