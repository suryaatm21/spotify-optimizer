#!/usr/bin/env python3
"""
Debug the mapping between ReccoBeats features and Track objects.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from backend.services.reccobeats import ReccoBeatsService
from backend.models import Track
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

async def debug_feature_mapping():
    """Debug why ReccoBeats features aren't being mapped to tracks."""
    
    # Connect to database
    engine = create_engine("sqlite:///db/spotify.db")
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Get a few tracks
    tracks = db.query(Track).limit(5).all()
    
    print("🔍 Debugging feature mapping")
    print("="*50)
    
    for track in tracks:
        print(f"\nTrack: {track.name[:30]}")
        print(f"  spotify_track_id: {track.spotify_track_id}")
        print(f"  cleaned ID: {track.spotify_track_id.split(':')[-1] if track.spotify_track_id else 'None'}")
        print(f"  current danceability: {track.danceability}")
    
    track_ids = [track.spotify_track_id for track in tracks if track.spotify_track_id]
    
    # Test ReccoBeats fetch
    service = ReccoBeatsService()
    features_map = await service.get_multiple_tracks_audio_features(track_ids)
    
    print(f"\n🎵 ReccoBeats returned features for {len(features_map)} tracks:")
    for spotify_id, features in features_map.items():
        print(f"  {spotify_id}: danceability={features.get('danceability', 'N/A')}")
    
    # Test the mapping logic from AudioFeaturesService
    print(f"\n🔗 Testing mapping logic:")
    track_map = {(t.spotify_track_id or "").split(":")[-1]: t for t in tracks}
    print(f"Track map keys: {list(track_map.keys())}")
    print(f"Features map keys: {list(features_map.keys())}")
    
    for spotify_id, features in features_map.items():
        track = track_map.get(spotify_id)
        print(f"\nSpotify ID: {spotify_id}")
        print(f"  Found track: {track.name if track else 'None'}")
        
        if track and features:
            mapped_features = service.map_features_to_spotify_format(features)
            print(f"  Mapped features: {mapped_features}")
            
            # Check if update would happen
            updated = False
            for name, value in mapped_features.items():
                if hasattr(track, name):
                    current_value = getattr(track, name)
                    print(f"    {name}: current={current_value}, new={value}, hasattr={hasattr(track, name)}")
                    if current_value is None:
                        print(f"      Would update {name} from None to {value}")
                        updated = True
                    elif current_value != value:
                        print(f"      Would update {name} from {current_value} to {value}")
                        updated = True
            
            print(f"  Would update: {updated}")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(debug_feature_mapping())
