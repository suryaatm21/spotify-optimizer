#!/usr/bin/env python3
"""
Test script to verify the schema validation fixes for AnalysisResponse.
"""
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from backend.schemas import AnalysisResponse, ClusterData, DataQualityReport
from datetime import datetime

def test_analysis_response_validation():
    """Test that AnalysisResponse can handle the new data structure correctly."""
    
    print("🧪 Testing AnalysisResponse schema validation...")
    
    # Sample ClusterData objects
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
    
    # Sample DataQualityReport
    data_quality = DataQualityReport(
        total_tracks=8,
        overall_completeness=0.75,
        feature_quality={"danceability": {"completeness": 1.0}, "energy": {"completeness": 0.5}},
        recommendation="Some features need improvement"
    )
    
    # Sample PCA coordinates with mixed types (Dict[str, Any])
    pca_coordinates = [
        {
            "track_id": 1,
            "x": 0.5,
            "y": -0.3,
            "name": "Test Song",
            "artist": "Test Artist"
        },
        {
            "track_id": 2,
            "x": -0.2,
            "y": 0.7,
            "name": "Another Song",
            "artist": "Another Artist"
        }
    ]
    
    try:
        # Test creating AnalysisResponse
        response = AnalysisResponse(
            id=1,
            playlist_id=5,
            cluster_count=2,
            cluster_method="kmeans",
            silhouette_score=0.75,
            clusters=clusters,
            data_quality=data_quality,
            analysis_metadata={"method": "kmeans", "n_clusters": 2},
            pca_coordinates=pca_coordinates,
            created_at=datetime.now()
        )
        
        print("✅ AnalysisResponse validation successful!")
        print(f"   Clusters: {len(response.clusters)}")
        print(f"   Data quality completeness: {response.data_quality.overall_completeness:.1%}")
        print(f"   PCA coordinates: {len(response.pca_coordinates)} points")
        print(f"   First PCA point: {response.pca_coordinates[0]}")
        
        # Test JSON serialization
        response_dict = response.model_dump()
        json_string = json.dumps(response_dict, default=str)
        print(f"✅ JSON serialization successful: {len(json_string)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ AnalysisResponse validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing schema validation fixes...\n")
    
    success = test_analysis_response_validation()
    
    if success:
        print("\n🎉 All schema validation tests passed!")
        print("  ✅ AnalysisResponse handles mixed PCA coordinate types")
        print("  ✅ DataQualityReport validation working")
        print("  ✅ JSON serialization working")
        print("  ✅ /analyze endpoint should now work without validation errors")
    else:
        print("\n❌ Schema validation tests failed - check the implementations")
