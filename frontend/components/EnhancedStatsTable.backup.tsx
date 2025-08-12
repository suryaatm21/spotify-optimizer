/**import React, { useState, useMemo, useEffect, useRef } from 'react';
import { ChevronDown, ChevronUp, Search, Music, Filter, Eye, EyeOff } from 'lucide-react';
import { Track, ClusterResult } from '../types';
import BulkActionsModal from './BulkActionsModal'; Enhanced StatsTable with track selection and bulk operations
 */
import { useState, useMemo, useEffect } from 'react';
import { ChevronUp, ChevronDown, Music, Search, X, Eye, EyeOff } from 'lucide-react';
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
      className="relative p-3 text-left border-r border-spotify-gray-600 last:border-r-0"
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
          {uniqueClusters.length > 0 && (
            <select
              value={selectedCluster ?? ''}
              onChange={(e) => setSelectedCluster(e.target.value ? parseInt(e.target.value) : null)}
              className="px-3 py-2 bg-spotify-gray-700 border border-spotify-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-spotify-green"
            >
              <option value="">All Clusters</option>
              {uniqueClusters.map((clusterId) => {
                const cluster = clusters.find(c => c.cluster_id === clusterId);
                const label = cluster?.label || `Cluster ${clusterId}`;
                return (
                  <option key={clusterId} value={clusterId}>
                    {label}
                  </option>
                );
              })}
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
        {selectedCluster !== null && (() => {
          const cluster = clusters.find(c => c.cluster_id === selectedCluster);
          const label = cluster?.label || `Cluster ${selectedCluster}`;
          return ` in ${label}`;
        })()}
        {searchQuery && ` matching "${searchQuery}"`}
      </div>

      {/* Table Container - Scrollable */}
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
              {columnVisibility.liveness && (
                <th className="p-3 text-left">{renderSortButton('liveness', 'Live')}</th>
              )}
              {columnVisibility.speechiness && (
                <th className="p-3 text-left">{renderSortButton('speechiness', 'Speech')}</th>
              )}
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
                      <p className="text-white font-medium break-words">{track.name}</p>
                    </div>
                  </div>
                )}
                {renderTableCell('artist', 
                  <p className="text-spotify-gray-300 break-words">{track.artist}</p>
                )}
                {renderTableCell('album', 
                  <p className="text-spotify-gray-300 break-words">{track.album || 'N/A'}</p>
                )}
                {uniqueClusters.length > 0 && columnVisibility.cluster && 
                  renderTableCell('cluster',
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-900/20 text-blue-300 border border-blue-700/30 break-words">
                      {(() => {
                        const clusterId = trackClusterMap.get(track.id);
                        if (clusterId === undefined) return 'N/A';
                        const cluster = clusters.find(c => c.cluster_id === clusterId);
                        return cluster?.label || `Cluster ${clusterId}`;
                      })()}
                    </span>
                  )
                }
                        const cluster = clusters.find(c => c.cluster_id === clusterId);
                        return cluster?.label || `Cluster ${clusterId}`;
                      })()}
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
                  </td>
                )}
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
      <BulkActionsModal
        selectedTracks={Array.from(selectedTracks)}
        onClose={() => setShowBulkActions(false)}
        onAction={onBulkAction}
      />
    )}
  </div>
  );
}
