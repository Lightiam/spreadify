from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spreadify.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database and create mock user if needed"""
    Base.metadata.create_all(bind=engine)
    
    # Initialize mock data
    from .init_mock_data import init_mock_data
    init_mock_data()
