#!/usr/bin/env python3
"""
Create a fallback mode for analytics endpoints when Spotify API has permission issues.
This allows the app to work with existing data while the API configuration is being resolved.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.dependencies import get_database
from backend.models import User, Track, Playlist

def check_existing_data():
    """Check what data we have available without making API calls."""
    
    print("🔍 Checking Existing Data Availability")
    print("=" * 50)
    
    db = next(get_database())
    
    # Check users
    users = db.query(User).all()
    print(f"👥 Users: {len(users)}")
    for user in users:
        print(f"   - {user.spotify_user_id} (token: ...{user.access_token[-4:] if user.access_token else 'None'})")
    
    # Check playlists
    playlists = db.query(Playlist).all()
    print(f"\n📁 Playlists: {len(playlists)}")
    for playlist in playlists:
        track_count = db.query(Track).filter(Track.playlist_id == playlist.id).count()
        print(f"   - {playlist.name} ({track_count} tracks)")
    
    # Check tracks and their audio features
    all_tracks = db.query(Track).all()
    print(f"\n🎵 Total Tracks: {len(all_tracks)}")
    
    if all_tracks:
        # Analyze audio features availability
        features_available = 0
        for track in all_tracks:
            if track.danceability is not None:  # Check if any audio features exist
                features_available += 1
        
        print(f"   - Tracks with audio features: {features_available}/{len(all_tracks)}")
        print(f"   - Coverage: {(features_available/len(all_tracks)*100):.1f}%")
        
        # Show a sample track
        sample_track = all_tracks[0]
        print(f"\n📊 Sample Track: {sample_track.name}")
        print(f"   - Artist: {sample_track.artist}")
        print(f"   - Spotify ID: {sample_track.spotify_track_id}")
        print(f"   - Danceability: {sample_track.danceability}")
        print(f"   - Energy: {sample_track.energy}")
        print(f"   - Valence: {sample_track.valence}")
    
    db.close()
    
    return len(all_tracks) > 0, features_available if all_tracks else 0

def create_fallback_strategy():
    """Create strategy for working without Spotify API access."""
    
    has_tracks, features_count = check_existing_data()
    
    print(f"\n💡 Fallback Strategy Recommendations:")
    print(f"=" * 50)
    
    if not has_tracks:
        print("❌ No existing tracks found")
        print("   - Cannot provide stats or optimization without track data")
        print("   - Must resolve Spotify API access to fetch initial playlist data")
        print("   - Consider manual data entry or CSV import as temporary solution")
    
    elif features_count == 0:
        print("⚠️  Tracks exist but no audio features")
        print("   - Stats endpoints can work with basic track info (name, artist, etc.)")
        print("   - Clustering/analysis will require audio features")
        print("   - Can implement fallback using track metadata only")
    
    else:
        print(f"✅ Partial data available ({features_count} tracks with features)")
        print("   - Stats and clustering can work with existing data")
        print("   - Optimize endpoint can use cached analysis results")
        print("   - No need for live Spotify API calls for these tracks")
    
    print(f"\n🔧 Immediate Fixes Needed:")
    print(f"   1. Modify endpoints to skip Spotify API when tracks exist")
    print(f"   2. Add fallback modes for basic playlist operations")
    print(f"   3. Improve error handling to gracefully degrade functionality")
    print(f"   4. Cache existing data and work offline until API is fixed")

if __name__ == "__main__":
    create_fallback_strategy()
