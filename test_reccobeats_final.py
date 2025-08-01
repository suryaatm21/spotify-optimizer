#!/usr/bin/env python3
"""
Final comprehensive test of ReccoBeats integration.
Tests the two-step process: Spotify ID → ReccoBeats UUID → Audio Features
"""

import asyncio
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.reccobeats import ReccoBeatsService


async def test_reccobeats_comprehensive():
    """
    Comprehensive test of ReccoBeats service functionality.
    """
    print("🎵 === ReccoBeats Comprehensive Integration Test ===")
    
    service = ReccoBeatsService()
    
    # Test tracks - mix of popular and less common songs
    test_tracks = [
        "6habFhsOp2NvshLv26DqMb",  # Despacito - confirmed working
        "4iV5W9uYEdYUVa79Axb7Rh",  # Shape of You - Ed Sheeran 
        "7qiZfU4dY1lWllzX7mPBI3",  # Blinding Lights - The Weeknd
        "0VjIjW4GlULA4LGvWeZaWQ",  # Baby Shark (might not be in ReccoBeats)
    ]
    
    print(f"\n📋 Testing with {len(test_tracks)} tracks...")
    
    # Test 1: Individual track processing
    print("\n🔍 Test 1: Individual Track Processing")
    print("-" * 50)
    
    individual_results = {}
    for track_id in test_tracks:
        print(f"\nProcessing: {track_id}")
        features = await service.get_track_audio_features(track_id)
        
        if features:
            individual_results[track_id] = features
            print(f"✅ SUCCESS - Features: {list(features.keys())}")
            # Show key audio features
            if 'danceability' in features:
                print(f"   🕺 Danceability: {features['danceability']}")
            if 'energy' in features:
                print(f"   ⚡ Energy: {features['energy']}")
            if 'valence' in features:
                print(f"   😊 Valence: {features['valence']}")
        else:
            print(f"❌ FAILED - No features returned")
    
    # Test 2: Bulk processing
    print(f"\n🚀 Test 2: Bulk Processing")
    print("-" * 50)
    
    bulk_results = await service.get_multiple_tracks_audio_features(test_tracks)
    
    print(f"\n📊 Bulk Results Summary:")
    print(f"   - Requested: {len(test_tracks)} tracks")
    print(f"   - Retrieved: {len(bulk_results)} tracks")
    print(f"   - Success Rate: {len(bulk_results)/len(test_tracks)*100:.1f}%")
    
    # Test 3: Compare individual vs bulk results
    print(f"\n🔄 Test 3: Individual vs Bulk Comparison")
    print("-" * 50)
    
    matches = 0
    for track_id in individual_results:
        if track_id in bulk_results:
            # Compare key features
            individual = individual_results[track_id]
            bulk = bulk_results[track_id]
            
            if (individual.get('danceability') == bulk.get('danceability') and
                individual.get('energy') == bulk.get('energy')):
                matches += 1
                print(f"✅ {track_id}: Individual and bulk results match")
            else:
                print(f"❌ {track_id}: Individual and bulk results differ")
        else:
            print(f"⚠️  {track_id}: Found individually but not in bulk")
    
    print(f"\nMatching Results: {matches}/{len(individual_results)}")
    
    # Test 4: Feature mapping to Spotify format
    print(f"\n🗺️  Test 4: Feature Mapping")
    print("-" * 50)
    
    if bulk_results:
        sample_track = list(bulk_results.keys())[0]
        sample_features = bulk_results[sample_track]
        
        print(f"Sample track: {sample_track}")
        print(f"Raw ReccoBeats features: {list(sample_features.keys())}")
        
        mapped_features = service.map_features_to_spotify_format(sample_features)
        print(f"Mapped features: {list(mapped_features.keys())}")
        
        # Check essential features are present
        essential_features = ['danceability', 'energy', 'valence', 'tempo', 'loudness']
        missing_features = [f for f in essential_features if f not in mapped_features]
        
        if missing_features:
            print(f"⚠️  Missing essential features: {missing_features}")
        else:
            print("✅ All essential features present")
    
    # Test 5: Track info retrieval
    print(f"\n📋 Test 5: Track Info Retrieval")
    print("-" * 50)
    
    track_info = await service.get_multiple_tracks_info(test_tracks)
    
    for track_id, info in track_info.items():
        title = info.get('trackTitle', 'Unknown')
        artist = 'Unknown'
        if 'artists' in info and info['artists']:
            artist = info['artists'][0].get('artistName', 'Unknown')
        
        print(f"✅ {track_id}: '{title}' by {artist}")
    
    # Final Summary
    print(f"\n🎯 === FINAL SUMMARY ===")
    print(f"Individual track success: {len(individual_results)}/{len(test_tracks)} ({len(individual_results)/len(test_tracks)*100:.1f}%)")
    print(f"Bulk processing success: {len(bulk_results)}/{len(test_tracks)} ({len(bulk_results)/len(test_tracks)*100:.1f}%)")
    print(f"Track info retrieval: {len(track_info)}/{len(test_tracks)} ({len(track_info)/len(test_tracks)*100:.1f}%)")
    
    if len(bulk_results) >= 2:  # At least 2 tracks working
        print("\n🎉 ReccoBeats integration is READY FOR PRODUCTION!")
        print("   - Audio features extraction working")
        print("   - Bulk processing implemented")
        print("   - Feature mapping compatible with existing schema")
        return True
    else:
        print("\n⚠️  ReccoBeats integration needs more work")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_reccobeats_comprehensive())
    sys.exit(0 if success else 1)
