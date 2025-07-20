"""
Tests for the audio features service.
"""
import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from backend.services.audio_features import AudioFeaturesService
from backend.models import Track


class TestAudioFeaturesService:
    """Test cases for AudioFeaturesService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = AudioFeaturesService()
    
    def test_analyze_data_quality_complete_data(self):
        """Test data quality analysis with complete data."""
        # Create tracks with complete audio features
        tracks = [
            Mock(
                danceability=0.8, energy=0.7, speechiness=0.1,
                acousticness=0.2, instrumentalness=0.0, liveness=0.1,
                valence=0.9, tempo=120.0
            ),
            Mock(
                danceability=0.6, energy=0.5, speechiness=0.05,
                acousticness=0.4, instrumentalness=0.0, liveness=0.15,
                valence=0.7, tempo=110.0
            )
        ]
        
        result = self.service.analyze_data_quality(tracks)
        
        assert result["total_tracks"] == 2
        assert result["overall_completeness"] == 1.0
        assert "Excellent data quality" in result["recommendation"]
    
    def test_analyze_data_quality_missing_data(self):
        """Test data quality analysis with missing data."""
        # Create tracks with some missing audio features
        tracks = [
            Mock(
                danceability=0.8, energy=None, speechiness=0.1,
                acousticness=None, instrumentalness=0.0, liveness=0.1,
                valence=0.9, tempo=120.0
            ),
            Mock(
                danceability=None, energy=0.5, speechiness=0.05,
                acousticness=0.4, instrumentalness=None, liveness=0.15,
                valence=None, tempo=110.0
            )
        ]
        
        result = self.service.analyze_data_quality(tracks)
        
        assert result["total_tracks"] == 2
        assert result["overall_completeness"] < 1.0
        assert result["overall_completeness"] > 0.0
    
    def test_impute_missing_features_knn(self):
        """Test KNN imputation with sufficient complete data."""
        # Create tracks with mixed complete and incomplete data
        tracks = [
            Track(
                id=1, danceability=0.8, energy=0.7, speechiness=0.1,
                acousticness=0.2, instrumentalness=0.0, liveness=0.1,
                valence=0.9, tempo=120.0
            ),
            Track(
                id=2, danceability=0.6, energy=0.5, speechiness=0.05,
                acousticness=0.4, instrumentalness=0.0, liveness=0.15,
                valence=0.7, tempo=110.0
            ),
            Track(
                id=3, danceability=0.7, energy=0.6, speechiness=0.08,
                acousticness=0.3, instrumentalness=0.0, liveness=0.12,
                valence=0.8, tempo=115.0
            ),
            Track(
                id=4, danceability=None, energy=None, speechiness=0.1,
                acousticness=0.2, instrumentalness=0.0, liveness=0.1,
                valence=0.9, tempo=120.0
            )
        ]
        
        result_tracks = self.service.impute_missing_features(tracks)
        
        # Check that missing values were filled
        assert result_tracks[3].danceability is not None
        assert result_tracks[3].energy is not None
        assert 0.0 <= result_tracks[3].danceability <= 1.0
        assert 0.0 <= result_tracks[3].energy <= 1.0
    
    def test_impute_missing_features_defaults(self):
        """Test fallback to defaults with insufficient data."""
        # Create tracks with all missing data
        tracks = [
            Track(
                id=1, danceability=None, energy=None, speechiness=None,
                acousticness=None, instrumentalness=None, liveness=None,
                valence=None, tempo=None
            )
        ]
        
        result_tracks = self.service.impute_missing_features(tracks)
        
        # Check that default values were used
        assert result_tracks[0].danceability == self.service.FEATURE_DEFAULTS["danceability"]
        assert result_tracks[0].energy == self.service.FEATURE_DEFAULTS["energy"]
        assert result_tracks[0].tempo == self.service.FEATURE_DEFAULTS["tempo"]
    
    @pytest.mark.asyncio
    async def test_fetch_missing_audio_features_success(self):
        """Test successful fetching of missing audio features."""
        # Mock tracks with missing features
        tracks = [
            Track(
                id=1, spotify_track_id="track1",
                danceability=None, energy=None, speechiness=0.1,
                acousticness=0.2, instrumentalness=0.0, liveness=0.1,
                valence=0.9, tempo=120.0
            )
        ]
        
        # Mock database session
        mock_db = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock Spotify API response
        mock_features_data = {
            "audio_features": [{
                "id": "track1",
                "danceability": 0.8,
                "energy": 0.7,
                "speechiness": 0.1,
                "acousticness": 0.2,
                "instrumentalness": 0.0,
                "liveness": 0.1,
                "valence": 0.9,
                "tempo": 120.0
            }]
        }
        
        with patch("backend.services.audio_features.get_spotify_client_credentials", new_callable=AsyncMock) as mock_creds, \
             patch("httpx.AsyncClient") as mock_client:
            
            mock_creds.return_value = "mock_token"
            
            # Mock the HTTP client response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_features_data
            
            mock_client_instance = Mock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Call the method
            result_tracks = await self.service.fetch_missing_audio_features(tracks, mock_db)
            
            # Check that missing features were filled
            assert result_tracks[0].danceability == 0.8
            assert result_tracks[0].energy == 0.7
    
    def test_clamp_feature_value(self):
        """Test feature value clamping."""
        # Test tempo clamping
        assert self.service._clamp_feature_value("tempo", 300.0) == 200.0
        assert self.service._clamp_feature_value("tempo", 30.0) == 50.0
        assert self.service._clamp_feature_value("tempo", 120.0) == 120.0
        
        # Test 0-1 feature clamping
        assert self.service._clamp_feature_value("danceability", 1.5) == 1.0
        assert self.service._clamp_feature_value("energy", -0.5) == 0.0
        assert self.service._clamp_feature_value("valence", 0.5) == 0.5
