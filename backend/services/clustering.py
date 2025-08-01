"""
Enhanced clustering service for analyzing Spotify playlist audio features using machine learning.
Implements advanced clustering algorithms, better normalization, and interpretable cluster labeling.
"""
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.cluster import SpectralClustering
from sklearn.preprocessing import StandardScaler, PowerTransformer
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from kneed import KneeLocator
import statistics
import logging
from sqlalchemy.orm import Session

from backend.models import Track, PlaylistAnalysis
from ..schemas import ClusterData, PlaylistStats, OptimizationSuggestion
from .audio_features import AudioFeaturesService

class ClusteringService:
    """
    Enhanced service for performing machine learning clustering analysis on Spotify tracks.
    Implements multiple clustering algorithms, smart preprocessing, and interpretable labels.
    """
    
    # Audio features to use for clustering (expanded set)
    AUDIO_FEATURES = [
        "danceability", "energy", "speechiness", "acousticness",
        "instrumentalness", "liveness", "valence", "tempo", "loudness"
    ]
    
    # Features that should be log-scaled before normalization
    LOG_SCALE_FEATURES = ["tempo", "loudness"]
    
    # Feature weights for clustering (higher = more important)
    FEATURE_WEIGHTS = {
        "danceability": 1.2,
        "energy": 1.2,
        "valence": 1.1,
        "acousticness": 1.0,
        "instrumentalness": 0.9,
        "speechiness": 0.8,
        "liveness": 0.7,
        "tempo": 1.0,
        "loudness": 0.8
    }
    
    def __init__(self, audio_features_service: AudioFeaturesService):
        """Initialize the enhanced clustering service with its dependencies."""
        self.scaler = StandardScaler()
        self.power_transformer = PowerTransformer(method='yeo-johnson', standardize=False)
        # Note: PCA instance is created fresh for each call to ensure deterministic behavior
        self.audio_features_service = audio_features_service
        self.logger = logging.getLogger(__name__)
    
    def _preprocess_features(self, tracks: List[Track]) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Enhanced feature preprocessing with log-scaling and smart normalization.
        
        Args:
            tracks: List of Track objects with audio features
            
        Returns:
            Tuple[np.ndarray, Dict[str, Any]]: Processed feature matrix and preprocessing metadata
            
        Raises:
            ValueError: If no valid features found
        """
        features_data = []
        preprocessing_info = {
            "log_scaled_features": [],
            "feature_ranges": {},
            "outlier_count": 0
        }
        
        for track in tracks:
            track_features = []
            for feature in self.AUDIO_FEATURES:
                value = getattr(track, feature)
                if value is not None:
                    # Apply log scaling for skewed features
                    if feature in self.LOG_SCALE_FEATURES and value > 0:
                        if feature == "tempo":
                            # Tempo: log scale and normalize
                            value = np.log(max(value, 1))  # Avoid log(0)
                        elif feature == "loudness":
                            # Loudness: shift to positive range then log scale
                            value = np.log(max(value + 60, 1))  # Shift typical range [-60, 0] to [0, 60]
                        if feature not in preprocessing_info["log_scaled_features"]:
                            preprocessing_info["log_scaled_features"].append(feature)
                    
                    track_features.append(value)
                else:
                    # Fallback to defaults
                    default_val = self.audio_features_service.FEATURE_DEFAULTS.get(feature, 0.5)
                    track_features.append(default_val)
            
            features_data.append(track_features)
        
        if not features_data:
            raise ValueError("No valid audio features found for clustering")
        
        features_array = np.array(features_data)
        
        # Store feature ranges for interpretation
        for i, feature in enumerate(self.AUDIO_FEATURES):
            preprocessing_info["feature_ranges"][feature] = {
                "min": float(np.min(features_array[:, i])),
                "max": float(np.max(features_array[:, i])),
                "mean": float(np.mean(features_array[:, i]))
            }
        
        # Use deterministic preprocessing - skip PowerTransformer for consistency
        # PowerTransformer can introduce randomness, use StandardScaler only
        try:
            # Create fresh scaler for deterministic behavior
            scaler = StandardScaler()
            normalized_features = scaler.fit_transform(features_array)
        except Exception as e:
            self.logger.warning(f"Scaling failed, using raw features: {e}")
            normalized_features = features_array
        
        # Apply feature weights
        for i, feature in enumerate(self.AUDIO_FEATURES):
            weight = self.FEATURE_WEIGHTS.get(feature, 1.0)
            normalized_features[:, i] *= weight
        
        # Detect outliers (optional: could be used for noise handling)
        outlier_threshold = 3  # Standard deviations
        outlier_mask = np.abs(normalized_features) > outlier_threshold
        preprocessing_info["outlier_count"] = int(np.sum(outlier_mask))
        
        return normalized_features, preprocessing_info
    
    def _find_optimal_clusters(self, features: np.ndarray, max_clusters: int = 8) -> int:
        """
        Find optimal number of clusters using multiple evaluation metrics.
        
        Args:
            features: Normalized feature matrix
            max_clusters: Maximum number of clusters to test
            
        Returns:
            int: Optimal number of clusters
        """
        if len(features) < 4:
            return min(len(features) - 1, 2)
        
        max_clusters = min(max_clusters, len(features) - 1)
        
        # Collect multiple metrics for cluster evaluation
        evaluation_results = []
        
        for k in range(2, max_clusters + 1):
            try:
                # Test with KMeans for consistency
                kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
                labels = kmeans.fit_predict(features)
                
                # Skip if all points in one cluster
                if len(set(labels)) < 2:
                    continue
                
                # Calculate multiple evaluation metrics
                silhouette_avg = silhouette_score(features, labels)
                calinski_score = calinski_harabasz_score(features, labels)
                
                # Calculate within-cluster sum of squares (WCSS) for elbow method
                wcss = kmeans.inertia_
                
                # Davies-Bouldin score (lower is better, so we'll invert it)
                from sklearn.metrics import davies_bouldin_score
                db_score = davies_bouldin_score(features, labels)
                
                evaluation_results.append({
                    'k': k,
                    'silhouette': silhouette_avg,
                    'calinski_harabasz': calinski_score,
                    'wcss': wcss,
                    'davies_bouldin': db_score,
                    'labels': labels
                })
                
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Clustering evaluation failed for k={k}: {e}")
                continue
        
        if not evaluation_results:
            return 2
        
        # Multi-criteria decision: combine multiple metrics
        optimal_k = self._select_optimal_k_multi_criteria(evaluation_results)
        return optimal_k
    
    def _select_optimal_k_multi_criteria(self, evaluation_results: List[Dict]) -> int:
        """
        Select optimal k using multiple criteria and scoring.
        
        Args:
            evaluation_results: List of evaluation metrics for different k values
            
        Returns:
            int: Optimal number of clusters
        """
        if len(evaluation_results) == 1:
            return evaluation_results[0]['k']
        
        # Normalize metrics to [0,1] for fair comparison
        def normalize_metric(values, higher_is_better=True):
            min_val, max_val = min(values), max(values)
            if max_val == min_val:
                return [0.5] * len(values)
            
            if higher_is_better:
                return [(v - min_val) / (max_val - min_val) for v in values]
            else:
                return [(max_val - v) / (max_val - min_val) for v in values]
        
        # Extract metric values
        k_values = [r['k'] for r in evaluation_results]
        silhouette_scores = [r['silhouette'] for r in evaluation_results]
        calinski_scores = [r['calinski_harabasz'] for r in evaluation_results]
        wcss_scores = [r['wcss'] for r in evaluation_results]
        db_scores = [r['davies_bouldin'] for r in evaluation_results]
        
        # Normalize metrics (higher normalized score = better)
        norm_silhouette = normalize_metric(silhouette_scores, higher_is_better=True)
        norm_calinski = normalize_metric(calinski_scores, higher_is_better=True)
        norm_wcss = normalize_metric(wcss_scores, higher_is_better=False)  # Lower WCSS is better
        norm_db = normalize_metric(db_scores, higher_is_better=False)  # Lower DB score is better
        
        # Calculate elbow score for WCSS
        elbow_scores = self._calculate_elbow_scores(k_values, wcss_scores)
        norm_elbow = normalize_metric(elbow_scores, higher_is_better=True)
        
        # Weighted combination of metrics
        weights = {
            'silhouette': 0.35,      # Primary metric for cluster separation
            'calinski': 0.20,        # Cluster compactness vs separation
            'elbow': 0.25,           # Elbow method for natural clustering
            'davies_bouldin': 0.20   # Inter vs intra-cluster distances
        }
        
        # Calculate composite scores
        composite_scores = []
        for i in range(len(evaluation_results)):
            score = (
                weights['silhouette'] * norm_silhouette[i] +
                weights['calinski'] * norm_calinski[i] +
                weights['elbow'] * norm_elbow[i] +
                weights['davies_bouldin'] * norm_db[i]
            )
            
            # Penalty for too many clusters (prefer simpler solutions)
            k_penalty = (k_values[i] - 2) * 0.05  # Small penalty for each additional cluster
            final_score = max(0, score - k_penalty)
            
            composite_scores.append(final_score)
        
        # Find k with highest composite score
        best_idx = composite_scores.index(max(composite_scores))
        optimal_k = evaluation_results[best_idx]['k']
        
        # Log the decision for transparency
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Optimal clusters selected: k={optimal_k}")
        logger.info(f"Evaluation scores: {dict(zip(k_values, composite_scores))}")
        
        return optimal_k
    
    def _calculate_elbow_scores(self, k_values: List[int], wcss_values: List[float]) -> List[float]:
        """
        Calculate elbow scores using the rate of change in WCSS.
        
        Args:
            k_values: List of k values
            wcss_values: Corresponding WCSS values
            
        Returns:
            List[float]: Elbow scores (higher = better elbow point)
        """
        if len(wcss_values) < 3:
            return [0.5] * len(wcss_values)
        
        # Calculate second derivatives (rate of change of rate of change)
        elbow_scores = [0.0] * len(wcss_values)
        
        for i in range(1, len(wcss_values) - 1):
            # Calculate curvature using second derivative approximation
            prev_slope = wcss_values[i] - wcss_values[i-1]
            next_slope = wcss_values[i+1] - wcss_values[i]
            curvature = abs(next_slope - prev_slope)
            elbow_scores[i] = curvature
        
        return elbow_scores
    
    def _apply_clustering_algorithm(
        self, 
        features: np.ndarray, 
        method: str, 
        n_clusters: Optional[int] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply the specified clustering algorithm with automatic parameter selection.
        
        Args:
            features: Normalized feature matrix
            method: Clustering method
            n_clusters: Number of clusters (auto-detected if None)
            
        Returns:
            Tuple[np.ndarray, Dict[str, Any]]: Cluster labels and algorithm metadata
        """
        algo_metadata = {"method": method}
        
        if method == "kmeans":
            if n_clusters is None:
                n_clusters = self._find_optimal_clusters(features)
            algo_metadata["n_clusters"] = n_clusters
            
            clusterer = KMeans(
                n_clusters=n_clusters, 
                random_state=42, 
                n_init="auto",
                max_iter=300
            )
            cluster_labels = clusterer.fit_predict(features)
            algo_metadata["inertia"] = float(clusterer.inertia_)
            
        elif method == "dbscan":
            # Auto-tune DBSCAN parameters
            from sklearn.neighbors import NearestNeighbors
            neighbors = NearestNeighbors(n_neighbors=4)
            neighbors_fit = neighbors.fit(features)
            distances, indices = neighbors_fit.kneighbors(features)
            distances = np.sort(distances[:, 3], axis=0)
            
            # Use elbow method to find optimal eps
            eps = np.percentile(distances, 75)  # Use 75th percentile as eps
            
            clusterer = DBSCAN(eps=eps, min_samples=max(2, len(features) // 10))
            cluster_labels = clusterer.fit_predict(features)
            
            algo_metadata["eps"] = float(eps)
            algo_metadata["min_samples"] = clusterer.min_samples
            algo_metadata["n_clusters"] = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            
        elif method == "gaussian_mixture":
            if n_clusters is None:
                n_clusters = self._find_optimal_clusters(features)
            algo_metadata["n_clusters"] = n_clusters
            
            clusterer = GaussianMixture(n_components=n_clusters, random_state=42)
            clusterer.fit(features)
            cluster_labels = clusterer.predict(features)
            algo_metadata["aic"] = float(clusterer.aic(features))
            algo_metadata["bic"] = float(clusterer.bic(features))
            
        elif method == "spectral":
            if n_clusters is None:
                n_clusters = self._find_optimal_clusters(features)
            algo_metadata["n_clusters"] = n_clusters
            
            clusterer = SpectralClustering(
                n_clusters=n_clusters, 
                random_state=42,
                affinity='rbf'
            )
            cluster_labels = clusterer.fit_predict(features)
            
        else:
            raise ValueError(f"Unsupported clustering method: {method}")
        
        return cluster_labels, algo_metadata
    
    def _label_cluster(self, center_features: Dict[str, float]) -> str:
        """
        Generate an interpretable label for a cluster based on its center features.
        
        Args:
            center_features: Dictionary of feature means for the cluster
            
        Returns:
            str: Human-readable cluster label
        """
        energy = center_features.get("energy", 0.5)
        valence = center_features.get("valence", 0.5)
        danceability = center_features.get("danceability", 0.5)
        acousticness = center_features.get("acousticness", 0.5)
        instrumentalness = center_features.get("instrumentalness", 0.5)
        tempo = center_features.get("tempo", 120)
        
        # High energy combinations
        if energy > 0.7:
            if valence > 0.7:
                if danceability > 0.7:
                    return "High-energy dance hits"
                else:
                    return "Upbeat & energetic"
            elif valence < 0.4:
                return "Intense & aggressive"
            else:
                return "High-energy tracks"
        
        # Low energy combinations
        elif energy < 0.4:
            if acousticness > 0.6:
                if valence < 0.4:
                    return "Mellow & melancholic"
                else:
                    return "Acoustic & chill"
            elif valence < 0.4:
                return "Sad & slow"
            else:
                return "Calm & relaxed"
        
        # Medium energy combinations
        else:
            if danceability > 0.7:
                return "Moderate dance tracks"
            elif acousticness > 0.6:
                return "Folk & acoustic"
            elif instrumentalness > 0.5:
                return "Instrumental pieces"
            elif valence > 0.7:
                return "Feel-good tracks"
            elif valence < 0.4:
                return "Bittersweet songs"
            else:
                return "Balanced mix"
    
    async def prepare_tracks_for_analysis(
        self, 
        tracks: List[Track], 
        db: Optional[Session] = None,
        user_access_token: Optional[str] = None
    ) -> Tuple[List[Track], Dict[str, Any]]:
        """
        Prepare tracks for clustering analysis by handling missing audio features.
        
        Args:
            tracks: List of Track objects
            db: Database session for updating tracks (optional)
            user_access_token: User's Spotify access token for API calls (optional)
            
        Returns:
            Tuple[List[Track], Dict[str, Any]]: Prepared tracks and quality report
        """
        # Analyze initial data quality
        initial_quality = self.audio_features_service.analyze_data_quality(tracks)
        
        # Try to fetch missing features from ReccoBeats API if database session provided
        if db is not None and initial_quality["overall_completeness"] < 0.9:
            tracks = await self.audio_features_service.fetch_and_impute_features(
                tracks, db
            )
        else:
            # If no database session, just impute missing features
            self.audio_features_service.impute_missing_features(tracks)
        
        # Analyze final data quality
        final_quality = self.audio_features_service.analyze_data_quality(tracks)
        
        quality_report = {
            "initial_quality": initial_quality,
            "final_quality": final_quality,
            "improvement": final_quality["overall_completeness"] - initial_quality["overall_completeness"]
        }
        
        return tracks, quality_report
    
    def cluster_tracks(
        self, 
        tracks: List[Track], 
        method: str = "kmeans", 
        n_clusters: Optional[int] = None,
        quality_report: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[ClusterData], float, Dict[str, Any]]:
        """
        Enhanced clustering analysis with automatic algorithm selection and interpretable labels.
        
        Args:
            tracks: List of Track objects to cluster (should be pre-processed)
            method: Clustering method ("kmeans", "dbscan", "gaussian_mixture", "spectral")
            n_clusters: Number of clusters (auto-detected if None)
            quality_report: Optional data quality report from preparation
            
        Returns:
            Tuple[List[ClusterData], float, Dict[str, Any]]: Cluster data, silhouette score, and analysis metadata
            
        Raises:
            ValueError: If invalid method or insufficient data
        """
        if len(tracks) < 2:
            raise ValueError("Need at least 2 tracks for clustering")
        
        # Enhanced feature preprocessing
        features, preprocessing_info = self._preprocess_features(tracks)
        
        # Apply clustering algorithm with automatic parameter selection
        cluster_labels, algo_metadata = self._apply_clustering_algorithm(
            features, method, n_clusters
        )
        
        # Calculate clustering quality metrics
        unique_labels = set(cluster_labels)
        if len(unique_labels) > 1:
            silhouette_avg = silhouette_score(features, cluster_labels)
            calinski_score = calinski_harabasz_score(features, cluster_labels)
        else:
            silhouette_avg = 0.0
            calinski_score = 0.0
        
        # Group tracks by cluster
        clusters_dict = {}
        for idx, label in enumerate(cluster_labels):
            if label not in clusters_dict:
                clusters_dict[label] = []
            clusters_dict[label].append((idx, tracks[idx]))
        
        # Calculate cluster centers and create ClusterData objects with labels
        clusters = []
        for cluster_id, cluster_tracks in clusters_dict.items():
            track_indices = [idx for idx, _ in cluster_tracks]
            cluster_features = features[track_indices]
            
            # Calculate center features (mean of normalized features)
            center_features_norm = np.mean(cluster_features, axis=0)
            
            # Convert back to interpretable feature values
            center_dict = {}
            for i, feature in enumerate(self.AUDIO_FEATURES):
                # Reverse the preprocessing to get interpretable values
                raw_value = float(center_features_norm[i])
                
                # Reverse feature weight
                weight = self.FEATURE_WEIGHTS.get(feature, 1.0)
                if weight != 0:
                    raw_value /= weight
                
                # Store for interpretation (these are still somewhat normalized)
                center_dict[feature] = raw_value
            
            # Generate interpretable label
            cluster_label = self._label_cluster(center_dict)
            
            cluster_data = ClusterData(
                cluster_id=int(cluster_id) if cluster_id >= 0 else -1,  # DBSCAN can have -1 (noise)
                track_count=len(cluster_tracks),
                center_features=center_dict,
                track_ids=[track.id for _, track in cluster_tracks],
                label=cluster_label  # Add interpretable label
            )
            
            clusters.append(cluster_data)
        
        # Sort clusters by size (descending)
        clusters.sort(key=lambda x: x.track_count, reverse=True)
        
        # Create comprehensive analysis metadata
        analysis_metadata = {
            "algorithm": algo_metadata,
            "preprocessing": preprocessing_info,
            "quality_metrics": {
                "silhouette_score": float(silhouette_avg),
                "calinski_harabasz_score": float(calinski_score),
                "n_clusters": len(unique_labels),
                "noise_points": int(sum(1 for label in cluster_labels if label == -1))
            },
            "feature_importance": dict(self.FEATURE_WEIGHTS),
            "data_quality": quality_report
        }
        
        return clusters, silhouette_avg, analysis_metadata
    
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
        clusters: List[ClusterData]
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
        
        # Suggestion 1: Identify outlier clusters (very small clusters)
        total_tracks = len(tracks)
        for cluster in clusters:
            if cluster.track_count == 1:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="outlier_removal",
                    description=f"Consider removing track that forms its own cluster (may not fit playlist theme)",
                    affected_tracks=cluster.track_ids,
                    confidence_score=0.7
                ))
        
        # Suggestion 2: Identify dominant cluster patterns
        if clusters:
            largest_cluster = max(clusters, key=lambda x: x.track_count)
            if largest_cluster.track_count / total_tracks > 0.6:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="theme_consistency",
                    description=f"Most tracks ({largest_cluster.track_count}/{total_tracks}) follow a consistent theme. Consider adding similar tracks.",
                    affected_tracks=largest_cluster.track_ids,
                    confidence_score=0.8
                ))
        
        # Suggestion 3: Energy flow optimization using cluster labels
        track_dict = {track.id: track for track in tracks}
        for cluster in clusters:
            if cluster.track_count >= 3 and cluster.label:
                cluster_tracks = [track_dict[track_id] for track_id in cluster.track_ids if track_id in track_dict]
                avg_energy = statistics.mean([track.energy for track in cluster_tracks if track.energy is not None])
                
                if "high-energy" in cluster.label.lower():
                    suggestions.append(OptimizationSuggestion(
                        suggestion_type="energy_balance",
                        description=f"'{cluster.label}' cluster detected. Consider interspersing with calmer tracks for better flow.",
                        affected_tracks=cluster.track_ids,
                        confidence_score=0.7
                    ))
                elif "calm" in cluster.label.lower() or "mellow" in cluster.label.lower():
                    suggestions.append(OptimizationSuggestion(
                        suggestion_type="energy_balance",
                        description=f"'{cluster.label}' cluster detected. Consider adding some energetic tracks for variety.",
                        affected_tracks=cluster.track_ids,
                        confidence_score=0.6
                    ))
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_pca_coordinates(self, tracks: List[Track]) -> List[Dict[str, float]]:
        """
        Get 2D PCA coordinates for visualization with enhanced preprocessing and deterministic behavior.
        
        Args:
            tracks: List of Track objects
            
        Returns:
            List[Dict[str, float]]: PCA coordinates with track IDs
        """
        if len(tracks) < 2:
            return []
        
        features, _ = self._preprocess_features(tracks)
        
        # Create a fresh PCA instance with full SVD for maximum determinism
        # Full SVD is more deterministic than randomized SVD
        pca = PCA(n_components=2, svd_solver="full", random_state=42)
        pca_coords = pca.fit_transform(features)
        
        # Ensure deterministic sign orientation for principal components to
        # prevent sign flips between repeated executions. We flip each
        # component so that the largest absolute loading is positive.
        for i in range(pca.components_.shape[0]):
            loading = pca.components_[i]
            # Identify index of the loading with largest absolute magnitude
            max_idx = np.argmax(np.abs(loading))
            if loading[max_idx] < 0:
                # Flip sign for this component axis
                pca.components_[i] *= -1
                pca_coords[:, i] *= -1
        
        # Additional determinism: ensure consistent ordering by sorting tracks by ID first
        # This ensures the same input order for PCA
        track_id_order = [(track.id, i, track) for i, track in enumerate(tracks)]
        track_id_order.sort(key=lambda x: x[0])  # Sort by track ID
        
        coordinates = []
        for track_id, original_idx, track in track_id_order:
            coordinates.append({
                "track_id": track.id,
                "x": float(pca_coords[original_idx][0]),
                "y": float(pca_coords[original_idx][1]),
                "name": track.name,
                "artist": track.artist
            })
        
        # Sort coordinates back by original track order for consistency
        coordinates.sort(key=lambda x: next(i for i, t in enumerate(tracks) if t.id == x["track_id"]))
        
        return coordinates
