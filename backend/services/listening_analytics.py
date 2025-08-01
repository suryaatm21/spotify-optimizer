"""
Listening behavior analytics service for Spotify playlist optimization.
Analyzes user listening patterns, skip rates, and track performance.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import logging
from sqlalchemy.orm import Session
from backend.models import User, Playlist, Track
import httpx

logger = logging.getLogger(__name__)

class ListeningAnalyticsService:
    """Service for analyzing user listening behavior and track performance."""
    
    def __init__(self):
        self.logger = logger
    
    async def analyze_track_performance(
        self, 
        user_id: str, 
        playlist_id: str,
        db: Session,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Analyze individual track performance within a playlist.
        
        Args:
            user_id: Spotify user ID
            playlist_id: Spotify playlist ID
            db: Database session
            access_token: User's Spotify access token
            
        Returns:
            Dict containing track performance analytics
        """
        try:
            # Get playlist tracks from database
            playlist = db.query(Playlist).filter(
                Playlist.spotify_id == playlist_id,
                Playlist.user_id == user_id
            ).first()
            
            if not playlist:
                raise ValueError(f"Playlist {playlist_id} not found for user {user_id}")
            
            # Get recently played tracks from Spotify
            recently_played = await self._fetch_recently_played(access_token)
            
            # Analyze track performance
            track_analytics = {}
            playlist_tracks = playlist.tracks
            
            for track in playlist_tracks:
                analytics = await self._analyze_single_track(
                    track, recently_played, access_token
                )
                track_analytics[track.spotify_id] = analytics
            
            # Calculate playlist-level insights
            playlist_insights = self._calculate_playlist_insights(track_analytics)
            
            return {
                "playlist_id": playlist_id,
                "track_analytics": track_analytics,
                "playlist_insights": playlist_insights,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing track performance: {str(e)}")
            raise
    
    async def identify_overskipped_tracks(
        self,
        user_id: str,
        playlist_id: str,
        db: Session,
        access_token: str,
        skip_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Identify tracks that are consistently skipped by the user.
        
        Args:
            user_id: Spotify user ID
            playlist_id: Spotify playlist ID
            db: Database session
            access_token: User's Spotify access token
            skip_threshold: Skip rate threshold (0.3 = 30% skip rate)
            
        Returns:
            List of overskipped track information
        """
        try:
            performance_data = await self.analyze_track_performance(
                user_id, playlist_id, db, access_token
            )
            
            overskipped_tracks = []
            
            for track_id, analytics in performance_data["track_analytics"].items():
                skip_rate = analytics.get("skip_rate", 0)
                
                if skip_rate >= skip_threshold:
                    track_info = await self._get_track_info(track_id, access_token)
                    
                    overskipped_tracks.append({
                        "track_id": track_id,
                        "track_name": track_info.get("name", "Unknown"),
                        "artist": track_info.get("artists", [{}])[0].get("name", "Unknown"),
                        "skip_rate": skip_rate,
                        "play_count": analytics.get("play_count", 0),
                        "skip_count": analytics.get("skip_count", 0),
                        "reasons": self._analyze_skip_reasons(analytics, track_info),
                        "confidence": self._calculate_confidence(analytics)
                    })
            
            # Sort by skip rate (highest first)
            overskipped_tracks.sort(key=lambda x: x["skip_rate"], reverse=True)
            
            return overskipped_tracks
            
        except Exception as e:
            self.logger.error(f"Error identifying overskipped tracks: {str(e)}")
            raise
    
    async def find_hidden_gems(
        self,
        user_id: str,
        playlist_id: str,
        db: Session,
        access_token: str,
        underplay_threshold: float = 0.2
    ) -> List[Dict[str, Any]]:
        """
        Find high-quality tracks that are under-played in the playlist.
        
        Args:
            user_id: Spotify user ID
            playlist_id: Spotify playlist ID
            db: Database session
            access_token: User's Spotify access token
            underplay_threshold: Play rate threshold for "under-played"
            
        Returns:
            List of hidden gem track information
        """
        try:
            performance_data = await self.analyze_track_performance(
                user_id, playlist_id, db, access_token
            )
            
            hidden_gems = []
            avg_play_rate = self._calculate_average_play_rate(
                performance_data["track_analytics"]
            )
            
            for track_id, analytics in performance_data["track_analytics"].items():
                play_rate = analytics.get("play_rate", 0)
                quality_score = analytics.get("quality_score", 0)
                
                # High quality but low play rate = hidden gem
                if (play_rate < underplay_threshold * avg_play_rate and 
                    quality_score > 0.7):
                    
                    track_info = await self._get_track_info(track_id, access_token)
                    
                    hidden_gems.append({
                        "track_id": track_id,
                        "track_name": track_info.get("name", "Unknown"),
                        "artist": track_info.get("artists", [{}])[0].get("name", "Unknown"),
                        "play_rate": play_rate,
                        "quality_score": quality_score,
                        "potential_rating": self._calculate_potential_rating(
                            quality_score, play_rate
                        ),
                        "reasons": self._analyze_underplay_reasons(analytics, track_info),
                        "promotion_suggestions": self._generate_promotion_suggestions(
                            analytics, track_info
                        )
                    })
            
            # Sort by potential rating (highest first)
            hidden_gems.sort(key=lambda x: x["potential_rating"], reverse=True)
            
            return hidden_gems
            
        except Exception as e:
            self.logger.error(f"Error finding hidden gems: {str(e)}")
            raise
    
    async def _fetch_recently_played(
        self, 
        access_token: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch recently played tracks from Spotify API."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.spotify.com/v1/me/player/recently-played",
                    headers=headers,
                    params={"limit": limit}
                )
                
                if response.status_code == 200:
                    return response.json().get("items", [])
                else:
                    self.logger.warning(f"Failed to fetch recently played: {response.status_code}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error fetching recently played: {str(e)}")
            return []
    
    async def _analyze_single_track(
        self,
        track: Track,
        recently_played: List[Dict[str, Any]],
        access_token: str
    ) -> Dict[str, Any]:
        """Analyze performance metrics for a single track."""
        track_id = track.spotify_id
        
        # Find all instances of this track in recently played
        track_plays = [
            item for item in recently_played 
            if item["track"]["id"] == track_id
        ]
        
        # Calculate basic metrics
        play_count = len(track_plays)
        
        # Estimate skip count (tracks played < 30 seconds apart suggest skips)
        skip_count = self._estimate_skip_count(track_plays)
        
        # Calculate rates
        total_encounters = play_count + skip_count
        skip_rate = skip_count / total_encounters if total_encounters > 0 else 0
        play_rate = play_count / total_encounters if total_encounters > 0 else 0
        
        # Get audio features for quality assessment
        audio_features = await self._get_track_audio_features(track_id, access_token)
        quality_score = self._calculate_quality_score(audio_features)
        
        return {
            "track_id": track_id,
            "play_count": play_count,
            "skip_count": skip_count,
            "skip_rate": skip_rate,
            "play_rate": play_rate,
            "quality_score": quality_score,
            "audio_features": audio_features,
            "last_played": track_plays[0]["played_at"] if track_plays else None
        }
    
    def _estimate_skip_count(self, track_plays: List[Dict[str, Any]]) -> int:
        """Estimate skip count based on play patterns."""
        # Simple heuristic: if the same track is played multiple times
        # with short intervals, earlier plays were likely skips
        if len(track_plays) <= 1:
            return 0
        
        # Sort by play time
        sorted_plays = sorted(track_plays, key=lambda x: x["played_at"])
        
        skip_count = 0
        for i in range(len(sorted_plays) - 1):
            current_time = datetime.fromisoformat(sorted_plays[i]["played_at"].replace('Z', '+00:00'))
            next_time = datetime.fromisoformat(sorted_plays[i + 1]["played_at"].replace('Z', '+00:00'))
            
            # If next play is within 2 minutes, likely a skip
            if (next_time - current_time).total_seconds() < 120:
                skip_count += 1
        
        return skip_count
    
    async def _get_track_info(self, track_id: str, access_token: str) -> Dict[str, Any]:
        """Get basic track information from Spotify API."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.spotify.com/v1/tracks/{track_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Error getting track info: {str(e)}")
            return {}
    
    async def _get_track_audio_features(self, track_id: str, access_token: str) -> Dict[str, Any]:
        """Get audio features for quality assessment."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.spotify.com/v1/audio-features/{track_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Error getting audio features: {str(e)}")
            return {}
    
    def _calculate_quality_score(self, audio_features: Dict[str, Any]) -> float:
        """Calculate a quality score based on audio features."""
        if not audio_features:
            return 0.5  # Default neutral score
        
        # Composite quality score based on multiple factors
        # Higher danceability, energy, and valence generally indicate popular tracks
        # Avoid extremely high speechiness (likely podcasts/interludes)
        # Moderate loudness is generally preferred
        
        danceability = audio_features.get("danceability", 0.5)
        energy = audio_features.get("energy", 0.5)
        valence = audio_features.get("valence", 0.5)
        speechiness = audio_features.get("speechiness", 0.5)
        acousticness = audio_features.get("acousticness", 0.5)
        
        # Quality factors
        base_quality = (danceability + energy + valence) / 3
        
        # Penalty for very high speechiness (likely not music)
        speech_penalty = max(0, speechiness - 0.66) * 0.5
        
        # Slight bonus for balanced acousticness
        acoustic_bonus = 0.1 * (1 - abs(acousticness - 0.5))
        
        quality = base_quality - speech_penalty + acoustic_bonus
        return max(0, min(1, quality))
    
    def _calculate_playlist_insights(self, track_analytics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall playlist performance insights."""
        if not track_analytics:
            return {}
        
        skip_rates = [analytics["skip_rate"] for analytics in track_analytics.values()]
        play_rates = [analytics["play_rate"] for analytics in track_analytics.values()]
        quality_scores = [analytics["quality_score"] for analytics in track_analytics.values()]
        
        return {
            "average_skip_rate": statistics.mean(skip_rates),
            "average_play_rate": statistics.mean(play_rates),
            "average_quality_score": statistics.mean(quality_scores),
            "skip_rate_std": statistics.stdev(skip_rates) if len(skip_rates) > 1 else 0,
            "problematic_tracks": sum(1 for rate in skip_rates if rate > 0.4),
            "high_performers": sum(1 for rate in play_rates if rate > 0.8),
            "total_tracks_analyzed": len(track_analytics)
        }
    
    def _calculate_average_play_rate(self, track_analytics: Dict[str, Dict[str, Any]]) -> float:
        """Calculate average play rate across all tracks."""
        if not track_analytics:
            return 0
        
        play_rates = [analytics["play_rate"] for analytics in track_analytics.values()]
        return statistics.mean(play_rates) if play_rates else 0
    
    def _analyze_skip_reasons(self, analytics: Dict[str, Any], track_info: Dict[str, Any]) -> List[str]:
        """Analyze potential reasons why a track is being skipped."""
        reasons = []
        
        audio_features = analytics.get("audio_features", {})
        
        # High speechiness might indicate podcast/interlude
        if audio_features.get("speechiness", 0) > 0.66:
            reasons.append("High speechiness (may be spoken word/podcast)")
        
        # Very low energy might not fit playlist vibe
        if audio_features.get("energy", 0.5) < 0.2:
            reasons.append("Very low energy")
        
        # Extreme tempo might be disruptive
        tempo = audio_features.get("tempo", 120)
        if tempo < 60 or tempo > 180:
            reasons.append("Unusual tempo")
        
        # Very long tracks might be skipped for time
        duration = track_info.get("duration_ms", 0)
        if duration > 360000:  # > 6 minutes
            reasons.append("Long duration")
        
        if not reasons:
            reasons.append("May not fit playlist mood/flow")
        
        return reasons
    
    def _analyze_underplay_reasons(self, analytics: Dict[str, Any], track_info: Dict[str, Any]) -> List[str]:
        """Analyze why a quality track might be under-played."""
        reasons = []
        
        # Track position in playlist might affect discovery
        reasons.append("May be positioned poorly in playlist")
        
        audio_features = analytics.get("audio_features", {})
        
        # High acousticness might indicate slower/quieter track
        if audio_features.get("acousticness", 0.5) > 0.7:
            reasons.append("Acoustic/ambient style may be overlooked")
        
        # Lower energy tracks might be skipped in certain contexts
        if audio_features.get("energy", 0.5) < 0.4:
            reasons.append("Lower energy might not match listening context")
        
        # Instrumentals might be overlooked
        if audio_features.get("instrumentalness", 0) > 0.5:
            reasons.append("Instrumental track may be underappreciated")
        
        return reasons
    
    def _calculate_potential_rating(self, quality_score: float, play_rate: float) -> float:
        """Calculate potential rating for hidden gems."""
        # High quality + low play rate = high potential
        return quality_score * (1 - play_rate)
    
    def _generate_promotion_suggestions(self, analytics: Dict[str, Any], track_info: Dict[str, Any]) -> List[str]:
        """Generate suggestions for promoting hidden gem tracks."""
        suggestions = []
        
        audio_features = analytics.get("audio_features", {})
        
        # Suggest playlist repositioning
        if audio_features.get("energy", 0.5) > 0.6:
            suggestions.append("Move to earlier in playlist for higher visibility")
        else:
            suggestions.append("Position as a mood transition track")
        
        # Suggest based on characteristics
        if audio_features.get("danceability", 0.5) > 0.7:
            suggestions.append("Highlight as a great dance track")
        
        if audio_features.get("valence", 0.5) > 0.7:
            suggestions.append("Feature as a mood booster")
        
        if audio_features.get("acousticness", 0.5) > 0.6:
            suggestions.append("Perfect for focused listening moments")
        
        return suggestions
    
    def _calculate_confidence(self, analytics: Dict[str, Any]) -> float:
        """Calculate confidence score for analytics results."""
        # Confidence based on sample size and consistency
        total_encounters = analytics.get("play_count", 0) + analytics.get("skip_count", 0)
        
        if total_encounters == 0:
            return 0.0
        elif total_encounters < 3:
            return 0.3
        elif total_encounters < 5:
            return 0.6
        elif total_encounters < 10:
            return 0.8
        else:
            return 0.9
