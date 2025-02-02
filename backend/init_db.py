import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.database import init_db

if __name__ == "__main__":
    # Remove existing database if it exists
    db_path = backend_dir / "spreadify.db"
    if db_path.exists():
        os.remove(db_path)
    
    # Initialize database with all tables
    init_db()
    print("Database initialized successfully")
