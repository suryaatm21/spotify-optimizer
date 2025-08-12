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
    
    def _preprocess_features(self, tracks: List[Track]) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Enhanced feature preprocessing with log-scaling and smart normalization.
        
        Args:
            tracks: List of Track objects with audio features
            
        Returns:
            Tuple[np.ndarray, np.ndarray, Dict[str, Any]]: Normalized features for clustering, 
            raw features for labeling, and preprocessing metadata
            
        Raises:
            ValueError: If no valid features found
        """
        features_data = []
        raw_features_data = []  # Store raw features for labeling
        preprocessing_info = {
            "log_scaled_features": [],
            "feature_ranges": {},
            "outlier_count": 0
        }
        
        for track in tracks:
            track_features = []
            raw_track_features = []  # Raw features before scaling
            
            for feature in self.AUDIO_FEATURES:
                value = getattr(track, feature)
                if value is not None:
                    # Store raw value for labeling (0-1 scale for most features)
                    if feature in ["tempo"]:
                        # Normalize tempo to 0-1 scale for consistent labeling
                        raw_value = min(max((value - 60) / (200 - 60), 0), 1)
                    elif feature in ["loudness"]:
                        # Normalize loudness to 0-1 scale
                        raw_value = min(max((value + 60) / 60, 0), 1)
                    else:
                        # Most features are already 0-1 scale
                        raw_value = min(max(value, 0), 1)
                    raw_track_features.append(raw_value)
                    
                    # Apply log scaling for clustering features
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
                    raw_track_features.append(default_val)
            
            features_data.append(track_features)
            raw_features_data.append(raw_track_features)
        
        if not features_data:
            raise ValueError("No valid audio features found for clustering")
        
        features_array = np.array(features_data)
        raw_features_array = np.array(raw_features_data)
        
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
        
        return normalized_features, raw_features_array, preprocessing_info
    
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
                max_iter=300,
            )
            cluster_labels = clusterer.fit_predict(features)
            algo_metadata["inertia"] = float(clusterer.inertia_)

        elif method == "dbscan":
            # Auto-tune DBSCAN parameters - handle small datasets
            from sklearn.neighbors import NearestNeighbors
            
            n_samples = len(features)
            n_neighbors = min(4, n_samples - 1)  # Ensure neighbors doesn't exceed samples
            
            if n_neighbors < 2:
                # Too few samples for DBSCAN, fall back to KMeans immediately
                self.logger.warning(f"DBSCAN: dataset too small (n_samples={n_samples}). Falling back to KMeans.")
                fallback_clusters = min(max(2, n_samples - 1), 2)
                clusterer = KMeans(n_clusters=fallback_clusters, random_state=42, n_init="auto")
                cluster_labels = clusterer.fit_predict(features)
                algo_metadata["fallback_to_kmeans"] = True
                algo_metadata["fallback_reason"] = f"Dataset too small ({n_samples} samples)"
                algo_metadata["n_clusters"] = fallback_clusters
                self.logger.info("DBSCAN->KMeans fallback: k=%d", fallback_clusters)
            else:
                neighbors = NearestNeighbors(n_neighbors=n_neighbors)
                neighbors_fit = neighbors.fit(features)
                distances, _ = neighbors_fit.kneighbors(features)
                distances = np.sort(distances[:, n_neighbors-1], axis=0)

                #
                # Planning (per repo guideline for large files):
                # - Replace single-percentile eps selection with a small search over percentiles.
                # - Score each candidate by silhouette and cluster count (prefer 2-6), penalize noise.
                # - Keep strong guards against eps<=0; if no viable candidate, fallback to KMeans.
                # - Preserve existing debug prints and metadata (add chosen percentile).

                # Log k-distance distribution for transparency
                try:
                    q25 = float(np.percentile(distances, 25))
                    q50 = float(np.percentile(distances, 50))
                    q75 = float(np.percentile(distances, 75))
                    q90 = float(np.percentile(distances, 90))
                    self.logger.info(
                        "DBSCAN: n_samples=%d n_neighbors=%d kdist q25=%.4f q50=%.4f q75=%.4f q90=%.4f",
                        n_samples, n_neighbors, q25, q50, q75, q90
                    )
                    print(
                        f"DBSCAN DEBUG: n_samples={n_samples} n_neighbors={n_neighbors} "
                        f"kdist q25={q25:.4f} q50={q50:.4f} q75={q75:.4f} q90={q90:.4f}"
                    )
                except Exception:
                    pass

                # Candidate percentiles to search; broad but small set to avoid overfitting
                candidate_percentiles = [60, 70, 75, 80, 85, 90, 95]
                min_eps = 1e-4
                base_min_samples = max(2, len(features) // 10)
                candidate_min_samples = sorted({base_min_samples, max(3, len(features) // 8)})

                best_score = -1e9
                best_labels = None
                best_eps = None
                best_ms = None
                best_pct = None

                def safe_eps(pct: float) -> float:
                    e = float(np.percentile(distances, pct))
                    if not np.isfinite(e) or e <= 0.0:
                        non_zero = distances[distances > 0]
                        if non_zero.size > 0:
                            e2 = float(np.percentile(non_zero, pct))
                            self.logger.info(
                                "DBSCAN: p%(pct).0f(all)=%.6f nonzero_p%(pct).0f=%.6f -> using nonzero",
                                float(e), e2, extra={}
                            )
                            print(f"DBSCAN DEBUG: eps non-positive ({e:.6f}); using nonzero p{int(pct)}={e2:.6f}")
                            e = e2
                    if not np.isfinite(e) or e <= 0.0:
                        e = min_eps
                        self.logger.info("DBSCAN: eps adjusted to minimum floor %.6f", e)
                        print(f"DBSCAN DEBUG: eps adjusted to minimum floor {e:.6f}")
                    return float(e)

                # Try small grid of (eps percentile, min_samples)
                for pct in candidate_percentiles:
                    e = safe_eps(pct)
                    for ms in candidate_min_samples:
                        try:
                            trial = DBSCAN(eps=e, min_samples=ms)
                            labels = trial.fit_predict(features)
                        except ValueError as ex:
                            # Skip invalid combos; try next
                            self.logger.info("DBSCAN trial failed: eps=%.5f ms=%d err=%s", e, ms, str(ex))
                            print(f"DBSCAN DEBUG: trial failed eps={e:.6f} ms={ms} -> {ex}")
                            continue

                        # Evaluate
                        unique = set(labels)
                        non_noise = [l for l in unique if l != -1]
                        c = len(non_noise)
                        noise_ratio = (labels == -1).sum() / len(labels)
                        if c < 2:
                            # Degenerate; continue search
                            continue
                        try:
                            sil = silhouette_score(features, labels)
                        except Exception:
                            sil = 0.0

                        # Score: prioritize silhouette; light preference for 2-6 clusters; penalize noise
                        cluster_pref_penalty = 0.06 * max(0, abs(4 - c))  # prefer ~4 clusters softly
                        noise_penalty = 0.30 * noise_ratio
                        score = float(sil) - cluster_pref_penalty - noise_penalty

                        if score > best_score:
                            best_score = score
                            best_labels = labels
                            best_eps = e
                            best_ms = ms
                            best_pct = pct

                if best_labels is None:
                    # No viable DBSCAN configuration; fallback to KMeans
                    self.logger.warning("DBSCAN: no viable configuration found; falling back to KMeans")
                    print("DBSCAN DEBUG: no viable configuration; fallback to KMeans")
                    fallback_clusters = min(max(2, len(features) // 15), 5)
                    clusterer = KMeans(n_clusters=fallback_clusters, random_state=42, n_init="auto")
                    cluster_labels = clusterer.fit_predict(features)
                    algo_metadata["fallback_to_kmeans"] = True
                    algo_metadata["fallback_reason"] = "DBSCAN produced no valid multi-cluster results"
                    algo_metadata["n_clusters"] = fallback_clusters
                    self.logger.info("DBSCAN->KMeans fallback: k=%d", fallback_clusters)
                    print(f"DBSCAN DEBUG: Fallback to KMeans with k={fallback_clusters}")
                else:
                    # Use best DBSCAN labels
                    cluster_labels = best_labels
                    # Post-check: if excessive noise or too few clusters, fallback to KMeans
                    non_noise_labels = set([l for l in set(cluster_labels) if l != -1])
                    noise_ratio = (cluster_labels == -1).sum() / len(cluster_labels)
                    if len(non_noise_labels) <= 1 or noise_ratio > 0.5:
                        self.logger.warning(
                            "DBSCAN: best config still weak (k=%d noise=%.1f%%). Fallback to KMeans. eps=%.4f(p%d) ms=%d",
                            len(non_noise_labels), noise_ratio * 100.0, best_eps, best_pct or -1, best_ms or -1
                        )
                        fallback_clusters = min(max(2, len(features) // 15), 5)
                        clusterer = KMeans(n_clusters=fallback_clusters, random_state=42, n_init="auto")
                        cluster_labels = clusterer.fit_predict(features)
                        algo_metadata["fallback_to_kmeans"] = True
                        algo_metadata["fallback_reason"] = (
                            f"Insufficient clusters ({len(non_noise_labels)}) or too much noise ({noise_ratio:.1%})"
                        )
                        algo_metadata["n_clusters"] = fallback_clusters
                        self.logger.info("DBSCAN->KMeans fallback: k=%d", fallback_clusters)
                        print(f"DBSCAN DEBUG: Fallback to KMeans with k={fallback_clusters}")
                    else:
                        # If DBSCAN marked noise (-1), softly assign them to nearest cluster
                        if (cluster_labels == -1).any():
                            self.logger.info("DBSCAN: assigning %d noise points to nearest clusters", int((cluster_labels == -1).sum()))
                            print(f"DBSCAN DEBUG: assigning {(cluster_labels == -1).sum()} noise points")
                            non_noise_mask = cluster_labels >= 0
                            unique = sorted(list(set(cluster_labels[non_noise_mask])))
                            if unique:
                                centroids = np.vstack([
                                    features[cluster_labels == lbl].mean(axis=0) for lbl in unique
                                ])
                                noise_idx = np.where(cluster_labels == -1)[0]
                                if len(noise_idx) > 0:
                                    pts = features[noise_idx]
                                    x2 = np.sum(pts ** 2, axis=1, keepdims=True)
                                    c2 = np.sum(centroids ** 2, axis=1, keepdims=True).T
                                    xc = pts @ centroids.T
                                    d2 = x2 + c2 - 2 * xc
                                    nearest = d2.argmin(axis=1)
                                    for i, idx in enumerate(noise_idx):
                                        cluster_labels[idx] = unique[nearest[i]]

                        # Convert to 1-based indices for UI consistency (DBSCAN only)
                        cluster_labels = cluster_labels + 1
                        algo_metadata["eps"] = float(best_eps) if best_eps is not None else None
                        algo_metadata["min_samples"] = int(best_ms) if best_ms is not None else None
                        algo_metadata["eps_percentile"] = int(best_pct) if best_pct is not None else None
                        # Exclude noise (-1) which is now 0 after +1; count only positive labels
                        n_unique = len(set([lbl for lbl in cluster_labels if lbl > 0]))
                        algo_metadata["n_clusters"] = n_unique
                        self.logger.info("DBSCAN: produced %d clusters (excl. noise)", n_unique)
                        print(f"DBSCAN DEBUG: produced {n_unique} clusters (1-based labels)")

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
                affinity="rbf",
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

    def _deduplicate_labels(self, clusters: List[ClusterData]) -> None:
        """
        Ensure cluster labels are unique by appending a short descriptor when duplicates occur.

        Args:
            clusters: list of ClusterData with initial labels
        """
        label_counts: Dict[str, int] = {}
        for c in clusters:
            base = c.label or "Cluster"
            label_counts[base] = label_counts.get(base, 0) + 1

        if all(cnt == 1 for cnt in label_counts.values()):
            return

        # Build compact descriptors from a couple of salient features
        def descriptor(c: ClusterData) -> str:
            e = c.center_features.get("energy", 0.5)
            d = c.center_features.get("danceability", 0.5)
            v = c.center_features.get("valence", 0.5)
            # Map to coarse buckets 1-5
            bucket = lambda x: int(min(5, max(1, round(x * 5))))
            return f"E{bucket(e)}-D{bucket(d)}-V{bucket(v)}"

        seen: Dict[str, int] = {}
        for c in clusters:
            base = c.label or "Cluster"
            if label_counts[base] > 1:
                seen[base] = seen.get(base, 0) + 1
                c.label = f"{base} ({descriptor(c)})"
    
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
        
        # Enhanced feature preprocessing - now returns raw features for labeling
        features, raw_features, preprocessing_info = self._preprocess_features(tracks)
        
        # Apply clustering algorithm with automatic parameter selection
        cluster_labels, algo_metadata = self._apply_clustering_algorithm(
            features, method, n_clusters
        )
        
        # Calculate clustering quality metrics
        unique_labels = set(cluster_labels)
        n_clusters_found = len(unique_labels)
        n_samples = len(features)
        if n_clusters_found > 1 and n_clusters_found < n_samples:
            try:
                silhouette_avg = silhouette_score(features, cluster_labels)
            except ValueError as e:
                # Robustness: if sklearn rejects the label configuration, default to 0
                self.logger.warning(f"Silhouette skipped: {e}")
                silhouette_avg = 0.0
            try:
                calinski_score = calinski_harabasz_score(features, cluster_labels)
            except ValueError as e:
                self.logger.warning(f"Calinski-Harabasz skipped: {e}")
                calinski_score = 0.0
        else:
            if n_clusters_found >= n_samples:
                self.logger.info(
                    f"Skipping cluster quality metrics: n_clusters={n_clusters_found} >= n_samples={n_samples}"
                )
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
            cluster_raw_features = raw_features[track_indices]  # Use raw features for labeling
            
            # Calculate center features using raw features for interpretable labeling
            center_features_raw = np.mean(cluster_raw_features, axis=0)
            
            # Convert to interpretable feature dictionary using raw feature scales
            center_dict = {}
            for i, feature in enumerate(self.AUDIO_FEATURES):
                # Use raw feature values which are already on 0-1 scale
                center_dict[feature] = float(center_features_raw[i])
            
            # Generate interpretable label using raw features
            cluster_label = self._label_cluster(center_dict)
            
            # Log cluster characteristics for debugging
            energy = center_dict.get("energy", 0.5)
            valence = center_dict.get("valence", 0.5)
            danceability = center_dict.get("danceability", 0.5)
            self.logger.info(f"Cluster {cluster_id} ({cluster_label}): "
                           f"Energy={energy:.3f}, Valence={valence:.3f}, Dance={danceability:.3f}")
            
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

        # Ensure labels are unique to avoid repeated names when K grows
        self._deduplicate_labels(clusters)

        # Create comprehensive analysis metadata
        analysis_metadata = {
            "algorithm": algo_metadata,
            "preprocessing": preprocessing_info,
            "quality_metrics": {
                "silhouette_score": float(silhouette_avg),
                "calinski_harabasz_score": float(calinski_score),
                "n_clusters": n_clusters_found,
                "noise_points": int(sum(1 for label in cluster_labels if label == -1)),
            },
            "feature_importance": dict(self.FEATURE_WEIGHTS),
            "data_quality": quality_report,
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
        
        features, _, _ = self._preprocess_features(tracks)
        
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

    def enhanced_cluster_analysis(
        self,
        tracks: List[Track],
        algorithm: str = "kmeans",
        num_clusters: Optional[int] = None,
        quality_report: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enhanced clustering analysis with automatic optimization and interpretable labels.
        
        Args:
            tracks: List of Track objects to cluster
            algorithm: Clustering algorithm to use
            num_clusters: Number of clusters (auto-detected if None)
            quality_report: Optional data quality report
            
        Returns:
            Dict containing clusters, scores, and metadata
        """
        if len(tracks) < 2:
            raise ValueError("Need at least 2 tracks for clustering")

        # Run clustering analysis
        clusters, silhouette_score, analysis_metadata = self.cluster_tracks(
            tracks, method=algorithm, n_clusters=num_clusters, quality_report=quality_report
        )

        # Extract cluster labels for interpretability
        cluster_labels = {}
        for cluster in clusters:
            cluster_labels[f"cluster_{cluster.cluster_id}"] = cluster.label

        return {
            "clusters": clusters,
            "silhouette_score": silhouette_score,
            "optimal_clusters": analysis_metadata.get("optimal_clusters"),
            "cluster_labels": cluster_labels,
            "analysis_metadata": analysis_metadata
        }

    def get_cluster_recommendations(
        self,
        tracks: List[Track],
        quality_report: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate cluster-based recommendations for improving playlist flow.
        
        Args:
            tracks: List of Track objects
            quality_report: Optional data quality report
            
        Returns:
            List of recommendation dictionaries
        """
        if len(tracks) < 3:
            return []

        # Run clustering to identify patterns
        clusters, silhouette_score, metadata = self.cluster_tracks(tracks)
        
        recommendations = []
        
        # Analyze cluster distribution
        cluster_sizes = [len(cluster.tracks) for cluster in clusters]
        avg_cluster_size = np.mean(cluster_sizes)
        
        # Recommend cluster balancing if needed
        for i, cluster in enumerate(clusters):
            if len(cluster.tracks) < avg_cluster_size * 0.5:
                recommendations.append({
                    "type": "cluster_balance",
                    "priority": "medium",
                    "description": f"Cluster {i+1} ({cluster.label}) has only {len(cluster.tracks)} tracks. Consider adding similar tracks.",
                    "cluster_id": cluster.cluster_id,
                    "cluster_label": cluster.label,
                    "suggested_action": "add_similar_tracks"
                })
            elif len(cluster.tracks) > avg_cluster_size * 2:
                recommendations.append({
                    "type": "cluster_balance",
                    "priority": "low",
                    "description": f"Cluster {i+1} ({cluster.label}) is very large with {len(cluster.tracks)} tracks. Consider splitting or diversifying.",
                    "cluster_id": cluster.cluster_id,
                    "cluster_label": cluster.label,
                    "suggested_action": "diversify_cluster"
                })

        # Recommend flow improvements based on clustering
        if silhouette_score < 0.3:
            recommendations.append({
                "type": "clustering_quality",
                "priority": "high",
                "description": f"Low clustering quality (score: {silhouette_score:.2f}). Playlist may lack coherent themes.",
                "suggested_action": "improve_coherence",
                "current_score": silhouette_score
            })

        return recommendations

    def get_cluster_statistics(
        self,
        tracks: List[Track],
        algorithm: str = "kmeans",
        quality_report: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed cluster statistics and insights.
        
        Args:
            tracks: List of Track objects
            algorithm: Clustering algorithm used
            quality_report: Optional data quality report
            
        Returns:
            Dictionary containing detailed statistics
        """
        if len(tracks) < 2:
            return {"error": "Need at least 2 tracks for statistics"}

        # Run clustering analysis
        clusters, silhouette_score, metadata = self.cluster_tracks(
            tracks, method=algorithm, quality_report=quality_report
        )

        # Calculate comprehensive statistics
        stats = {
            "algorithm": algorithm,
            "total_tracks": len(tracks),
            "num_clusters": len(clusters),
            "silhouette_score": silhouette_score,
            "cluster_distribution": [],
            "feature_analysis": {},
            "quality_metrics": {
                "silhouette_score": silhouette_score,
                "calinski_harabasz_score": metadata.get("calinski_score", 0)
            }
        }

        # Cluster distribution analysis
        for cluster in clusters:
            cluster_stats = {
                "cluster_id": cluster.cluster_id,
                "label": cluster.label,
                "track_count": len(cluster.tracks),
                "percentage": (len(cluster.tracks) / len(tracks)) * 100,
                "avg_features": {}
            }
            
            # Calculate average features for this cluster
            if cluster.tracks:
                for feature in self.AUDIO_FEATURES:
                    values = [getattr(track, feature, 0) or 0 for track in cluster.tracks]
                    cluster_stats["avg_features"][feature] = np.mean(values) if values else 0
                    
            stats["cluster_distribution"].append(cluster_stats)

        # Overall feature analysis
        for feature in self.AUDIO_FEATURES:
            values = [getattr(track, feature, 0) or 0 for track in tracks]
            if values:
                stats["feature_analysis"][feature] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values)
                }

        return stats
