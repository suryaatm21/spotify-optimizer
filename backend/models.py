"""
Database models using SQLAlchemy for the Spotify Playlist Optimizer.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """
    User model for storing Spotify user information.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    spotify_user_id = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    playlists = relationship("Playlist", back_populates="user")

class Playlist(Base):
    """
    Playlist model for storing Spotify playlist information.
    """
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    spotify_playlist_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_tracks = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="playlists")
    tracks = relationship("Track", back_populates="playlist")
    analyses = relationship("PlaylistAnalysis", back_populates="playlist")

class Track(Base):
    """
    Track model for storing Spotify track information and audio features.
    """
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    spotify_track_id = Column(String(255), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    features_imputed = Column(Boolean, default=False)  # True if audio features are based on imputation
    popularity = Column(Integer, nullable=True)
    
    # Audio features
    danceability = Column(Float, nullable=True)
    energy = Column(Float, nullable=True)
    key = Column(Integer, nullable=True)
    loudness = Column(Float, nullable=True)
    mode = Column(Integer, nullable=True)
    speechiness = Column(Float, nullable=True)
    acousticness = Column(Float, nullable=True)
    instrumentalness = Column(Float, nullable=True)
    liveness = Column(Float, nullable=True)
    valence = Column(Float, nullable=True)
    tempo = Column(Float, nullable=True)
    
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    playlist = relationship("Playlist", back_populates="tracks")

class PlaylistAnalysis(Base):
    """
    Playlist analysis model for storing clustering results and statistics.
    """
    __tablename__ = "playlist_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    cluster_count = Column(Integer, nullable=False)
    cluster_method = Column(String(50), nullable=False)  # e.g., "kmeans", "dbscan"
    silhouette_score = Column(Float, nullable=True)
    analysis_data = Column(Text, nullable=True)  # JSON string of analysis results
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    playlist = relationship("Playlist", back_populates="analyses")
