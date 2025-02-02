import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.database import init_db, SessionLocal
from app.db.models import Channel, ChannelSettings, Stream

if __name__ == "__main__":
    # Remove existing database if it exists
    db_path = backend_dir / "spreadify.db"
    if db_path.exists():
        os.remove(db_path)
    
    # Initialize database with all tables
    init_db()
    
    # Create test channel
    db = SessionLocal()
    channel = Channel(
        name="Test Channel",
        description="A test channel for development",
        owner_id="anonymous"
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    
    # Create channel settings
    settings = ChannelSettings(
        channel_id=channel.id,
        monetization_enabled=False
    )
    db.add(settings)
    
    # Create test stream
    stream = Stream(
        title="Test Stream",
        description="A test stream for development",
        channel_id=channel.id,
        owner_id="anonymous"
    )
    db.add(stream)
    db.commit()
    db.close()
    
    print("Database initialized successfully with test data")
