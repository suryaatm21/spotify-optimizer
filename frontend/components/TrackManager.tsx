/**
 * TrackManager - CRUD operations for track management within playlists
 * Provides functionality to add and remove tracks from playlists
 */
import { useState } from 'react';
import { Search, Plus, Trash2, X, RefreshCw, Music } from 'lucide-react';
import { mutate } from 'swr';

interface TrackManagerProps {
  playlistId: string;
  tracks?: any[];
  onTracksUpdated?: () => void;
}

interface SearchResult {
  id: string;
  name: string;
  artists: { name: string }[];
  album: { name: string };
  duration_ms: number;
  preview_url?: string;
}

export default function TrackManager({
  playlistId,
  tracks = [],
  onTracksUpdated,
}: TrackManagerProps) {
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTracks, setSelectedTracks] = useState<Set<string>>(new Set());

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Search using Spotify API through our backend
      const response = await fetch(
        `/api/search?q=${encodeURIComponent(searchQuery)}&type=track&limit=20`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to search tracks');
      }

      const data = await response.json();
      setSearchResults(data.tracks?.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search tracks');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddTracks = async (trackIds: string[]) => {
    if (trackIds.length === 0) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/playlists/${playlistId}/tracks?refresh=true`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          track_ids: trackIds,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add tracks');
      }

      // Clear selections and search
      setSelectedTracks(new Set());
      setSearchResults([]);
      setSearchQuery('');
      setIsSearching(false);

      // Refresh tracks list
      mutate(`/api/analytics/playlists/${playlistId}/tracks`);
      mutate(`/api/analytics/playlists/${playlistId}/stats`);

      if (onTracksUpdated) {
        onTracksUpdated();
      }

      console.log(`Added ${trackIds.length} tracks to playlist`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add tracks');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveTrack = async (spotifyTrackId: string, trackName: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to remove "${trackName}" from this playlist?`
    );

    if (!confirmed) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/playlists/${playlistId}/tracks/${spotifyTrackId}?refresh=true`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to remove track');
      }

      // Refresh tracks list
      mutate(`/api/analytics/playlists/${playlistId}/tracks`);
      mutate(`/api/analytics/playlists/${playlistId}/stats`);

      if (onTracksUpdated) {
        onTracksUpdated();
      }

      console.log(`Removed track: ${trackName}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove track');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTrackSelection = (trackId: string) => {
    const newSelection = new Set(selectedTracks);
    if (newSelection.has(trackId)) {
      newSelection.delete(trackId);
    } else {
      newSelection.add(trackId);
    }
    setSelectedTracks(newSelection);
  };

  const formatDuration = (durationMs: number): string => {
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Track Management
        </h3>
        
        <button
          onClick={() => setIsSearching(!isSearching)}
          className="flex items-center px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          disabled={isLoading}
        >
          {isSearching ? (
            <>
              <X className="w-4 h-4 mr-1" />
              Cancel
            </>
          ) : (
            <>
              <Plus className="w-4 h-4 mr-1" />
              Add Tracks
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Search Interface */}
      {isSearching && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <h4 className="font-medium text-green-900 mb-3">Search & Add Tracks</h4>
          
          <div className="flex space-x-2 mb-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Search for tracks, artists, or albums..."
              disabled={isLoading}
            />
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
              disabled={isLoading || !searchQuery.trim()}
            >
              {isLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-600">
                  {searchResults.length} results found
                </span>
                {selectedTracks.size > 0 && (
                  <button
                    onClick={() => handleAddTracks(Array.from(selectedTracks))}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 transition-colors"
                    disabled={isLoading}
                  >
                    Add {selectedTracks.size} selected
                  </button>
                )}
              </div>
              
              <div className="max-h-96 overflow-y-auto">
                {searchResults.map((track) => (
                  <div
                    key={track.id}
                    className={`flex items-center p-3 border rounded-md mb-2 cursor-pointer transition-colors ${
                      selectedTracks.has(track.id)
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => toggleTrackSelection(track.id)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedTracks.has(track.id)}
                      onChange={() => {}} // Handled by parent onClick
                      className="mr-3 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                    />
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center">
                        <Music className="w-4 h-4 text-gray-400 mr-2 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {track.name}
                          </p>
                          <p className="text-sm text-gray-500 truncate">
                            {track.artists.map(a => a.name).join(', ')} • {track.album.name}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <span className="text-sm text-gray-400 ml-2">
                      {formatDuration(track.duration_ms)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {searchResults.length === 0 && searchQuery && !isLoading && (
            <div className="text-center py-8 text-gray-500">
              <Music className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No tracks found for "{searchQuery}"</p>
              <p className="text-sm">Try a different search term</p>
            </div>
          )}
        </div>
      )}

      {/* Current Tracks with Remove Options */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">
          Current Tracks ({tracks.length})
        </h4>
        
        {tracks.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Music className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No tracks in this playlist</p>
            <p className="text-sm">Add some tracks to get started</p>
          </div>
        ) : (
          <div className="max-h-96 overflow-y-auto">
            {tracks.map((track, index) => (
              <div
                key={`${track.spotify_track_id}-${index}`}
                className="flex items-center p-3 border border-gray-200 rounded-md mb-2 hover:bg-gray-50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center">
                    <Music className="w-4 h-4 text-gray-400 mr-2 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {track.name}
                      </p>
                      <p className="text-sm text-gray-500 truncate">
                        {track.artist} • {track.album}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-400">
                    {formatDuration(track.duration_ms)}
                  </span>
                  <button
                    onClick={() => handleRemoveTrack(track.spotify_track_id, track.name)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                    disabled={isLoading}
                    title="Remove track"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
