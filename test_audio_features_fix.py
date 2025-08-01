#!/usr/bin/env python3
"""
Test script to verify audio features are being fetched and stored correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.audio_features import AudioFeaturesService, get_app_access_token
from backend.models import Track
from backend.dependencies import get_database


async def test_audio_features_fetching():
    """Test the complete audio features fetching pipeline."""
    print("🧪 Testing Audio Features Pipeline...")
    print("=" * 50)
    
    # Test 1: Verify we can get an access token
    print("\n1. Testing Spotify API authentication...")
    try:
        token = await get_app_access_token()
        if token and len(token) > 20:
            print(f"✅ Successfully obtained access token (length: {len(token)})")
        else:
            print("❌ Failed to obtain valid access token")
            return False
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    # Test 2: Test direct API call to audio features endpoint
    print("\n2. Testing direct Spotify API call...")
    try:
        import httpx
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Use a known popular track ID for testing
        test_track_id = "4uLU6hMCjMI75M1A2tKUQC"  # "Never Gonna Give You Up"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spotify.com/v1/audio-features",
                headers=headers,
                params={"ids": test_track_id},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                features = data.get("audio_features", [])
                
                if features and features[0]:
                    feature_data = features[0]
                    print("✅ Successfully retrieved audio features from Spotify!")
                    print(f"   Danceability: {feature_data.get('danceability')}")
                    print(f"   Energy: {feature_data.get('energy')}")
                    print(f"   Valence: {feature_data.get('valence')}")
                    print(f"   Tempo: {feature_data.get('tempo')}")
                else:
                    print("❌ No audio features returned")
                    return False
            else:
                print(f"❌ API call failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False
    
    # Test 3: Test the AudioFeaturesService
    print("\n3. Testing AudioFeaturesService...")
    try:
        service = AudioFeaturesService()
        
        # Create mock tracks with missing features
        mock_tracks = []
        for i in range(3):
            track = Track()
            track.id = i + 1
            track.spotify_track_id = f"test_track_{i}"
            track.name = f"Test Track {i}"
            track.artist = "Test Artist"
            
            # Set all audio features to None (missing)
            for feature in service.AUDIO_FEATURES:
                setattr(track, feature, None)
            
            mock_tracks.append(track)
        
        print(f"✅ Created {len(mock_tracks)} mock tracks with missing features")
        
        # Test the data quality analysis
        quality_report = service.analyze_data_quality(mock_tracks)
        print(f"✅ Data quality analysis: {quality_report.get('overall_completeness', 0):.1%} complete")
        
        # Test imputation (without database)
        imputed_tracks = service.impute_missing_features(mock_tracks.copy())
        
        # Check if features were filled
        filled_count = 0
        for track in imputed_tracks:
            for feature in service.AUDIO_FEATURES:
                if getattr(track, feature) is not None:
                    filled_count += 1
        
        expected_filled = len(mock_tracks) * len(service.AUDIO_FEATURES)
        if filled_count == expected_filled:
            print(f"✅ Successfully imputed {filled_count} missing values")
        else:
            print(f"❌ Expected {expected_filled} filled values, got {filled_count}")
            return False
            
    except Exception as e:
        print(f"❌ AudioFeaturesService test failed: {e}")
        return False
    
    print("\n4. Testing database integration...")
    try:
        # Test with actual database connection
        from backend.dependencies import SessionLocal
        
        db = SessionLocal()
        
        # Get actual tracks from database
        tracks = db.query(Track).limit(5).all()
        
        if tracks:
            print(f"✅ Found {len(tracks)} tracks in database")
            
            # Check current state of audio features
            missing_features_count = 0
            for track in tracks:
                for feature in service.AUDIO_FEATURES:
                    if getattr(track, feature) is None:
                        missing_features_count += 1
            
            print(f"   Current missing features: {missing_features_count}")
            
            # Test quality analysis on real data
            quality_report = service.analyze_data_quality(tracks)
            print(f"   Current data completeness: {quality_report.get('overall_completeness', 0):.1%}")
            
        else:
            print("⚠️  No tracks found in database")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False
    
    print("\n✅ All audio features tests passed!")
    print("\n💡 Next steps:")
    print("   1. Ensure frontend calls the analysis endpoint with fetch_missing_features=true")
    print("   2. Run a playlist analysis to trigger audio features fetching")
    print("   3. Check the track details again to see if N/A values are populated")
    
    return True


async def main():
    """Run the audio features tests."""
    success = await test_audio_features_fetching()
    if not success:
        print("\n❌ Some tests failed. Check the error messages above.")
        sys.exit(1)
    else:
        print("\n🎉 Audio features pipeline is working correctly!")


if __name__ == "__main__":
    asyncio.run(main())
