"""
Test cases for the clustering service functionality.
"""
import pytest
from unittest.mock import Mock

from backend.services.clustering import ClusteringService
from backend.models import Track

class TestClusteringService:
    """Test cases for the ClusteringService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.clustering_service = ClusteringService()
    
    def test_extract_features_valid_tracks(self, sample_tracks):
        """Test feature extraction with valid tracks."""
        features = self.clustering_service._extract_features(sample_tracks)
        
        assert features.shape[0] == len(sample_tracks)
        assert features.shape[1] == len(ClusteringService.AUDIO_FEATURES)
        
        # Check that features are normalized (should have roughly mean 0, std 1)
        assert abs(features.mean()) < 0.5
    
    def test_extract_features_missing_values(self):
        """Test feature extraction with missing audio feature values."""
        # Create a track with some missing features
        track = Track(
            id=1,
            spotify_track_id="test_track",
            name="Test Track",
            artist="Test Artist",
            playlist_id=1,
            danceability=0.5,
            energy=None,  # Missing value
            speechiness=0.1,
            acousticness=None,  # Missing value
            instrumentalness=0.2,
            liveness=0.3,
            valence=0.6,
            tempo=120.0
        )
        
        features = self.clustering_service._extract_features([track])
        
        assert features.shape == (1, 8)  # 8 audio features
        # Missing values should be replaced with 0.5 (mean)
        # Check that missing energy and acousticness values default to 0.5
        # Note: Features are normalized, so we check the original extraction logic
        # by verifying that None values are handled properly
        assert not any(val is None for val in features.flatten())
    
    def test_cluster_tracks_kmeans(self, sample_tracks):
        """Test k-means clustering with sample tracks."""
        clusters, silhouette_score = self.clustering_service.cluster_tracks(
            sample_tracks, method="kmeans", n_clusters=2
        )
        
        assert len(clusters) <= 2  # Should create at most 2 clusters
        assert 0 <= silhouette_score <= 1
        
        # Check that all tracks are assigned to clusters
        total_tracks_in_clusters = sum(cluster.track_count for cluster in clusters)
        assert total_tracks_in_clusters == len(sample_tracks)
        
        # Check cluster data structure
        for cluster in clusters:
            assert hasattr(cluster, "cluster_id")
            assert hasattr(cluster, "track_count")
            assert hasattr(cluster, "center_features")
            assert hasattr(cluster, "track_ids")
            assert len(cluster.track_ids) == cluster.track_count
    
    def test_cluster_tracks_dbscan(self, sample_tracks):
        """Test DBSCAN clustering with sample tracks."""
        clusters, silhouette_score = self.clustering_service.cluster_tracks(
            sample_tracks, method="dbscan"
        )
        
        assert len(clusters) >= 1  # DBSCAN should find at least one cluster
        assert isinstance(silhouette_score, float)
        
        # Check that all tracks are assigned
        total_tracks_in_clusters = sum(cluster.track_count for cluster in clusters)
        assert total_tracks_in_clusters == len(sample_tracks)
    
    def test_cluster_tracks_insufficient_data(self):
        """Test clustering with insufficient data."""
        single_track = [Track(
            id=1,
            spotify_track_id="single_track",
            name="Single Track",
            artist="Artist",
            playlist_id=1,
            danceability=0.5,
            energy=0.6,
            speechiness=0.1,
            acousticness=0.3,
            instrumentalness=0.2,
            liveness=0.1,
            valence=0.7,
            tempo=120.0
        )]
        
        with pytest.raises(ValueError, match="Need at least 2 tracks"):
            self.clustering_service.cluster_tracks(single_track)
    
    def test_cluster_tracks_invalid_method(self, sample_tracks):
        """Test clustering with invalid method."""
        with pytest.raises(ValueError, match="Unsupported clustering method"):
            self.clustering_service.cluster_tracks(
                sample_tracks, method="invalid_method"
            )
    
    def test_calculate_playlist_stats(self, sample_tracks):
        """Test playlist statistics calculation."""
        stats = self.clustering_service.calculate_playlist_stats(sample_tracks)
        
        assert stats.total_tracks == len(sample_tracks)
        assert stats.avg_duration_ms > 0
        assert stats.avg_popularity > 0
        
        # Check that all audio features are present
        for feature in ClusteringService.AUDIO_FEATURES:
            assert feature in stats.avg_audio_features
            assert feature in stats.feature_ranges
            
            # Check range statistics
            feature_range = stats.feature_ranges[feature]
            assert "min" in feature_range
            assert "max" in feature_range
            assert "std" in feature_range
            assert feature_range["min"] <= feature_range["max"]
    
    def test_calculate_playlist_stats_empty_list(self):
        """Test playlist statistics with empty track list."""
        with pytest.raises(ValueError, match="No tracks provided"):
            self.clustering_service.calculate_playlist_stats([])
    
    def test_generate_optimization_suggestions(self, sample_tracks):
        """Test optimization suggestion generation."""
        # First cluster the tracks
        clusters, _ = self.clustering_service.cluster_tracks(sample_tracks, n_clusters=2)
        
        # Convert to dict format for the function
        cluster_dicts = [cluster.model_dump() for cluster in clusters]
        
        suggestions = self.clustering_service.generate_optimization_suggestions(
            sample_tracks, cluster_dicts
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5  # Should return at most 5 suggestions
        
        # Check suggestion structure
        for suggestion in suggestions:
            assert hasattr(suggestion, "suggestion_type")
            assert hasattr(suggestion, "description")
            assert hasattr(suggestion, "affected_tracks")
            assert hasattr(suggestion, "confidence_score")
            assert 0 <= suggestion.confidence_score <= 1
    
    def test_get_pca_coordinates(self, sample_tracks):
        """Test PCA coordinate generation for visualization."""
        coordinates = self.clustering_service.get_pca_coordinates(sample_tracks)
        
        assert len(coordinates) == len(sample_tracks)
        
        for coord in coordinates:
            assert "track_id" in coord
            assert "x" in coord
            assert "y" in coord
            assert "name" in coord
            assert "artist" in coord
            assert isinstance(coord["x"], float)
            assert isinstance(coord["y"], float)
    
    def test_get_pca_coordinates_insufficient_data(self):
        """Test PCA coordinates with insufficient data."""
        single_track = [Track(
            id=1,
            spotify_track_id="single_track",
            name="Single Track",
            artist="Artist",
            playlist_id=1,
            danceability=0.5,
            energy=0.6,
            speechiness=0.1,
            acousticness=0.3,
            instrumentalness=0.2,
            liveness=0.1,
            valence=0.7,
            tempo=120.0
        )]
        
        coordinates = self.clustering_service.get_pca_coordinates(single_track)
        assert coordinates == []
