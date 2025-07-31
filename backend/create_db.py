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

    # --- Start: Force clean database creation ---
    # Delete the old database file if it exists to ensure a fresh start.
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database at: {DB_PATH}")
    # --- End: Force clean database creation ---

    database_url = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    print(f"Creating database at URL: {database_url}")

    # Create engine
    engine = create_engine(database_url)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("All tables to be created:", Base.metadata.tables.keys())
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_database()