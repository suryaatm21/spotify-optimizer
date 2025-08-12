"""
Enhanced Clustering router for advanced playlist analysis.
Provides multiple clustering algorithms with automatic optimization.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.dependencies import get_database, get_current_user, get_clustering_service
from backend.models import User, Playlist, Track
from ..services.clustering import ClusteringService

router = APIRouter()

@router.post("/clustering/analyze/{playlist_id}")
async def analyze_playlist_enhanced(
    playlist_id: int,
    algorithm: str = Query("kmeans", description="Clustering algorithm to use"),
    num_clusters: Optional[int] = Query(None, description="Number of clusters (auto-detected if not provided)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    clustering_service: ClusteringService = Depends(get_clustering_service)
):
    """
    Analyze playlist with enhanced clustering algorithms.
    Supports kmeans, dbscan, gaussian_mixture, and spectral clustering.
    """
    # Validate algorithm parameter
    valid_algorithms = ["kmeans", "dbscan", "gaussian_mixture", "spectral"]
    if algorithm not in valid_algorithms:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid algorithm. Must be one of: {', '.join(valid_algorithms)}"
        )
    
    # Get playlist and verify ownership
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id, 
        Playlist.user_id == current_user.id
    ).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Get tracks for the playlist
    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    if not tracks:
        raise HTTPException(
            status_code=404, 
            detail="No tracks found in playlist. Please sync tracks first."
        )

    try:
        # Prepare tracks for analysis
        prepared_tracks, quality_report = await clustering_service.prepare_tracks_for_analysis(
            tracks,
            db=db,
            user_access_token=current_user.access_token
        )

        # Enhanced clustering with automatic optimization
        result = clustering_service.enhanced_cluster_analysis(
            prepared_tracks, 
            algorithm=algorithm,
            num_clusters=num_clusters,
            quality_report=quality_report
        )
        
        return {
            "playlist_id": playlist_id,
            "algorithm": algorithm,
            "clusters": [cluster.model_dump() for cluster in result["clusters"]],
            "silhouette_score": result["silhouette_score"],
            "optimal_clusters": result.get("optimal_clusters"),
            "cluster_labels": result.get("cluster_labels", {}),
            "analysis_metadata": result.get("analysis_metadata", {}),
            "quality_report": quality_report.model_dump() if quality_report else None
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering analysis failed: {str(e)}")

@router.get("/clustering/recommendations/{playlist_id}")
async def get_cluster_recommendations(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    clustering_service: ClusteringService = Depends(get_clustering_service)
):
    """
    Get cluster-based recommendations for improving playlist flow.
    """
    # Verify playlist ownership
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id, 
        Playlist.user_id == current_user.id
    ).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Get tracks and generate recommendations
    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    if not tracks:
        raise HTTPException(
            status_code=404, 
            detail="No tracks found in playlist."
        )

    try:
        # Prepare tracks and run clustering
        prepared_tracks, quality_report = await clustering_service.prepare_tracks_for_analysis(
            tracks,
            db=db,
            user_access_token=current_user.access_token
        )

        # Get cluster-based recommendations
        recommendations = clustering_service.get_cluster_recommendations(
            prepared_tracks,
            quality_report
        )
        
        return {
            "playlist_id": playlist_id,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate recommendations: {str(e)}"
        )

@router.get("/clustering/stats/{playlist_id}")
async def get_cluster_statistics(
    playlist_id: int,
    algorithm: str = Query("kmeans", description="Algorithm used for clustering"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    clustering_service: ClusteringService = Depends(get_clustering_service)
):
    """
    Get detailed cluster statistics and insights.
    """
    # Verify playlist ownership
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id, 
        Playlist.user_id == current_user.id
    ).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    tracks = db.query(Track).filter(Track.playlist_id == playlist_id).all()
    if not tracks:
        raise HTTPException(
            status_code=404, 
            detail="No tracks found in playlist."
        )

    try:
        # Prepare tracks for analysis
        prepared_tracks, quality_report = await clustering_service.prepare_tracks_for_analysis(
            tracks,
            db=db,
            user_access_token=current_user.access_token
        )

        # Get cluster statistics
        stats = clustering_service.get_cluster_statistics(
            prepared_tracks,
            algorithm=algorithm,
            quality_report=quality_report
        )
        
        return {
            "playlist_id": playlist_id,
            "algorithm": algorithm,
            "statistics": stats,
            "track_count": len(prepared_tracks)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate cluster statistics: {str(e)}"
        )
