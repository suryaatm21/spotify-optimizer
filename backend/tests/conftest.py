"""
Pytest configuration and fixtures for the Spotify Playlist Optimizer API tests.
"""
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta

import sys
from pathlib import Path

# Ensure the project root is on the import path so that the "backend"
# package can be imported as a namespace package.
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.main import app
from backend.dependencies import get_database
from backend.models import Base, User, Playlist, Track

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_spotify_optimizer.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_database() -> Generator[Session, None, None]:
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the dependency
app.dependency_overrides[get_database] = override_get_database

@pytest.fixture(scope="session")
def setup_database():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_database) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create a sample user for testing."""
    # Ensure the table is clean to avoid UNIQUE constraint errors across tests
    db_session.query(User).delete()
    db_session.query(Playlist).delete()
    db_session.query(Track).delete()
    db_session.commit()

    user = User(
        spotify_user_id="test_user_123",
        display_name="Test User",
        email="test@example.com",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_playlist(db_session: Session, sample_user: User) -> Playlist:
    """Create a sample playlist for testing."""
    playlist = Playlist(
        spotify_playlist_id="test_playlist_123",
        name="Test Playlist",
        description="A test playlist",
        user_id=sample_user.id,
        total_tracks=3,
        is_public=True
    )
    db_session.add(playlist)
    db_session.commit()
    db_session.refresh(playlist)
    return playlist

@pytest.fixture
def sample_tracks(db_session: Session, sample_playlist: Playlist) -> list[Track]:
    """Create sample tracks for testing."""
    tracks = [
        Track(
            spotify_track_id="track_1",
            name="High Energy Song",
            artist="Artist 1",
            album="Album 1",
            duration_ms=210000,
            popularity=85,
            playlist_id=sample_playlist.id,
            danceability=0.8,
            energy=0.9,
            speechiness=0.1,
            acousticness=0.2,
            instrumentalness=0.1,
            liveness=0.3,
            valence=0.8,
            tempo=128.0
        ),
        Track(
            spotify_track_id="track_2",
            name="Chill Song",
            artist="Artist 2",
            album="Album 2",
            duration_ms=195000,
            popularity=70,
            playlist_id=sample_playlist.id,
            danceability=0.4,
            energy=0.3,
            speechiness=0.05,
            acousticness=0.8,
            instrumentalness=0.2,
            liveness=0.1,
            valence=0.4,
            tempo=85.0
        ),
        Track(
            spotify_track_id="track_3",
            name="Dance Track",
            artist="Artist 3",
            album="Album 3",
            duration_ms=230000,
            popularity=90,
            playlist_id=sample_playlist.id,
            danceability=0.9,
            energy=0.8,
            speechiness=0.15,
            acousticness=0.1,
            instrumentalness=0.05,
            liveness=0.4,
            valence=0.7,
            tempo=120.0
        )
    ]
    
    for track in tracks:
        db_session.add(track)
    
    db_session.commit()
    
    for track in tracks:
        db_session.refresh(track)
    
    return tracks

@pytest.fixture
def auth_headers(sample_user: User) -> dict:
    """Create authentication headers for testing."""
    from backend.dependencies import create_access_token
    
    token = create_access_token(data={"sub": sample_user.spotify_user_id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_spotify_responses():
    """Mock Spotify API responses for testing."""
    return {
        "playlists": {
            "items": [
                {
                    "id": "test_playlist_123",
                    "name": "Test Playlist",
                    "description": "A test playlist",
                    "public": True,
                    "tracks": {"total": 3}
                }
            ]
        },
        "tracks": {
            "items": [
                {
                    "track": {
                        "id": "track_1",
                        "name": "High Energy Song",
                        "artists": [{"name": "Artist 1"}],
                        "album": {"name": "Album 1"},
                        "duration_ms": 210000,
                        "popularity": 85
                    }
                }
            ]
        },
        "audio_features": {
            "audio_features": [
                {
                    "id": "track_1",
                    "danceability": 0.8,
                    "energy": 0.9,
                    "speechiness": 0.1,
                    "acousticness": 0.2,
                    "instrumentalness": 0.1,
                    "liveness": 0.3,
                    "valence": 0.8,
                    "tempo": 128.0
                }
            ]
        }
    }
