/**
 * Playlist Optimization Page - Comprehensive analysis and optimization features.
 * Showcases the full power of the enhanced backend optimization system.
 */
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeft, Music, TrendingUp, Zap, Brain } from 'lucide-react';
import useSWR from 'swr';

import Layout from '@/components/Layout';
import OptimizationDashboard from '@/components/OptimizationDashboard';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import { useAuth } from '@/hooks/useAuth';
import { fetcher } from '@/lib/api';

export default function PlaylistOptimization() {
  const router = useRouter();
  const { playlistId } = router.query;
  const { user, isLoading: authLoading } = useAuth();
  const [playlistName, setPlaylistName] = useState<string>('');

  // Fetch playlist details
  const { data: playlist, error: playlistError } = useSWR(
    playlistId && user ? `/api/analytics/playlists` : null,
    fetcher,
  );

  useEffect(() => {
    if (playlist && playlistId) {
      const currentPlaylist = playlist.find(
        (p: any) => p.id === parseInt(playlistId as string),
      );
      if (currentPlaylist) {
        setPlaylistName(currentPlaylist.name);
      }
    }
  }, [playlist, playlistId]);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/');
    }
  }, [user, authLoading, router]);

  if (authLoading) {
    return (
      <Layout title="Loading...">
        <div className="flex items-center justify-center min-h-screen">
          <LoadingSpinner />
        </div>
      </Layout>
    );
  }

  if (!user) {
    return null;
  }

  if (playlistError) {
    return (
      <Layout title="Error">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <ErrorMessage message="Failed to load playlist data. Please try again." />
        </div>
      </Layout>
    );
  }

  if (!playlistId) {
    return (
      <Layout title="No Playlist">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <ErrorMessage message="No playlist selected. Please return to the dashboard and select a playlist." />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Optimize: ${playlistName || 'Playlist'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="flex items-center space-x-2 text-spotify-gray-400 hover:text-white transition-colors mb-4">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Dashboard</span>
          </button>

          <div className="flex items-center space-x-4">
            <div className="bg-gradient-to-br from-spotify-green to-green-500 p-3 rounded-xl">
              <Music className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">
                {playlistName || 'Playlist Optimization'}
              </h1>
              <p className="text-spotify-gray-400">
                Comprehensive analysis and optimization powered by machine
                learning
              </p>
            </div>
          </div>

          {/* Feature highlights */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-spotify-gray-800/30 rounded-lg p-4 border border-spotify-gray-700">
              <div className="flex items-center space-x-2 mb-2">
                <Brain className="h-5 w-5 text-purple-400" />
                <span className="text-white font-medium">Smart Clustering</span>
              </div>
              <p className="text-spotify-gray-400 text-sm">
                4 advanced algorithms with auto-optimization
              </p>
            </div>

            <div className="bg-spotify-gray-800/30 rounded-lg p-4 border border-spotify-gray-700">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="h-5 w-5 text-blue-400" />
                <span className="text-white font-medium">
                  Behavioral Analytics
                </span>
              </div>
              <p className="text-spotify-gray-400 text-sm">
                Skip patterns and hidden gem discovery
              </p>
            </div>

            <div className="bg-spotify-gray-800/30 rounded-lg p-4 border border-spotify-gray-700">
              <div className="flex items-center space-x-2 mb-2">
                <Zap className="h-5 w-5 text-yellow-400" />
                <span className="text-white font-medium">
                  Flow Optimization
                </span>
              </div>
              <p className="text-spotify-gray-400 text-sm">
                Energy transitions and tempo analysis
              </p>
            </div>

            <div className="bg-spotify-gray-800/30 rounded-lg p-4 border border-spotify-gray-700">
              <div className="flex items-center space-x-2 mb-2">
                <Music className="h-5 w-5 text-green-400" />
                <span className="text-white font-medium">
                  Smart Recommendations
                </span>
              </div>
              <p className="text-spotify-gray-400 text-sm">
                Actionable improvements with priority scoring
              </p>
            </div>
          </div>
        </div>

        {/* Main Optimization Dashboard */}
        <OptimizationDashboard playlistId={parseInt(playlistId as string)} />

        {/* Footer Info */}
        <div className="mt-12 p-6 bg-spotify-gray-800/30 rounded-xl border border-spotify-gray-700">
          <h3 className="text-lg font-semibold text-white mb-3">
            🎯 About This Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-spotify-gray-300">
            <div>
              <h4 className="font-medium text-white mb-2">
                Enhanced Clustering
              </h4>
              <p>
                Uses advanced machine learning algorithms (K-Means, DBSCAN,
                Gaussian Mixture, Spectral) with automatic parameter
                optimization and interpretable cluster labeling.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-white mb-2">
                Listening Analytics
              </h4>
              <p>
                Analyzes estimated listening behavior, skip patterns, and track
                performance to identify hidden gems and engagement
                opportunities.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-white mb-2">
                Optimization Engine
              </h4>
              <p>
                Provides actionable recommendations for improving playlist flow,
                energy transitions, and overall listening experience.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-white mb-2">
                Smart Recommendations
              </h4>
              <p>
                Generates priority-scored suggestions for track replacements,
                flow improvements, and playlist optimization strategies.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
