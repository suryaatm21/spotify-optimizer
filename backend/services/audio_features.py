from typing import List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from backend.models import Track
from backend.services.reccobeats import ReccoBeatsService


class AudioFeaturesService:
    """
    Service for managing audio features data quality. It uses ReccoBeats as the
    primary source for audio features and provides robust methods for imputing
    any remaining missing data to ensure high-quality inputs for clustering.
    """

    AUDIO_FEATURES = [
        "danceability", "energy", "key", "loudness", "mode",
        "speechiness", "acousticness", "instrumentalness",
        "liveness", "valence", "tempo"
    ]

    FEATURE_DEFAULTS = {
        "danceability": 0.5, "energy": 0.5, "key": 0, "loudness": -5.0, "mode": 0,
        "speechiness": 0.1, "acousticness": 0.5, "instrumentalness": 0.0,
        "liveness": 0.2, "valence": 0.5, "tempo": 120.0
    }

    def __init__(self, reccobeats_service: ReccoBeatsService):
        """Initializes the service with its dependencies and ML models."""
        self.reccobeats_service = reccobeats_service
        self.imputer = KNNImputer(n_neighbors=5, weights="distance")
        self.scaler = StandardScaler()

    async def fetch_and_impute_features(self, tracks: List[Track], db: Session) -> List[Track]:
        """
        Orchestrates fetching missing audio features from ReccoBeats and imputing any
        remaining gaps to ensure data completeness.

        Args:
            tracks: A list of Track objects to process.
            db: The database session for committing changes.

        Returns:
            The list of tracks with audio features updated.
        """
        if not tracks:
            return []

        tracks_to_process = [
            t for t in tracks
            if t.features_imputed or any(getattr(t, f) is None for f in self.AUDIO_FEATURES)
        ]
        if not tracks_to_process:
            print("✅ All tracks have complete audio features.")
            return tracks

        await self._fetch_from_reccobeats(tracks_to_process)
        self.impute_missing_features(tracks_to_process)

        # The caller is responsible for the database session commit.
        return tracks

    async def _fetch_from_reccobeats(self, tracks: List[Track]):
        """Fetches features from ReccoBeats and updates track objects in-place."""
        track_ids_to_fetch = [t.spotify_track_id for t in tracks if t.spotify_track_id]
        if not track_ids_to_fetch:
            return

        print(f"🎵 Fetching features for {len(track_ids_to_fetch)} tracks from ReccoBeats.")
        try:
            features_map = await self.reccobeats_service.get_multiple_tracks_audio_features(track_ids_to_fetch)
        except Exception as e:
            print(f"❌ ReccoBeats fetch failed: {e}")
            return

        if not features_map:
            print("⚠️ ReccoBeats returned no features.")
            return

        print(f"✅ Fetched {len(features_map)} feature sets from ReccoBeats.")
        track_map = {(t.spotify_track_id or "").split(":")[-1]: t for t in tracks}

        updated_count = 0
        for spotify_id, features in features_map.items():
            track = track_map.get(spotify_id)
            if not track or not features:
                continue

            mapped_features = self.reccobeats_service.map_features_to_spotify_format(features)
            updated = False
            for name, value in mapped_features.items():
                # Update if field exists and either is None OR track is marked as imputed
                if hasattr(track, name) and (getattr(track, name) is None or track.features_imputed):
                    setattr(track, name, value)
                    updated = True
            if updated:
                track.features_imputed = False
                updated_count += 1
        print(f"Updated {updated_count} tracks with new features from ReccoBeats.")

    def impute_missing_features(self, tracks: List[Track]):
        """Intelligently imputes missing features using KNN and statistical fallbacks."""
        return self._impute_missing_features(tracks)

    def _impute_missing_features(self, tracks: List[Track]):
        """Intelligently imputes missing features using KNN and statistical fallbacks."""
        if not tracks:
            return

        df = pd.DataFrame([t.__dict__ for t in tracks])
        features_df = df[self.AUDIO_FEATURES].copy()  # Create a defensive copy to avoid pandas warnings

        if features_df.isnull().all().all():
            self._fill_with_defaults(tracks)
            return

        # Pre-impute columns with too few values for KNN to work reliably
        for feature in self.AUDIO_FEATURES:
            if features_df[feature].notna().sum() < 2:
                fallback_val = self.FEATURE_DEFAULTS[feature]
                features_df.loc[features_df[feature].isna(), feature] = fallback_val

        if features_df.isnull().values.any():
            scaled_features = self.scaler.fit_transform(features_df)
            imputed_scaled = self.imputer.fit_transform(scaled_features)
            imputed_features = self.scaler.inverse_transform(imputed_scaled)
            imputed_df = pd.DataFrame(imputed_features, columns=self.AUDIO_FEATURES, index=features_df.index)
        else:
            imputed_df = features_df

        # Update track objects safely to avoid SettingWithCopyWarning
        for i, track in enumerate(tracks):
            for feature in self.AUDIO_FEATURES:
                setattr(track, feature, float(imputed_df.iloc[i][feature]))
                track.features_imputed = True

    def _fill_with_defaults(self, tracks: List[Track]):
        """Fills all missing audio features with default values."""
        print("⚠️ All feature data is missing. Filling with defaults.")
        for track in tracks:
            for feature in self.AUDIO_FEATURES:
                if getattr(track, feature) is None:
                    setattr(track, feature, self.FEATURE_DEFAULTS[feature])
                    track.features_imputed = True  # Mark as imputed since these are defaults

    def _clamp_feature_value(self, feature: str, value: float) -> float:
        """Ensures imputed feature values are within valid ranges."""
        if feature in ["key", "mode"]:
            return round(value)
        if feature == "tempo":
            return max(50.0, min(250.0, value))
        return max(0.0, min(1.0, value))

    def analyze_data_quality(self, tracks: List[Track]) -> Dict[str, Any]:
        """Analyzes the quality and completeness of audio feature data."""
        total_tracks = len(tracks)
        if not total_tracks: return {"error": "No tracks provided"}

        feature_quality = {}
        overall_missing = 0
        for feature in self.AUDIO_FEATURES:
            missing = sum(1 for t in tracks if getattr(t, feature) is None)
            feature_quality[feature] = {
                "present": total_tracks - missing,
                "missing": missing,
                "completeness": (total_tracks - missing) / total_tracks
            }
            overall_missing += missing

        total_values = total_tracks * len(self.AUDIO_FEATURES)
        completeness = (total_values - overall_missing) / total_values if total_values > 0 else 0

        return {
            "total_tracks": total_tracks,
            "overall_completeness": completeness,
            "feature_quality": feature_quality,
            "recommendation": self._get_quality_recommendation(completeness)
        }

    def _get_quality_recommendation(self, completeness: float) -> str:
        """Returns a human-readable recommendation based on data quality."""
        if completeness >= 0.9: return "Excellent data quality - clustering will be highly reliable."
        if completeness >= 0.7: return "Good data quality - clustering will be reliable."
        if completeness >= 0.5: return "Moderate data quality - results may be skewed."
        return "Poor data quality - recommend fetching more data before analysis."
