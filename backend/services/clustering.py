"""
Clustering service for analyzing Spotify playlist audio features using machine learning.
"""
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import statistics

from models import Track
from schemas import ClusterData, PlaylistStats, OptimizationSuggestion

class ClusteringService:
    """
    Service for performing machine learning clustering analysis on Spotify tracks.
    """
    
    # Audio features to use for clustering
    AUDIO_FEATURES = [
        "danceability", "energy", "speechiness", "acousticness",
        "instrumentalness", "liveness", "valence", "tempo"
    ]
    
    def __init__(self):
        """Initialize the clustering service with default configuration."""
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)  # For visualization
    
    def _extract_features(self, tracks: List[Track]) -> np.ndarray:
        """
        Extract audio features from tracks for clustering.
        
        Args:
            tracks: List of Track objects with audio features
            
        Returns:
            np.ndarray: Normalized feature matrix
            
        Raises:
            ValueError: If no valid features found
        """
        features_data = []
        
        for track in tracks:
            track_features = []
            for feature in self.AUDIO_FEATURES:
                value = getattr(track, feature)
                if value is not None:
                    # Normalize tempo to 0-1 range (typical range 50-200 BPM)
                    if feature == "tempo":
                        value = min(max((value - 50) / 150, 0), 1)
                    track_features.append(value)
                else:
                    # Use mean value for missing features
                    track_features.append(0.5)
            
            features_data.append(track_features)
        
        if not features_data:
            raise ValueError("No valid audio features found for clustering")
        
        features_array = np.array(features_data)
        
        # Normalize features using StandardScaler
        normalized_features = self.scaler.fit_transform(features_array)
        
        return normalized_features
    
    def cluster_tracks(
        self, 
        tracks: List[Track], 
        method: str = "kmeans", 
        n_clusters: int = 3
    ) -> Tuple[List[ClusterData], float]:
        """
        Perform clustering analysis on tracks using specified method.
        
        Args:
            tracks: List of Track objects to cluster
            method: Clustering method ("kmeans" or "dbscan")
            n_clusters: Number of clusters for k-means
            
        Returns:
            Tuple[List[ClusterData], float]: Cluster data and silhouette score
            
        Raises:
            ValueError: If invalid method or insufficient data
        """
        if len(tracks) < 2:
            raise ValueError("Need at least 2 tracks for clustering")
        
        # Extract and normalize features
        features = self._extract_features(tracks)
        
        # Apply clustering algorithm
        if method == "kmeans":
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        elif method == "dbscan":
            # Use DBSCAN with automatic cluster detection
            clusterer = DBSCAN(eps=0.5, min_samples=2)
        else:
            raise ValueError(f"Unsupported clustering method: {method}")
        
        cluster_labels = clusterer.fit_predict(features)
        
        # Calculate silhouette score
        if len(set(cluster_labels)) > 1:
            silhouette_avg = silhouette_score(features, cluster_labels)
        else:
            silhouette_avg = 0.0
        
        # Group tracks by cluster
        clusters_dict = {}
        for idx, label in enumerate(cluster_labels):
            if label not in clusters_dict:
                clusters_dict[label] = []
            clusters_dict[label].append((idx, tracks[idx]))
        
        # Calculate cluster centers and create ClusterData objects
        clusters = []
        for cluster_id, cluster_tracks in clusters_dict.items():
            track_indices = [idx for idx, _ in cluster_tracks]
            cluster_features = features[track_indices]
            
            # Calculate center features (mean of normalized features)
            center_features = np.mean(cluster_features, axis=0)
            
            # Convert back to original feature names
            center_dict = {}
            for i, feature in enumerate(self.AUDIO_FEATURES):
                value = float(center_features[i])
                # Denormalize tempo
                if feature == "tempo":
                    value = (value * 150) + 50
                center_dict[feature] = value
            
            cluster_data = ClusterData(
                cluster_id=int(cluster_id) if cluster_id >= 0 else -1,  # DBSCAN can have -1 (noise)
                track_count=len(cluster_tracks),
                center_features=center_dict,
                track_ids=[track.id for _, track in cluster_tracks]
            )
            
            clusters.append(cluster_data)
        
        # Sort clusters by size (descending)
        clusters.sort(key=lambda x: x.track_count, reverse=True)
        
        return clusters, silhouette_avg
    
    def calculate_playlist_stats(self, tracks: List[Track]) -> PlaylistStats:
        """
        Calculate statistical summary of playlist audio features.
        
        Args:
            tracks: List of Track objects
            
        Returns:
            PlaylistStats: Statistical summary
        """
        if not tracks:
            raise ValueError("No tracks provided for statistics calculation")
        
        # Calculate basic statistics
        total_tracks = len(tracks)
        durations = [track.duration_ms for track in tracks if track.duration_ms is not None]
        popularities = [track.popularity for track in tracks if track.popularity is not None]
        
        avg_duration_ms = statistics.mean(durations) if durations else 0
        avg_popularity = statistics.mean(popularities) if popularities else 0
        
        # Calculate audio feature statistics
        feature_stats = {}
        feature_ranges = {}
        
        for feature in self.AUDIO_FEATURES:
            values = []
            for track in tracks:
                value = getattr(track, feature)
                if value is not None:
                    values.append(value)
            
            if values:
                feature_stats[feature] = statistics.mean(values)
                feature_ranges[feature] = {
                    "min": min(values),
                    "max": max(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0
                }
            else:
                feature_stats[feature] = 0
                feature_ranges[feature] = {"min": 0, "max": 0, "std": 0}
        
        return PlaylistStats(
            total_tracks=total_tracks,
            avg_duration_ms=avg_duration_ms,
            avg_popularity=avg_popularity,
            avg_audio_features=feature_stats,
            feature_ranges=feature_ranges
        )
    
    def generate_optimization_suggestions(
        self, 
        tracks: List[Track], 
        clusters: List[Dict[str, Any]]
    ) -> List[OptimizationSuggestion]:
        """
        Generate optimization suggestions based on clustering analysis.
        
        Args:
            tracks: List of Track objects
            clusters: Clustering analysis results
            
        Returns:
            List[OptimizationSuggestion]: Optimization suggestions
        """
        suggestions = []
        
        # Convert clusters to ClusterData objects if needed
        if clusters and isinstance(clusters[0], dict):
            cluster_objects = [ClusterData(**cluster) for cluster in clusters]
        else:
            cluster_objects = clusters
        
        # Suggestion 1: Identify outlier clusters (very small clusters)
        total_tracks = len(tracks)
        for cluster in cluster_objects:
            if cluster.track_count == 1:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="outlier_removal",
                    description=f"Consider removing track that forms its own cluster (may not fit playlist theme)",
                    affected_tracks=cluster.track_ids,
                    confidence_score=0.7
                ))
        
        # Suggestion 2: Identify dominant cluster patterns
        if cluster_objects:
            largest_cluster = max(cluster_objects, key=lambda x: x.track_count)
            if largest_cluster.track_count / total_tracks > 0.6:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="theme_consistency",
                    description=f"Most tracks ({largest_cluster.track_count}/{total_tracks}) follow a consistent theme. Consider adding similar tracks.",
                    affected_tracks=largest_cluster.track_ids,
                    confidence_score=0.8
                ))
        
        # Suggestion 3: Energy flow optimization
        track_dict = {track.id: track for track in tracks}
        for cluster in cluster_objects:
            if cluster.track_count >= 3:
                cluster_tracks = [track_dict[track_id] for track_id in cluster.track_ids if track_id in track_dict]
                avg_energy = statistics.mean([track.energy for track in cluster_tracks if track.energy is not None])
                
                if avg_energy > 0.8:
                    suggestions.append(OptimizationSuggestion(
                        suggestion_type="energy_balance",
                        description=f"High-energy cluster detected. Consider interspersing with lower-energy tracks for better flow.",
                        affected_tracks=cluster.track_ids,
                        confidence_score=0.6
                    ))
                elif avg_energy < 0.3:
                    suggestions.append(OptimizationSuggestion(
                        suggestion_type="energy_balance",
                        description=f"Low-energy cluster detected. Consider adding some higher-energy tracks for variety.",
                        affected_tracks=cluster.track_ids,
                        confidence_score=0.6
                    ))
        
        # Suggestion 4: Valence (mood) diversity
        valences = [track.valence for track in tracks if track.valence is not None]
        if valences:
            valence_std = statistics.stdev(valences) if len(valences) > 1 else 0
            avg_valence = statistics.mean(valences)
            
            if valence_std < 0.15:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="mood_diversity",
                    description=f"Low mood diversity detected (std: {valence_std:.2f}). Consider adding tracks with different emotional tones.",
                    affected_tracks=[track.id for track in tracks],
                    confidence_score=0.5
                ))
            
            if avg_valence < 0.3:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="mood_balance",
                    description=f"Playlist skews toward negative valence (avg: {avg_valence:.2f}). Consider adding some uplifting tracks.",
                    affected_tracks=[track.id for track in tracks],
                    confidence_score=0.6
                ))
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_pca_coordinates(self, tracks: List[Track]) -> List[Dict[str, float]]:
        """
        Get 2D PCA coordinates for visualization.
        
        Args:
            tracks: List of Track objects
            
        Returns:
            List[Dict[str, float]]: PCA coordinates with track IDs
        """
        if len(tracks) < 2:
            return []
        
        features = self._extract_features(tracks)
        pca_coords = self.pca.fit_transform(features)
        
        coordinates = []
        for i, track in enumerate(tracks):
            coordinates.append({
                "track_id": track.id,
                "x": float(pca_coords[i][0]),
                "y": float(pca_coords[i][1]),
                "name": track.name,
                "artist": track.artist
            })
        
        return coordinates
