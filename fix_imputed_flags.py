#!/usr/bin/env python3
"""
Database migration script to fix tracks that were incorrectly marked as 
having real features when they actually have default/imputed values.
"""
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Track
from backend.services.audio_features import AudioFeaturesService

def fix_imputed_flags():
    """
    Find tracks with default values and mark them as features_imputed=True
    so they can be retried with ReccoBeats.
    """
    # Connect to database
    engine = create_engine("sqlite:///db/spotify.db")
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Find tracks with default values that are incorrectly marked as real
    default_values = AudioFeaturesService.FEATURE_DEFAULTS
    
    # Look for tracks with the exact pattern of default values
    tracks_with_defaults = db.query(Track).filter(
        Track.danceability == default_values["danceability"],
        Track.energy == default_values["energy"],
        Track.tempo == default_values["tempo"],
        Track.features_imputed == False  # Incorrectly marked as real
    ).all()
    
    print(f"🔍 Found {len(tracks_with_defaults)} tracks with default values incorrectly marked as real")
    
    if tracks_with_defaults:
        print("Sample tracks to be fixed:")
        for track in tracks_with_defaults[:5]:
            print(f"  - {track.name[:40]:<40} | danceability: {track.danceability}")
        
        # Update the flags
        for track in tracks_with_defaults:
            track.features_imputed = True
        
        db.commit()
        print(f"✅ Updated {len(tracks_with_defaults)} tracks to features_imputed=True")
    
    # Show summary
    total_tracks = db.query(Track).count()
    imputed_tracks = db.query(Track).filter(Track.features_imputed == True).count()
    real_tracks = total_tracks - imputed_tracks
    
    print(f"\n📊 Database summary:")
    print(f"  Total tracks: {total_tracks}")
    print(f"  Real features: {real_tracks}")
    print(f"  Imputed features: {imputed_tracks}")
    print(f"  Coverage: {real_tracks/total_tracks*100:.1f}%" if total_tracks else "N/A")
    
    db.close()

if __name__ == "__main__":
    fix_imputed_flags()
