#!/usr/bin/env python3
"""
Test script to verify JSON serialization of ClusterData objects is working correctly.
"""
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from backend.schemas import ClusterData

def test_cluster_data_serialization():
    """Test that ClusterData objects can be properly serialized to JSON."""
    
    # Create a sample ClusterData object
    cluster_data = ClusterData(
        cluster_id=1,
        track_count=5,
        center_features={
            "danceability": 0.7,
            "energy": 0.8,
            "valence": 0.6,
            "tempo": 120.0
        },
        track_ids=[1, 2, 3, 4, 5]
    )
    
    print("🧪 Testing ClusterData JSON serialization...")
    
    try:
        # Convert to dictionary first (the fix)
        cluster_dict = cluster_data.model_dump()
        print(f"✅ ClusterData.model_dump() works: {type(cluster_dict)}")
        
        # Now serialize to JSON
        json_string = json.dumps(cluster_dict)
        print(f"✅ JSON serialization works: {len(json_string)} characters")
        
        # Test deserializing back
        parsed_data = json.loads(json_string)
        print(f"✅ JSON deserialization works: {type(parsed_data)}")
        
        # Test creating new ClusterData from parsed data
        restored_cluster = ClusterData(**parsed_data)
        print(f"✅ ClusterData recreation works: cluster_id={restored_cluster.cluster_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_list_serialization():
    """Test serializing a list of ClusterData objects (what the endpoint does)."""
    
    # Create a list of ClusterData objects
    clusters = [
        ClusterData(
            cluster_id=1,
            track_count=5,
            center_features={"danceability": 0.7, "energy": 0.8},
            track_ids=[1, 2, 3, 4, 5]
        ),
        ClusterData(
            cluster_id=2,
            track_count=3,
            center_features={"danceability": 0.3, "energy": 0.4},
            track_ids=[6, 7, 8]
        )
    ]
    
    print("\n🧪 Testing List[ClusterData] JSON serialization...")
    
    try:
        # Convert list to dictionaries (the fix)
        clusters_dict = [cluster.model_dump() for cluster in clusters]
        print(f"✅ List comprehension works: {len(clusters_dict)} clusters")
        
        # Serialize complex structure like in the endpoint
        analysis_data = json.dumps({
            "clusters": clusters_dict,
            "silhouette_score": 0.75,
            "analysis_metadata": {"method": "kmeans", "n_clusters": 2}
        })
        print(f"✅ Complex JSON serialization works: {len(analysis_data)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ List serialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing JSON serialization fixes for ClusterData...\n")
    
    test1_passed = test_cluster_data_serialization()
    test2_passed = test_list_serialization()
    
    if test1_passed and test2_passed:
        print("\n🎉 All JSON serialization tests passed!")
        print("  ✅ ClusterData objects can be serialized to JSON")
        print("  ✅ List[ClusterData] can be serialized to JSON")
        print("  ✅ /analyze endpoint should now work without TypeError")
    else:
        print("\n❌ Some tests failed - check the implementations")
