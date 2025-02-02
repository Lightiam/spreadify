import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.database import init_db, SessionLocal
from app.db.models import User
from app.auth import get_password_hash
import uuid

if __name__ == "__main__":
    # Remove existing database if it exists
    db_path = backend_dir / "spreadify.db"
    if db_path.exists():
        os.remove(db_path)
    
    # Initialize database with all tables
    init_db()
    
    # Create test user
    db = SessionLocal()
    test_user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("test123")
    )
    db.add(test_user)
    db.commit()
    db.close()
    
    print("Database initialized successfully with test user")
