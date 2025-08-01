#!/usr/bin/env python3
"""
Debug script to test ReccoBeats bulk fetch functionality
and identify why it's returning empty results for large playlists.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from backend.services.reccobeats import ReccoBeatsService

async def test_reccobeats_bulk_fetch():
    """Test ReccoBeats bulk fetch with sample Spotify track IDs."""
    
    # Sample track IDs from various popular songs
    test_track_ids = [
        "4iV5W9uYEdYUVa79Axb7Rh",  # Never Gonna Give You Up - Rick Astley
        "0VjIjW4GlULA7QWCRXHpzD",  # Blinding Lights - The Weeknd
        "1uNFoZAHBGtllmzznpCI3s",  # Shape of You - Ed Sheeran  
        "6dGnYIeXmHdcikdzNNDMm2",  # Someone You Loved - Lewis Capaldi
        "7qiZfU4dY1lWllzX7mPBI3",  # Bad Guy - Billie Eilish
    ]
    
    print(f"🧪 Testing ReccoBeats bulk fetch with {len(test_track_ids)} tracks")
    print(f"Track IDs: {test_track_ids}")
    
    service = ReccoBeatsService()
    
    # Test step 1: UUID lookup
    print("\n" + "="*50)
    print("STEP 1: Testing UUID lookup")
    print("="*50)
    
    uuid_map = await service._get_multiple_reccobeats_uuids(test_track_ids)
    print(f"UUID map result: {uuid_map}")
    print(f"Found UUIDs for {len(uuid_map)} out of {len(test_track_ids)} tracks")
    
    if not uuid_map:
        print("❌ No UUIDs found - stopping test")
        return
    
    # Test step 2: Audio features fetch
    print("\n" + "="*50)
    print("STEP 2: Testing audio features fetch")
    print("="*50)
    
    features_result = await service.get_multiple_tracks_audio_features(test_track_ids)
    print(f"Features result: {features_result}")
    print(f"Got features for {len(features_result)} tracks")
    
    # Test individual lookup for comparison
    print("\n" + "="*50)
    print("STEP 3: Testing individual lookups for comparison")
    print("="*50)
    
    for track_id in test_track_ids[:2]:  # Test first 2 only
        print(f"\nTesting individual lookup for: {track_id}")
        uuid = await service._get_reccobeats_uuid(track_id)
        print(f"UUID: {uuid}")
        
        if uuid:
            individual_features = await service.get_track_audio_features(track_id)
            print(f"Individual features: {individual_features}")
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Bulk UUID lookup: {len(uuid_map)}/{len(test_track_ids)} found")
    print(f"Bulk features fetch: {len(features_result)}/{len(test_track_ids)} found")

if __name__ == "__main__":
    asyncio.run(test_reccobeats_bulk_fetch())
