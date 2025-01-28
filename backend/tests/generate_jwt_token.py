from jose import jwt
from datetime import datetime, timedelta, UTC

def generate_test_token():
    """Generate a test JWT token for WebSocket authentication."""
    payload = {
        'sub': 'test-user',
        'email': 'test@example.com',
        'exp': datetime.now(UTC) + timedelta(minutes=15)
    }
    
    # Get JWT secret from environment or use default
    jwt_secret = 'spreadify_secret_key_change_in_production'
    
    token = jwt.encode(
        payload,
        jwt_secret,
        algorithm='HS256'
    )
    return token

if __name__ == '__main__':
    print(generate_test_token())
