"""
API endpoints for listening behavior analytics and optimization features.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.dependencies import get_database, get_current_user
from backend.services.listening_analytics import ListeningAnalyticsService
from backend.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["listening-analytics"])

# Initialize analytics service
analytics_service = ListeningAnalyticsService()

@router.get("/track-performance/{playlist_id}")
async def get_track_performance(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Analyze track performance within a specific playlist.
    
    Returns detailed analytics for each track including play rates,
    skip rates, and quality assessments.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        performance_data = await analytics_service.analyze_track_performance(
            user_id=current_user.spotify_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token
        )
        
        return {
            "success": True,
            "data": performance_data,
            "message": f"Analyzed performance for playlist {playlist_id}"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error analyzing track performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze track performance"
        )

@router.get("/overskipped/{playlist_id}")
async def get_overskipped_tracks(
    playlist_id: str,
    skip_threshold: float = 0.3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Identify tracks that are consistently skipped in a playlist.
    
    Args:
        playlist_id: Spotify playlist ID
        skip_threshold: Skip rate threshold (default 0.3 = 30%)
        
    Returns:
        List of overskipped tracks with analysis and recommendations
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        # Validate skip threshold
        if not 0 <= skip_threshold <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip threshold must be between 0 and 1"
            )
        
        overskipped_tracks = await analytics_service.identify_overskipped_tracks(
            user_id=current_user.spotify_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token,
            skip_threshold=skip_threshold
        )
        
        from datetime import datetime
        
        return {
            "success": True,
            "data": {
                "overskipped_tracks": overskipped_tracks,
                "threshold_used": skip_threshold,
                "total_problematic": len(overskipped_tracks),
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            "message": f"Found {len(overskipped_tracks)} overskipped tracks"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error identifying overskipped tracks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to identify overskipped tracks"
        )

@router.get("/hidden-gems/{playlist_id}")
async def get_hidden_gems(
    playlist_id: str,
    underplay_threshold: float = 0.2,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Find high-quality tracks that are under-played in a playlist.
    
    Args:
        playlist_id: Spotify playlist ID
        underplay_threshold: Play rate threshold for "under-played" (default 0.2 = 20%)
        
    Returns:
        List of hidden gem tracks with promotion suggestions
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        # Validate underplay threshold
        if not 0 <= underplay_threshold <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Underplay threshold must be between 0 and 1"
            )
        
        hidden_gems = await analytics_service.find_hidden_gems(
            user_id=current_user.spotify_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token,
            underplay_threshold=underplay_threshold
        )
        
        from datetime import datetime
        
        return {
            "success": True,
            "data": {
                "hidden_gems": hidden_gems,
                "threshold_used": underplay_threshold,
                "total_gems_found": len(hidden_gems),
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            "message": f"Found {len(hidden_gems)} hidden gems"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error finding hidden gems: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find hidden gems"
        )

@router.get("/playlist-insights/{playlist_id}")
async def get_playlist_insights(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get comprehensive playlist insights including performance metrics,
    problematic tracks, and optimization opportunities.
    """
    try:
        if not current_user.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Spotify access token required"
            )
        
        # Get track performance data
        performance_data = await analytics_service.analyze_track_performance(
            user_id=current_user.spotify_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token
        )
        
        # Get overskipped tracks
        overskipped = await analytics_service.identify_overskipped_tracks(
            user_id=current_user.spotify_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token,
            skip_threshold=0.3
        )
        
        # Get hidden gems
        hidden_gems = await analytics_service.find_hidden_gems(
            user_id=current_user.spotify_id,
            playlist_id=playlist_id,
            db=db,
            access_token=current_user.access_token,
            underplay_threshold=0.2
        )
        
        # Compile comprehensive insights
        insights = {
            "playlist_id": playlist_id,
            "performance_summary": performance_data["playlist_insights"],
            "optimization_opportunities": {
                "overskipped_tracks": len(overskipped),
                "hidden_gems": len(hidden_gems),
                "total_tracks": performance_data["playlist_insights"]["total_tracks_analyzed"]
            },
            "recommendations": _generate_playlist_recommendations(
                performance_data["playlist_insights"], 
                overskipped, 
                hidden_gems
            ),
            "analysis_timestamp": performance_data["analysis_timestamp"]
        }
        
        return {
            "success": True,
            "data": insights,
            "message": "Generated comprehensive playlist insights"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating playlist insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate playlist insights"
        )

def _generate_playlist_recommendations(
    playlist_insights: Dict[str, Any],
    overskipped: List[Dict[str, Any]],
    hidden_gems: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate actionable recommendations based on playlist analysis."""
    recommendations = []
    
    # High skip rate recommendation
    avg_skip_rate = playlist_insights.get("average_skip_rate", 0)
    if avg_skip_rate > 0.3:
        recommendations.append({
            "type": "skip_rate_optimization",
            "priority": "high",
            "title": "High Skip Rate Detected",
            "description": f"Average skip rate is {avg_skip_rate:.1%}. Consider removing or repositioning problematic tracks.",
            "action": "Review overskipped tracks for removal",
            "impact": "Improved playlist flow and user engagement"
        })
    
    # Hidden gems recommendation
    if len(hidden_gems) > 0:
        recommendations.append({
            "type": "hidden_gems_promotion",
            "priority": "medium",
            "title": "Promote Hidden Gems",
            "description": f"Found {len(hidden_gems)} high-quality tracks that are under-played.",
            "action": "Reposition gems earlier in playlist",
            "impact": "Better track discovery and playlist value"
        })
    
    # Problematic tracks recommendation
    problematic_count = playlist_insights.get("problematic_tracks", 0)
    if problematic_count > 0:
        recommendations.append({
            "type": "problematic_track_cleanup",
            "priority": "high",
            "title": "Remove Problematic Tracks",
            "description": f"{problematic_count} tracks have very high skip rates (>40%).",
            "action": "Consider removing or replacing these tracks",
            "impact": "Cleaner playlist experience"
        })
    
    # Quality improvement recommendation
    avg_quality = playlist_insights.get("average_quality_score", 0.5)
    if avg_quality < 0.6:
        recommendations.append({
            "type": "quality_improvement",
            "priority": "medium",
            "title": "Improve Track Quality",
            "description": f"Average track quality score is {avg_quality:.1%}. Look for higher-quality alternatives.",
            "action": "Replace lower-quality tracks with similar but better alternatives",
            "impact": "Enhanced overall playlist quality"
        })
    
    # Diversity recommendation based on skip rate variance
    skip_variance = playlist_insights.get("skip_rate_std", 0)
    if skip_variance > 0.3:
        recommendations.append({
            "type": "consistency_improvement",
            "priority": "low",
            "title": "Improve Track Consistency",
            "description": "Wide variation in track performance suggests inconsistent playlist flow.",
            "action": "Analyze track positioning and transitions",
            "impact": "More consistent listening experience"
        })
    
    return recommendations

# Add router to main application
def include_analytics_router(app):
    """Include analytics router in main FastAPI application."""
    app.include_router(router)
