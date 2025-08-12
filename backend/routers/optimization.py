"""
API endpoints for playlist optimization features.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.dependencies import get_database, get_current_user
from backend.services.optimization import PlaylistOptimizationService
from backend.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["playlist-optimization"])

# Initialize optimization service
optimization_service = PlaylistOptimizationService()

@router.post("/{playlist_id}")
async def optimize_playlist(
    playlist_id: str,
    optimization_goals: Optional[List[str]] = Query(
        default=None,
        description="Optimization goals: flow, quality, discovery, energy"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Generate comprehensive optimization recommendations for a playlist.
    
    Args:
        playlist_id: Spotify playlist ID
        optimization_goals: List of goals like ['flow', 'quality', 'discovery', 'energy']
        
    Returns:
        Comprehensive optimization recommendations with actionable insights
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        # Validate optimization goals
        valid_goals = ['flow', 'quality', 'discovery', 'energy']
        if optimization_goals:
            invalid_goals = [goal for goal in optimization_goals if goal not in valid_goals]
            if invalid_goals:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid optimization goals: {invalid_goals}. Valid goals: {valid_goals}"
                )
        
        optimization_result = await optimization_service.optimize_playlist(
            user_id=current_user.spotify_user_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token,
            optimization_goals=optimization_goals
        )
        
        return {
            "success": True,
            "data": optimization_result,
            "message": f"Generated {len(optimization_result['recommendations'])} optimization recommendations"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error optimizing playlist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize playlist"
        )

@router.get("/{playlist_id}/flow")
async def optimize_playlist_flow(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get specific recommendations for improving playlist flow.
    Focuses on energy transitions, tempo progressions, and track ordering.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        optimization_result = await optimization_service.optimize_playlist(
            user_id=current_user.spotify_user_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token,
            optimization_goals=['flow']
        )
        
        # Filter only flow-related recommendations
        flow_recommendations = [
            rec for rec in optimization_result['recommendations']
            if rec['type'] in ['reorder_tracks', 'balance_energy']
        ]
        
        return {
            "success": True,
            "data": {
                "playlist_id": playlist_id,
                "flow_recommendations": flow_recommendations,
                "summary": {
                    "total_flow_issues": len(flow_recommendations),
                    "energy_issues": len([r for r in flow_recommendations if 'energy' in r['title'].lower()]),
                    "tempo_issues": len([r for r in flow_recommendations if 'tempo' in r['title'].lower()]),
                    "potential_improvement": optimization_result['summary']['estimated_improvement']
                },
                "optimization_timestamp": optimization_result['optimization_timestamp']
            },
            "message": f"Found {len(flow_recommendations)} flow optimization opportunities"
        }
        
    except Exception as e:
        logger.error(f"Error optimizing playlist flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize playlist flow"
        )

@router.get("/{playlist_id}/quality")
async def optimize_playlist_quality(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get specific recommendations for improving playlist quality.
    Focuses on removing problematic tracks and suggesting replacements.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        optimization_result = await optimization_service.optimize_playlist(
            user_id=current_user.spotify_user_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token,
            optimization_goals=['quality']
        )
        
        # Filter only quality-related recommendations
        quality_recommendations = [
            rec for rec in optimization_result['recommendations']
            if rec['type'] in ['remove_track', 'replace_track']
        ]
        
        return {
            "success": True,
            "data": {
                "playlist_id": playlist_id,
                "quality_recommendations": quality_recommendations,
                "summary": {
                    "tracks_to_remove": len([r for r in quality_recommendations if r['type'] == 'remove_track']),
                    "replacement_suggestions": len([r for r in quality_recommendations if r['type'] == 'replace_track']),
                    "current_quality_score": optimization_result['playlist_metrics'].get('average_quality_score', 0.5),
                    "potential_improvement": optimization_result['summary']['estimated_improvement']
                },
                "optimization_timestamp": optimization_result['optimization_timestamp']
            },
            "message": f"Found {len(quality_recommendations)} quality improvement opportunities"
        }
        
    except Exception as e:
        logger.error(f"Error optimizing playlist quality: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize playlist quality"
        )

@router.get("/{playlist_id}/discovery")
async def optimize_playlist_discovery(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get specific recommendations for improving music discovery.
    Focuses on promoting hidden gems and suggesting new tracks.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        optimization_result = await optimization_service.optimize_playlist(
            user_id=current_user.spotify_user_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token,
            optimization_goals=['discovery']
        )
        
        # Filter only discovery-related recommendations
        discovery_recommendations = [
            rec for rec in optimization_result['recommendations']
            if rec['type'] in ['promote_track', 'add_track']
        ]
        
        return {
            "success": True,
            "data": {
                "playlist_id": playlist_id,
                "discovery_recommendations": discovery_recommendations,
                "summary": {
                    "hidden_gems_to_promote": len([r for r in discovery_recommendations if r['type'] == 'promote_track']),
                    "new_tracks_suggested": len([r for r in discovery_recommendations if r['type'] == 'add_track']),
                    "discovery_potential": optimization_result['summary']['estimated_improvement']
                },
                "optimization_timestamp": optimization_result['optimization_timestamp']
            },
            "message": f"Found {len(discovery_recommendations)} discovery enhancement opportunities"
        }
        
    except Exception as e:
        logger.error(f"Error optimizing playlist discovery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize playlist discovery"
        )

@router.get("/{playlist_id}/summary")
async def get_optimization_summary(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get a high-level summary of optimization opportunities for a playlist.
    Provides overview without detailed recommendations.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        optimization_result = await optimization_service.optimize_playlist(
            user_id=current_user.spotify_user_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token,
            optimization_goals=['flow', 'quality', 'discovery', 'energy']
        )
        
        summary = optimization_result['summary']
        metrics = optimization_result['playlist_metrics']
        
        return {
            "success": True,
            "data": {
                "playlist_id": playlist_id,
                "optimization_score": round((1 - metrics.get('optimization_potential', 0)) * 100),
                "total_opportunities": summary['total_recommendations'],
                "priority_breakdown": summary['priority_breakdown'],
                "key_metrics": {
                    "average_skip_rate": metrics.get('average_skip_rate', 0),
                    "average_quality_score": metrics.get('average_quality_score', 0.5),
                    "average_energy": metrics.get('average_energy', 0.5),
                    "total_tracks": metrics.get('total_tracks', 0)
                },
                "top_recommendations": summary['top_priorities'][:3],
                "estimated_improvement": round(summary['estimated_improvement'] * 100),
                "recommendation_categories": {
                    "flow_improvements": summary['recommendation_types'].get('reorder_tracks', 0),
                    "quality_improvements": summary['recommendation_types'].get('remove_track', 0) + summary['recommendation_types'].get('replace_track', 0),
                    "discovery_enhancements": summary['recommendation_types'].get('promote_track', 0) + summary['recommendation_types'].get('add_track', 0),
                    "energy_balancing": summary['recommendation_types'].get('balance_energy', 0)
                },
                "optimization_timestamp": optimization_result['optimization_timestamp']
            },
            "message": "Generated optimization summary"
        }
        
    except Exception as e:
        logger.error(f"Error generating optimization summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate optimization summary"
        )

@router.get("/recommendations/{playlist_id}")
async def get_optimization_recommendations(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get comprehensive optimization recommendations for a playlist.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        # Use the main optimization endpoint
        optimization_result = await optimize_playlist(
            playlist_id=playlist_id,
            optimization_goals=["flow", "quality", "discovery", "energy"],
            current_user=current_user,
            db=db
        )
        
        recommendations = optimization_result.get("data", {}).get("recommendations", [])
        
        return {
            "playlist_id": playlist_id,
            "recommendations": recommendations,
            "optimization_score": optimization_result.get("data", {}).get("overall_score", 0.5),
            "total_recommendations": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get optimization recommendations"
        )

@router.get("/energy-analysis/{playlist_id}")
async def analyze_energy_transitions(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Analyze energy transitions in the playlist.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        # Get flow optimization data which includes energy analysis
        flow_result = await optimize_playlist_flow(
            playlist_id=playlist_id,
            current_user=current_user,
            db=db
        )
        
        flow_data = flow_result.get("data", {})
        
        return {
            "playlist_id": playlist_id,
            "flow_score": flow_data.get("flow_score", 0.5),
            "energy_transitions": flow_data.get("transition_analysis", {}),
            "problematic_transitions": len([t for t in flow_data.get("transition_analysis", {}).get("problematic_transitions", [])]),
            "recommendations": flow_data.get("recommendations", [])
        }
        
    except Exception as e:
        logger.error(f"Error analyzing energy transitions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze energy transitions"
        )

@router.get("/tempo-flow/{playlist_id}")
async def optimize_tempo_flow(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get tempo flow optimization suggestions.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        # Get flow optimization which includes tempo analysis
        flow_result = await optimize_playlist_flow(
            playlist_id=playlist_id,
            current_user=current_user,
            db=db
        )
        
        flow_data = flow_result.get("data", {})
        
        return {
            "playlist_id": playlist_id,
            "tempo_analysis": {
                "avg_tempo": flow_data.get("avg_tempo", 120),
                "tempo_variance": flow_data.get("tempo_variance", 0),
                "tempo_progression": flow_data.get("tempo_progression", "stable")
            },
            "recommendations": [r for r in flow_data.get("recommendations", []) if "tempo" in r.get("description", "").lower()],
            "flow_score": flow_data.get("flow_score", 0.5)
        }
        
    except Exception as e:
        logger.error(f"Error optimizing tempo flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize tempo flow"
        )

@router.get("/track-replacements/{playlist_id}")
async def get_track_replacements(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get track replacement suggestions.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        # Get quality optimization which includes replacement suggestions
        quality_result = await optimize_playlist_quality(
            playlist_id=playlist_id,
            current_user=current_user,
            db=db
        )
        
        quality_data = quality_result.get("data", {})
        recommendations = quality_data.get("recommendations", [])
        
        # Filter for replacement-type recommendations
        replacements = []
        for rec in recommendations:
            if rec.get("action_type") in ["replace_track", "remove_track"]:
                replacements.append({
                    "current_track": rec.get("track_name", "Unknown Track"),
                    "suggested_track": rec.get("replacement_suggestion", "Find similar higher-quality track"),
                    "reason": rec.get("description", "Quality improvement"),
                    "priority": rec.get("priority", "medium")
                })
        
        return {
            "playlist_id": playlist_id,
            "replacements": replacements,
            "total_suggestions": len(replacements)
        }
        
    except Exception as e:
        logger.error(f"Error getting track replacements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get track replacements"
        )
