/**
 * Reusable table component for displaying track statistics and audio features.
 */
import { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Music } from 'lucide-react';
import { ITrack, IClusterData } from '@/types/playlist';

interface IStatsTableProps {
  tracks: ITrack[];
  clusters?: IClusterData[];
}

type SortField = keyof ITrack | 'cluster';
type SortDirection = 'asc' | 'desc';

export default function StatsTable({
  tracks,
  clusters = [],
}: IStatsTableProps) {
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);

  // Create a map of track ID to cluster ID
  const trackClusterMap = useMemo(() => {
    const map = new Map<number, number>();
    clusters.forEach((cluster) => {
      cluster.track_ids.forEach((trackId) => {
        map.set(trackId, cluster.cluster_id);
      });
    });
    return map;
  }, [clusters]);

  // Get cluster color for a track
  const getClusterColor = (trackId: number) => {
    const clusterId = trackClusterMap.get(trackId);
    if (clusterId === undefined) return 'bg-spotify-gray-600';

    const colors = [
      'bg-red-500',
      'bg-blue-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-orange-500',
    ];

    return colors[clusterId % colors.length] || 'bg-spotify-gray-600';
  };

  // Filter and sort tracks
  const filteredAndSortedTracks = useMemo(() => {
    let filtered = tracks;

    // Filter by selected cluster
    if (selectedCluster !== null) {
      filtered = tracks.filter(
        (track) => trackClusterMap.get(track.id) === selectedCluster,
      );
    }

    // Sort tracks (create a new array to avoid mutating props)
    return [...filtered].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      if (sortField === 'cluster') {
        aValue = trackClusterMap.get(a.id) ?? -1;
        bValue = trackClusterMap.get(b.id) ?? -1;
      } else {
        aValue = a[sortField];
        bValue = b[sortField];
      }

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;

      // Sort logic
      let comparison = 0;
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        comparison = aValue.localeCompare(bValue);
      } else {
        comparison = aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [tracks, trackClusterMap, selectedCluster, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? (
      <ChevronUp className="h-4 w-4" />
    ) : (
      <ChevronDown className="h-4 w-4" />
    );
  };

  const formatDuration = (ms: number | null | undefined) => {
    if (!ms) return 'N/A';
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const formatAudioFeature = (value: number | null) => {
    if (value === null || value === undefined) return 'N/A';
    return (value * 100).toFixed(0) + '%';
  };

  return (
    <div className="space-y-4">
      {/* Cluster Filter */}
      {clusters.length > 0 && (
        <div className="flex items-center space-x-4">
          <span className="text-spotify-gray-300 font-medium">
            Filter by cluster:
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSelectedCluster(null)}
              className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                selectedCluster === null
                  ? 'bg-spotify-green text-white'
                  : 'bg-spotify-gray-700 text-spotify-gray-300 hover:bg-spotify-gray-600'
              }`}>
              All
            </button>
            {clusters.map((cluster) => (
              <button
                key={cluster.cluster_id}
                onClick={() => setSelectedCluster(cluster.cluster_id)}
                className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                  selectedCluster === cluster.cluster_id
                    ? 'bg-spotify-green text-white'
                    : 'bg-spotify-gray-700 text-spotify-gray-300 hover:bg-spotify-gray-600'
                }`}>
                {cluster.label || `Cluster ${cluster.cluster_id + 1}`} (
                {cluster.track_count})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-spotify-gray-700">
              {clusters.length > 0 && (
                <th className="text-left p-3">
                  <button
                    onClick={() => handleSort('cluster')}
                    className="flex items-center space-x-1 text-spotify-gray-300 hover:text-white transition-colors">
                    <span>Cluster</span>
                    {getSortIcon('cluster')}
                  </button>
                </th>
              )}

              <th className="text-left p-3">
                <button
                  onClick={() => handleSort('name')}
                  className="flex items-center space-x-1 text-spotify-gray-300 hover:text-white transition-colors">
                  <span>Track</span>
                  {getSortIcon('name')}
                </button>
              </th>

              <th className="text-left p-3">
                <button
                  onClick={() => handleSort('duration_ms')}
                  className="flex items-center space-x-1 text-spotify-gray-300 hover:text-white transition-colors">
                  <span>Duration</span>
                  {getSortIcon('duration_ms')}
                </button>
              </th>

              <th className="text-left p-3">
                <button
                  onClick={() => handleSort('popularity')}
                  className="flex items-center space-x-1 text-spotify-gray-300 hover:text-white transition-colors">
                  <span>Popularity</span>
                  {getSortIcon('popularity')}
                </button>
              </th>

              <th className="text-left p-3">
                <button
                  onClick={() => handleSort('energy')}
                  className="flex items-center space-x-1 text-spotify-gray-300 hover:text-white transition-colors">
                  <span>Energy</span>
                  {getSortIcon('energy')}
                </button>
              </th>

              <th className="text-left p-3">
                <button
                  onClick={() => handleSort('danceability')}
                  className="flex items-center space-x-1 text-spotify-gray-300 hover:text-white transition-colors">
                  <span>Danceability</span>
                  {getSortIcon('danceability')}
                </button>
              </th>

              <th className="text-left p-3">
                <button
                  onClick={() => handleSort('valence')}
                  className="flex items-center space-x-1 text-spotify-gray-300 hover:text-white transition-colors">
                  <span>Valence</span>
                  {getSortIcon('valence')}
                </button>
              </th>

              <th className="text-left p-3">
                <button
                  onClick={() => handleSort('tempo')}
                  className="flex items-center space-x-1 text-spotify-gray-300 hover:text-white transition-colors">
                  <span>Tempo</span>
                  {getSortIcon('tempo')}
                </button>
              </th>
            </tr>
          </thead>

          <tbody>
            {filteredAndSortedTracks.map((track) => (
              <tr
                key={track.id}
                className="border-b border-spotify-gray-800 hover:bg-spotify-gray-800/50 transition-colors">
                {clusters.length > 0 && (
                  <td className="p-3">
                    <div className="flex items-center space-x-2">
                      <div
                        className={`w-3 h-3 rounded-full ${getClusterColor(
                          track.id,
                        )}`}
                      />
                      <span className="text-spotify-gray-300">
                        {(trackClusterMap.get(track.id) ?? -1) + 1}
                      </span>
                    </div>
                  </td>
                )}

                <td className="p-3">
                  <div>
                    <div className="text-white font-medium truncate max-w-xs">
                      {track.name}
                    </div>
                    <div className="text-spotify-gray-400 text-xs truncate max-w-xs">
                      {track.artist}
                    </div>
                  </div>
                </td>

                <td className="p-3 text-spotify-gray-300">
                  {track.duration_ms
                    ? formatDuration(track.duration_ms)
                    : 'N/A'}
                </td>

                <td className="p-3 text-spotify-gray-300">
                  {track.popularity ?? 'N/A'}
                </td>

                <td className="p-3 text-spotify-gray-300">
                  {formatAudioFeature(track.energy ?? null)}
                </td>

                <td className="p-3 text-spotify-gray-300">
                  {formatAudioFeature(track.danceability ?? null)}
                </td>

                <td className="p-3 text-spotify-gray-300">
                  {formatAudioFeature(track.valence ?? null)}
                </td>

                <td className="p-3 text-spotify-gray-300">
                  {track.tempo ? Math.round(track.tempo) + ' BPM' : 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredAndSortedTracks.length === 0 && (
          <div className="text-center py-8">
            <Music className="h-12 w-12 text-spotify-gray-500 mx-auto mb-3" />
            <p className="text-spotify-gray-400">No tracks found</p>
          </div>
        )}
      </div>

      {/* Results summary */}
      <div className="text-spotify-gray-400 text-sm">
        Showing {filteredAndSortedTracks.length} of {tracks.length} tracks
      </div>
    </div>
  );
}
