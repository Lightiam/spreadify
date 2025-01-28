from jose import jwt
from datetime import datetime, timedelta, UTC
import os

def generate_test_token():
    """Generate a test JWT token for WebSocket authentication."""
    # Get JWT secret from environment
    jwt_secret = os.getenv('JWT_SECRET', 'spreadify_secret_key_change_in_production')

    # Create payload
    payload = {
        'sub': 'test-user',
        'email': 'test@example.com',
        'exp': datetime.now(UTC) + timedelta(minutes=15)
    }

    # Generate token
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    
    print(f'\nGenerated token: {token}\n')
    print('Test with:')
    print(f'''curl -v -N \\
  -H "Connection: Upgrade" \\
  -H "Upgrade: websocket" \\
  -H "Sec-WebSocket-Version: 13" \\
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \\
  -H "Authorization: Bearer {token}" \\
  "http://localhost:8000/webrtc/signal/test-room"''')

if __name__ == '__main__':
    generate_test_token()
