from uuid import UUID
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User, Channel

# Mock user ID that will be used consistently across the application
MOCK_USER_ID = UUID('00000000-0000-0000-0000-000000000000')

def init_mock_data():
    engine = create_engine('sqlite:///./app.db')
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Check if mock user exists
    mock_user = db.query(User).filter(User.id == MOCK_USER_ID).first()
    if not mock_user:
        mock_user = User(
            id=MOCK_USER_ID,
            email="dev@example.com",
            username="dev",
            password_hash="mock",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(mock_user)
        
        # Create a default channel for the mock user
        default_channel = Channel(
            name="Default Channel",
            description="Default streaming channel",
            owner_id=MOCK_USER_ID,
            created_at=datetime.utcnow()
        )
        db.add(default_channel)
        
        db.commit()
    
    db.close()

if __name__ == "__main__":
    init_mock_data()
