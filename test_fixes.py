#!/usr/bin/env python3
"""
Simple test to verify the AudioFeaturesService fixes.
"""
import asyncio
import sys
import warnings
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from backend.services.reccobeats import ReccoBeatsService
from backend.services.audio_features import AudioFeaturesService
from backend.models import Track

def test_public_method():
    """Test that impute_missing_features is now public."""
    reccobeats_service = ReccoBeatsService()
    audio_service = AudioFeaturesService(reccobeats_service)
    
    # This should not raise AttributeError
    assert hasattr(audio_service, 'impute_missing_features'), "impute_missing_features method should be public"
    print("✅ impute_missing_features method is accessible")

def test_pandas_warning():
    """Test that pandas warnings are resolved."""
    reccobeats_service = ReccoBeatsService()
    audio_service = AudioFeaturesService(reccobeats_service)
    
    # Create test tracks with missing features
    test_tracks = [
        Track(
            id=1, 
            spotify_track_id='test1',
            name='Test Track',
            artist='Test Artist',
            danceability=None,
            energy=None,
            speechiness=None,
            acousticness=None,
            instrumentalness=None,
            liveness=None,
            valence=None,
            tempo=None,
            key=None,
            loudness=None,
            mode=None,
            features_imputed=True
        )
    ]
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # This should not produce pandas warnings
        audio_service.impute_missing_features(test_tracks)
        
        # Check for pandas warnings
        pandas_warnings = [warning for warning in w if 'pandas' in str(warning.message).lower() or 'settingwithcopy' in str(warning.message).lower()]
        
        if pandas_warnings:
            print("❌ Pandas warnings still present:")
            for warning in pandas_warnings:
                print(f"   {warning.message}")
            return False
        else:
            print("✅ No pandas SettingWithCopyWarning detected")
            return True

if __name__ == "__main__":
    print("🧪 Testing AudioFeaturesService fixes...\n")
    
    try:
        test_public_method()
        warning_test_passed = test_pandas_warning()
        
        if warning_test_passed:
            print("\n🎉 All tests passed! Both issues are resolved:")
            print("  ✅ impute_missing_features method is now public")
            print("  ✅ Pandas SettingWithCopyWarning is resolved")
            print("  ✅ /analyze endpoint should now work without 500 errors")
        else:
            print("\n❌ Pandas warning test failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
