/**
 * Enhanced StatsTable with track selection and bulk operations
 */
import { useState, useMemo, useEffect } from 'react';
import { ChevronUp, ChevronDown, Music, Search, X } from 'lucide-react';
import { ITrack, IClusterData } from '@/types/playlist';

interface IEnhancedStatsTableProps {
  tracks: ITrack[];
  clusters?: IClusterData[];
  selectedTrackIds?: string[];
  onSelectionChange?: (trackIds: string[]) => void;
  onBulkAction?: () => void;
}

type SortField = keyof ITrack | 'cluster';
type SortDirection = 'asc' | 'desc';

export default function EnhancedStatsTable({
  tracks,
  clusters = [],
  selectedTrackIds = [],
  onSelectionChange,
  onBulkAction,
}: IEnhancedStatsTableProps) {
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showBulkActions, setShowBulkActions] = useState(false);
  
  // Use external selection state
  const selectedTracks = useMemo(() => new Set(selectedTrackIds), [selectedTrackIds]);
  const setSelectedTracks = (newSelection: Set<string>) => {
    if (onSelectionChange) {
      onSelectionChange(Array.from(newSelection));
    }
  };

  // Update showBulkActions when selectedTrackIds changes
  useEffect(() => {
    setShowBulkActions(selectedTrackIds.length > 0);
  }, [selectedTrackIds]);

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

  // Get unique clusters from track-cluster mapping  
  const uniqueClusters = useMemo(() => {
    const clusterIds = new Set<number>();
    tracks.forEach((track) => {
      const clusterId = trackClusterMap.get(track.id);
      if (clusterId !== undefined) {
        clusterIds.add(clusterId);
      }
    });
    return Array.from(clusterIds).sort((a, b) => a - b);
  }, [tracks, trackClusterMap]);

  // Filter and sort tracks
  const filteredAndSortedTracks = useMemo(() => {
    let filtered = tracks;

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (track) =>
          track.name.toLowerCase().includes(query) ||
          track.artist.toLowerCase().includes(query) ||
          (track.album && track.album.toLowerCase().includes(query)),
      );
    }

    // Apply cluster filter
    if (selectedCluster !== null) {
      filtered = filtered.filter(
        (track) => trackClusterMap.get(track.id) === selectedCluster,
      );
    }

    // Sort tracks
    return [...filtered].sort((a, b) => {
      let aValue: any, bValue: any;

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

      let comparison = 0;
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        comparison = aValue.localeCompare(bValue);
      } else {
        comparison = aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [tracks, trackClusterMap, selectedCluster, searchQuery, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleSelectTrack = (trackId: string) => {
    const newSelection = new Set(selectedTracks);
    if (newSelection.has(trackId)) {
      newSelection.delete(trackId);
    } else {
      newSelection.add(trackId);
    }
    setSelectedTracks(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedTracks.size === filteredAndSortedTracks.length && filteredAndSortedTracks.length > 0) {
      // Deselect all
      setSelectedTracks(new Set());
    } else {
      // Select all filtered tracks
      const allTrackIds = new Set(filteredAndSortedTracks.map(track => track.spotify_track_id));
      setSelectedTracks(allTrackIds);
    }
  };

  const formatAudioFeature = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') return value.toFixed(3);
    return 'N/A';
  };

  const renderSortButton = (field: SortField, label: string) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center space-x-1 text-spotify-gray-300 hover:text-white transition-colors text-xs font-medium"
    >
      <span>{label}</span>
      {sortField === field && (
        sortDirection === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
      )}
    </button>
  );

  // Check if all visible tracks are selected
  const allSelected = filteredAndSortedTracks.length > 0 && 
    filteredAndSortedTracks.every(track => selectedTracks.has(track.spotify_track_id));
  
  // Check if some but not all tracks are selected
  const partiallySelected = filteredAndSortedTracks.some(track => selectedTracks.has(track.spotify_track_id)) && !allSelected;

  return (
    <div className="space-y-4">
      {/* Search and Filter Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-spotify-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search tracks, artists, or albums..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-spotify-gray-700 border border-spotify-gray-600 rounded-lg text-white placeholder-spotify-gray-400 focus:outline-none focus:ring-2 focus:ring-spotify-green"
          />
        </div>
        
        {uniqueClusters.length > 0 && (
          <select
            value={selectedCluster ?? ''}
            onChange={(e) => setSelectedCluster(e.target.value ? parseInt(e.target.value) : null)}
            className="px-3 py-2 bg-spotify-gray-700 border border-spotify-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-spotify-green"
          >
            <option value="">All Clusters</option>
            {uniqueClusters.map((clusterId) => (
              <option key={clusterId} value={clusterId}>
                Cluster {clusterId}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Bulk Actions Bar */}
      {showBulkActions && (
        <div className="bg-spotify-green/10 border border-spotify-green/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-spotify-green font-medium">
                {selectedTracks.size} track{selectedTracks.size !== 1 ? 's' : ''} selected
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={onBulkAction}
                className="px-3 py-1 bg-spotify-green text-black rounded-md hover:bg-spotify-green/90 transition-colors text-sm font-medium"
              >
                Bulk Actions
              </button>
              <button
                onClick={() => {
                  setSelectedTracks(new Set());
                }}
                className="p-1 text-spotify-gray-400 hover:text-white transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Results count */}
      <div className="text-sm text-spotify-gray-400">
        Showing {filteredAndSortedTracks.length} of {tracks.length} tracks
        {selectedCluster !== null && ` in Cluster ${selectedCluster}`}
        {searchQuery && ` matching "${searchQuery}"`}
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-spotify-gray-800/50 rounded-lg border border-spotify-gray-700">
        <table className="w-full">
          <thead>
            <tr className="border-b border-spotify-gray-700">
              <th className="p-3 text-left">
                <input
                  type="checkbox"
                  checked={allSelected}
                  ref={(input) => {
                    if (input) input.indeterminate = partiallySelected;
                  }}
                  onChange={handleSelectAll}
                  className="h-4 w-4 text-spotify-green focus:ring-spotify-green border-spotify-gray-600 bg-spotify-gray-700 rounded"
                />
              </th>
              <th className="p-3 text-left">{renderSortButton('name', 'Track')}</th>
              <th className="p-3 text-left">{renderSortButton('artist', 'Artist')}</th>
              <th className="p-3 text-left">{renderSortButton('album', 'Album')}</th>
              {uniqueClusters.length > 0 && (
                <th className="p-3 text-left">{renderSortButton('cluster', 'Cluster')}</th>
              )}
              <th className="p-3 text-left">{renderSortButton('popularity', 'Pop')}</th>
              <th className="p-3 text-left">{renderSortButton('danceability', 'Dance')}</th>
              <th className="p-3 text-left">{renderSortButton('energy', 'Energy')}</th>
              <th className="p-3 text-left">{renderSortButton('valence', 'Valence')}</th>
              <th className="p-3 text-left">{renderSortButton('tempo', 'Tempo')}</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedTracks.map((track) => (
              <tr
                key={track.id}
                className={`border-b border-spotify-gray-700/50 hover:bg-spotify-gray-700/30 transition-colors ${
                  selectedTracks.has(track.spotify_track_id) ? 'bg-spotify-green/10' : ''
                }`}
              >
                <td className="p-3">
                  <input
                    type="checkbox"
                    checked={selectedTracks.has(track.spotify_track_id)}
                    onChange={() => handleSelectTrack(track.spotify_track_id)}
                    className="h-4 w-4 text-spotify-green focus:ring-spotify-green border-spotify-gray-600 bg-spotify-gray-700 rounded"
                  />
                </td>
                <td className="p-3">
                  <div className="flex items-center space-x-3">
                    <Music className="h-4 w-4 text-spotify-gray-400 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-white font-medium truncate">{track.name}</p>
                    </div>
                  </div>
                </td>
                <td className="p-3">
                  <p className="text-spotify-gray-300 truncate">{track.artist}</p>
                </td>
                <td className="p-3">
                  <p className="text-spotify-gray-300 truncate">{track.album || 'N/A'}</p>
                </td>
                {uniqueClusters.length > 0 && (
                  <td className="p-3">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-900/20 text-blue-300 border border-blue-700/30">
                      {trackClusterMap.get(track.id) ?? 'N/A'}
                    </span>
                  </td>
                )}
                <td className="p-3">
                  <span className="text-spotify-gray-300">{track.popularity ?? 'N/A'}</span>
                </td>
                <td className="p-3">
                  <span className="text-spotify-gray-300">{formatAudioFeature(track.danceability)}</span>
                </td>
                <td className="p-3">
                  <span className="text-spotify-gray-300">{formatAudioFeature(track.energy)}</span>
                </td>
                <td className="p-3">
                  <span className="text-spotify-gray-300">{formatAudioFeature(track.valence)}</span>
                </td>
                <td className="p-3">
                  <span className="text-spotify-gray-300">{formatAudioFeature(track.tempo)}</span>
                </td>
              </tr>
            ))}
            {filteredAndSortedTracks.length === 0 && (
              <tr>
                <td colSpan={10} className="p-8 text-center">
                  <div className="text-spotify-gray-400">
                    <Music className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium mb-2">No tracks found</p>
                    <p className="text-sm">
                      {searchQuery ? `No tracks match "${searchQuery}"` : 'No tracks available'}
                      {selectedCluster !== null && ` in Cluster ${selectedCluster}`}
                    </p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
