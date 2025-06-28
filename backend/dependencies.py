"""
Dependencies for the Spotify Playlist Optimizer API.
Handles database connections, OAuth2 authentication, and common dependencies.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from backend.models import User

# HTTP client for Spotify token refresh
import httpx
# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spotify_optimizer.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
security = HTTPBearer()

def get_database() -> Generator[Session, None, None]:
    """
    Database dependency that provides a SQLAlchemy session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing the data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        spotify_user_id: str = payload.get("sub")
        if spotify_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database)
) -> User:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        credentials: HTTP authorization credentials containing the JWT token
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If user is not found or token is invalid
    """
    token = credentials.credentials
    payload = verify_token(token)
    spotify_user_id = payload.get("sub")
    
    user = db.query(User).filter(User.spotify_user_id == spotify_user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Refresh Spotify token if expired
    if user.token_expires_at and user.token_expires_at <= datetime.utcnow():
        refresh_spotify_token(user, db)

    return user

def refresh_spotify_token(user: User, db: Session) -> None:
    """Refresh the user's Spotify access token if possible."""
    if not user.refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    creds = get_spotify_client_credentials()
    data = {
        "grant_type": "refresh_token",
        "refresh_token": user.refresh_token,
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
    }
    response = httpx.post(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to refresh access token")

    token_info = response.json()
    user.access_token = token_info["access_token"]
    if "refresh_token" in token_info:
        user.refresh_token = token_info["refresh_token"]
    user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_info.get("expires_in", 3600))
    db.commit()

def get_spotify_client_credentials() -> dict:
    """
    Get Spotify API client credentials from environment variables.
    
    Returns:
        dict: Dictionary containing client_id, client_secret, and redirect_uri
        
    Raises:
        HTTPException: If credentials are not configured
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:3000/callback")
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Spotify API credentials not configured"
        )
    
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }
