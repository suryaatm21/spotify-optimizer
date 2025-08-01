#!/usr/bin/env python3
"""
Test script to verify that the /analyze endpoint is now working correctly after fixes.
"""
import requests
import json
from pathlib import Path

def test_analyze_endpoint():
    """Test the analyze endpoint with a real request."""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing /analyze endpoint after JSON serialization fixes...\n")
    
    # First, test if the server is running
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not accessible: {e}")
        return False
    
    # Test the analyze endpoint
    try:
        # Sample request payload
        analyze_payload = {
            "playlist_id": 5,
            "cluster_method": "kmeans",
            "cluster_count": 3,
            "fetch_missing_features": True
        }
        
        print(f"📡 Sending POST request to /api/analytics/playlists/5/analyze")
        print(f"   Payload: {json.dumps(analyze_payload, indent=2)}")
        
        response = requests.post(
            f"{base_url}/api/analytics/playlists/5/analyze",
            json=analyze_payload,
            timeout=30
        )
        
        print(f"📨 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request successful!")
            
            try:
                response_data = response.json()
                print(f"✅ Response is valid JSON with {len(response_data)} top-level keys")
                
                # Check for expected fields
                expected_fields = ["id", "playlist_id", "clusters", "silhouette_score"]
                for field in expected_fields:
                    if field in response_data:
                        print(f"✅ Response contains '{field}' field")
                    else:
                        print(f"⚠️  Response missing '{field}' field")
                
                if "clusters" in response_data:
                    clusters = response_data["clusters"]
                    print(f"✅ Found {len(clusters)} clusters in response")
                    
                    if clusters and isinstance(clusters[0], dict):
                        print("✅ Clusters are properly serialized as dictionaries")
                        print(f"   Sample cluster keys: {list(clusters[0].keys())}")
                    
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Response is not valid JSON: {e}")
                print(f"   Response text: {response.text[:200]}...")
                return False
                
        elif response.status_code == 500:
            print("❌ Internal Server Error - checking response for details")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Raw error: {response.text[:500]}...")
            return False
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing /analyze endpoint after ClusterData JSON serialization fixes...\n")
    
    success = test_analyze_endpoint()
    
    if success:
        print("\n🎉 Endpoint test passed!")
        print("  ✅ /analyze endpoint working correctly")
        print("  ✅ ClusterData JSON serialization working")
        print("  ✅ No more 'Object of type ClusterData is not JSON serializable' errors")
    else:
        print("\n❌ Endpoint test failed - there may still be issues")
        print("  🔍 Check the server logs for detailed error information")
