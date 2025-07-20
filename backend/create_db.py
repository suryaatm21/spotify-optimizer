"""
Database initialization script for the Spotify Playlist Optimizer.
Run this script to create the database tables.
"""
import os
import sys
from pathlib import Path
# Ensure project root is in sys.path for absolute imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from sqlalchemy import create_engine
from backend.models import Base

def create_database():
    """Create all database tables."""
    # Build a robust path to the database file in the `db/` directory
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DB_PATH = PROJECT_ROOT / "db" / "spotify.db"
    DB_PATH.parent.mkdir(exist_ok=True)  # Ensure the db/ directory exists

    database_url = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    print(f"Creating database at: {DB_PATH}")

    # Create engine
    engine = create_engine(database_url)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    print(f"Tables created: {', '.join(Base.metadata.tables.keys())}")

if __name__ == "__main__":
    create_database()
