#!/usr/bin/env python3
"""
Quick test to examine all features available from ReccoBeats API.
"""
import asyncio
import sys
import os
import json

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.reccobeats import ReccoBeatsService


async def examine_reccobeats_features():
    """Examine what features ReccoBeats actually provides."""
    print("🔍 Examining ReccoBeats Feature Set")
    print("=" * 40)
    
    service = ReccoBeatsService()
    
    # Test with a popular track
    test_track_id = "6habFhsOp2NvshLv26DqMb"  # Despacito
    
    print(f"Testing with track: {test_track_id}")
    
    # Get track info first
    print("\n📋 Track Info:")
    track_info = await service.get_track_details(test_track_id)
    if track_info:
        print(json.dumps(track_info, indent=2)[:500] + "...")
        print(f"Available fields: {list(track_info.keys())}")
    
    # Get audio features
    print("\n🎵 Audio Features:")
    features = await service.get_track_audio_features(test_track_id)
    if features:
        print(json.dumps(features, indent=2))
        print(f"\nAvailable features: {list(features.keys())}")
        print(f"Feature count: {len(features)}")
        
        # Check for genre/mood indicators
        genre_fields = [k for k in features.keys() if 'genre' in k.lower()]
        mood_fields = [k for k in features.keys() if any(word in k.lower() for word in ['mood', 'emotion', 'valence', 'arousal'])]
        year_fields = [k for k in features.keys() if any(word in k.lower() for word in ['year', 'release', 'date'])]
        
        print(f"\nGenre-related fields: {genre_fields}")
        print(f"Mood-related fields: {mood_fields}")
        print(f"Year-related fields: {year_fields}")
    else:
        print("❌ No features returned")


if __name__ == "__main__":
    asyncio.run(examine_reccobeats_features())
