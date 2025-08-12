/**
 * Comprehensive Optimization Dashboard showcasing all advanced features.
 * Integrates clustering, listening analytics, and optimization engine.
 */
import { useState, useEffect } from 'react';
import { Brain, TrendingUp, RefreshCw, Settings } from 'lucide-react';
import { clusteringApi, playlistApi } from '@/lib/api';

interface IOptimizationDashboardProps {
  playlistId: number;
}

interface IDashboardData {
  clustering?: any;
  listeningAnalytics?: any;
  optimization?: any;
  trackPerformance?: any;
  hiddenGems?: any;
  energyAnalysis?: any;
  trackReplacements?: any;
}

export default function OptimizationDashboard({
  playlistId,
}: IOptimizationDashboardProps) {
  const [data, setData] = useState<IDashboardData>({});
  const [loading, setLoading] = useState(false);
  // Focus on clustering for now; stash analytics/optimization
  const [activeTab, setActiveTab] = useState<'clustering'>('clustering');
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<
    'kmeans' | 'dbscan' | 'gaussian_mixture' | 'spectral'
  >('kmeans');
  // K-Means controls: Auto vs Manual K
  const [kmeansMode, setKmeansMode] = useState<'auto' | 'manual'>('auto');
  const [manualK, setManualK] = useState<number>(5);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const numClustersParam =
        selectedAlgorithm === 'kmeans' && kmeansMode === 'manual' && manualK > 1
          ? manualK
          : undefined;

      const clusteringResult = await clusteringApi.analyzePlaylist(
        playlistId.toString(),
        selectedAlgorithm,
        numClustersParam,
      );

      setData({ clustering: clusteringResult });
    } catch (error) {
      console.error('Failed to load optimization data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Helper for cluster quality color
  const getScoreColor = (score: number, threshold: number = 0.5) => {
    if (score >= threshold + 0.3) return 'text-green-400';
    if (score >= threshold) return 'text-yellow-400';
    return 'text-red-400';
  };

  // Refresh playlist and reload clustering
  const refreshPlaylistAndAnalysis = async () => {
    setLoading(true);
    try {
      await playlistApi.refreshPlaylist(playlistId.toString());
      await loadAllData();
    } catch (error) {
      console.error('Failed to refresh playlist and analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  // (Removed broken/dead JSX from previous dashboard sections)
  // (removed stray parenthesis)

  const renderClustering = () => (
    <div className="space-y-6">
      {/* Algorithm Selection */}
      <div className="bg-spotify-gray-800/50 rounded-xl p-6 border border-spotify-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Settings className="h-5 w-5 mr-2" />
          Clustering Algorithm
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {(['kmeans', 'dbscan', 'gaussian_mixture', 'spectral'] as const).map(
            (algo) => (
              <button
                key={algo}
                onClick={() => setSelectedAlgorithm(algo)}
                className={`p-3 rounded-lg text-center transition-colors ${
                  selectedAlgorithm === algo
                    ? 'bg-spotify-green text-white'
                    : 'bg-spotify-gray-700 text-spotify-gray-300 hover:bg-spotify-gray-600'
                }`}>
                {algo
                  .replace('_', ' ')
                  .replace(/\\b\\w/g, (l) => l.toUpperCase())}
              </button>
            ),
          )}
        </div>

        {/* K-Means Specific Controls */}
        {selectedAlgorithm === 'kmeans' && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-white">
                Cluster Count:
              </span>
              <div className="flex space-x-2">
                <button
                  onClick={() => setKmeansMode('auto')}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    kmeansMode === 'auto'
                      ? 'bg-spotify-green text-white'
                      : 'bg-spotify-gray-700 text-spotify-gray-300 hover:bg-spotify-gray-600'
                  }`}>
                  Auto
                </button>
                <button
                  onClick={() => setKmeansMode('manual')}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    kmeansMode === 'manual'
                      ? 'bg-spotify-green text-white'
                      : 'bg-spotify-gray-700 text-spotify-gray-300 hover:bg-spotify-gray-600'
                  }`}>
                  Manual
                </button>
              </div>
            </div>

            {kmeansMode === 'manual' && (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-spotify-gray-400">
                  Number of clusters:
                </span>
                <select
                  value={manualK}
                  onChange={(e) => setManualK(parseInt(e.target.value))}
                  className="px-3 py-1 bg-spotify-gray-700 text-white rounded border border-spotify-gray-600 focus:border-spotify-green focus:outline-none text-sm">
                  {[2, 3, 4, 5, 6, 7, 8, 9, 10].map((k) => (
                    <option key={k} value={k}>
                      {k} clusters
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        {/* Analyze Button */}
        <div className="mt-4">
          <button
            onClick={loadAllData}
            disabled={loading}
            className="bg-spotify-green hover:bg-spotify-green/90 disabled:opacity-50 text-white font-semibold py-2 px-6 rounded-lg transition-colors flex items-center space-x-2">
            {loading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Brain className="h-4 w-4" />
            )}
            <span>{loading ? 'Analyzing...' : 'Run Analysis'}</span>
          </button>
        </div>
      </div>

      {/* Cluster Analysis */}
      {data.clustering && (
        <div className="bg-spotify-gray-800/50 rounded-xl p-6 border border-spotify-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Brain className="h-5 w-5 mr-2" />
            Cluster Analysis Results
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">
                {data.clustering.clusters?.length || 0}
              </div>
              <div className="text-spotify-gray-400 text-sm">
                Clusters Found
              </div>
            </div>
            <div className="text-center">
              <div
                className={`text-2xl font-bold ${getScoreColor(
                  data.clustering.silhouette_score,
                  0.3,
                )}`}>
                {(data.clustering.silhouette_score * 100).toFixed(1)}%
              </div>
              <div className="text-spotify-gray-400 text-sm">Quality Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">
                {data.clustering.optimal_clusters || 'Auto'}
              </div>
              <div className="text-spotify-gray-400 text-sm">Optimal Count</div>
            </div>
          </div>

          {/* Cluster Details */}
          <div className="space-y-3">
            {data.clustering.clusters?.map((cluster: any, index: number) => (
              <div
                key={index}
                className="bg-spotify-gray-700/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-white">
                    Cluster {index + 1}: {cluster.label || 'Unlabeled'}
                  </h4>
                  <span className="text-spotify-gray-400 text-sm">
                    {cluster.tracks?.length || 0} tracks
                  </span>
                </div>
                <p className="text-spotify-gray-300 text-sm">
                  {cluster.description || 'No description available'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
          <TrendingUp className="h-6 w-6 text-spotify-green" />
          <span>Clustering Dashboard</span>
        </h2>
        <button
          onClick={refreshPlaylistAndAnalysis}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-spotify-green hover:bg-spotify-green-dark text-white rounded-lg transition-colors disabled:opacity-50">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Playlist & Analysis</span>
        </button>
      </div>

      {/* Tab Navigation (Clustering only for now) */}
      <div className="border-b border-spotify-gray-700">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('clustering')}
            className={`flex items-center space-x-2 py-3 px-1 border-b-2 font-medium text-sm transition-colors ${'border-spotify-green text-spotify-green'}`}>
            <Brain className="h-4 w-4" />
            <span>Clustering</span>
          </button>
        </nav>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-spotify-green" />
          <span className="ml-3 text-spotify-gray-400">
            Loading clustering data...
          </span>
        </div>
      ) : (
        <div>{activeTab === 'clustering' && renderClustering()}</div>
      )}
    </div>
  );
}
