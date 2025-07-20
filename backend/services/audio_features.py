"""
Audio features service for handling missing data and improving clustering quality.
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
import statistics
import httpx
from sqlalchemy.orm import Session

from backend.models import Track
from backend.dependencies import get_spotify_client_credentials


class AudioFeaturesService:
    """
    Service for managing audio features data quality and handling missing values.
    """
    
    AUDIO_FEATURES = [
        "danceability", "energy", "speechiness", "acousticness",
        "instrumentalness", "liveness", "valence", "tempo"
    ]
    
    # Typical ranges and defaults for audio features
    FEATURE_DEFAULTS = {
        "danceability": 0.5,
        "energy": 0.5,
        "speechiness": 0.1,  # Most songs have low speechiness
        "acousticness": 0.3,
        "instrumentalness": 0.2,  # Most songs have vocals
        "liveness": 0.15,  # Most songs are studio recordings
        "valence": 0.5,
        "tempo": 120.0  # Common tempo
    }
    
    def __init__(self):
        """Initialize the audio features service."""
        self.imputer = KNNImputer(n_neighbors=5, weights="distance")
        self.scaler = StandardScaler()
    
    async def fetch_missing_audio_features(
        self, 
        tracks: List[Track], 
        db: Session
    ) -> List[Track]:
        """
        Fetch missing audio features from Spotify API and update database.
        
        Args:
            tracks: List of Track objects
            db: Database session
            
        Returns:
            List[Track]: Updated tracks with fetched audio features
        """
        # Find tracks with missing audio features
        tracks_missing_features = []
        track_ids_to_fetch = []
        
        for track in tracks:
            missing_count = sum(1 for feature in self.AUDIO_FEATURES 
                              if getattr(track, feature) is None)
            
            if missing_count > 0:
                tracks_missing_features.append(track)
                track_ids_to_fetch.append(track.spotify_track_id)
        
        if not track_ids_to_fetch:
            return tracks
        
        print(f"Fetching missing audio features for {len(track_ids_to_fetch)} tracks...")
        
        # Get Spotify client credentials
        client_credentials = await get_spotify_client_credentials()
        headers = {"Authorization": f"Bearer {client_credentials}"}
        
        features_map = {}
        
        async with httpx.AsyncClient() as client:
            # Fetch in chunks of 100 (Spotify API limit)
            CHUNK_SIZE = 100
            for i in range(0, len(track_ids_to_fetch), CHUNK_SIZE):
                ids_chunk = track_ids_to_fetch[i:i + CHUNK_SIZE]
                
                try:
                    response = await client.get(
                        "https://api.spotify.com/v1/audio-features",
                        headers=headers,
                        params={"ids": ",".join(ids_chunk)},
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        for feature_data in data.get("audio_features", []):
                            if feature_data and feature_data.get("id"):
                                features_map[feature_data["id"]] = feature_data
                    else:
                        print(f"Failed to fetch audio features chunk: {response.status_code}")
                        
                except Exception as e:
                    print(f"Error fetching audio features: {e}")
                    continue
        
        # Update tracks with fetched features
        updated_tracks = []
        for track in tracks_missing_features:
            features = features_map.get(track.spotify_track_id, {})
            updated = False
            
            for feature in self.AUDIO_FEATURES:
                if getattr(track, feature) is None and features.get(feature) is not None:
                    setattr(track, feature, features[feature])
                    updated = True
            
            if updated:
                updated_tracks.append(track)
        
        # Commit updates to database
        if updated_tracks:
            try:
                db.commit()
                for track in updated_tracks:
                    db.refresh(track)
                print(f"Updated {len(updated_tracks)} tracks with audio features")
            except Exception as e:
                print(f"Error updating tracks in database: {e}")
                db.rollback()
        
        return tracks
    
    def impute_missing_features(self, tracks: List[Track]) -> List[Track]:
        """
        Intelligently impute missing audio features using KNN and statistical methods.
        
        Args:
            tracks: List of Track objects
            
        Returns:
            List[Track]: Tracks with imputed features
        """
        if len(tracks) < 3:
            # Not enough data for KNN, use defaults
            return self._fill_with_defaults(tracks)
        
        # Create feature matrix
        feature_matrix = []
        track_indices_with_missing = []
        
        for i, track in enumerate(tracks):
            row = []
            has_missing = False
            
            for feature in self.AUDIO_FEATURES:
                value = getattr(track, feature)
                if value is None:
                    row.append(np.nan)
                    has_missing = True
                else:
                    # Normalize tempo to 0-1 range for consistent scaling
                    if feature == "tempo":
                        value = min(max((value - 50) / 150, 0), 1)
                    row.append(value)
            
            feature_matrix.append(row)
            if has_missing:
                track_indices_with_missing.append(i)
        
        if not track_indices_with_missing:
            return tracks  # No missing features
        
        feature_matrix = np.array(feature_matrix)
        
        # Check if we have enough complete cases for KNN
        complete_cases = ~np.isnan(feature_matrix).any(axis=1)
        complete_count = np.sum(complete_cases)
        
        if complete_count >= 3:
            # Use KNN imputation
            try:
                # Adjust number of neighbors based on available data
                n_neighbors = min(5, complete_count)
                self.imputer.set_params(n_neighbors=n_neighbors)
                
                imputed_matrix = self.imputer.fit_transform(feature_matrix)
                
                # Update tracks with imputed values
                for i in track_indices_with_missing:
                    for j, feature in enumerate(self.AUDIO_FEATURES):
                        if getattr(tracks[i], feature) is None:
                            value = float(imputed_matrix[i][j])
                            
                            # Denormalize tempo
                            if feature == "tempo":
                                value = (value * 150) + 50
                            
                            # Ensure values are within valid ranges
                            value = self._clamp_feature_value(feature, value)
                            setattr(tracks[i], feature, value)
                
                print(f"Imputed missing features for {len(track_indices_with_missing)} tracks using KNN")
                
            except Exception as e:
                print(f"KNN imputation failed: {e}, falling back to statistical imputation")
                return self._statistical_imputation(tracks)
        else:
            # Not enough complete cases, use statistical imputation
            return self._statistical_imputation(tracks)
        
        return tracks
    
    def _statistical_imputation(self, tracks: List[Track]) -> List[Track]:
        """
        Fill missing values using statistical measures from available data.
        
        Args:
            tracks: List of Track objects
            
        Returns:
            List[Track]: Tracks with statistically imputed features
        """
        # Calculate feature statistics from available data
        feature_stats = {}
        
        for feature in self.AUDIO_FEATURES:
            values = []
            for track in tracks:
                value = getattr(track, feature)
                if value is not None:
                    values.append(value)
            
            if values:
                # Use median for robustness against outliers
                feature_stats[feature] = statistics.median(values)
            else:
                # Use default if no values available
                feature_stats[feature] = self.FEATURE_DEFAULTS[feature]
        
        # Fill missing values
        updated_count = 0
        for track in tracks:
            for feature in self.AUDIO_FEATURES:
                if getattr(track, feature) is None:
                    setattr(track, feature, feature_stats[feature])
                    updated_count += 1
        
        if updated_count > 0:
            print(f"Filled {updated_count} missing values using statistical imputation")
        
        return tracks
    
    def _fill_with_defaults(self, tracks: List[Track]) -> List[Track]:
        """
        Fill missing values with sensible defaults.
        
        Args:
            tracks: List of Track objects
            
        Returns:
            List[Track]: Tracks with default values
        """
        updated_count = 0
        for track in tracks:
            for feature in self.AUDIO_FEATURES:
                if getattr(track, feature) is None:
                    setattr(track, feature, self.FEATURE_DEFAULTS[feature])
                    updated_count += 1
        
        if updated_count > 0:
            print(f"Filled {updated_count} missing values with defaults")
        
        return tracks
    
    def _clamp_feature_value(self, feature: str, value: float) -> float:
        """
        Ensure feature values are within valid ranges.
        
        Args:
            feature: Feature name
            value: Feature value
            
        Returns:
            float: Clamped value
        """
        if feature == "tempo":
            return max(50.0, min(200.0, value))
        elif feature in ["key", "mode"]:
            return value  # These are integers, handled separately
        else:
            # Most features are 0-1 range
            return max(0.0, min(1.0, value))
    
    def analyze_data_quality(self, tracks: List[Track]) -> Dict[str, Any]:
        """
        Analyze the quality of audio features data.
        
        Args:
            tracks: List of Track objects
            
        Returns:
            Dict[str, Any]: Data quality report
        """
        total_tracks = len(tracks)
        if total_tracks == 0:
            return {"error": "No tracks provided"}
        
        feature_quality = {}
        overall_missing = 0
        
        for feature in self.AUDIO_FEATURES:
            missing_count = sum(1 for track in tracks 
                              if getattr(track, feature) is None)
            present_count = total_tracks - missing_count
            
            feature_quality[feature] = {
                "present": present_count,
                "missing": missing_count,
                "completeness": present_count / total_tracks
            }
            
            overall_missing += missing_count
        
        total_possible_values = total_tracks * len(self.AUDIO_FEATURES)
        overall_completeness = (total_possible_values - overall_missing) / total_possible_values
        
        return {
            "total_tracks": total_tracks,
            "overall_completeness": overall_completeness,
            "feature_quality": feature_quality,
            "recommendation": self._get_quality_recommendation(overall_completeness)
        }
    
    def _get_quality_recommendation(self, completeness: float) -> str:
        """
        Get recommendation based on data completeness.
        
        Args:
            completeness: Overall data completeness ratio
            
        Returns:
            str: Recommendation message
        """
        if completeness >= 0.9:
            return "Excellent data quality - clustering analysis will be highly reliable"
        elif completeness >= 0.7:
            return "Good data quality - clustering analysis will be reliable with minor imputation"
        elif completeness >= 0.5:
            return "Moderate data quality - clustering analysis will be moderately reliable after imputation"
        else:
            return "Poor data quality - recommend fetching more complete data for reliable analysis"
