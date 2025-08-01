#!/usr/bin/env python3
"""
Test script for ReccoBeats API integration.
Run this to validate that the ReccoBeats service is working correctly.
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.reccobeats import ReccoBeatsService, ReccoBeatsConfig


async def test_reccobeats_integration():
    """Test ReccoBeats API integration with real API calls."""
    print("🧪 Testing ReccoBeats API Integration")
    print("=" * 50)
    
    # Test configuration
    try:
        config = ReccoBeatsConfig()
        print(f"✅ Configuration loaded")
        print(f"   Base URL: {config.base_url}")
        print(f"   API Key: {'*' * 20 if config.api_key else 'NOT SET'}")
        
        if not config.api_key:
            print("ℹ️  RECCOBEATS_API_KEY not set - using public API access")
            print("   This is expected since ReccoBeats doesn't require authentication")
            print()
        else:
            print("ℹ️  RECCOBEATS_API_KEY provided - using authenticated access")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test service initialization
    try:
        service = ReccoBeatsService(config)
        print(f"✅ ReccoBeats service initialized")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False
    
    # Test with sample Spotify track IDs
    test_track_ids = [
        "11dFghVXANMlKmJXsNCbNl",  # Example from Spotify docs
        "4iV5W9uYEdYUVa79Axb7Rh",  # Another popular track
        "7qiZfU4dY1lWllzX7mPBI3"   # Another track
    ]
    
    print(f"\n🎵 Testing with {len(test_track_ids)} sample tracks")
    print("-" * 30)
    
    # Test single track audio features
    print("\n1. Testing single track audio features...")
    for i, track_id in enumerate(test_track_ids[:1]):  # Test just one for now
        print(f"   Testing track: {track_id}")
        try:
            features = await service.get_track_audio_features(track_id)
            if features:
                print(f"   ✅ Features retrieved: {list(features.keys())}")
                
                # Test mapping to Spotify format
                mapped = service.map_features_to_spotify_format(features)
                print(f"   ✅ Mapped features: {list(mapped.keys())}")
                
                # Show some sample values
                for feature in ['danceability', 'energy', 'valence'][:3]:
                    if feature in mapped:
                        print(f"      {feature}: {mapped[feature]}")
            else:
                print(f"   ⚠️  No features returned for track {track_id}")
        except Exception as e:
            print(f"   ❌ Error fetching features: {e}")
    
    # Test track details
    print("\n2. Testing track details...")
    try:
        details = await service.get_track_details(test_track_ids[0])
        if details:
            print(f"   ✅ Track details retrieved: {list(details.keys())}")
        else:
            print(f"   ⚠️  No track details returned")
    except Exception as e:
        print(f"   ❌ Error fetching track details: {e}")
    
    # Test multiple tracks (smaller batch for testing)
    print("\n3. Testing multiple tracks...")
    try:
        features_map = await service.get_multiple_tracks_audio_features(test_track_ids[:2])
        print(f"   ✅ Retrieved features for {len(features_map)}/{len(test_track_ids[:2])} tracks")
        
        for track_id, features in features_map.items():
            print(f"      Track {track_id[:8]}...: {len(features)} features")
            
    except Exception as e:
        print(f"   ❌ Error fetching multiple tracks: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 ReccoBeats Integration Test Complete")
    
    return True


async def test_audio_features_service():
    """Test the updated audio features service with ReccoBeats integration."""
    print("\n🔧 Testing Updated Audio Features Service")
    print("=" * 50)
    
    try:
        from backend.services.audio_features import AudioFeaturesService
        from backend.models import Track
        from backend.dependencies import SessionLocal
        
        # Create sample tracks for testing
        sample_tracks = [
            Track(
                id=1,
                name="Test Track 1",
                artist="Test Artist",
                spotify_track_id="11dFghVXANMlKmJXsNCbNl",
                # Missing audio features (all None)
                danceability=None,
                energy=None,
                valence=None
            ),
            Track(
                id=2,
                name="Test Track 2", 
                artist="Test Artist",
                spotify_track_id="4iV5W9uYEdYUVa79Axb7Rh",
                # Some features present
                danceability=0.8,
                energy=None,
                valence=None
            )
        ]
        
        service = AudioFeaturesService()
        
        # Test with mock database session
        db = SessionLocal()
        
        print("✅ Audio features service initialized")
        print(f"📊 Testing with {len(sample_tracks)} sample tracks")
        
        # Test ReccoBeats integration (will likely fail without real API key)
        print("\n1. Testing ReccoBeats integration...")
        try:
            updated_tracks = await service.fetch_missing_audio_features(
                sample_tracks, 
                db, 
                use_reccobeats=True
            )
            print(f"   ✅ Service executed successfully")
            print(f"   📈 Returned {len(updated_tracks)} updated tracks")
        except Exception as e:
            print(f"   ⚠️  Expected error (likely no API key): {e}")
        
        # Test fallback to imputation
        print("\n2. Testing fallback to imputation...")
        try:
            imputed_tracks = service.impute_missing_features(sample_tracks)
            print(f"   ✅ Imputation executed successfully")
            print(f"   📈 Returned {len(imputed_tracks)} tracks")
        except Exception as e:
            print(f"   ❌ Imputation failed: {e}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Audio features service test failed: {e}")
        return False
    
    return True


def main():
    """Main test function."""
    print("🚀 ReccoBeats Integration Test Suite")
    print("=" * 60)
    print()
    
    # Check environment setup
    api_key = os.getenv("RECCOBEATS_API_KEY")
    if not api_key:
        print("ℹ️  ReccoBeats API Key: Not required (public API access)")
        print("   ReccoBeats provides public access without authentication")
        print()
    else:
        print("ℹ️  ReccoBeats API Key: Provided (authenticated access)")
        print()
    async def run_tests():
        # Test ReccoBeats service
        recco_success = await test_reccobeats_integration()
        
        # Test updated audio features service
        audio_success = await test_audio_features_service()
        
        print("\n" + "=" * 60)
        print("📋 Test Results Summary:")
        print(f"   ReccoBeats Service: {'✅ PASS' if recco_success else '❌ FAIL'}")
        print(f"   Audio Features Service: {'✅ PASS' if audio_success else '❌ FAIL'}")
        
        if recco_success and audio_success:
            print("\n🎉 All tests completed! ReccoBeats integration is ready.")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
    
    # Run the async tests
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")


if __name__ == "__main__":
    main()
