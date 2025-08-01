#!/usr/bin/env python3
"""
Test the Spotify API directly with a real track ID from our database.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_api_direct():
    """Test API call directly."""
    print("🔍 Testing Spotify Audio Features API Directly")
    print("=" * 50)
    
    try:
        from backend.services.audio_features import get_app_access_token
        from backend.dependencies import SessionLocal
        from backend.models import Track
        import httpx
        
        # Get a real track ID from database
        db = SessionLocal()
        track = db.query(Track).first()
        db.close()
        
        if not track:
            print("❌ No tracks in database")
            return
        
        track_id = track.spotify_track_id
        print(f"Testing with track: {track.name}")
        print(f"Spotify ID: {track_id}")
        
        # Get access token
        print("\n1. Getting access token...")
        token = await get_app_access_token()
        print(f"✅ Token obtained: {len(token)} chars")
        
        # Make API call
        print("\n2. Making API call...")
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spotify.com/v1/audio-features",
                headers=headers,
                params={"ids": track_id},
                timeout=30.0
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Success! Response received:")
                
                features_list = data.get("audio_features", [])
                print(f"Features array length: {len(features_list)}")
                
                if features_list and features_list[0]:
                    features = features_list[0]
                    print(f"✅ Audio features for {track.name}:")
                    print(f"   Danceability: {features.get('danceability')}")
                    print(f"   Energy: {features.get('energy')}")
                    print(f"   Valence: {features.get('valence')}")
                    print(f"   Tempo: {features.get('tempo')}")
                    print(f"   Acousticness: {features.get('acousticness')}")
                    print(f"   Speechiness: {features.get('speechiness')}")
                else:
                    print("❌ No features in response")
                    print(f"Raw response: {data}")
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response text: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api_direct())
