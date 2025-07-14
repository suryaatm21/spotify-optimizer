"""
Analytics router for playlist analysis and clustering functionality.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import httpx
import json

from ..dependencies import get_database, get_current_user
from ..models import User, Playlist, Track, PlaylistAnalysis
from ..schemas import (
    PlaylistResponse, TrackResponse, AnalysisRequest, AnalysisResponse,
    PlaylistStats, OptimizationResponse
)
from ..services.clustering import ClusteringService

router = APIRouter()

async def _fetch_and_store_playlist_tracks(
    playlist: Playlist, current_user: User, db: Session
) -> List[Track]:
    """
    Fetches tracks and audio features for a given playlist from Spotify,
    stores them in the database, and returns the list of Track ORM objects.
    Raises HTTPException if Spotify API calls fail.
    """
    async with httpx.AsyncClient() as client:
        # Get user's access token
        access_token = current_user.access_token
        
        print(f"DEBUG: Using access token ending in ...{access_token[-4:]} for user {current_user.spotify_user_id}")

        # Get playlist tracks from Spotify
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Fetch tracks from Spotify
        tracks_response = await client.get(
            f"https://api.spotify.com/v1/playlists/{playlist.spotify_playlist_id}/tracks",
            headers=headers,
            params={"limit": 100, "fields": "items(track(id,name,artists,album,duration_ms,popularity))"}
        )
        
        if tracks_response.status_code != 200:
            print(f"ERROR: Failed to fetch playlist tracks from Spotify. Status: {tracks_response.status_code}, Response: {tracks_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch tracks from Spotify: {tracks_response.text}"
            )
        
        tracks_data = tracks_response.json()
        
        track_ids = []
        for item in tracks_data.get("items", []):
            track_info = item.get("track")
            if track_info and track_info.get("id"):
                track_ids.append(track_info["id"])

        features_map = {}
        if track_ids:
            # Spotify API allows up to 100 IDs per request. Fetch in chunks to avoid errors.
            CHUNK_SIZE = 100
            for i in range(0, len(track_ids), CHUNK_SIZE):
                ids_chunk = track_ids[i : i + CHUNK_SIZE]
                features_response = await client.get(
                    "https://api.spotify.com/v1/audio-features",
                    headers=headers,
                    params={"ids": ",".join(ids_chunk)}
                )

                if features_response.status_code != 200:
                    error_payload = features_response.json()
                    print(
                        f"ERROR: Failed to fetch audio features from Spotify. "
                        f"Status: {features_response.status_code}, Response: {error_payload}"
                    )
                    # Instead of failing the entire request, skip this chunk so other tracks can be processed.
                    continue

                features_data = features_response.json()
                # Merge results into the main map
                for f in features_data.get("audio_features", []):
                    if f and f.get("id"):
                        features_map[f["id"]] = f

    # Store tracks in database
    new_tracks = []
    for item in tracks_data.get("items", []):
        track_data = item.get("track")
        if not track_data or not track_data.get("id"):
            continue
            
        features = features_map.get(track_data["id"], {})
        
        track = Track(
            spotify_track_id=track_data["id"],
            name=track_data["name"],
            artist=", ".join([artist["name"] for artist in track_data.get("artists", [])]),
            album=track_data.get("album", {}).get("name"),
            duration_ms=track_data.get("duration_ms"),
            popularity=track_data.get("popularity"),
            playlist_id=playlist.id,
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
        new_tracks.append(track)
    
    if new_tracks:
        db.commit()
        for track in new_tracks:
            db.refresh(track)
    
    return new_tracks

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
    If tracks are not in the database, they are fetched from Spotify.
    """
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
    new_tracks = await _fetch_and_store_playlist_tracks(playlist, current_user, db)
    
    return [TrackResponse.from_orm(track) for track in new_tracks]

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
    if not tracks:
        tracks = await _fetch_and_store_playlist_tracks(playlist, current_user, db)
    
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
    # Convert ClusterData objects to dictionaries for JSON serialization
    serializable_clusters = [cluster.model_dump() for cluster in clusters]
    
    analysis = PlaylistAnalysis(
        playlist_id=playlist_id,
        cluster_count=analysis_request.cluster_count,
        cluster_method=analysis_request.cluster_method,
        silhouette_score=silhouette_score,
        analysis_data=json.dumps(serializable_clusters)
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
        tracks = await _fetch_and_store_playlist_tracks(playlist, current_user, db)

    if not tracks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tracks found for this playlist. It might be empty."
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
    if not tracks:
        tracks = await _fetch_and_store_playlist_tracks(playlist, current_user, db)

    if not tracks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tracks found for this playlist. It might be empty."
        )
        
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



@router.get("/debug/playlists/{playlist_id}")
async def debug_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Debug endpoint to check playlist and user data."""
    try:
        # Check if playlist exists
        playlist = db.query(Playlist).filter(
            Playlist.id == playlist_id,
            Playlist.user_id == current_user.id
        ).first()
        
        if not playlist:
            return {
                "error": "Playlist not found",
                "playlist_id": playlist_id,
                "user_id": current_user.id,
                "all_playlists": [p.id for p in db.query(Playlist).filter(Playlist.user_id == current_user.id).all()]
            }
        
        tracks_count = db.query(Track).filter(Track.playlist_id == playlist_id).count()
        
        return {
            "playlist_found": True,
            "playlist": {
                "id": playlist.id,
                "spotify_id": playlist.spotify_playlist_id,
                "name": playlist.name,
                "user_id": playlist.user_id
            },
            "tracks_count": tracks_count,
            "user": {
                "id": current_user.id,
                "spotify_id": current_user.spotify_user_id
            }
        }
    except Exception as e:
        return {"error": str(e)}
