#!/usr/bin/env python3
"""
Test script to validate Spotify API audio features request format.
This script tests the exact request format against Spotify documentation.
"""

import asyncio
import httpx
import os
from pathlib import Path

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.dependencies import get_database
from backend.models import User

async def test_audio_features_request():
    """Test audio features request with proper error handling."""
    
    # Get a user from database to test with
    db = next(get_database())
    user = db.query(User).first()
    
    if not user or not user.access_token:
        print("❌ No user with access token found in database")
        return
    
    print(f"✅ Testing with user: {user.spotify_user_id}")
    print(f"✅ Token ending in: ...{user.access_token[-4:]}")
    
    # Test track IDs (example from Spotify docs)
    test_track_ids = ["11dFghVXANMlKmJXsNCbNl"]  # Example from docs
    
    async with httpx.AsyncClient() as client:
        # Test the exact request format from our code
        headers = {"Authorization": f"Bearer {user.access_token}"}
        url = "https://api.spotify.com/v1/audio-features"
        params = {"ids": ",".join(test_track_ids)}
        
        print(f"\n🔍 Making request:")
        print(f"URL: {url}")
        print(f"Headers: Authorization: Bearer {user.access_token[:10]}...")
        print(f"Params: {params}")
        
        try:
            response = await client.get(url, headers=headers, params=params)
            
            print(f"\n📊 Response:")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS! Audio features received:")
                print(f"Number of features: {len(data.get('audio_features', []))}")
                for feature in data.get('audio_features', []):
                    if feature:
                        print(f"  Track {feature.get('id')}: danceability={feature.get('danceability')}")
            else:
                print(f"❌ Error response:")
                try:
                    error_data = response.json()
                    print(f"Error JSON: {error_data}")
                except:
                    print(f"Error text: {response.text}")
                    
                # Specific error handling
                if response.status_code == 401:
                    print("🔑 401 = Token expired/revoked - user needs re-authentication")
                elif response.status_code == 403:
                    print("⚙️ 403 = OAuth configuration issue - check app credentials")
                elif response.status_code == 400:
                    print("📝 400 = Bad request - check request format")
                    
        except Exception as e:
            print(f"❌ Request failed with exception: {e}")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_audio_features_request())
