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
import httpx
from datetime import datetime, timedelta
from dotenv import load_dotenv

from .models import User

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spotify.db")

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
    Automatically refreshes expired Spotify access tokens.
    
    Args:
        credentials: HTTP authorization credentials containing the JWT token
        db: Database session
        
    Returns:
        User: Current authenticated user with valid access token
        
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
    
    # Check if access token is expired and refresh if needed
    now = datetime.utcnow()
    if user.token_expires_at and user.token_expires_at <= now:
        print(f"DEBUG: Access token expired for user {user.spotify_user_id}, refreshing...")
        
        if not user.refresh_token:
            print("ERROR: No refresh token available")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token expired and no refresh token available. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Refresh the access token
        try:
            credentials = get_spotify_client_credentials()
            
            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": user.refresh_token,
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"]
            }
            
            # Make request to Spotify token endpoint
            response = httpx.post(
                "https://accounts.spotify.com/api/token",
                data=refresh_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                print(f"ERROR: Failed to refresh token. Status: {response.status_code}, Response: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh access token. Please log in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token_data = response.json()
            
            # Update user with new tokens
            user.access_token = token_data["access_token"]
            if "refresh_token" in token_data:  # Spotify may or may not provide a new refresh token
                user.refresh_token = token_data["refresh_token"]
            user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            
            db.commit()
            db.refresh(user)
            
            print(f"DEBUG: Successfully refreshed access token for user {user.spotify_user_id}")
            
        except Exception as e:
            print(f"ERROR: Exception during token refresh: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh access token. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        print(f"DEBUG: Access token for user {user.spotify_user_id} is still valid")
    
    return user

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
