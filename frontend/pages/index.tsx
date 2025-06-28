/**
 * Main dashboard page for the Spotify Playlist Optimizer.
 * Displays user playlists and provides access to analysis features.
 */
import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { Music, BarChart3, Settings, LogOut, Loader2 } from "lucide-react";
import useSWR from "swr";

import Layout from "@/components/Layout";
import PlaylistCard from "@/components/PlaylistCard";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorMessage from "@/components/ErrorMessage";
import { useAuth } from "@/hooks/useAuth";
import { fetcher } from "@/lib/api";
import { IPlaylist } from "@/types/playlist";

export default function Dashboard() {
  const router = useRouter();
  const { user, logout, isLoading: authLoading } = useAuth();
  const [selectedPlaylist, setSelectedPlaylist] = useState<IPlaylist | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  // Ensure component is mounted before using router
  useEffect(() => {
    setIsMounted(true);
    
    // Debug: Log authentication info
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      console.log("Debug - Auth state:", {
        user: user,
        hasToken: !!token,
        tokenLength: token?.length,
        tokenPreview: token?.substring(0, 50) + "...",
        isLoading: authLoading
      });
      
      // If we have a token but no user, there might be a token verification issue
      if (token && !user && !authLoading) {
        console.warn("Warning: Token exists but user is null. Token might be invalid or expired.");
      }
    }
  }, [user, authLoading]);

  // Fetch user playlists
  const { 
    data: playlists, 
    error: playlistsError, 
    isLoading: playlistsLoading,
    mutate: refreshPlaylists 
  } = useSWR<IPlaylist[]>(
    user ? "/api/analytics/playlists" : null,
    fetcher
  );

  const handlePlaylistSelect = (playlist: IPlaylist) => {
    setSelectedPlaylist(playlist);
    if (isMounted) {
      router.push(`/playback-stats/${playlist.id}`);
    }
  };

  const handleRefreshPlaylists = async () => {
    await refreshPlaylists();
  };

  const handleLogout = async () => {
    await logout();
    if (isMounted) {
      router.push("/");
    }
  };

  // Show loading spinner while checking auth or component is mounting
  if (authLoading || !isMounted) {
    return (
      <div className="min-h-screen bg-spotify-gray-900 flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  // Show login page if not authenticated
  if (!user) {
    return (
      <Layout
        title="Spotify Playlist Optimizer"
        description="Analyze and optimize your Spotify playlists with machine learning"
      >
        <div className="min-h-screen bg-gradient-to-br from-spotify-gray-900 via-spotify-gray-800 to-spotify-black flex items-center justify-center">
          <div className="max-w-md w-full space-y-8 p-8">
            <div className="text-center">
              <Music className="h-16 w-16 text-spotify-green mx-auto mb-4" />
              <h1 className="text-4xl font-bold text-white mb-2">
                Spotify Playlist Optimizer
              </h1>
              <p className="text-spotify-gray-300 mb-8">
                Analyze and optimize your Spotify playlists with machine learning clustering algorithms
              </p>
              
              <a
                href="/api/auth/login"
                className="inline-flex items-center space-x-3 px-8 py-4 bg-spotify-green hover:bg-spotify-green/90 text-white font-semibold rounded-full transition-colors text-lg"
              >
                <Music className="h-5 w-5" />
                <span>Connect to Spotify</span>
              </a>
              
              <div className="mt-8 text-spotify-gray-400 text-sm">
                <p>This app requires access to your Spotify account to:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>View your playlists</li>
                  <li>Analyze audio features</li>
                  <li>Provide optimization suggestions</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout
      title="Dashboard - Spotify Playlist Optimizer"
      description="Analyze and optimize your Spotify playlists with machine learning"
    >
      <div className="min-h-screen bg-gradient-to-br from-spotify-gray-900 via-spotify-gray-800 to-spotify-black">
        {/* Header */}
        <header className="bg-spotify-black/50 backdrop-blur-sm border-b border-spotify-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-3">
                <Music className="h-8 w-8 text-spotify-green" />
                <h1 className="text-xl font-bold text-white">
                  Spotify Playlist Optimizer
                </h1>
              </div>
              
              <div className="flex items-center space-x-4">
                <span className="text-spotify-gray-300">
                  Welcome, {user.display_name || user.spotify_user_id}
                </span>
                
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-spotify-gray-700 hover:bg-spotify-gray-600 text-white transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Dashboard Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-spotify-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-spotify-gray-700">
              <div className="flex items-center space-x-3">
                <Music className="h-8 w-8 text-spotify-green" />
                <div>
                  <p className="text-spotify-gray-300 text-sm">Total Playlists</p>
                  <p className="text-white text-2xl font-bold">
                    {playlists?.length || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-spotify-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-spotify-gray-700">
              <div className="flex items-center space-x-3">
                <BarChart3 className="h-8 w-8 text-blue-400" />
                <div>
                  <p className="text-spotify-gray-300 text-sm">Analyzed</p>
                  <p className="text-white text-2xl font-bold">0</p>
                </div>
              </div>
            </div>

            <div className="bg-spotify-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-spotify-gray-700">
              <div className="flex items-center space-x-3">
                <Settings className="h-8 w-8 text-purple-400" />
                <div>
                  <p className="text-spotify-gray-300 text-sm">Optimized</p>
                  <p className="text-white text-2xl font-bold">0</p>
                </div>
              </div>
            </div>
          </div>

          {/* Playlists Section */}
          <div className="bg-spotify-gray-800/30 backdrop-blur-sm rounded-xl p-6 border border-spotify-gray-700">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Your Playlists</h2>
              
              <button
                onClick={handleRefreshPlaylists}
                disabled={playlistsLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-spotify-green hover:bg-spotify-green/90 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                {playlistsLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Music className="h-4 w-4" />
                )}
                <span>Refresh Playlists</span>
              </button>
            </div>

            {/* Loading State */}
            {playlistsLoading && (
              <div className="flex justify-center py-12">
                <LoadingSpinner size="medium" />
              </div>
            )}

            {/* Error State */}
            {playlistsError && (
              <ErrorMessage 
                message="Failed to load playlists. Please try again."
                onRetry={handleRefreshPlaylists}
              />
            )}

            {/* Empty State */}
            {!playlistsLoading && !playlistsError && (!playlists || playlists.length === 0) && (
              <div className="text-center py-12">
                <Music className="h-16 w-16 text-spotify-gray-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">
                  No Playlists Found
                </h3>
                <p className="text-spotify-gray-400 mb-4">
                  Create some playlists in Spotify and refresh to get started.
                </p>
                <button
                  onClick={handleRefreshPlaylists}
                  className="px-4 py-2 bg-spotify-green hover:bg-spotify-green/90 text-white rounded-lg transition-colors"
                >
                  Refresh Playlists
                </button>
              </div>
            )}

            {/* Playlists Grid */}
            {playlists && playlists.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {playlists.map((playlist) => (
                  <PlaylistCard
                    key={playlist.id}
                    playlist={playlist}
                    onSelect={handlePlaylistSelect}
                    selected={selectedPlaylist?.id === playlist.id}
                  />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </Layout>
  );
}
