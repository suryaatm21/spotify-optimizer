#!/usr/bin/env python3
"""
Simple test to update one track's audio features.
"""
import sys
sys.path.insert(0, '.')

def test_sync():
    """Test synchronous operations only."""
    print("🔧 Testing Audio Features (Sync Mode)")
    print("=" * 40)
    
    from backend.dependencies import SessionLocal
    from backend.models import Track
    
    db = SessionLocal()
    
    try:
        # Get one track
        track = db.query(Track).first()
        
        if not track:
            print("No tracks found")
            return
        
        print(f"Track: {track.name}")
        print(f"Spotify ID: {track.spotify_track_id}")
        
        # Check current state
        missing_features = []
        for feature in ['danceability', 'energy', 'valence', 'tempo']:
            value = getattr(track, feature)
            if value is None:
                missing_features.append(feature)
            print(f"{feature}: {value}")
        
        print(f"Missing features: {len(missing_features)}")
        
        if missing_features:
            print("\n⚠️ This track has missing audio features.")
            print("To fix this:")
            print("1. Start the backend server")
            print("2. Go to the frontend")
            print("3. Click 'Analyze Playlist' for this track's playlist")
            print("4. The analysis will automatically fetch missing audio features")
        else:
            print("\n✅ This track has all audio features!")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_sync()
