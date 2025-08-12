/**
 * BulkActionsModal - Modal for handling bulk track operations
 */
import { useState } from 'react';
import { X, Move, Trash2, Plus, Search } from 'lucide-react';
import { mutate } from 'swr';

interface BulkActionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedTrackIds: string[];
  currentPlaylistId: string;
  trackNames: string[];
}

interface CreatePlaylistForm {
  name: string;
  description: string;
  is_public: boolean;
}

export default function BulkActionsModal({
  isOpen,
  onClose,
  selectedTrackIds,
  currentPlaylistId,
  trackNames,
}: BulkActionsModalProps) {
  const [action, setAction] = useState<'move' | 'delete' | 'create-and-move' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [playlists, setPlaylists] = useState<any[]>([]);
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<string>('');
  
  // Create new playlist form
  const [createForm, setCreateForm] = useState<CreatePlaylistForm>({
    name: '',
    description: '',
    is_public: true,
  });

  const handleSearchPlaylists = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/playlists', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPlaylists(data.filter((p: any) => p.id.toString() !== currentPlaylistId));
      }
    } catch (err) {
      console.error('Failed to fetch playlists:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMoveToExisting = async () => {
    if (!selectedPlaylistId) return;
    
    setIsLoading(true);
    setError(null);

    try {
      // Remove from current playlist
      for (const trackId of selectedTrackIds) {
        await fetch(`/api/playlists/${currentPlaylistId}/tracks/${trackId}`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
      }

      // Add to target playlist
      const response = await fetch(`/api/playlists/${selectedPlaylistId}/tracks?refresh=true`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          track_ids: selectedTrackIds,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to move tracks');
      }

      // Refresh current playlist data
      mutate(`/api/analytics/playlists/${currentPlaylistId}/tracks`);
      mutate(`/api/analytics/playlists/${currentPlaylistId}/stats`);
      
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to move tracks');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAndMove = async () => {
    if (!createForm.name.trim()) {
      setError('Playlist name is required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Create new playlist
      const createResponse = await fetch('/api/playlists', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(createForm),
      });

      if (!createResponse.ok) {
        throw new Error('Failed to create playlist');
      }

      const newPlaylist = await createResponse.json();

      // Remove from current playlist
      for (const trackId of selectedTrackIds) {
        await fetch(`/api/playlists/${currentPlaylistId}/tracks/${trackId}`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
      }

      // Add to new playlist
      await fetch(`/api/playlists/${newPlaylist.id}/tracks?refresh=true`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          track_ids: selectedTrackIds,
        }),
      });

      // Refresh data
      mutate(`/api/analytics/playlists/${currentPlaylistId}/tracks`);
      mutate(`/api/analytics/playlists/${currentPlaylistId}/stats`);
      mutate('/api/playlists');
      
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create playlist and move tracks');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const confirmed = window.confirm(
      `Are you sure you want to remove ${selectedTrackIds.length} track${selectedTrackIds.length !== 1 ? 's' : ''} from this playlist?`
    );

    if (!confirmed) return;

    setIsLoading(true);
    setError(null);

    try {
      for (const trackId of selectedTrackIds) {
        await fetch(`/api/playlists/${currentPlaylistId}/tracks/${trackId}`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
      }

      // Refresh current playlist data
      mutate(`/api/analytics/playlists/${currentPlaylistId}/tracks`);
      mutate(`/api/analytics/playlists/${currentPlaylistId}/stats`);
      
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove tracks');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-spotify-gray-800 rounded-xl max-w-md w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              Bulk Actions ({selectedTrackIds.length} tracks)
            </h3>
            <button
              onClick={onClose}
              className="text-spotify-gray-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-900/20 border border-red-700 rounded-md">
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          {/* Track Preview */}
          <div className="mb-4 p-3 bg-spotify-gray-700/50 rounded-md">
            <p className="text-sm text-spotify-gray-300 mb-2">Selected tracks:</p>
            <div className="max-h-24 overflow-y-auto">
              {trackNames.slice(0, 3).map((name, index) => (
                <p key={index} className="text-white text-sm truncate">• {name}</p>
              ))}
              {trackNames.length > 3 && (
                <p className="text-spotify-gray-400 text-sm">
                  ... and {trackNames.length - 3} more
                </p>
              )}
            </div>
          </div>

          {!action && (
            <div className="space-y-3">
              <button
                onClick={() => {
                  setAction('move');
                  handleSearchPlaylists();
                }}
                className="w-full flex items-center p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Move className="w-5 h-5 mr-2" />
                Move to Existing Playlist
              </button>
              
              <button
                onClick={() => setAction('create-and-move')}
                className="w-full flex items-center p-3 bg-spotify-green text-black rounded-lg hover:bg-spotify-green/90 transition-colors font-medium"
              >
                <Plus className="w-5 h-5 mr-2" />
                Create New Playlist & Move
              </button>
              
              <button
                onClick={handleDelete}
                className="w-full flex items-center p-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                disabled={isLoading}
              >
                <Trash2 className="w-5 h-5 mr-2" />
                Remove from Playlist
              </button>
            </div>
          )}

          {action === 'move' && (
            <div className="space-y-4">
              <h4 className="font-medium text-white">Select Playlist</h4>
              
              <div className="max-h-48 overflow-y-auto space-y-2">
                {playlists.map((playlist) => (
                  <button
                    key={playlist.id}
                    onClick={() => setSelectedPlaylistId(playlist.id.toString())}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedPlaylistId === playlist.id.toString()
                        ? 'bg-spotify-green/20 border border-spotify-green'
                        : 'bg-spotify-gray-700 hover:bg-spotify-gray-600'
                    }`}
                  >
                    <p className="text-white font-medium">{playlist.name}</p>
                    <p className="text-spotify-gray-400 text-sm">{playlist.total_tracks} tracks</p>
                  </button>
                ))}
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={() => setAction(null)}
                  className="flex-1 px-4 py-2 text-spotify-gray-300 border border-spotify-gray-600 rounded-lg hover:bg-spotify-gray-700 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleMoveToExisting}
                  disabled={!selectedPlaylistId || isLoading}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {isLoading ? 'Moving...' : 'Move Tracks'}
                </button>
              </div>
            </div>
          )}

          {action === 'create-and-move' && (
            <div className="space-y-4">
              <h4 className="font-medium text-white">Create New Playlist</h4>
              
              <div className="space-y-3">
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder="Playlist name"
                  className="w-full px-3 py-2 bg-spotify-gray-700 border border-spotify-gray-600 rounded-lg text-white placeholder-spotify-gray-400 focus:outline-none focus:ring-2 focus:ring-spotify-green"
                />
                
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="Description (optional)"
                  rows={2}
                  className="w-full px-3 py-2 bg-spotify-gray-700 border border-spotify-gray-600 rounded-lg text-white placeholder-spotify-gray-400 focus:outline-none focus:ring-2 focus:ring-spotify-green"
                />
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={createForm.is_public}
                    onChange={(e) => setCreateForm({ ...createForm, is_public: e.target.checked })}
                    className="h-4 w-4 text-spotify-green focus:ring-spotify-green border-spotify-gray-600 bg-spotify-gray-700 rounded mr-2"
                  />
                  <span className="text-spotify-gray-300 text-sm">Make playlist public</span>
                </label>
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={() => setAction(null)}
                  className="flex-1 px-4 py-2 text-spotify-gray-300 border border-spotify-gray-600 rounded-lg hover:bg-spotify-gray-700 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleCreateAndMove}
                  disabled={!createForm.name.trim() || isLoading}
                  className="flex-1 px-4 py-2 bg-spotify-green text-black rounded-lg hover:bg-spotify-green/90 transition-colors disabled:opacity-50 font-medium"
                >
                  {isLoading ? 'Creating...' : 'Create & Move'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
