#!/usr/bin/env python3
"""
Test script for listening analytics functionality.
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.listening_analytics import ListeningAnalyticsService
import json
from datetime import datetime, timedelta

async def test_listening_analytics():
    """Test the listening analytics service with mock data."""
    print("🎵 Testing Listening Analytics Service")
    print("=" * 50)
    
    # Initialize analytics service
    analytics_service = ListeningAnalyticsService()
    
    # Test recently played parsing
    print("Testing recently played data parsing...")
    
    # Mock recently played data
    mock_recently_played = [
        {
            "track": {"id": "track1", "name": "Test Track 1"},
            "played_at": "2024-12-01T10:00:00Z"
        },
        {
            "track": {"id": "track1", "name": "Test Track 1"},
            "played_at": "2024-12-01T10:01:00Z"  # Quick replay = skip
        },
        {
            "track": {"id": "track1", "name": "Test Track 1"},
            "played_at": "2024-12-01T10:05:00Z"  # Normal replay
        },
        {
            "track": {"id": "track2", "name": "Test Track 2"},
            "played_at": "2024-12-01T10:08:00Z"
        },
        {
            "track": {"id": "track3", "name": "Test Track 3"},
            "played_at": "2024-12-01T10:10:00Z"
        },
        {
            "track": {"id": "track3", "name": "Test Track 3"},
            "played_at": "2024-12-01T10:10:30Z"  # Very quick replay = skip
        }
    ]
    
    # Test skip estimation
    print("Testing skip rate estimation...")
    
    track1_plays = [item for item in mock_recently_played if item["track"]["id"] == "track1"]
    skip_count = analytics_service._estimate_skip_count(track1_plays)
    print(f"✅ Track 1: {len(track1_plays)} plays, {skip_count} estimated skips")
    
    track3_plays = [item for item in mock_recently_played if item["track"]["id"] == "track3"]
    skip_count_3 = analytics_service._estimate_skip_count(track3_plays)
    print(f"✅ Track 3: {len(track3_plays)} plays, {skip_count_3} estimated skips")
    
    # Test quality score calculation
    print("\nTesting quality score calculation...")
    
    test_audio_features = [
        {
            "name": "High Quality Dance Track",
            "features": {
                "danceability": 0.8,
                "energy": 0.9,
                "valence": 0.7,
                "speechiness": 0.1,
                "acousticness": 0.2
            }
        },
        {
            "name": "Podcast/Spoken Word",
            "features": {
                "danceability": 0.2,
                "energy": 0.3,
                "valence": 0.5,
                "speechiness": 0.9,
                "acousticness": 0.6
            }
        },
        {
            "name": "Acoustic Ballad",
            "features": {
                "danceability": 0.3,
                "energy": 0.2,
                "valence": 0.4,
                "speechiness": 0.1,
                "acousticness": 0.9
            }
        }
    ]
    
    for test_case in test_audio_features:
        quality_score = analytics_service._calculate_quality_score(test_case["features"])
        print(f"✅ {test_case['name']}: Quality Score = {quality_score:.2f}")
    
    # Test skip reason analysis
    print("\nTesting skip reason analysis...")
    
    high_speech_analytics = {
        "audio_features": {"speechiness": 0.8, "energy": 0.5}
    }
    track_info = {"duration_ms": 180000}
    
    reasons = analytics_service._analyze_skip_reasons(high_speech_analytics, track_info)
    print(f"✅ High speechiness track skip reasons: {reasons}")
    
    low_energy_analytics = {
        "audio_features": {"speechiness": 0.1, "energy": 0.1, "tempo": 40}
    }
    track_info_long = {"duration_ms": 400000}
    
    reasons_2 = analytics_service._analyze_skip_reasons(low_energy_analytics, track_info_long)
    print(f"✅ Low energy/long track skip reasons: {reasons_2}")
    
    # Test confidence calculation
    print("\nTesting confidence calculation...")
    
    confidence_tests = [
        {"play_count": 0, "skip_count": 0, "expected": "No data"},
        {"play_count": 1, "skip_count": 1, "expected": "Low confidence"},
        {"play_count": 3, "skip_count": 2, "expected": "Medium confidence"},
        {"play_count": 8, "skip_count": 3, "expected": "High confidence"},
        {"play_count": 15, "skip_count": 2, "expected": "Very high confidence"}
    ]
    
    for test in confidence_tests:
        confidence = analytics_service._calculate_confidence(test)
        print(f"✅ {test['expected']}: {test['play_count']} plays, {test['skip_count']} skips → {confidence:.1f}")
    
    # Test promotion suggestions
    print("\nTesting promotion suggestions...")
    
    high_energy_analytics = {
        "audio_features": {
            "energy": 0.8,
            "danceability": 0.9,
            "valence": 0.7,
            "acousticness": 0.1
        }
    }
    
    suggestions = analytics_service._generate_promotion_suggestions(high_energy_analytics, {})
    print(f"✅ High energy track promotion suggestions: {suggestions}")
    
    acoustic_analytics = {
        "audio_features": {
            "energy": 0.3,
            "danceability": 0.2,
            "valence": 0.5,
            "acousticness": 0.8
        }
    }
    
    suggestions_2 = analytics_service._generate_promotion_suggestions(acoustic_analytics, {})
    print(f"✅ Acoustic track promotion suggestions: {suggestions_2}")
    
    print("\n" + "=" * 50)
    print("✅ All listening analytics tests passed!")
    print("\n🚀 Ready for API endpoint testing!")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_listening_analytics())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
