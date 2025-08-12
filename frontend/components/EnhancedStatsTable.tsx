/**
 * Enhanced Stats Table with scrollable container, resizable columns, and text wrapping
 */
import React, { useState, useMemo, useEffect, useRef } from 'react';
import { ChevronDown, ChevronUp, Search, Music, Eye, EyeOff } from 'lucide-react';

interface Track {
  id: number;
  spotify_track_id: string;
  name: string;
  artist: string;
  album?: string;
  popularity?: number;
  danceability?: number;
  energy?: number;
  valence?: number;
  tempo?: number;
  acousticness?: number;
  instrumentalness?: number;
  liveness?: number;
  speechiness?: number;
  loudness?: number;
  key?: number;
  mode?: number;
}

interface ClusterResult {
  cluster_id: number;
  label?: string;
  track_ids: number[];
}

interface IEnhancedStatsTableProps {
  tracks: Track[];
  clusters?: ClusterResult[];
  selectedTrackIds?: string[];
  onSelectionChange?: (selectedIds: string[]) => void;
  onBulkAction?: (action: string, data: any) => void;
}

type SortField = 'name' | 'artist' | 'album' | 'popularity' | 'cluster' | 'danceability' | 'energy' | 'valence' | 'tempo' | 'acousticness' | 'instrumentalness' | 'liveness' | 'speechiness' | 'loudness' | 'key' | 'mode';
type SortDirection = 'asc' | 'desc';

interface ColumnVisibility {
  cluster: boolean;
  popularity: boolean;
  danceability: boolean;
  energy: boolean;
  valence: boolean;
  tempo: boolean;
  acousticness: boolean;
  instrumentalness: boolean;
  liveness: boolean;
  speechiness: boolean;
  loudness: boolean;
  key: boolean;
  mode: boolean;
}

interface ColumnWidths {
  checkbox: number;
  track: number;
  artist: number;
  album: number;
  cluster: number;
  popularity: number;
  danceability: number;
  energy: number;
  valence: number;
  tempo: number;
  acousticness: number;
  instrumentalness: number;
  liveness: number;
  speechiness: number;
  loudness: number;
  key: number;
  mode: number;
}

const defaultColumnVisibility: ColumnVisibility = {
  cluster: true,
  popularity: true,
  danceability: true,
  energy: true,
  valence: true,
  tempo: true,
  acousticness: false,
  instrumentalness: false,
  liveness: false,
  speechiness: false,
  loudness: false,
  key: false,
  mode: false,
};

const defaultColumnWidths: ColumnWidths = {
  checkbox: 50,
  track: 250,
  artist: 200,
  album: 200,
  cluster: 120,
  popularity: 80,
  danceability: 100,
  energy: 80,
  valence: 80,
  tempo: 80,
  acousticness: 100,
  instrumentalness: 110,
  liveness: 80,
  speechiness: 90,
  loudness: 80,
  key: 60,
  mode: 80,
};

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
  const [columnVisibility, setColumnVisibility] = useState<ColumnVisibility>(defaultColumnVisibility);
  const [columnWidths, setColumnWidths] = useState<ColumnWidths>(defaultColumnWidths);
  const [resizingColumn, setResizingColumn] = useState<string | null>(null);
  const [startX, setStartX] = useState(0);
  const [startWidth, setStartWidth] = useState(0);
  const [showColumnControls, setShowColumnControls] = useState(false);
  
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

  // Column resizing functionality
  const handleResizeStart = (columnKey: string, e: React.MouseEvent) => {
    e.preventDefault();
    setResizingColumn(columnKey);
    setStartX(e.clientX);
    setStartWidth(columnWidths[columnKey as keyof ColumnWidths]);
  };

  const handleResizeMove = (e: MouseEvent) => {
    if (!resizingColumn) return;
    
    const diff = e.clientX - startX;
    const newWidth = Math.max(50, startWidth + diff); // Minimum width of 50px
    
    setColumnWidths(prev => ({
      ...prev,
      [resizingColumn]: newWidth
    }));
  };

  const handleResizeEnd = () => {
    setResizingColumn(null);
    setStartX(0);
    setStartWidth(0);
  };

  useEffect(() => {
    if (resizingColumn) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      
      return () => {
        document.removeEventListener('mousemove', handleResizeMove);
        document.removeEventListener('mouseup', handleResizeEnd);
      };
    }
  }, [resizingColumn, startX, startWidth]);

  // Close column controls when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showColumnControls && !(event.target as Element).closest('.column-controls')) {
        setShowColumnControls(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showColumnControls]);

  // Get cluster color for a track - matches ClusterChart color scheme
  const getClusterColor = (trackId: number) => {
    const clusterId = trackClusterMap.get(trackId);
    if (clusterId === undefined) return { bg: 'bg-spotify-gray-600', border: 'border-spotify-gray-500', text: 'text-spotify-gray-300' };

    const colors = [
      { bg: 'bg-red-500', border: 'border-red-400', text: 'text-red-100' },      // #ef4444
      { bg: 'bg-blue-500', border: 'border-blue-400', text: 'text-blue-100' },   // #3b82f6
      { bg: 'bg-emerald-500', border: 'border-emerald-400', text: 'text-emerald-100' }, // #10b981
      { bg: 'bg-amber-500', border: 'border-amber-400', text: 'text-amber-100' }, // #f59e0b
      { bg: 'bg-violet-500', border: 'border-violet-400', text: 'text-violet-100' }, // #8b5cf6
      { bg: 'bg-pink-500', border: 'border-pink-400', text: 'text-pink-100' },   // #ec4899
      { bg: 'bg-indigo-500', border: 'border-indigo-400', text: 'text-indigo-100' }, // #6366f1
      { bg: 'bg-orange-500', border: 'border-orange-400', text: 'text-orange-100' }, // #f97316
    ];

    return colors[clusterId % colors.length] || { bg: 'bg-spotify-gray-600', border: 'border-spotify-gray-500', text: 'text-spotify-gray-300' };
  };

  // Create a map of track ID to cluster ID
  const trackClusterMap = useMemo(() => {
    const map = new Map<number, number>();
    clusters.forEach((cluster) => {
      cluster.track_ids.forEach((trackId: number) => {
        map.set(trackId, cluster.cluster_id);
      });
    });
    return map;
  }, [clusters]);

  // Get unique clusters for filtering
  const uniqueClusters = useMemo(() => {
    return clusters.map(cluster => ({
      id: cluster.cluster_id,
      label: cluster.label || `Cluster ${cluster.cluster_id}`,
      count: cluster.track_ids.length
    }));
  }, [clusters]);

  // Filtering and sorting
  const filteredAndSortedTracks = useMemo(() => {
    let filtered = tracks;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(track =>
        track.name.toLowerCase().includes(query) ||
        track.artist.toLowerCase().includes(query) ||
        (track.album && track.album.toLowerCase().includes(query))
      );
    }

    // Filter by cluster
    if (selectedCluster !== null) {
      filtered = filtered.filter(track => trackClusterMap.get(track.id) === selectedCluster);
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortField) {
        case 'cluster':
          aValue = trackClusterMap.get(a.id) ?? -1;
          bValue = trackClusterMap.get(b.id) ?? -1;
          break;
        default:
          aValue = a[sortField];
          bValue = b[sortField];
      }

      if (aValue == null) aValue = '';
      if (bValue == null) bValue = '';

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
    });

    return filtered;
  }, [tracks, searchQuery, selectedCluster, sortField, sortDirection, trackClusterMap]);

  // Selection handlers
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
    if (allSelected) {
      setSelectedTracks(new Set());
    } else {
      const allTrackIds = filteredAndSortedTracks.map(track => track.spotify_track_id);
      setSelectedTracks(new Set(allTrackIds));
    }
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const formatAudioFeature = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'N/A';
    if (value >= 1) return Math.round(value).toString(); // For values like tempo, loudness
    return `${Math.round(value * 100)}%`; // For 0-1 scale features
  };

  const formatKey = (key: number | null | undefined): string => {
    if (key === null || key === undefined) return 'N/A';
    const keyNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    return keyNames[key] || 'N/A';
  };

  const formatMode = (mode: number | null | undefined): string => {
    if (mode === null || mode === undefined) return 'N/A';
    return mode === 1 ? 'Major' : mode === 0 ? 'Minor' : 'N/A';
  };

  const toggleColumnVisibility = (column: keyof ColumnVisibility) => {
    setColumnVisibility(prev => ({
      ...prev,
      [column]: !prev[column]
    }));
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

  const renderResizableHeader = (columnKey: string, children: React.ReactNode) => (
    <th 
      className="relative p-3 text-left border-r border-spotify-gray-600 last:border-r-0 bg-spotify-gray-800"
      style={{ width: `${columnWidths[columnKey as keyof ColumnWidths]}px`, minWidth: '50px' }}
    >
      <div className="flex items-center justify-between">
        {children}
      </div>
      <div
        className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-spotify-green/50 transition-colors"
        onMouseDown={(e) => handleResizeStart(columnKey, e)}
      />
    </th>
  );

  const renderTableCell = (columnKey: string, children: React.ReactNode, className = '') => (
    <td 
      className={`p-3 border-r border-spotify-gray-700/30 last:border-r-0 ${className}`}
      style={{ 
        width: `${columnWidths[columnKey as keyof ColumnWidths]}px`, 
        minWidth: '50px',
        maxWidth: `${columnWidths[columnKey as keyof ColumnWidths]}px`
      }}
    >
      <div className="overflow-hidden">
        {children}
      </div>
    </td>
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

        <div className="flex gap-2">
          {/* Cluster Filter */}
          {uniqueClusters.length > 0 && (
            <select
              value={selectedCluster ?? ''}
              onChange={(e) => setSelectedCluster(e.target.value ? parseInt(e.target.value) : null)}
              className="px-3 py-2 bg-spotify-gray-700 border border-spotify-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-spotify-green"
            >
              <option value="">All Clusters</option>
              {uniqueClusters.map(cluster => (
                <option key={cluster.id} value={cluster.id}>
                  {cluster.label} ({cluster.count})
                </option>
              ))}
            </select>
          )}

          {/* Column Visibility Toggle */}
          <div className="relative column-controls">
            <button
              onClick={() => setShowColumnControls(!showColumnControls)}
              className="px-3 py-2 bg-spotify-gray-700 border border-spotify-gray-600 rounded-lg text-white hover:bg-spotify-gray-600 transition-colors flex items-center gap-2"
            >
              <Eye className="h-4 w-4" />
              Columns
            </button>
            
            {showColumnControls && (
              <div className="absolute right-0 top-full mt-2 bg-spotify-gray-800 border border-spotify-gray-700 rounded-lg shadow-lg z-10 p-4 w-64">
                <h4 className="text-white font-medium mb-3">Show/Hide Columns</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {Object.entries(columnVisibility).map(([key, visible]) => (
                    <label key={key} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={visible}
                        onChange={() => toggleColumnVisibility(key as keyof ColumnVisibility)}
                        className="h-4 w-4 text-spotify-green focus:ring-spotify-green border-spotify-gray-600 bg-spotify-gray-700 rounded"
                      />
                      <span className="text-spotify-gray-300 text-sm capitalize">
                        {key === 'cluster' ? 'Cluster' : 
                         key === 'popularity' ? 'Popularity' :
                         key === 'danceability' ? 'Danceability' :
                         key === 'energy' ? 'Energy' :
                         key === 'valence' ? 'Valence' :
                         key === 'tempo' ? 'Tempo' :
                         key === 'acousticness' ? 'Acousticness' :
                         key === 'instrumentalness' ? 'Instrumentalness' :
                         key === 'liveness' ? 'Liveness' :
                         key === 'speechiness' ? 'Speechiness' :
                         key === 'loudness' ? 'Loudness' :
                         key === 'key' ? 'Key' :
                         key === 'mode' ? 'Mode' : key}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Track Count and Selection Status */}
      <div className="text-sm text-spotify-gray-400">
        {selectedTracks.size > 0 && (
          <span className="mr-4 text-spotify-green">
            {selectedTracks.size} selected
          </span>
        )}
        {filteredAndSortedTracks.length} tracks
        {selectedCluster !== null && (() => {
          const cluster = clusters.find(c => c.cluster_id === selectedCluster);
          const label = cluster?.label || `Cluster ${selectedCluster}`;
          return ` in ${label}`;
        })()}
        {searchQuery && ` matching "${searchQuery}"`}
      </div>

      {/* Scrollable Table Container */}
      <div className="bg-spotify-gray-800/50 rounded-lg border border-spotify-gray-700">
        <div className="overflow-auto max-h-[600px]" style={{ minHeight: '400px' }}>
          <table className="w-full table-fixed">
            <thead className="sticky top-0 bg-spotify-gray-800 z-10">
              <tr className="border-b border-spotify-gray-700">
                {renderResizableHeader('checkbox', 
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(input) => {
                      if (input) input.indeterminate = partiallySelected;
                    }}
                    onChange={handleSelectAll}
                    className="h-4 w-4 text-spotify-green focus:ring-spotify-green border-spotify-gray-600 bg-spotify-gray-700 rounded"
                  />
                )}
                {renderResizableHeader('track', renderSortButton('name', 'Track'))}
                {renderResizableHeader('artist', renderSortButton('artist', 'Artist'))}
                {renderResizableHeader('album', renderSortButton('album', 'Album'))}
                {uniqueClusters.length > 0 && columnVisibility.cluster && 
                  renderResizableHeader('cluster', renderSortButton('cluster', 'Cluster'))
                }
                {columnVisibility.popularity && 
                  renderResizableHeader('popularity', renderSortButton('popularity', 'Pop'))
                }
                {columnVisibility.danceability && 
                  renderResizableHeader('danceability', renderSortButton('danceability', 'Dance'))
                }
                {columnVisibility.energy && 
                  renderResizableHeader('energy', renderSortButton('energy', 'Energy'))
                }
                {columnVisibility.valence && 
                  renderResizableHeader('valence', renderSortButton('valence', 'Valence'))
                }
                {columnVisibility.tempo && 
                  renderResizableHeader('tempo', renderSortButton('tempo', 'Tempo'))
                }
                {columnVisibility.acousticness && 
                  renderResizableHeader('acousticness', renderSortButton('acousticness', 'Acoustic'))
                }
                {columnVisibility.instrumentalness && 
                  renderResizableHeader('instrumentalness', renderSortButton('instrumentalness', 'Instru.'))
                }
                {columnVisibility.liveness && 
                  renderResizableHeader('liveness', renderSortButton('liveness', 'Live'))
                }
                {columnVisibility.speechiness && 
                  renderResizableHeader('speechiness', renderSortButton('speechiness', 'Speech'))
                }
                {columnVisibility.loudness && 
                  renderResizableHeader('loudness', renderSortButton('loudness', 'Loud'))
                }
                {columnVisibility.key && 
                  renderResizableHeader('key', renderSortButton('key', 'Key'))
                }
                {columnVisibility.mode && 
                  renderResizableHeader('mode', renderSortButton('mode', 'Mode'))
                }
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
                  {renderTableCell('checkbox', 
                    <input
                      type="checkbox"
                      checked={selectedTracks.has(track.spotify_track_id)}
                      onChange={() => handleSelectTrack(track.spotify_track_id)}
                      className="h-4 w-4 text-spotify-green focus:ring-spotify-green border-spotify-gray-600 bg-spotify-gray-700 rounded"
                    />
                  )}
                  {renderTableCell('track', 
                    <div className="flex items-center space-x-3">
                      <Music className="h-4 w-4 text-spotify-gray-400 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-white font-medium break-words leading-tight">{track.name}</p>
                      </div>
                    </div>
                  )}
                  {renderTableCell('artist', 
                    <p className="text-spotify-gray-300 break-words leading-tight">{track.artist}</p>
                  )}
                  {renderTableCell('album', 
                    <p className="text-spotify-gray-300 break-words leading-tight">{track.album || 'N/A'}</p>
                  )}
                  {uniqueClusters.length > 0 && columnVisibility.cluster && 
                    renderTableCell('cluster',
                      (() => {
                        const clusterId = trackClusterMap.get(track.id);
                        if (clusterId === undefined) {
                          return (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-spotify-gray-600 text-spotify-gray-300 border border-spotify-gray-500">
                              N/A
                            </span>
                          );
                        }
                        
                        const cluster = clusters.find(c => c.cluster_id === clusterId);
                        const colors = getClusterColor(track.id);
                        
                        return (
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text} border ${colors.border}`}>
                            {cluster?.label || `Cluster ${clusterId}`}
                          </span>
                        );
                      })()
                    )
                  }
                  {columnVisibility.popularity && 
                    renderTableCell('popularity',
                      <span className="text-spotify-gray-300">{track.popularity ?? 'N/A'}</span>
                    )
                  }
                  {columnVisibility.danceability && 
                    renderTableCell('danceability',
                      <span className="text-spotify-gray-300">{formatAudioFeature(track.danceability)}</span>
                    )
                  }
                  {columnVisibility.energy && 
                    renderTableCell('energy',
                      <span className="text-spotify-gray-300">{formatAudioFeature(track.energy)}</span>
                    )
                  }
                  {columnVisibility.valence && 
                    renderTableCell('valence',
                      <span className="text-spotify-gray-300">{formatAudioFeature(track.valence)}</span>
                    )
                  }
                  {columnVisibility.tempo && 
                    renderTableCell('tempo',
                      <span className="text-spotify-gray-300">{formatAudioFeature(track.tempo)}</span>
                    )
                  }
                  {columnVisibility.acousticness && 
                    renderTableCell('acousticness',
                      <span className="text-spotify-gray-300">{formatAudioFeature(track.acousticness)}</span>
                    )
                  }
                  {columnVisibility.instrumentalness && 
                    renderTableCell('instrumentalness',
                      <span className="text-spotify-gray-300">{formatAudioFeature(track.instrumentalness)}</span>
                    )
                  }
                  {columnVisibility.liveness && 
                    renderTableCell('liveness',
                      <span className="text-spotify-gray-300">{formatAudioFeature(track.liveness)}</span>
                    )
                  }
                  {columnVisibility.speechiness && 
                    renderTableCell('speechiness',
                      <span className="text-spotify-gray-300">{formatAudioFeature(track.speechiness)}</span>
                    )
                  }
                  {columnVisibility.loudness && 
                    renderTableCell('loudness',
                      <span className="text-spotify-gray-300">{formatAudioFeature(track.loudness)}</span>
                    )
                  }
                  {columnVisibility.key && 
                    renderTableCell('key',
                      <span className="text-spotify-gray-300">{formatKey(track.key)}</span>
                    )
                  }
                  {columnVisibility.mode && 
                    renderTableCell('mode',
                      <span className="text-spotify-gray-300">{formatMode(track.mode)}</span>
                    )
                  }
                </tr>
              ))}
              {filteredAndSortedTracks.length === 0 && (
                <tr>
                  <td colSpan={20} className="p-8 text-center">
                    <div className="text-spotify-gray-400">
                      <Music className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p className="text-lg font-medium mb-2">No tracks found</p>
                      <p className="text-sm">
                        {searchQuery ? `No tracks match "${searchQuery}"` : 'No tracks available'}
                        {selectedCluster !== null && (() => {
                          const cluster = clusters.find(c => c.cluster_id === selectedCluster);
                          const label = cluster?.label || `Cluster ${selectedCluster}`;
                          return ` in ${label}`;
                        })()}
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bulk Actions Modal */}
      {showBulkActions && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-spotify-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-white text-lg font-medium mb-4">
              Bulk Actions ({selectedTracks.size} tracks selected)
            </h3>
            <div className="space-y-3">
              <button
                onClick={() => {
                  if (onBulkAction) {
                    onBulkAction('move', { trackIds: Array.from(selectedTracks) });
                  }
                  setShowBulkActions(false);
                }}
                className="w-full px-4 py-2 bg-spotify-green text-white rounded-lg hover:bg-spotify-green/80 transition-colors"
              >
                Move to Playlist
              </button>
              <button
                onClick={() => {
                  if (onBulkAction) {
                    onBulkAction('delete', { trackIds: Array.from(selectedTracks) });
                  }
                  setShowBulkActions(false);
                }}
                className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Remove from Playlist
              </button>
              <button
                onClick={() => setShowBulkActions(false)}
                className="w-full px-4 py-2 bg-spotify-gray-600 text-white rounded-lg hover:bg-spotify-gray-500 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
