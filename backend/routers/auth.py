"""
Authentication router for Spotify OAuth2 flow.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import urllib.parse
from datetime import datetime, timedelta

from backend.dependencies import (
    get_database,
    get_spotify_client_credentials,
    create_access_token,
    get_current_user,
)
from backend.models import User
from backend.schemas import AuthCallbackRequest, TokenResponse, UserResponse

router = APIRouter()

@router.get("/login")
async def spotify_login():
    """
    Initiate Spotify OAuth2 login flow.
    
    Returns:
        RedirectResponse: Redirect to Spotify authorization URL
    """
    credentials = get_spotify_client_credentials()
    
    # Spotify OAuth2 parameters
    params = {
        "client_id": credentials["client_id"],
        "response_type": "code",
        "redirect_uri": credentials["redirect_uri"],
        "scope": (
            "user-read-private user-read-email playlist-read-private "
            "playlist-read-collaborative user-library-read"
        ),
        "state": "random_state_string"  # In production, use a secure random state
    }
    
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=auth_url)

@router.post("/callback", response_model=TokenResponse)
async def spotify_callback(
    callback_data: AuthCallbackRequest,
    db: Session = Depends(get_database)
):
    """
    Handle Spotify OAuth2 callback and exchange authorization code for tokens.
    
    Args:
        callback_data: OAuth callback data containing authorization code
        db: Database session
        
    Returns:
        TokenResponse: JWT access token and user information
        
    Raises:
        HTTPException: If OAuth flow fails or user creation fails
    """
    credentials = get_spotify_client_credentials()
    
    # Exchange authorization code for access token
    token_data = {
        "grant_type": "authorization_code",
        "code": callback_data.code,
        "redirect_uri": credentials["redirect_uri"],
        "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"]
    }
    
    async with httpx.AsyncClient() as client:
        # Get access token from Spotify
        token_response = await client.post(
            "https://accounts.spotify.com/api/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for access token"
            )
        
        token_info = token_response.json()
        
        # Get user profile from Spotify
        profile_response = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {token_info['access_token']}"}
        )
        
        if profile_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user profile from Spotify"
            )
        
        profile_data = profile_response.json()
    
    # Create or update user in database
    user = db.query(User).filter(User.spotify_user_id == profile_data["id"]).first()
    
    if user:
        # Update existing user
        user.access_token = token_info["access_token"]
        user.refresh_token = token_info.get("refresh_token")
        user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_info["expires_in"])
        user.display_name = profile_data.get("display_name")
        user.email = profile_data.get("email")
    else:
        # Create new user
        user = User(
            spotify_user_id=profile_data["id"],
            display_name=profile_data.get("display_name"),
            email=profile_data.get("email"),
            access_token=token_info["access_token"],
            refresh_token=token_info.get("refresh_token"),
            token_expires_at=datetime.utcnow() + timedelta(seconds=token_info["expires_in"])
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    
    # Create JWT token for our API
    access_token = create_access_token(
        data={"sub": user.spotify_user_id},
        expires_delta=timedelta(minutes=30)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
        scope=token_info.get("scope")
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: User information
    """
    return UserResponse.from_orm(current_user)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Refresh Spotify access token using refresh token.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TokenResponse: New JWT access token
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    if not current_user.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token available"
        )
    
    credentials = get_spotify_client_credentials()
    
    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": current_user.refresh_token,
        "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data=refresh_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh access token"
            )
        
        token_info = response.json()
    
    # Update user with new token
    current_user.access_token = token_info["access_token"]
    if "refresh_token" in token_info:
        current_user.refresh_token = token_info["refresh_token"]
    current_user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_info["expires_in"])
    
    db.commit()
    
    # Create new JWT token
    access_token = create_access_token(
        data={"sub": current_user.spotify_user_id},
        expires_delta=timedelta(minutes=30)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Invalidate the user's tokens and log them out."""
    current_user.access_token = ""
    current_user.refresh_token = None
    current_user.token_expires_at = None
    db.commit()
    return {"message": "Logged out"}
