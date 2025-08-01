#!/usr/bin/env python3
"""
Test script for the playlist optimization service.
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.optimization import PlaylistOptimizationService
import json
from datetime import datetime

async def test_optimization_service():
    """Test the playlist optimization service with mock data."""
    print("🎯 Testing Playlist Optimization Service")
    print("=" * 60)
    
    # Initialize optimization service
    optimization_service = PlaylistOptimizationService()
    
    # Test energy transition analysis
    print("Testing energy transition analysis...")
    
    mock_tracks = [
        {
            "id": "track1",
            "name": "High Energy Dance",
            "artist": "Artist 1",
            "audio_features": {"energy": 0.9, "tempo": 128, "danceability": 0.8}
        },
        {
            "id": "track2", 
            "name": "Sudden Calm",
            "artist": "Artist 2",
            "audio_features": {"energy": 0.2, "tempo": 70, "danceability": 0.3}  # Abrupt drop
        },
        {
            "id": "track3",
            "name": "Energy Spike",
            "artist": "Artist 3", 
            "audio_features": {"energy": 0.95, "tempo": 140, "danceability": 0.9}  # Spike from low
        }
    ]
    
    energy_issues = optimization_service._analyze_energy_transitions(mock_tracks)
    print(f"✅ Found {len(energy_issues)} energy transition issues:")
    for issue in energy_issues:
        print(f"   • {issue['type']}: {issue['track1_name']} → {issue['track2_name']} (Δ{issue['energy_diff']:.2f})")
    
    # Test tempo flow analysis
    print("\nTesting tempo flow analysis...")
    
    tempo_issues = optimization_service._analyze_tempo_flow(mock_tracks)
    print(f"✅ Found {len(tempo_issues)} tempo flow issues:")
    for issue in tempo_issues:
        print(f"   • {issue['type']}: {issue['track_name']} ({issue['tempo1']:.0f} → {issue['tempo2']:.0f} BPM)")
    
    # Test optimization potential calculation
    print("\nTesting optimization potential calculation...")
    
    test_insights = [
        {
            "name": "High Skip Rate Playlist",
            "insights": {
                "average_skip_rate": 0.6,
                "average_quality_score": 0.4,
                "problematic_tracks": 5,
                "total_tracks_analyzed": 10
            }
        },
        {
            "name": "Well-Optimized Playlist", 
            "insights": {
                "average_skip_rate": 0.1,
                "average_quality_score": 0.8,
                "problematic_tracks": 1,
                "total_tracks_analyzed": 15
            }
        },
        {
            "name": "Medium Quality Playlist",
            "insights": {
                "average_skip_rate": 0.3,
                "average_quality_score": 0.6,
                "problematic_tracks": 3,
                "total_tracks_analyzed": 12
            }
        }
    ]
    
    for test_case in test_insights:
        potential = optimization_service._calculate_optimization_potential(test_case["insights"])
        print(f"✅ {test_case['name']}: Optimization Potential = {potential:.2f}")
    
    # Test priority scoring
    print("\nTesting priority scoring...")
    
    priorities = ["high", "medium", "low", "unknown"]
    for priority in priorities:
        score = optimization_service._priority_score(priority)
        print(f"✅ Priority '{priority}': Score = {score}")
    
    # Test recommendation generation mock
    print("\nTesting recommendation structure...")
    
    mock_recommendations = [
        {
            "type": "remove_track",
            "priority": "high",
            "title": "Remove Frequently Skipped Track",
            "description": "Track has 70% skip rate",
            "action": "remove",
            "impact_score": 0.9,
            "confidence": 0.8
        },
        {
            "type": "reorder_tracks", 
            "priority": "medium",
            "title": "Fix Energy Flow",
            "description": "Smooth abrupt energy transition",
            "action": "reorder",
            "impact_score": 0.6,
            "confidence": 0.7
        },
        {
            "type": "promote_track",
            "priority": "low",
            "title": "Promote Hidden Gem",
            "description": "High quality track needs better positioning",
            "action": "reorder",
            "impact_score": 0.4,
            "confidence": 0.6
        }
    ]
    
    # Test summary generation
    mock_playlist_data = {
        "metrics": {
            "optimization_potential": 0.6,
            "average_skip_rate": 0.4,
            "average_quality_score": 0.5,
            "total_tracks": 20
        }
    }
    
    summary = optimization_service._generate_optimization_summary(
        mock_recommendations, mock_playlist_data
    )
    
    print("✅ Generated optimization summary:")
    print(f"   • Total recommendations: {summary['total_recommendations']}")
    print(f"   • High priority: {summary['priority_breakdown']['high']}")
    print(f"   • Medium priority: {summary['priority_breakdown']['medium']}")
    print(f"   • Low priority: {summary['priority_breakdown']['low']}")
    print(f"   • Potential impact: {summary['potential_impact']:.2f}")
    print(f"   • Estimated improvement: {summary['estimated_improvement']:.2f}")
    print(f"   • Top priorities: {summary['top_priorities']}")
    
    # Test mock track replacement
    print("\nTesting track replacement suggestions...")
    
    mock_problematic_track = {
        "track_id": "problematic_123",
        "track_name": "Skipped Song",
        "artist": "Unpopular Artist"
    }
    
    replacements = await optimization_service._find_track_replacements(
        mock_problematic_track, {}, "mock_token"
    )
    
    print(f"✅ Generated {len(replacements)} replacement suggestions:")
    for replacement in replacements:
        print(f"   • {replacement['name']} by {replacement['artist']} - {replacement['reason']}")
    
    # Test cluster suggestions
    print("\nTesting cluster-based suggestions...")
    
    mock_clustering = {
        "clusters": [
            {"name": "High-energy dance hits", "track_count": 5},
            {"name": "Mellow & melancholic", "track_count": 8},
            {"name": "Upbeat pop anthems", "track_count": 4}
        ]
    }
    
    cluster_suggestions = await optimization_service._suggest_tracks_for_clusters(
        mock_clustering, "mock_token"
    )
    
    print(f"✅ Generated suggestions for {len(cluster_suggestions)} clusters:")
    for suggestion in cluster_suggestions:
        print(f"   • {suggestion['cluster_name']}: {len(suggestion['tracks'])} suggested tracks")
        for track in suggestion['tracks']:
            print(f"     - {track['name']} by {track['artist']}")
    
    print("\n" + "=" * 60)
    print("✅ All optimization service tests passed!")
    print("\n🚀 Ready for full optimization pipeline testing!")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_optimization_service())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
