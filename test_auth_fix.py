#!/usr/bin/env python3
"""
Test script to verify the audio features authorization fix.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.audio_features import get_app_access_token


async def test_auth_fix():
    """Test that we can get a proper Spotify app access token."""
    print("🧪 Testing Spotify authentication fix...")
    
    try:
        # Test getting an app access token
        token = await get_app_access_token()
        
        if token and isinstance(token, str) and len(token) > 50:
            print("✅ Successfully obtained Spotify app access token")
            print(f"   Token length: {len(token)} characters")
            print(f"   Token preview: {token[:20]}...")
            return True
        else:
            print(f"❌ Invalid token received: {token}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to get access token: {e}")
        return False


async def test_audio_features_request():
    """Test making an actual request to Spotify's audio features endpoint."""
    import httpx
    
    print("\n🧪 Testing audio features API request...")
    
    try:
        # Get access token
        token = await get_app_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test with a known track ID (a popular song)
        test_track_id = "4uLU6hMCjMI75M1A2tKUQC"  # "Never Gonna Give You Up" by Rick Astley
        
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
                    print("✅ Successfully retrieved audio features!")
                    print(f"   Track ID: {feature_data.get('id', 'N/A')}")
                    print(f"   Danceability: {feature_data.get('danceability', 'N/A')}")
                    print(f"   Energy: {feature_data.get('energy', 'N/A')}")
                    print(f"   Valence: {feature_data.get('valence', 'N/A')}")
                    return True
                else:
                    print("❌ No audio features returned")
                    return False
            else:
                print(f"❌ API request failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🔧 Testing Spotify Audio Features Authorization Fix")
    print("=" * 55)
    
    # Test 1: Token acquisition
    token_test = await test_auth_fix()
    
    # Test 2: API request
    if token_test:
        api_test = await test_audio_features_request()
        
        if api_test:
            print("\n🎉 All tests passed! The authorization fix is working correctly.")
            print("✅ Audio features should now be fetched properly instead of returning N/A")
        else:
            print("\n⚠️  Token obtained but API request failed. Check network/credentials.")
    else:
        print("\n❌ Token acquisition failed. Check Spotify credentials in .env file.")


if __name__ == "__main__":
    asyncio.run(main())
