from jose import jwt
from datetime import datetime, timedelta, UTC
import os

def generate_test_token():
    """Generate a test JWT token for WebSocket authentication."""
    jwt_secret = os.getenv('JWT_SECRET', 'spreadify_secret_key_change_in_production')
    payload = {
        'sub': 'test-user',
        'email': 'test@example.com',
        'exp': datetime.now(UTC) + timedelta(minutes=15)
    }
    return jwt.encode(payload, jwt_secret, algorithm='HS256')

if __name__ == '__main__':
    print(generate_test_token(), end='')
