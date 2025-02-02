from datetime import datetime
from sqlalchemy.orm import Session
from .models import Channel, Stream, ChannelSettings

def init_mock_data(db: Session):
    # Create test channel
    channel = Channel(
        name="Default Channel",
        description="Default streaming channel",
        owner_id="anonymous",
        created_at=datetime.utcnow()
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
        owner_id="anonymous",
        created_at=datetime.utcnow()
    )
    db.add(stream)
    db.commit()
