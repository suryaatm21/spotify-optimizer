#!/usr/bin/env python3
"""
Enhanced debug script to test the complete audio features pipeline with real database tracks.
Tests the new clustering enhancements including multiple algorithms and interpretable labels.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.dependencies import SessionLocal
from backend.models import Track
from backend.services.audio_features import AudioFeaturesService
from backend.services.clustering import ClusteringService


async def debug_enhanced_clustering_pipeline():
    """Debug the enhanced audio features and clustering pipeline."""
    print("🔍 Enhanced Audio Features & Clustering Pipeline Debug")
    print("=" * 55)
    
    db = SessionLocal()
    
    try:
        # Get tracks from database
        tracks = db.query(Track).limit(10).all()  # Get more tracks for better clustering
        
        if not tracks:
            print("❌ No tracks found in database")
            return
        
        print(f"📊 Found {len(tracks)} tracks to test")
        
        # Initialize services
        audio_service = AudioFeaturesService()
        clustering_service = ClusteringService(audio_service)
        
        # Show initial state
        print(f"\n🔍 Initial Track Analysis:")
        for i, track in enumerate(tracks[:3]):  # Show first 3
            print(f"\nTrack {i+1}: {track.name[:40]}...")
            print(f"  Spotify ID: {track.spotify_track_id}")
            
            missing_features = []
            for feature in audio_service.AUDIO_FEATURES:
                value = getattr(track, feature)
                if value is None:
                    missing_features.append(feature)
                else:
                    print(f"  {feature}: {value}")
            
            if missing_features:
                print(f"  Missing: {', '.join(missing_features)}")
        
        # Test enhanced audio features preparation
        print(f"\n🔄 Testing Enhanced Audio Features Pipeline...")
        prepared_tracks, quality_report = await clustering_service.prepare_tracks_for_analysis(tracks, db)
        
        print(f"📈 Data Quality Report:")
        print(f"  Initial completeness: {quality_report['initial_quality']['overall_completeness']:.1%}")
        print(f"  Final completeness: {quality_report['final_quality']['overall_completeness']:.1%}")
        print(f"  Improvement: {quality_report['improvement']:.1%}")
        
        # Test multiple clustering algorithms
        clustering_methods = ["kmeans", "dbscan", "gaussian_mixture", "spectral"]
        
        print(f"\n🤖 Testing Enhanced Clustering Algorithms:")
        print("-" * 50)
        
        for method in clustering_methods:
            try:
                print(f"\n🔬 Testing {method.upper()}:")
                
                clusters, silhouette_score, metadata = clustering_service.cluster_tracks(
                    prepared_tracks, 
                    method=method,
                    quality_report=quality_report
                )
                
                print(f"  ✅ Success - {len(clusters)} clusters found")
                print(f"  📊 Silhouette Score: {silhouette_score:.3f}")
                print(f"  🏷️  Cluster Labels:")
                
                for cluster in clusters[:3]:  # Show first 3 clusters
                    label = cluster.label or "Unlabeled"
                    print(f"    • Cluster {cluster.cluster_id}: '{label}' ({cluster.track_count} tracks)")
                
                # Show algorithm-specific metadata
                algo_info = metadata.get("algorithm", {})
                if "n_clusters" in algo_info:
                    print(f"  🔧 Clusters detected: {algo_info['n_clusters']}")
                if "eps" in algo_info:
                    print(f"  � DBSCAN eps: {algo_info['eps']:.3f}")
                if "aic" in algo_info:
                    print(f"  🔧 Gaussian AIC: {algo_info['aic']:.1f}")
                
                print(f"  📈 Quality Metrics:")
                quality_metrics = metadata.get("quality_metrics", {})
                for metric, value in quality_metrics.items():
                    if isinstance(value, float):
                        print(f"    {metric}: {value:.3f}")
                    else:
                        print(f"    {metric}: {value}")
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
        
        # Test enhanced preprocessing visualization
        print(f"\n📊 Enhanced Feature Preprocessing Analysis:")
        print("-" * 50)
        
        try:
            features, preprocessing_info = clustering_service._preprocess_features(prepared_tracks)
            
            print(f"Feature matrix shape: {features.shape}")
            print(f"Log-scaled features: {preprocessing_info.get('log_scaled_features', [])}")
            print(f"Outlier count: {preprocessing_info.get('outlier_count', 0)}")
            
            # Show feature ranges
            feature_ranges = preprocessing_info.get('feature_ranges', {})
            print(f"\nFeature Ranges:")
            for feature, ranges in list(feature_ranges.items())[:5]:  # Show first 5
                print(f"  {feature}: {ranges['min']:.3f} - {ranges['max']:.3f} (mean: {ranges['mean']:.3f})")
                
        except Exception as e:
            print(f"❌ Preprocessing analysis failed: {e}")
        
        # Test PCA coordinates for visualization
        print(f"\n📈 PCA Visualization Coordinates:")
        print("-" * 40)
        
        try:
            pca_coords = clustering_service.get_pca_coordinates(prepared_tracks)
            print(f"Generated PCA coordinates for {len(pca_coords)} tracks")
            
            if pca_coords:
                # Show sample coordinates
                print("Sample coordinates:")
                for coord in pca_coords[:3]:
                    print(f"  {coord['name'][:20]}: ({coord['x']:.3f}, {coord['y']:.3f})")
        
        except Exception as e:
            print(f"❌ PCA coordinates failed: {e}")
        
        # Test optimization suggestions with labels
        print(f"\n💡 Enhanced Optimization Suggestions:")
        print("-" * 45)
        
        try:
            # Use kmeans for suggestions (most reliable)
            clusters, _, _ = clustering_service.cluster_tracks(prepared_tracks, method="kmeans")
            suggestions = clustering_service.generate_optimization_suggestions(prepared_tracks, clusters)
            
            print(f"Generated {len(suggestions)} suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"\n{i}. {suggestion.suggestion_type.title()}:")
                print(f"   {suggestion.description}")
                print(f"   Confidence: {suggestion.confidence_score:.1%}")
                print(f"   Affects {len(suggestion.affected_tracks)} tracks")
        
        except Exception as e:
            print(f"❌ Suggestions failed: {e}")
        
        print(f"\n🎉 Enhanced Clustering Pipeline Test Complete!")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(debug_enhanced_clustering_pipeline())
