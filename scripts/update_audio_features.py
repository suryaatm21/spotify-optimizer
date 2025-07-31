#!/usr/bin/env python3
"""
Script to manually fetch and update missing audio features for existing tracks.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.dependencies import SessionLocal
from backend.models import Track
from backend.services.audio_features import AudioFeaturesService


async def update_missing_audio_features():
    """Update missing audio features for all tracks in database."""
    print("🔧 Updating Missing Audio Features...")
    print("=" * 40)
    
    db = SessionLocal()
    
    try:
        # Get all tracks
        tracks = db.query(Track).all()
        print(f"Found {len(tracks)} tracks in database")
        
        if not tracks:
            print("No tracks found. Import some playlists first.")
            return
        
        # Check current missing features
        service = AudioFeaturesService()
        quality_report = service.analyze_data_quality(tracks)
        
        print(f"Current data completeness: {quality_report.get('overall_completeness', 0):.1%}")
        
        # Count tracks with missing features
        tracks_with_missing = []
        for track in tracks:
            missing_count = sum(1 for feature in service.AUDIO_FEATURES 
                              if getattr(track, feature) is None)
            if missing_count > 0:
                tracks_with_missing.append(track)
        
        print(f"Tracks with missing features: {len(tracks_with_missing)}")
        
        if tracks_with_missing:
            print("\nFetching missing audio features from Spotify...")
            
            # Use the audio features service to fetch missing data
            updated_tracks = await service.fetch_missing_audio_features(tracks_with_missing, db)
            
            # Check results
            print("\nChecking results...")
            final_quality = service.analyze_data_quality(tracks)
            print(f"Final data completeness: {final_quality.get('overall_completeness', 0):.1%}")
            
            # Show some examples
            print("\nExample tracks with updated features:")
            for track in tracks[:3]:
                features_str = []
                for feature in ['danceability', 'energy', 'valence', 'tempo']:
                    value = getattr(track, feature)
                    if value is not None:
                        if feature == 'tempo':
                            features_str.append(f"{feature}: {value:.0f}")
                        else:
                            features_str.append(f"{feature}: {value:.2f}")
                    else:
                        features_str.append(f"{feature}: N/A")
                
                print(f"  - {track.name[:25]}... | {' | '.join(features_str)}")
        
        else:
            print("All tracks already have complete audio features!")
    
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(update_missing_audio_features())
