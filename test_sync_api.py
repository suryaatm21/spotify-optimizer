#!/usr/bin/env python3
"""
Test Spotify API with synchronous requests to isolate the issue.
"""
import sys
import requests
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_api_sync():
    """Test API with synchronous requests."""
    print("🔍 Testing Spotify API (Synchronous)")
    print("=" * 40)
    
    try:
        from backend.dependencies import get_spotify_client_credentials
        from backend.dependencies import SessionLocal
        from backend.models import Track
        
        # Get credentials
        creds = get_spotify_client_credentials()
        print(f"✅ Credentials loaded")
        
        # Get access token using requests
        print("\n1. Getting access token...")
        token_data = {
            "grant_type": "client_credentials",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"]
        }
        
        token_response = requests.post(
            "https://accounts.spotify.com/api/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        
        if token_response.status_code != 200:
            print(f"❌ Token request failed: {token_response.status_code}")
            print(f"Response: {token_response.text}")
            return
        
        token = token_response.json()["access_token"]
        print(f"✅ Token obtained: {len(token)} chars")
        
        # Get a real track ID
        db = SessionLocal()
        track = db.query(Track).first()
        db.close()
        
        track_id = track.spotify_track_id
        print(f"\n2. Testing with track: {track.name}")
        print(f"   Spotify ID: {track_id}")
        
        # Make API call
        print("\n3. Fetching audio features...")
        headers = {"Authorization": f"Bearer {token}"}
        
        api_response = requests.get(
            "https://api.spotify.com/v1/audio-features",
            headers=headers,
            params={"ids": track_id},
            timeout=30
        )
        
        print(f"Status: {api_response.status_code}")
        
        if api_response.status_code == 200:
            data = api_response.json()
            features_list = data.get("audio_features", [])
            
            if features_list and features_list[0]:
                features = features_list[0]
                print("✅ SUCCESS! Real audio features:")
                print(f"   Danceability: {features.get('danceability'):.3f}")
                print(f"   Energy: {features.get('energy'):.3f}")
                print(f"   Valence: {features.get('valence'):.3f}")
                print(f"   Tempo: {features.get('tempo'):.1f}")
                
                # Compare with defaults
                print(f"\n📊 Compare with defaults (what you're seeing):")
                print(f"   Danceability: 0.500 (default) vs {features.get('danceability'):.3f} (real)")
                print(f"   Energy: 0.500 (default) vs {features.get('energy'):.3f} (real)")
                print(f"   Valence: 0.500 (default) vs {features.get('valence'):.3f} (real)")
                print(f"   Tempo: 120.0 (default) vs {features.get('tempo'):.1f} (real)")
                
                if (abs(features.get('danceability', 0.5) - 0.5) < 0.001 and 
                    abs(features.get('energy', 0.5) - 0.5) < 0.001 and
                    abs(features.get('valence', 0.5) - 0.5) < 0.001 and
                    abs(features.get('tempo', 120) - 120) < 1):
                    print("\n⚠️  This track happens to have values very close to defaults!")
                else:
                    print("\n✅ These are real, unique values from Spotify!")
                    
            else:
                print("❌ No features in response")
                print(f"Response: {data}")
        else:
            print(f"❌ API Error: {api_response.status_code}")
            print(f"Response: {api_response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_sync()
