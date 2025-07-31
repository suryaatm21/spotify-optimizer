"""
Analytics router for playlist analysis and clustering functionality.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import httpx
import json

from backend.dependencies import (
    get_database, get_current_user, get_clustering_service, 
    get_audio_features_service
)
from backend.models import User, Playlist, Track, PlaylistAnalysis
from backend.schemas import (
    PlaylistResponse, TrackResponse, AnalysisRequest, AnalysisResponse,
    PlaylistStats, OptimizationResponse, DataQualityReport
)
from ..services.clustering import ClusteringService
from ..services.audio_features import AudioFeaturesService

router = APIRouter()

async def _fetch_and_store_playlist_tracks(
    playlist: Playlist, 
    current_user: User, 
    db: Session,
    audio_features_service: AudioFeaturesService
) -> List[Track]:
    """
    Fetches tracks and audio features for a given playlist from Spotify,
    stores them in the database, and returns the list of Track ORM objects.
    Raises HTTPException if Spotify API calls fail.
    """
    async with httpx.AsyncClient() as client:
        access_token = current_user.access_token
        headers = {"Authorization": f"Bearer {access_token}"}

        tracks_response = await client.get(
            f"https://api.spotify.com/v1/playlists/{playlist.spotify_playlist_id}/tracks",
            headers=headers,
            params={"limit": 100, "fields": "items(track(id,name,artists,album,duration_ms,popularity))"}
        )

        if tracks_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch tracks from Spotify: {tracks_response.text}"
            )

        tracks_data = tracks_response.json()

    # Store tracks in database
    new_tracks = []
    for item in tracks_data.get("items", []):
        track_data = item.get("track")
        if not track_data or not track_data.get("id") or not track_data.get("name"):
            continue

        spotify_track_id = track_data["id"]
        
        # Check if track already exists for this specific playlist
        existing_track = db.query(Track).filter(
            Track.spotify_track_id == spotify_track_id,
            Track.playlist_id == playlist.id
        ).first()
        
        if existing_track:
            # Track already exists for this playlist, skip
            new_tracks.append(existing_track)
            continue

        # Create new track record for this playlist
        track = Track(
            spotify_track_id=spotify_track_id,
            name=track_data["name"],
            artist=", ".join([artist["name"] for artist in track_data.get("artists", [])]),
            album=track_data.get("album", {}).get("name"),
            duration_ms=track_data.get("duration_ms"),
            popularity=track_data.get("popularity"),
            playlist_id=playlist.id,
        )
        
        new_tracks.append(track)
        db.add(track)

    db.commit()

    # Fetch and impute audio features for tracks that don't have them
    tracks_needing_features = [track for track in new_tracks if track.danceability is None]
    if tracks_needing_features:
        await audio_features_service.fetch_and_impute_features(tracks_needing_features, db)
        db.commit()

    for track in new_tracks:
        db.refresh(track)

    return new_tracks

@router.get("/playlists/{playlist_id}/optimize", status_code=status.HTTP_501_NOT_IMPLEMENTED, include_in_schema=False)
async def optimize_playlist(playlist_id: int):
    """
    Placeholder for playlist optimization feature. Temporarily disabled per user request.
    """
    return {"message": "Optimization feature temporarily disabled."}

@router.get("/playlists", response_model=List[PlaylistResponse])
async def get_user_playlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get all playlists for the current user from Spotify and store in database.
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.access_token}"}
        response = await client.get("https://api.spotify.com/v1/me/playlists", headers=headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch playlists from Spotify: {response.text}"
            )

        playlists_data = response.json()
        user_playlists = []
        for item in playlists_data.get("items", []):
            playlist = db.query(Playlist).filter_by(spotify_playlist_id=item["id"]).first()
            if not playlist:
                playlist = Playlist(
                    spotify_playlist_id=item["id"],
                    name=item["name"],
                    description=item.get("description", ""),
                    user_id=current_user.id,
                    total_tracks=item["tracks"]["total"],
                    is_public=item["public"]
                )
                db.add(playlist)
            else:
                playlist.name = item["name"]
                playlist.description = item.get("description", "")
                playlist.total_tracks = item["tracks"]["total"]
                playlist.is_public = item["public"]
            user_playlists.append(playlist)
        
        db.commit()
        for p in user_playlists:
            db.refresh(p)
            
    return user_playlists

@router.get("/playlists/{playlist_id}/tracks", response_model=List[TrackResponse])
async def get_playlist_tracks(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    audio_features_service: AudioFeaturesService = Depends(get_audio_features_service)
):
    """
    Get all tracks for a specific playlist with audio features.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    if not tracks:
        tracks = await _fetch_and_store_playlist_tracks(
            playlist=playlist,
            current_user=current_user,
            db=db,
            audio_features_service=audio_features_service
        )
        
    return tracks

@router.post("/playlists/{playlist_id}/analyze", response_model=AnalysisResponse)
async def analyze_playlist(
    playlist_id: int,
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    clustering_service: ClusteringService = Depends(get_clustering_service)
):
    """
    Analyze a playlist using machine learning clustering.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    if not tracks:
        raise HTTPException(status_code=404, detail="No tracks found in playlist. Please sync first.")

    prepared_tracks, quality_report = await clustering_service.prepare_tracks_for_analysis(
        tracks,
        db=db,
        user_access_token=current_user.access_token
    )

    try:
        clusters, silhouette_score, analysis_metadata = clustering_service.cluster_tracks(
            prepared_tracks, 
            method=analysis_request.cluster_method,
            n_clusters=analysis_request.cluster_count,
            quality_report=quality_report
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Convert ClusterData objects to dictionaries for JSON serialization
    clusters_dict = [cluster.model_dump() for cluster in clusters]
    analysis_data = json.dumps({
        "clusters": clusters_dict,
        "silhouette_score": silhouette_score,
        "analysis_metadata": analysis_metadata
    })
    analysis_record = PlaylistAnalysis(
        playlist_id=playlist_id,
        analysis_data=analysis_data,
        cluster_method=analysis_request.cluster_method,
        cluster_count=analysis_request.cluster_count,
        silhouette_score=silhouette_score
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    pca_coordinates = clustering_service.get_pca_coordinates(prepared_tracks)

    # Handle the data quality report structure
    data_quality_obj = None
    if quality_report and "final_quality" in quality_report:
        final_quality = quality_report["final_quality"]
        data_quality_obj = DataQualityReport(
            total_tracks=final_quality.get("total_tracks", 0),
            overall_completeness=final_quality.get("overall_completeness", 0.0),
            feature_quality=final_quality.get("feature_quality", {}),
            recommendation=final_quality.get("recommendation", "No recommendations available")
        )

    return AnalysisResponse(
        id=analysis_record.id,
        playlist_id=playlist_id,
        cluster_count=analysis_request.cluster_count,
        cluster_method=analysis_request.cluster_method,
        silhouette_score=silhouette_score,
        clusters=clusters,
        data_quality=data_quality_obj,
        analysis_metadata=analysis_metadata,
        pca_coordinates=pca_coordinates,
        created_at=analysis_record.created_at
    )

@router.get("/playlists/{playlist_id}/data-quality", response_model=DataQualityReport)
async def get_playlist_data_quality(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    audio_features_service: AudioFeaturesService = Depends(get_audio_features_service)
):
    """
    Analyze the data quality of a playlist's audio features.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    if not tracks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tracks found in playlist")

    quality_report = audio_features_service.analyze_data_quality(tracks)
    return DataQualityReport(**quality_report)

@router.get("/playlists/{playlist_id}/stats", response_model=PlaylistStats)
async def get_playlist_stats(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    clustering_service: ClusteringService = Depends(get_clustering_service)
):
    """
    Get statistical analysis of a playlist's audio features.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    if not tracks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tracks found in playlist")

    stats = clustering_service.calculate_playlist_stats(tracks)
    return stats

# Duplicate /playlists/{playlist_id}/optimize endpoint removed per user request to prevent repeated 501 errors. Only the disabled placeholder route remains active for this path.

@router.post("/playlists/{playlist_id}/fetch-audio-features")
async def fetch_audio_features(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    audio_features_service: AudioFeaturesService = Depends(get_audio_features_service)
):
    """
    Manually fetch missing audio features for all tracks in a playlist.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    if not tracks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tracks found in playlist")

    initial_quality = audio_features_service.analyze_data_quality(tracks)

    try:
        await audio_features_service.fetch_missing_audio_features(
            tracks, db, current_user.access_token
        )
        final_quality = audio_features_service.analyze_data_quality(tracks)
        
        return {
            "message": "Audio features fetching completed",
            "playlist_id": playlist_id,
            "total_tracks": len(tracks),
            "initial_completeness": initial_quality.get("overall_completeness", 0),
            "final_completeness": final_quality.get("overall_completeness", 0),
            "improvement": final_quality.get("overall_completeness", 0) - initial_quality.get("overall_completeness", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch audio features: {str(e)}")

@router.get("/debug/playlists/{playlist_id}")
async def debug_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Debug endpoint to check playlist and user data."""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        return {"error": "Playlist not found", "playlist_id": playlist_id, "user_id": current_user.id}

    tracks_count = db.query(Track).filter(Track.playlist_id == playlist_id).count()
    return {
        "playlist_found": True,
        "playlist": {"id": playlist.id, "name": playlist.name},
        "tracks_count": tracks_count,
        "user": {"id": current_user.id, "spotify_id": current_user.spotify_user_id}
    }
