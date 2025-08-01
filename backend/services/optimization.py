"""
Core playlist optimization engine.
Provides actionable recommendations for improving playlist quality and flow.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import statistics
import logging
from sqlalchemy.orm import Session
from backend.models import User, Playlist, Track
from backend.services.listening_analytics import ListeningAnalyticsService
from backend.services.clustering import ClusteringService
import httpx
import random

logger = logging.getLogger(__name__)

class PlaylistOptimizationService:
    """Service for generating actionable playlist optimization recommendations."""
    
    def __init__(self):
        self.logger = logger
        self.analytics_service = ListeningAnalyticsService()
        # Note: clustering_service will be initialized when needed with proper dependencies
    
    async def optimize_playlist(
        self,
        user_id: str,
        playlist_id: str,
        db: Session,
        access_token: str,
        optimization_goals: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive optimization recommendations for a playlist.
        
        Args:
            user_id: Spotify user ID
            playlist_id: Spotify playlist ID
            db: Database session
            access_token: User's Spotify access token
            optimization_goals: Specific goals like ['flow', 'discovery', 'energy']
            
        Returns:
            Dict containing optimization recommendations
        """
        try:
            # Default optimization goals
            if optimization_goals is None:
                optimization_goals = ['flow', 'quality', 'discovery']
            
            # Get comprehensive playlist data
            playlist_data = await self._gather_playlist_data(
                user_id, playlist_id, db, access_token
            )
            
            # Generate optimization recommendations
            recommendations = []
            
            if 'flow' in optimization_goals:
                flow_recs = await self._optimize_flow(playlist_data, access_token)
                recommendations.extend(flow_recs)
            
            if 'quality' in optimization_goals:
                quality_recs = await self._optimize_quality(playlist_data, access_token)
                recommendations.extend(quality_recs)
            
            if 'discovery' in optimization_goals:
                discovery_recs = await self._optimize_discovery(playlist_data, access_token)
                recommendations.extend(discovery_recs)
            
            if 'energy' in optimization_goals:
                energy_recs = await self._optimize_energy_balance(playlist_data)
                recommendations.extend(energy_recs)
            
            # Sort recommendations by priority and impact
            recommendations.sort(key=lambda x: (
                self._priority_score(x['priority']),
                -x.get('impact_score', 0)
            ))
            
            # Calculate optimization summary
            summary = self._generate_optimization_summary(recommendations, playlist_data)
            
            return {
                "playlist_id": playlist_id,
                "optimization_goals": optimization_goals,
                "recommendations": recommendations,
                "summary": summary,
                "playlist_metrics": playlist_data.get("metrics", {}),
                "optimization_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing playlist: {str(e)}")
            raise
    
    async def _gather_playlist_data(
        self,
        user_id: str,
        playlist_id: str,
        db: Session,
        access_token: str
    ) -> Dict[str, Any]:
        """Gather comprehensive data about the playlist for optimization."""
        # Get listening analytics
        track_performance = await self.analytics_service.analyze_track_performance(
            user_id, playlist_id, db, access_token
        )
        
        # Get overskipped tracks
        overskipped = await self.analytics_service.identify_overskipped_tracks(
            user_id, playlist_id, db, access_token
        )
        
        # Get hidden gems
        hidden_gems = await self.analytics_service.find_hidden_gems(
            user_id, playlist_id, db, access_token
        )
        
        # Get playlist tracks with audio features
        playlist_tracks = await self._get_playlist_tracks_with_features(
            playlist_id, access_token
        )
        
        # Get clustering analysis (simplified for now)
        clustering_data = None
        if len(playlist_tracks.get('tracks_list', [])) >= 3:  # Need minimum tracks for clustering
            try:
                # For now, create a basic mock clustering structure
                # TODO: Implement proper clustering when dependencies are available
                clustering_data = {
                    "clusters": [
                        {"name": "Main cluster", "track_count": len(playlist_tracks.get('tracks_list', []))}
                    ]
                }
            except Exception as e:
                self.logger.warning(f"Clustering failed: {str(e)}")
        
        return {
            "track_performance": track_performance,
            "overskipped": overskipped,
            "hidden_gems": hidden_gems,
            "tracks": playlist_tracks,
            "clustering": clustering_data,
            "metrics": self._calculate_playlist_metrics(track_performance, playlist_tracks)
        }
    
    async def _optimize_flow(
        self,
        playlist_data: Dict[str, Any],
        access_token: str
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for improving playlist flow."""
        recommendations = []
        
        tracks = playlist_data.get("tracks", {}).get("tracks_list", [])
        if len(tracks) < 2:
            return recommendations
        
        # Analyze energy transitions
        energy_issues = self._analyze_energy_transitions(tracks)
        
        for issue in energy_issues:
            if issue['type'] == 'abrupt_energy_drop':
                recommendations.append({
                    "type": "reorder_tracks",
                    "priority": "high",
                    "title": "Fix Abrupt Energy Drop",
                    "description": f"Large energy drop between tracks {issue['track1_name']} and {issue['track2_name']}",
                    "action": "reorder",
                    "details": {
                        "move_track_id": issue['track2_id'],
                        "suggested_position": "later",
                        "reason": "Smooth energy transition"
                    },
                    "impact_score": 0.8,
                    "confidence": 0.7
                })
            
            elif issue['type'] == 'energy_spike':
                recommendations.append({
                    "type": "reorder_tracks",
                    "priority": "medium",
                    "title": "Smooth Energy Spike",
                    "description": f"Large energy increase between tracks {issue['track1_name']} and {issue['track2_name']}",
                    "action": "reorder",
                    "details": {
                        "move_track_id": issue['track2_id'],
                        "suggested_position": "earlier",
                        "reason": "Gradual energy buildup"
                    },
                    "impact_score": 0.6,
                    "confidence": 0.6
                })
        
        # Analyze tempo consistency
        tempo_issues = self._analyze_tempo_flow(tracks)
        
        for issue in tempo_issues:
            recommendations.append({
                "type": "reorder_tracks",
                "priority": "medium",
                "title": "Improve Tempo Flow",
                "description": f"Tempo jump from {issue['tempo1']:.0f} to {issue['tempo2']:.0f} BPM",
                "action": "reorder",
                "details": {
                    "move_track_id": issue['track_id'],
                    "reason": "Better tempo progression"
                },
                "impact_score": 0.5,
                "confidence": 0.5
            })
        
        return recommendations
    
    async def _optimize_quality(
        self,
        playlist_data: Dict[str, Any],
        access_token: str
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for improving track quality."""
        recommendations = []
        
        overskipped = playlist_data.get("overskipped", [])
        
        # Remove highly skipped tracks
        for track in overskipped:
            if track['skip_rate'] > 0.5 and track['confidence'] > 0.6:
                recommendations.append({
                    "type": "remove_track",
                    "priority": "high",
                    "title": "Remove Frequently Skipped Track",
                    "description": f"'{track['track_name']}' by {track['artist']} has {track['skip_rate']:.1%} skip rate",
                    "action": "remove",
                    "details": {
                        "track_id": track['track_id'],
                        "track_name": track['track_name'],
                        "artist": track['artist'],
                        "skip_rate": track['skip_rate'],
                        "reasons": track['reasons']
                    },
                    "impact_score": 0.9,
                    "confidence": track['confidence']
                })
        
        # Suggest replacements for removed tracks
        for track in overskipped[:3]:  # Top 3 problematic tracks
            if track['skip_rate'] > 0.4:
                replacement_suggestions = await self._find_track_replacements(
                    track, playlist_data, access_token
                )
                
                if replacement_suggestions:
                    recommendations.append({
                        "type": "replace_track",
                        "priority": "medium",
                        "title": "Replace with Better Alternative",
                        "description": f"Found better alternatives for '{track['track_name']}'",
                        "action": "replace",
                        "details": {
                            "remove_track_id": track['track_id'],
                            "suggestions": replacement_suggestions[:3],  # Top 3 suggestions
                            "reason": "Higher quality alternatives available"
                        },
                        "impact_score": 0.7,
                        "confidence": 0.6
                    })
        
        return recommendations
    
    async def _optimize_discovery(
        self,
        playlist_data: Dict[str, Any],
        access_token: str
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for better music discovery."""
        recommendations = []
        
        hidden_gems = playlist_data.get("hidden_gems", [])
        
        # Promote hidden gems
        for gem in hidden_gems[:3]:  # Top 3 hidden gems
            recommendations.append({
                "type": "promote_track",
                "priority": "medium",
                "title": "Promote Hidden Gem",
                "description": f"'{gem['track_name']}' by {gem['artist']} is high quality but under-played",
                "action": "reorder",
                "details": {
                    "track_id": gem['track_id'],
                    "track_name": gem['track_name'],
                    "artist": gem['artist'],
                    "current_play_rate": gem['play_rate'],
                    "quality_score": gem['quality_score'],
                    "promotion_suggestions": gem['promotion_suggestions']
                },
                "impact_score": 0.6,
                "confidence": 0.7
            })
        
        # Suggest new tracks based on clustering
        clustering_data = playlist_data.get("clustering")
        if clustering_data:
            cluster_suggestions = await self._suggest_tracks_for_clusters(
                clustering_data, access_token
            )
            
            for suggestion in cluster_suggestions[:2]:  # Top 2 cluster suggestions
                recommendations.append({
                    "type": "add_track",
                    "priority": "low",
                    "title": f"Add Track to {suggestion['cluster_name']} Cluster",
                    "description": f"Enhance your {suggestion['cluster_name'].lower()} with similar tracks",
                    "action": "add",
                    "details": {
                        "cluster_name": suggestion['cluster_name'],
                        "suggested_tracks": suggestion['tracks'][:3],
                        "reason": "Strengthen cluster diversity"
                    },
                    "impact_score": 0.4,
                    "confidence": 0.5
                })
        
        return recommendations
    
    async def _optimize_energy_balance(
        self,
        playlist_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for better energy balance."""
        recommendations = []
        
        tracks = playlist_data.get("tracks", {}).get("tracks_list", [])
        if len(tracks) < 5:
            return recommendations
        
        # Calculate energy distribution
        energies = [track.get("audio_features", {}).get("energy", 0.5) for track in tracks]
        avg_energy = statistics.mean(energies)
        energy_std = statistics.stdev(energies) if len(energies) > 1 else 0
        
        # Check for energy imbalance
        high_energy_count = sum(1 for e in energies if e > 0.7)
        low_energy_count = sum(1 for e in energies if e < 0.3)
        
        if high_energy_count / len(tracks) > 0.7:
            recommendations.append({
                "type": "balance_energy",
                "priority": "medium",
                "title": "Too Much High Energy",
                "description": f"{high_energy_count}/{len(tracks)} tracks are high energy. Add some calmer tracks.",
                "action": "add",
                "details": {
                    "target_energy_range": [0.3, 0.6],
                    "suggested_count": min(3, high_energy_count // 3),
                    "placement": "interspersed"
                },
                "impact_score": 0.6,
                "confidence": 0.7
            })
        
        elif low_energy_count / len(tracks) > 0.7:
            recommendations.append({
                "type": "balance_energy",
                "priority": "medium",
                "title": "Too Much Low Energy",
                "description": f"{low_energy_count}/{len(tracks)} tracks are low energy. Add some energetic tracks.",
                "action": "add",
                "details": {
                    "target_energy_range": [0.6, 0.9],
                    "suggested_count": min(3, low_energy_count // 3),
                    "placement": "strategic"
                },
                "impact_score": 0.6,
                "confidence": 0.7
            })
        
        return recommendations
    
    async def _get_playlist_tracks_with_features(
        self,
        playlist_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        """Get playlist tracks with their audio features."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Get playlist tracks
            async with httpx.AsyncClient() as client:
                tracks_response = await client.get(
                    f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                    headers=headers,
                    params={"limit": 100}
                )
                
                if tracks_response.status_code != 200:
                    return {"tracks_list": [], "features_df": None}
                
                tracks_data = tracks_response.json()
                tracks = tracks_data.get("items", [])
                
                # Get audio features for all tracks
                track_ids = [item["track"]["id"] for item in tracks if item["track"]["id"]]
                
                if not track_ids:
                    return {"tracks_list": [], "features_df": None}
                
                features_response = await client.get(
                    "https://api.spotify.com/v1/audio-features",
                    headers=headers,
                    params={"ids": ",".join(track_ids)}
                )
                
                features_data = features_response.json() if features_response.status_code == 200 else {"audio_features": []}
                audio_features = features_data.get("audio_features", [])
                
                # Combine track info with audio features
                tracks_with_features = []
                features_list = []
                
                for i, item in enumerate(tracks):
                    track = item["track"]
                    features = audio_features[i] if i < len(audio_features) and audio_features[i] else {}
                    
                    track_data = {
                        "id": track["id"],
                        "name": track["name"],
                        "artist": track["artists"][0]["name"] if track["artists"] else "Unknown",
                        "audio_features": features
                    }
                    
                    tracks_with_features.append(track_data)
                    
                    if features:
                        features_list.append({
                            "danceability": features.get("danceability", 0.5),
                            "energy": features.get("energy", 0.5),
                            "valence": features.get("valence", 0.5),
                            "acousticness": features.get("acousticness", 0.5),
                            "instrumentalness": features.get("instrumentalness", 0.5),
                            "speechiness": features.get("speechiness", 0.5),
                            "liveness": features.get("liveness", 0.5),
                            "tempo": features.get("tempo", 120),
                            "loudness": features.get("loudness", -10)
                        })
                
                # Create DataFrame for clustering
                import pandas as pd
                features_df = pd.DataFrame(features_list) if features_list else None
                
                return {
                    "tracks_list": tracks_with_features,
                    "features_df": features_df
                }
                
        except Exception as e:
            self.logger.error(f"Error getting playlist tracks with features: {str(e)}")
            return {"tracks_list": [], "features_df": None}
    
    def _analyze_energy_transitions(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze energy transitions between consecutive tracks."""
        issues = []
        
        for i in range(len(tracks) - 1):
            track1 = tracks[i]
            track2 = tracks[i + 1]
            
            energy1 = track1.get("audio_features", {}).get("energy", 0.5)
            energy2 = track2.get("audio_features", {}).get("energy", 0.5)
            
            energy_diff = energy2 - energy1
            
            # Detect abrupt energy drops
            if energy_diff < -0.4:
                issues.append({
                    "type": "abrupt_energy_drop",
                    "track1_id": track1["id"],
                    "track1_name": track1["name"],
                    "track2_id": track2["id"],
                    "track2_name": track2["name"],
                    "energy_diff": energy_diff
                })
            
            # Detect energy spikes
            elif energy_diff > 0.5:
                issues.append({
                    "type": "energy_spike",
                    "track1_id": track1["id"],
                    "track1_name": track1["name"],
                    "track2_id": track2["id"],
                    "track2_name": track2["name"],
                    "energy_diff": energy_diff
                })
        
        return issues
    
    def _analyze_tempo_flow(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze tempo flow issues."""
        issues = []
        
        for i in range(len(tracks) - 1):
            track1 = tracks[i]
            track2 = tracks[i + 1]
            
            tempo1 = track1.get("audio_features", {}).get("tempo", 120)
            tempo2 = track2.get("audio_features", {}).get("tempo", 120)
            
            tempo_diff = abs(tempo2 - tempo1)
            
            # Detect large tempo jumps
            if tempo_diff > 40:  # More than 40 BPM difference
                issues.append({
                    "type": "tempo_jump",
                    "track_id": track2["id"],
                    "track_name": track2["name"],
                    "tempo1": tempo1,
                    "tempo2": tempo2,
                    "tempo_diff": tempo_diff
                })
        
        return issues
    
    async def _find_track_replacements(
        self,
        problematic_track: Dict[str, Any],
        playlist_data: Dict[str, Any],
        access_token: str
    ) -> List[Dict[str, Any]]:
        """Find better alternatives for a problematic track."""
        # This would use Spotify's recommendation API in a real implementation
        # For now, return mock suggestions based on the track's characteristics
        
        track_name = problematic_track["track_name"]
        artist = problematic_track["artist"]
        
        # Mock replacement suggestions
        suggestions = [
            {
                "track_id": f"replacement_1_{problematic_track['track_id']}",
                "name": f"Similar to {track_name}",
                "artist": "Various Artists",
                "reason": "Similar style, better engagement",
                "confidence": 0.7
            },
            {
                "track_id": f"replacement_2_{problematic_track['track_id']}",
                "name": f"Alternative to {track_name}",
                "artist": artist,
                "reason": "Same artist, more popular",
                "confidence": 0.6
            }
        ]
        
        return suggestions
    
    async def _suggest_tracks_for_clusters(
        self,
        clustering_data: Dict[str, Any],
        access_token: str
    ) -> List[Dict[str, Any]]:
        """Suggest new tracks to enhance existing clusters."""
        suggestions = []
        
        clusters = clustering_data.get("clusters", [])
        
        for cluster in clusters[:2]:  # Top 2 clusters
            cluster_name = cluster["name"]
            
            # Mock track suggestions for the cluster
            suggestions.append({
                "cluster_name": cluster_name,
                "tracks": [
                    {
                        "track_id": f"suggestion_1_{cluster['name']}",
                        "name": f"Perfect for {cluster_name}",
                        "artist": "Recommended Artist",
                        "reason": "Matches cluster characteristics"
                    },
                    {
                        "track_id": f"suggestion_2_{cluster['name']}",
                        "name": f"Enhances {cluster_name}",
                        "artist": "Discovery Artist",
                        "reason": "Adds variety to cluster"
                    }
                ]
            })
        
        return suggestions
    
    def _calculate_playlist_metrics(
        self,
        track_performance: Dict[str, Any],
        tracks_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive playlist metrics."""
        insights = track_performance.get("playlist_insights", {})
        tracks = tracks_data.get("tracks_list", [])
        
        # Audio feature averages
        if tracks:
            energies = [t.get("audio_features", {}).get("energy", 0.5) for t in tracks]
            valences = [t.get("audio_features", {}).get("valence", 0.5) for t in tracks]
            danceabilities = [t.get("audio_features", {}).get("danceability", 0.5) for t in tracks]
            
            audio_metrics = {
                "average_energy": statistics.mean(energies) if energies else 0.5,
                "average_valence": statistics.mean(valences) if valences else 0.5,
                "average_danceability": statistics.mean(danceabilities) if danceabilities else 0.5,
                "energy_variance": statistics.variance(energies) if len(energies) > 1 else 0
            }
        else:
            audio_metrics = {}
        
        return {
            **insights,
            **audio_metrics,
            "total_tracks": len(tracks),
            "optimization_potential": self._calculate_optimization_potential(insights)
        }
    
    def _calculate_optimization_potential(self, insights: Dict[str, Any]) -> float:
        """Calculate how much the playlist could be improved (0-1 scale)."""
        skip_rate = insights.get("average_skip_rate", 0)
        quality_score = insights.get("average_quality_score", 0.5)
        problematic_tracks = insights.get("problematic_tracks", 0)
        total_tracks = insights.get("total_tracks_analyzed", 1)
        
        # Higher skip rate = more potential
        skip_potential = min(skip_rate * 2, 1.0)
        
        # Lower quality = more potential
        quality_potential = max(0, 1 - quality_score)
        
        # More problematic tracks = more potential
        problematic_ratio = problematic_tracks / total_tracks
        problematic_potential = min(problematic_ratio * 2, 1.0)
        
        # Average the potentials
        overall_potential = (skip_potential + quality_potential + problematic_potential) / 3
        
        return min(overall_potential, 1.0)
    
    def _generate_optimization_summary(
        self,
        recommendations: List[Dict[str, Any]],
        playlist_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a summary of optimization recommendations."""
        total_recs = len(recommendations)
        high_priority = sum(1 for r in recommendations if r["priority"] == "high")
        medium_priority = sum(1 for r in recommendations if r["priority"] == "medium")
        low_priority = sum(1 for r in recommendations if r["priority"] == "low")
        
        # Calculate potential impact
        avg_impact = statistics.mean([r.get("impact_score", 0) for r in recommendations]) if recommendations else 0
        
        # Count recommendation types
        type_counts = {}
        for rec in recommendations:
            rec_type = rec["type"]
            type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
        
        metrics = playlist_data.get("metrics", {})
        optimization_potential = metrics.get("optimization_potential", 0)
        
        return {
            "total_recommendations": total_recs,
            "priority_breakdown": {
                "high": high_priority,
                "medium": medium_priority,
                "low": low_priority
            },
            "recommendation_types": type_counts,
            "potential_impact": avg_impact,
            "optimization_potential": optimization_potential,
            "estimated_improvement": min(avg_impact * optimization_potential, 1.0),
            "top_priorities": [
                rec["title"] for rec in recommendations[:3] if rec["priority"] == "high"
            ]
        }
    
    def _priority_score(self, priority: str) -> int:
        """Convert priority string to numeric score for sorting."""
        priority_map = {"high": 1, "medium": 2, "low": 3}
        return priority_map.get(priority, 4)
