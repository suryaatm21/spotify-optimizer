#!/usr/bin/env python3
"""
Debug script to analyze ReccoBeats coverage for real playlist data
and test the features_imputed flag logic.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from backend.services.reccobeats import ReccoBeatsService
from backend.services.audio_features import AudioFeaturesService
from backend.models import Track
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

async def analyze_playlist_coverage():
    """Analyze ReccoBeats coverage for tracks in database."""
    
    # Connect to database
    engine = create_engine("sqlite:///db/spotify.db")
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Get sample tracks from database
    tracks = db.query(Track).limit(20).all()  # Test with first 20 tracks
    
    if not tracks:
        print("❌ No tracks found in database. Run /tracks endpoint first.")
        return
    
    print(f"🧪 Testing ReccoBeats coverage for {len(tracks)} tracks from database")
    
    track_ids = [track.spotify_track_id for track in tracks if track.spotify_track_id]
    imputed_tracks = [track for track in tracks if track.features_imputed]
    
    print(f"Track IDs to test: {len(track_ids)}")
    print(f"Currently imputed tracks: {len(imputed_tracks)}")
    
    # Test ReccoBeats coverage
    service = ReccoBeatsService()
    
    print("\n" + "="*60)
    print("TESTING RECCOBEATS COVERAGE")
    print("="*60)
    
    features_result = await service.get_multiple_tracks_audio_features(track_ids)
    found_count = len(features_result)
    coverage_rate = found_count / len(track_ids) * 100 if track_ids else 0
    
    print(f"✅ ReccoBeats found features for {found_count}/{len(track_ids)} tracks")
    print(f"📊 Coverage rate: {coverage_rate:.1f}%")
    
    # Test the imputation logic
    print("\n" + "="*60)
    print("TESTING AUDIO FEATURES SERVICE LOGIC")
    print("="*60)
    
    audio_service = AudioFeaturesService(service)
    
    # Test with tracks that need features
    tracks_needing_features = [
        track for track in tracks 
        if track.features_imputed or any(getattr(track, f) is None for f in audio_service.AUDIO_FEATURES)
    ]
    
    print(f"Tracks needing features: {len(tracks_needing_features)}")
    
    if tracks_needing_features:
        print("Before fetch_and_impute_features:")
        for track in tracks_needing_features[:5]:  # Show first 5
            print(f"  {track.name[:30]:<30} | imputed: {track.features_imputed} | danceability: {track.danceability}")
        
        await audio_service.fetch_and_impute_features(tracks_needing_features, db)
        
        print("\nAfter fetch_and_impute_features:")
        for track in tracks_needing_features[:5]:  # Show first 5
            print(f"  {track.name[:30]:<30} | imputed: {track.features_imputed} | danceability: {track.danceability}")
    
    # Analyze data quality
    print("\n" + "="*60)
    print("DATA QUALITY ANALYSIS")
    print("="*60)
    
    quality_report = audio_service.analyze_data_quality(tracks)
    print(f"Overall completeness: {quality_report['overall_completeness']:.2%}")
    print(f"Recommendation: {quality_report['recommendation']}")
    
    # Show feature-by-feature quality
    print("\nFeature completeness:")
    for feature, quality in quality_report['feature_quality'].items():
        print(f"  {feature:<15}: {quality['completeness']:.1%} ({quality['present']}/{quality['present']+quality['missing']})")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(analyze_playlist_coverage())
