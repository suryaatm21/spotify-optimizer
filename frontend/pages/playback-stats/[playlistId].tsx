/**
 * Dynamic route for displaying playlist analysis and statistics.
 * Shows track details, clustering results, and optimization suggestions.
 */
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeft, Play, BarChart3, Loader2, RefreshCw } from 'lucide-react';
import useSWR from 'swr';

import Layout from '@/components/Layout';
import StatsTable from '@/components/StatsTable';
import ClusterChart from '@/components/ClusterChart';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import OptimizationPanel from '@/components/OptimizationPanel';
import { useAuth } from '@/hooks/useAuth';
import { fetcher } from '@/lib/api';
import {
  ITrack,
  IPlaylistStats,
  IAnalysisResult,
  IOptimizationSuggestion,
} from '@/types/playlist';

export default function PlaylistStats() {
  const router = useRouter();
  const { user } = useAuth();
  const [isMounted, setIsMounted] = useState(false);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisMethod, setAnalysisMethod] = useState<'kmeans' | 'dbscan'>(
    'kmeans',
  );
  const [clusterCount, setClusterCount] = useState(3);

  // Ensure component is mounted before using router
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Get playlistId from router when ready
  const playlistId = router.isReady
    ? (router.query.playlistId as string)
    : null;

  // Fetch playlist tracks
  const {
    data: tracks,
    error: tracksError,
    isLoading: tracksLoading,
  } = useSWR<ITrack[]>(
    playlistId ? `/api/analytics/playlists/${playlistId}/tracks` : null,
    fetcher,
  );

  // Fetch playlist statistics
  const {
    data: stats,
    error: statsError,
    isLoading: statsLoading,
  } = useSWR<IPlaylistStats>(
    playlistId ? `/api/analytics/playlists/${playlistId}/stats` : null,
    fetcher,
  );

  // Fetch optimization suggestions - DISABLED to prevent 501 errors from disabled endpoint
  // const {
  //   data: optimizations,
  //   error: optimizationsError,
  //   mutate: refreshOptimizations,
  // } = useSWR<{ suggestions: IOptimizationSuggestion[] }>(
  //   playlistId ? `/api/analytics/playlists/${playlistId}/optimize` : null,
  //   fetcher,
  // );
  const optimizations = null; // Placeholder to prevent UI errors

  const [analysisResult, setAnalysisResult] = useState<IAnalysisResult | null>(
    null,
  );

  const handleAnalyzePlaylist = async () => {
    if (!playlistId) return;

    setIsAnalyzing(true);
    try {
      const response = await fetch(
        `/api/analytics/playlists/${playlistId}/analyze`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            playlist_id: parseInt(playlistId as string),
            cluster_method: analysisMethod,
            cluster_count: clusterCount,
          }),
        },
      );

      if (!response.ok) {
        throw new Error('Failed to analyze playlist');
      }

      const result = await response.json();
      setAnalysisResult(result);
    } catch (error) {
      console.error('Analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleBackToDashboard = () => {
    if (isMounted) {
      router.push('/');
    }
  };

  // Show loading spinner while checking auth or component is mounting
  if (!isMounted) {
    return (
      <Layout title="Loading..." description="Loading playlist analysis data">
        <div className="min-h-screen bg-spotify-gray-900 flex items-center justify-center">
          <LoadingSpinner size="large" />
        </div>
      </Layout>
    );
  }

  // Redirect if not authenticated
  if (!user) {
    if (isMounted) {
      router.push('/');
    }
    return null;
  }

  // Show loading state while router is not ready
  if (!router.isReady || !playlistId) {
    return (
      <Layout title="Loading..." description="Loading playlist analysis data">
        <div className="min-h-screen bg-spotify-gray-900 flex items-center justify-center">
          <LoadingSpinner size="large" />
        </div>
      </Layout>
    );
  }

  // Show loading state
  if (tracksLoading || statsLoading) {
    return (
      <Layout
        title="Loading Playlist..."
        description="Loading playlist analysis data">
        <div className="min-h-screen bg-spotify-gray-900 flex items-center justify-center">
          <LoadingSpinner size="large" />
        </div>
      </Layout>
    );
  }

  // Show error state
  if (tracksError || statsError) {
    return (
      <Layout
        title="Error Loading Playlist"
        description="Failed to load playlist data">
        <div className="min-h-screen bg-spotify-gray-900 flex items-center justify-center">
          <ErrorMessage
            message="Failed to load playlist data. Please try again."
            onRetry={() => router.reload()}
          />
        </div>
      </Layout>
    );
  }

  return (
    <Layout
      title="Playlist Analysis - Spotify Playlist Optimizer"
      description="Detailed analysis and statistics for your Spotify playlist">
      <div className="min-h-screen bg-gradient-to-br from-spotify-gray-900 via-spotify-gray-800 to-spotify-black">
        {/* Header */}
        <header className="bg-spotify-black/50 backdrop-blur-sm border-b border-spotify-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleBackToDashboard}
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-spotify-gray-700 hover:bg-spotify-gray-600 text-white transition-colors">
                  <ArrowLeft className="h-4 w-4" />
                  <span>Back to Dashboard</span>
                </button>

                <div>
                  <h1 className="text-xl font-bold text-white">
                    Playlist Analysis
                  </h1>
                  <p className="text-spotify-gray-300 text-sm">
                    {tracks?.length || 0} tracks
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {/* Analysis Controls */}
                <div className="flex items-center space-x-2">
                  <select
                    value={analysisMethod}
                    onChange={(e) =>
                      setAnalysisMethod(e.target.value as 'kmeans' | 'dbscan')
                    }
                    className="px-3 py-2 bg-spotify-gray-700 text-white rounded-lg border border-spotify-gray-600 focus:border-spotify-green focus:outline-none">
                    <option value="kmeans">K-Means</option>
                    <option value="dbscan">DBSCAN</option>
                  </select>

                  {analysisMethod === 'kmeans' && (
                    <select
                      value={clusterCount}
                      onChange={(e) =>
                        setClusterCount(parseInt(e.target.value))
                      }
                      className="px-3 py-2 bg-spotify-gray-700 text-white rounded-lg border border-spotify-gray-600 focus:border-spotify-green focus:outline-none">
                      {[2, 3, 4, 5, 6].map((num) => (
                        <option key={num} value={num}>
                          {num} clusters
                        </option>
                      ))}
                    </select>
                  )}

                  <button
                    onClick={handleAnalyzePlaylist}
                    disabled={isAnalyzing}
                    className="flex items-center gap-2 bg-spotify-green hover:bg-spotify-green/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg transition-colors">
                    {isAnalyzing ? (
                      <Loader2 className="animate-spin" size={16} />
                    ) : (
                      <RefreshCw size={16} />
                    )}
                    <span>
                      {isAnalyzing ? 'Analyzing...' : 'Analyze Playlist'}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Stats and Chart */}
            <div className="lg:col-span-2 space-y-8">
              {/* Statistics Overview */}
              {stats && (
                <div className="bg-spotify-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-spotify-gray-700">
                  <h2 className="text-xl font-bold text-white mb-4">
                    Playlist Statistics
                  </h2>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-spotify-green">
                        {stats.total_tracks}
                      </p>
                      <p className="text-spotify-gray-400 text-sm">
                        Total Tracks
                      </p>
                    </div>

                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-400">
                        {Math.round(stats.avg_duration_ms / 60000)}m
                      </p>
                      <p className="text-spotify-gray-400 text-sm">
                        Avg Duration
                      </p>
                    </div>

                    <div className="text-center">
                      <p className="text-2xl font-bold text-yellow-400">
                        {Math.round(stats.avg_popularity)}
                      </p>
                      <p className="text-spotify-gray-400 text-sm">
                        Avg Popularity
                      </p>
                    </div>

                    <div className="text-center">
                      <p className="text-2xl font-bold text-purple-400">
                        {Math.round(stats.avg_audio_features.energy * 100)}%
                      </p>
                      <p className="text-spotify-gray-400 text-sm">
                        Avg Energy
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Cluster Visualization */}
              {analysisResult && (
                <div className="bg-spotify-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-spotify-gray-700">
                  <h2 className="text-xl font-bold text-white mb-4">
                    Cluster Analysis
                  </h2>
                  <ClusterChart
                    clusters={analysisResult.clusters}
                    tracks={tracks || []}
                    pcaCoordinates={analysisResult.pca_coordinates}
                  />
                </div>
              )}
            </div>

            {/* Right Column - Optimization Suggestions */}
            <div className="space-y-8">
              {/* Optimization panel disabled - endpoint temporarily unavailable */}
              {/* {optimizations && (
                <OptimizationPanel
                  suggestions={optimizations.suggestions}
                  onRefresh={refreshOptimizations}
                />
              )} */}
            </div>
          </div>

          {/* Tracks Table */}
          {tracks && tracks.length > 0 && (
            <div className="mt-8 bg-spotify-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-spotify-gray-700">
              <h2 className="text-xl font-bold text-white mb-4">
                Track Details
              </h2>
              <StatsTable
                tracks={tracks}
                clusters={analysisResult?.clusters || []}
              />
            </div>
          )}
        </main>
      </div>
    </Layout>
  );
}

export async function getServerSideProps() {
  // Return empty props to enable SSR and disable static generation
  // This prevents router issues during build time
  return {
    props: {},
  };
}
