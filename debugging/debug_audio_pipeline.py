#!/usr/bin/env python3
"""
Debug script to test the complete audio features pipeline with real database tracks.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.dependencies import SessionLocal
from backend.models import Track
from backend.services.audio_features import AudioFeaturesService


async def debug_audio_features_pipeline():
    """Debug the complete audio features pipeline."""
    print("🔍 Debugging Audio Features Pipeline")
    print("=" * 45)
    
    db = SessionLocal()
    
    try:
        # Get a few tracks from database
        tracks = db.query(Track).limit(3).all()
        
        if not tracks:
            print("❌ No tracks found in database")
            return
        
        print(f"📊 Found {len(tracks)} tracks to test")
        
        # Show initial state
        service = AudioFeaturesService()
        for i, track in enumerate(tracks):
            print(f"\nTrack {i+1}: {track.name[:30]}...")
            print(f"  Spotify ID: {track.spotify_track_id}")
            
            missing_features = []
            for feature in service.AUDIO_FEATURES:
                value = getattr(track, feature)
                if value is None:
                    missing_features.append(feature)
                else:
                    print(f"  {feature}: {value}")
            
            if missing_features:
                print(f"  Missing: {', '.join(missing_features)}")
        
        # Test fetching audio features
        print(f"\n🔄 Testing audio features fetching...")
        
        # Count initial missing features
        initial_missing = 0
        for track in tracks:
            for feature in service.AUDIO_FEATURES:
                if getattr(track, feature) is None:
                    initial_missing += 1
        
        print(f"Initial missing features: {initial_missing}")
        
        # Call the fetch method
        updated_tracks = await service.fetch_missing_audio_features(tracks, db)
        
        # Count final missing features
        final_missing = 0
        for track in tracks:
            for feature in service.AUDIO_FEATURES:
                if getattr(track, feature) is None:
                    final_missing += 1
        
        print(f"Final missing features: {final_missing}")
        print(f"Features fetched: {initial_missing - final_missing}")
        
        # Show final state
        print(f"\n📊 Final track states:")
        for i, track in enumerate(tracks):
            print(f"\nTrack {i+1}: {track.name[:30]}...")
            for feature in service.AUDIO_FEATURES[:4]:  # Show first 4 features
                value = getattr(track, feature)
                if value is not None:
                    if feature == 'tempo':
                        print(f"  {feature}: {value:.0f}")
                    else:
                        print(f"  {feature}: {value:.3f}")
                else:
                    print(f"  {feature}: N/A")
        
        # Test data quality analysis
        quality_report = service.analyze_data_quality(tracks)
        print(f"\n📈 Data Quality Report:")
        print(f"Overall completeness: {quality_report.get('overall_completeness', 0):.1%}")
        print(f"Recommendation: {quality_report.get('recommendation', 'N/A')}")
        
        # Test clustering preparation
        print(f"\n🔧 Testing clustering preparation...")
        from backend.services.clustering import ClusteringService
        clustering_service = ClusteringService()
        
        prepared_tracks, prep_quality = await clustering_service.prepare_tracks_for_analysis(tracks, db)
        
        print(f"Prepared {len(prepared_tracks)} tracks for clustering")
        
        # Check if all features are now populated
        all_populated = True
        for track in prepared_tracks:
            for feature in service.AUDIO_FEATURES:
                if getattr(track, feature) is None:
                    all_populated = False
                    break
            if not all_populated:
                break
        
        if all_populated:
            print("✅ All tracks now have complete audio features!")
        else:
            print("❌ Some tracks still have missing features after preparation")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(debug_audio_features_pipeline())
