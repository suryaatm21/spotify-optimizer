"""
Analytics router for playlist analysis and clustering functionality.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import httpx
import json

from dependencies import get_database, get_current_user
from models import User, Playlist, Track, PlaylistAnalysis
from schemas import (
    PlaylistResponse, TrackResponse, AnalysisRequest, AnalysisResponse,
    PlaylistStats, OptimizationResponse
)
from services.clustering import ClusteringService

router = APIRouter()

@router.get("/playlists", response_model=List[PlaylistResponse])
async def get_user_playlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get all playlists for the current user from Spotify and store in database.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[PlaylistResponse]: List of user playlists
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.spotify.com/v1/me/playlists",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
            params={"limit": 50}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch playlists from Spotify"
            )
        
        playlists_data = response.json()
    
    # Store playlists in database
    playlists = []
    for playlist_data in playlists_data["items"]:
        # Check if playlist already exists
        existing_playlist = db.query(Playlist).filter(
            Playlist.spotify_playlist_id == playlist_data["id"]
        ).first()
        
        if existing_playlist:
            # Update existing playlist
            existing_playlist.name = playlist_data["name"]
            existing_playlist.description = playlist_data.get("description")
            existing_playlist.total_tracks = playlist_data["tracks"]["total"]
            existing_playlist.is_public = playlist_data["public"]
            playlist = existing_playlist
        else:
            # Create new playlist
            playlist = Playlist(
                spotify_playlist_id=playlist_data["id"],
                name=playlist_data["name"],
                description=playlist_data.get("description"),
                user_id=current_user.id,
                total_tracks=playlist_data["tracks"]["total"],
                is_public=playlist_data["public"]
            )
            db.add(playlist)
        
        playlists.append(playlist)
    
    db.commit()
    return [PlaylistResponse.from_orm(playlist) for playlist in playlists]

@router.get("/playlists/{playlist_id}/tracks", response_model=List[TrackResponse])
async def get_playlist_tracks(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get all tracks for a specific playlist with audio features.
    
    Args:
        playlist_id: Database ID of the playlist
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[TrackResponse]: List of tracks with audio features
        
    Raises:
        HTTPException: If playlist not found or access denied
    """
    # Get playlist from database
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id,
        Playlist.user_id == current_user.id
    ).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Check if tracks are already in database
    existing_tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    if existing_tracks:
        return [TrackResponse.from_orm(track) for track in existing_tracks]
    
    # Fetch tracks from Spotify
    async with httpx.AsyncClient() as client:
        tracks_response = await client.get(
            f"https://api.spotify.com/v1/playlists/{playlist.spotify_playlist_id}/tracks",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
            params={"limit": 100, "fields": "items(track(id,name,artists,album,duration_ms,popularity))"}
        )
        
        if tracks_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch tracks from Spotify"
            )
        
        tracks_data = tracks_response.json()
        track_ids = [item["track"]["id"] for item in tracks_data["items"] if item["track"]["id"]]
        
        # Get audio features for all tracks
        if track_ids:
            features_response = await client.get(
                "https://api.spotify.com/v1/audio-features",
                headers={"Authorization": f"Bearer {current_user.access_token}"},
                params={"ids": ",".join(track_ids)}
            )
            
            if features_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch audio features from Spotify"
                )
            
            features_data = features_response.json()
            features_map = {f["id"]: f for f in features_data["audio_features"] if f}
    
    # Store tracks in database
    tracks = []
    for item in tracks_data["items"]:
        track_data = item["track"]
        if not track_data["id"]:
            continue
            
        features = features_map.get(track_data["id"], {})
        
        track = Track(
            spotify_track_id=track_data["id"],
            name=track_data["name"],
            artist=", ".join([artist["name"] for artist in track_data["artists"]]),
            album=track_data["album"]["name"] if track_data["album"] else None,
            duration_ms=track_data.get("duration_ms"),
            popularity=track_data.get("popularity"),
            playlist_id=playlist_id,
            danceability=features.get("danceability"),
            energy=features.get("energy"),
            key=features.get("key"),
            loudness=features.get("loudness"),
            mode=features.get("mode"),
            speechiness=features.get("speechiness"),
            acousticness=features.get("acousticness"),
            instrumentalness=features.get("instrumentalness"),
            liveness=features.get("liveness"),
            valence=features.get("valence"),
            tempo=features.get("tempo")
        )
        
        db.add(track)
        tracks.append(track)
    
    db.commit()
    return [TrackResponse.from_orm(track) for track in tracks]

@router.post("/playlists/{playlist_id}/analyze", response_model=AnalysisResponse)
async def analyze_playlist(
    playlist_id: int,
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Analyze a playlist using machine learning clustering.
    
    Args:
        playlist_id: Database ID of the playlist
        analysis_request: Analysis configuration
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AnalysisResponse: Clustering analysis results
        
    Raises:
        HTTPException: If playlist not found or insufficient tracks
    """
    # Verify playlist ownership
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id,
        Playlist.user_id == current_user.id
    ).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Get tracks with audio features
    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    
    if len(tracks) < analysis_request.cluster_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Playlist must have at least {analysis_request.cluster_count} tracks for clustering"
        )
    
    # Perform clustering analysis
    clustering_service = ClusteringService()
    clusters, silhouette_score = clustering_service.cluster_tracks(
        tracks, 
        method=analysis_request.cluster_method,
        n_clusters=analysis_request.cluster_count
    )
    
    # Store analysis results
    analysis = PlaylistAnalysis(
        playlist_id=playlist_id,
        cluster_count=analysis_request.cluster_count,
        cluster_method=analysis_request.cluster_method,
        silhouette_score=silhouette_score,
        analysis_data=json.dumps(clusters)
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return AnalysisResponse(
        id=analysis.id,
        playlist_id=playlist_id,
        cluster_count=analysis_request.cluster_count,
        cluster_method=analysis_request.cluster_method,
        silhouette_score=silhouette_score,
        clusters=clusters,
        created_at=analysis.created_at
    )

@router.get("/playlists/{playlist_id}/stats", response_model=PlaylistStats)
async def get_playlist_stats(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get statistical analysis of a playlist's audio features.
    
    Args:
        playlist_id: Database ID of the playlist
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PlaylistStats: Statistical summary of playlist
        
    Raises:
        HTTPException: If playlist not found
    """
    # Verify playlist ownership
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id,
        Playlist.user_id == current_user.id
    ).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    
    if not tracks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tracks found for playlist"
        )
    
    # Calculate statistics using ClusteringService
    clustering_service = ClusteringService()
    stats = clustering_service.calculate_playlist_stats(tracks)
    
    return stats

@router.get("/playlists/{playlist_id}/optimize", response_model=OptimizationResponse)
async def get_optimization_suggestions(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get optimization suggestions for a playlist based on clustering analysis.
    
    Args:
        playlist_id: Database ID of the playlist
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        OptimizationResponse: Optimization suggestions and current stats
        
    Raises:
        HTTPException: If playlist not found or no analysis available
    """
    # Verify playlist ownership
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id,
        Playlist.user_id == current_user.id
    ).first()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Get latest analysis
    latest_analysis = db.query(PlaylistAnalysis).filter(
        PlaylistAnalysis.playlist_id == playlist_id
    ).order_by(PlaylistAnalysis.created_at.desc()).first()
    
    if not latest_analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No analysis found. Please analyze the playlist first."
        )
    
    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    clustering_service = ClusteringService()
    
    # Get current stats
    current_stats = clustering_service.calculate_playlist_stats(tracks)
    
    # Generate optimization suggestions
    clusters = json.loads(latest_analysis.analysis_data)
    suggestions = clustering_service.generate_optimization_suggestions(tracks, clusters)
    
    return OptimizationResponse(
        playlist_id=playlist_id,
        current_stats=current_stats,
        suggestions=suggestions,
        analysis_id=latest_analysis.id
    )
