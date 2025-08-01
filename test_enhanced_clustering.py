#!/usr/bin/env python3
"""
Comprehensive test and demonstration of the enhanced clustering system.
This script showcases all the improvements implemented for meaningful cluster interpretation.
"""
import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.clustering import ClusteringService
from backend.services.audio_features import AudioFeaturesService
from backend.models import Track
from backend.schemas import ClusterData


def create_diverse_test_tracks():
    """Create a diverse set of test tracks with varied audio features for clustering demo."""
    tracks = [
        # High-energy dance hits
        Track(id=1, name="Upbeat Dance Track", artist="DJ Energy", spotify_track_id="1", 
              danceability=0.9, energy=0.95, valence=0.85, tempo=128, loudness=-3.5,
              acousticness=0.1, instrumentalness=0.0, speechiness=0.05, liveness=0.2),
        
        Track(id=2, name="Party Anthem", artist="Club Master", spotify_track_id="2",
              danceability=0.85, energy=0.9, valence=0.8, tempo=132, loudness=-4.0,
              acousticness=0.15, instrumentalness=0.0, speechiness=0.08, liveness=0.25),
        
        # Mellow acoustic tracks
        Track(id=3, name="Quiet Reflection", artist="Folk Singer", spotify_track_id="3",
              danceability=0.3, energy=0.2, valence=0.3, tempo=80, loudness=-12.0,
              acousticness=0.9, instrumentalness=0.0, speechiness=0.03, liveness=0.1),
        
        Track(id=4, name="Campfire Song", artist="Acoustic Duo", spotify_track_id="4",
              danceability=0.4, energy=0.25, valence=0.45, tempo=75, loudness=-10.0,
              acousticness=0.85, instrumentalness=0.0, speechiness=0.04, liveness=0.15),
        
        # Instrumental electronic
        Track(id=5, name="Synth Journey", artist="Electronic Producer", spotify_track_id="5",
              danceability=0.7, energy=0.8, valence=0.6, tempo=110, loudness=-6.0,
              acousticness=0.1, instrumentalness=0.9, speechiness=0.02, liveness=0.05),
        
        Track(id=6, name="Ambient Soundscape", artist="Sound Designer", spotify_track_id="6",
              danceability=0.2, energy=0.3, valence=0.5, tempo=95, loudness=-8.0,
              acousticness=0.2, instrumentalness=0.95, speechiness=0.01, liveness=0.08),
        
        # Intense rock/aggressive
        Track(id=7, name="Heavy Metal Thunder", artist="Metal Band", spotify_track_id="7",
              danceability=0.5, energy=0.95, valence=0.2, tempo=145, loudness=-2.0,
              acousticness=0.05, instrumentalness=0.7, speechiness=0.1, liveness=0.4),
        
        Track(id=8, name="Punk Energy", artist="Punk Rockers", spotify_track_id="8",
              danceability=0.6, energy=0.9, valence=0.25, tempo=150, loudness=-3.0,
              acousticness=0.02, instrumentalness=0.3, speechiness=0.15, liveness=0.45),
        
        # Feel-good pop
        Track(id=9, name="Sunshine Pop", artist="Happy Band", spotify_track_id="9",
              danceability=0.75, energy=0.7, valence=0.9, tempo=120, loudness=-5.0,
              acousticness=0.3, instrumentalness=0.0, speechiness=0.06, liveness=0.2),
        
        Track(id=10, name="Feel Good Vibes", artist="Pop Star", spotify_track_id="10",
               danceability=0.8, energy=0.75, valence=0.85, tempo=115, loudness=-4.5,
               acousticness=0.25, instrumentalness=0.0, speechiness=0.08, liveness=0.18),
        
        # Sad ballads
        Track(id=11, name="Heartbreak Ballad", artist="Emotional Singer", spotify_track_id="11",
              danceability=0.25, energy=0.15, valence=0.1, tempo=65, loudness=-15.0,
              acousticness=0.7, instrumentalness=0.0, speechiness=0.03, liveness=0.1),
        
        Track(id=12, name="Melancholy Blues", artist="Blues Artist", spotify_track_id="12",
              danceability=0.3, energy=0.2, valence=0.15, tempo=70, loudness=-12.0,
              acousticness=0.6, instrumentalness=0.2, speechiness=0.04, liveness=0.25),
    ]
    
    # Set required attributes for all tracks
    for track in tracks:
        track.features_imputed = False
        track.playlist_id = 1
        
    return tracks


async def demonstrate_clustering_enhancements():
    """Comprehensive demonstration of all clustering enhancements."""
    print("🎵 === Enhanced Clustering System Demonstration ===")
    print("This demo showcases all implemented improvements for meaningful cluster interpretation")
    print("=" * 80)
    
    # Create diverse test tracks
    tracks = create_diverse_test_tracks()
    print(f"📊 Created {len(tracks)} diverse test tracks")
    
    # Initialize services
    audio_service = AudioFeaturesService()
    clustering_service = ClusteringService(audio_service)
    
    # Demonstrate enhanced preprocessing
    print(f"\n🔧 Enhanced Feature Preprocessing:")
    print("-" * 40)
    
    features, preprocessing_info = clustering_service._preprocess_features(tracks)
    print(f"✅ Feature matrix shape: {features.shape}")
    print(f"✅ Log-scaled features: {preprocessing_info.get('log_scaled_features', [])}")
    print(f"✅ Feature weights applied: {dict(clustering_service.FEATURE_WEIGHTS)}")
    print(f"✅ Outliers detected: {preprocessing_info.get('outlier_count', 0)}")
    
    # Test all clustering algorithms
    algorithms = ["kmeans", "dbscan", "gaussian_mixture", "spectral"]
    results = {}
    
    print(f"\n🤖 Testing Multiple Clustering Algorithms:")
    print("=" * 50)
    
    for algorithm in algorithms:
        try:
            print(f"\n🔬 Algorithm: {algorithm.upper()}")
            print("-" * 30)
            
            clusters, silhouette_score, metadata = clustering_service.cluster_tracks(
                tracks, method=algorithm
            )
            
            results[algorithm] = {
                "clusters": clusters,
                "silhouette_score": silhouette_score,
                "metadata": metadata
            }
            
            print(f"✅ Success: {len(clusters)} clusters found")
            print(f"📊 Silhouette Score: {silhouette_score:.3f}")
            print(f"🏷️  Interpretable Cluster Labels:")
            
            for cluster in clusters:
                print(f"   • Cluster {cluster.cluster_id}: '{cluster.label}' ({cluster.track_count} tracks)")
                
                # Show key features for interpretation
                center = cluster.center_features
                key_features = []
                if center.get("energy", 0) > 0.7:
                    key_features.append(f"High Energy ({center['energy']:.2f})")
                if center.get("valence", 0) > 0.7:
                    key_features.append(f"Positive Mood ({center['valence']:.2f})")
                if center.get("acousticness", 0) > 0.6:
                    key_features.append(f"Acoustic ({center['acousticness']:.2f})")
                if center.get("danceability", 0) > 0.7:
                    key_features.append(f"Danceable ({center['danceability']:.2f})")
                
                if key_features:
                    print(f"     Features: {', '.join(key_features)}")
            
            # Show algorithm-specific metrics
            algo_info = metadata.get("algorithm", {})
            quality_metrics = metadata.get("quality_metrics", {})
            
            print(f"📈 Quality Metrics:")
            if "calinski_harabasz_score" in quality_metrics:
                print(f"   Calinski-Harabasz: {quality_metrics['calinski_harabasz_score']:.2f}")
            if "noise_points" in quality_metrics:
                print(f"   Noise points: {quality_metrics['noise_points']}")
                
        except Exception as e:
            print(f"❌ {algorithm} failed: {e}")
            results[algorithm] = None
    
    # Find best algorithm based on silhouette score
    best_algorithm = None
    best_score = -1
    for algo, result in results.items():
        if result and result["silhouette_score"] > best_score:
            best_score = result["silhouette_score"]
            best_algorithm = algo
    
    if best_algorithm:
        print(f"\n🏆 Best Algorithm: {best_algorithm.upper()} (Silhouette: {best_score:.3f})")
        best_clusters = results[best_algorithm]["clusters"]
        
        # Demonstrate enhanced optimization suggestions
        print(f"\n💡 Enhanced Optimization Suggestions:")
        print("-" * 40)
        
        suggestions = clustering_service.generate_optimization_suggestions(tracks, best_clusters)
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion.suggestion_type.replace('_', ' ').title()}:")
            print(f"   📝 {suggestion.description}")
            print(f"   🎯 Confidence: {suggestion.confidence_score:.1%}")
            print(f"   🎵 Affects: {len(suggestion.affected_tracks)} tracks")
        
        # Demonstrate PCA visualization coordinates
        print(f"\n📊 PCA Visualization Coordinates:")
        print("-" * 35)
        
        pca_coords = clustering_service.get_pca_coordinates(tracks)
        print(f"✅ Generated coordinates for {len(pca_coords)} tracks")
        
        # Group coordinates by cluster for visualization
        track_to_cluster = {}
        for cluster in best_clusters:
            for track_id in cluster.track_ids:
                track_to_cluster[track_id] = cluster
        
        print(f"\nSample coordinates by cluster:")
        for coord in pca_coords[:6]:  # Show first 6
            cluster = track_to_cluster.get(coord["track_id"])
            cluster_label = cluster.label if cluster else "Unknown"
            print(f"   {coord['name'][:25]:25} | Cluster: {cluster_label:20} | ({coord['x']:6.2f}, {coord['y']:6.2f})")
    
    # Demonstrate comprehensive analysis metadata
    print(f"\n📋 Comprehensive Analysis Metadata:")
    print("-" * 40)
    
    if best_algorithm and results[best_algorithm]:
        metadata = results[best_algorithm]["metadata"]
        
        print("Feature Importance Weights:")
        for feature, weight in metadata.get("feature_importance", {}).items():
            print(f"   {feature:15}: {weight:.1f}")
        
        print(f"\nPreprocessing Information:")
        preprocessing = metadata.get("preprocessing", {})
        print(f"   Log-scaled features: {len(preprocessing.get('log_scaled_features', []))}")
        print(f"   Outlier detection: {preprocessing.get('outlier_count', 0)} points")
        
        print(f"\nQuality Metrics Summary:")
        quality = metadata.get("quality_metrics", {})
        for metric, value in quality.items():
            if isinstance(value, (int, float)):
                print(f"   {metric:20}: {value:.3f}")
            else:
                print(f"   {metric:20}: {value}")
    
    print(f"\n🎉 === Enhanced Clustering Demonstration Complete ===")
    print("Key improvements implemented:")
    print("✅ Multiple clustering algorithms (K-Means, DBSCAN, Gaussian Mixture, Spectral)")
    print("✅ Smart preprocessing with log-scaling and feature weighting")
    print("✅ Automatic optimal cluster detection")
    print("✅ Interpretable cluster labels based on audio characteristics")
    print("✅ Enhanced optimization suggestions using cluster semantics")
    print("✅ Comprehensive analysis metadata and quality metrics")
    print("✅ Improved PCA visualization with better normalization")


if __name__ == "__main__":
    asyncio.run(demonstrate_clustering_enhancements())
