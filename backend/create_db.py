"""
Database initialization script for the Spotify Playlist Optimizer.
Run this script to create the database tables.
"""
import os
from sqlalchemy import create_engine
from models import Base

def create_database():
    """Create all database tables."""
    # Get database URL from environment variable or use default SQLite
    database_url = os.getenv("DATABASE_URL", "sqlite:///./spotify_optimizer.db")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_database()
