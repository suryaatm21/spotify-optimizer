#!/usr/bin/env python3
"""
Test script to verify current token scopes and test minimal audio features request.
"""

import asyncio
import httpx
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.dependencies import get_database
from backend.models import User

async def test_token_and_scopes():
    """Test current token scopes and minimal audio features access."""
    
    # Get a user from database
    db = next(get_database())
    user = db.query(User).first()
    
    if not user or not user.access_token:
        print("❌ No user with access token found in database")
        return
    
    token = user.access_token
    print(f"✅ Testing with user: {user.spotify_user_id}")
    print(f"✅ Token ending in: ...{token[-4:]}")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Test basic profile access (should work with our scopes)
        print(f"\n🔍 Test 1: Basic profile access")
        try:
            response = await client.get("https://api.spotify.com/v1/me", headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Profile access works - User: {data.get('display_name')}")
            else:
                print(f"❌ Profile access failed: {response.text}")
        except Exception as e:
            print(f"❌ Profile request failed: {e}")
        
        # 2. Test minimal single audio features request  
        print(f"\n🔍 Test 2: Single audio features (minimal)")
        single_track_id = "11dFghVXANMlKmJXsNCbNl"  # Example from Spotify docs
        try:
            response = await client.get(
                f"https://api.spotify.com/v1/audio-features/{single_track_id}",
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Single audio features works - Track: {data.get('id')}")
                print(f"   Danceability: {data.get('danceability')}")
            else:
                error_data = response.json() if response.content else {}
                print(f"❌ Single audio features failed: {error_data}")
        except Exception as e:
            print(f"❌ Single audio features request failed: {e}")
        
        # 3. Test bulk audio features request (our current approach)
        print(f"\n🔍 Test 3: Bulk audio features (our approach)")
        try:
            response = await client.get(
                "https://api.spotify.com/v1/audio-features",
                headers=headers,
                params={"ids": single_track_id}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                features = data.get('audio_features', [])
                print(f"✅ Bulk audio features works - {len(features)} features returned")
                if features and features[0]:
                    print(f"   First track danceability: {features[0].get('danceability')}")
            else:
                error_data = response.json() if response.content else {}
                print(f"❌ Bulk audio features failed: {error_data}")
                
                # Detailed error analysis
                if response.status_code == 403:
                    print("🔍 403 Analysis:")
                    print(f"   - Token appears valid (got here)")
                    print(f"   - May be scope issue or app configuration")
                    print(f"   - Check Spotify Developer Dashboard settings")
                elif response.status_code == 401:
                    print("🔍 401 Analysis:")
                    print(f"   - Token expired or invalid")
                    print(f"   - Need re-authentication")
                    
        except Exception as e:
            print(f"❌ Bulk audio features request failed: {e}")
        
        # 4. Test if we can access user's playlists (scope verification)
        print(f"\n🔍 Test 4: Playlists access (scope verification)")
        try:
            response = await client.get(
                "https://api.spotify.com/v1/me/playlists",
                headers=headers,
                params={"limit": 1}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                playlists = data.get('items', [])
                print(f"✅ Playlists access works - {len(playlists)} playlists")
                if playlists:
                    print(f"   First playlist: {playlists[0].get('name')}")
            else:
                print(f"❌ Playlists access failed: {response.text}")
        except Exception as e:
            print(f"❌ Playlists request failed: {e}")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_token_and_scopes())
