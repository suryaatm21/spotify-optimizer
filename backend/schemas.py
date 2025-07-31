"""
Pydantic schemas for request/response validation in the Spotify Playlist Optimizer API.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Base schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    spotify_user_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None

class UserCreate(UserBase):
    """Schema for creating a new user."""
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

class UserResponse(UserBase):
    """Schema for user response data."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Playlist schemas
class PlaylistBase(BaseModel):
    """Base playlist schema with common fields."""
    spotify_playlist_id: str
    name: str
    description: Optional[str] = None
    total_tracks: int = 0
    is_public: bool = True

class PlaylistCreate(PlaylistBase):
    """Schema for creating a new playlist."""
    user_id: int

class PlaylistResponse(PlaylistBase):
    """Schema for playlist response data."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Track schemas
class TrackBase(BaseModel):
    """Base track schema with common fields."""
    spotify_track_id: str
    name: str
    artist: str
    album: Optional[str] = None
    duration_ms: Optional[int] = None
    popularity: Optional[int] = None

class AudioFeatures(BaseModel):
    """Schema for Spotify audio features."""
    danceability: Optional[float] = Field(None, ge=0.0, le=1.0)
    energy: Optional[float] = Field(None, ge=0.0, le=1.0)
    key: Optional[int] = Field(None, ge=0, le=11)
    loudness: Optional[float] = None
    mode: Optional[int] = Field(None, ge=0, le=1)
    speechiness: Optional[float] = Field(None, ge=0.0, le=1.0)
    acousticness: Optional[float] = Field(None, ge=0.0, le=1.0)
    instrumentalness: Optional[float] = Field(None, ge=0.0, le=1.0)
    liveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    valence: Optional[float] = Field(None, ge=0.0, le=1.0)
    tempo: Optional[float] = Field(None, gt=0.0)

class TrackCreate(TrackBase, AudioFeatures):
    """Schema for creating a new track with audio features."""
    playlist_id: int

class TrackResponse(TrackBase, AudioFeatures):
    """Schema for track response data."""
    id: int
    playlist_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Analysis schemas
class ClusterData(BaseModel):
    """Schema for individual cluster data."""
    cluster_id: int
    track_count: int
    center_features: Dict[str, float]
    track_ids: List[int]

class DataQualityReport(BaseModel):
    """Schema for data quality analysis."""
    total_tracks: int
    overall_completeness: float
    feature_quality: Dict[str, Dict[str, Any]]
    recommendation: str

class AnalysisRequest(BaseModel):
    """Schema for playlist analysis request."""
    playlist_id: int
    cluster_method: str = Field(default="kmeans", pattern="^(kmeans|dbscan)$")
    cluster_count: Optional[int] = Field(default=3, ge=2, le=10)
    fetch_missing_features: bool = Field(default=True, description="Whether to attempt fetching missing audio features from Spotify")

class AnalysisResponse(BaseModel):
    """Schema for playlist analysis response."""
    id: int
    playlist_id: int
    cluster_count: int
    cluster_method: str
    silhouette_score: Optional[float] = None
    clusters: List[ClusterData]
    data_quality: Optional[DataQualityReport] = None
    analysis_metadata: Optional[Dict[str, Any]] = None
    pca_coordinates: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Authentication schemas
class TokenResponse(BaseModel):
    """Schema for OAuth token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

class AuthCallbackRequest(BaseModel):
    """Schema for OAuth callback request."""
    code: str
    state: Optional[str] = None

# Statistics schemas
class PlaylistStats(BaseModel):
    """Schema for playlist statistics."""
    total_tracks: int
    avg_duration_ms: float
    avg_popularity: float
    avg_audio_features: Dict[str, float]
    feature_ranges: Dict[str, Dict[str, float]]  # min, max, std for each feature

class OptimizationSuggestion(BaseModel):
    """Schema for playlist optimization suggestions."""
    suggestion_type: str
    description: str
    affected_tracks: List[int]
    confidence_score: float = Field(ge=0.0, le=1.0)

class OptimizationResponse(BaseModel):
    """Schema for playlist optimization response."""
    playlist_id: int
    current_stats: PlaylistStats
    suggestions: List[OptimizationSuggestion]
    analysis_id: int
