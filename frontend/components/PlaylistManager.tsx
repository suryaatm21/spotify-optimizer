/**
 * PlaylistManager - CRUD operations for playlist management
 * Provides functionality to create, update, and delete playlists
 */
import { useState } from 'react';
import { Trash2, Edit3, Plus, Save, X, RefreshCw } from 'lucide-react';
import { mutate } from 'swr';

interface PlaylistManagerProps {
  playlistId?: string;
  playlistName?: string;
  playlistDescription?: string;
  isPublic?: boolean;
  onPlaylistUpdated?: () => void;
}

interface CreatePlaylistForm {
  name: string;
  description: string;
  is_public: boolean;
}

interface UpdatePlaylistForm {
  name?: string;
  description?: string;
  is_public?: boolean;
}

export default function PlaylistManager({
  playlistId,
  playlistName = '',
  playlistDescription = '',
  isPublic = true,
  onPlaylistUpdated,
}: PlaylistManagerProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [editForm, setEditForm] = useState<UpdatePlaylistForm>({
    name: playlistName,
    description: playlistDescription,
    is_public: isPublic,
  });

  const [createForm, setCreateForm] = useState<CreatePlaylistForm>({
    name: '',
    description: '',
    is_public: true,
  });

  const handleCreatePlaylist = async () => {
    if (!createForm.name.trim()) {
      setError('Playlist name is required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/playlists', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(createForm),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create playlist');
      }

      const newPlaylist = await response.json();
      
      // Reset form
      setCreateForm({ name: '', description: '', is_public: true });
      setIsCreating(false);
      
      // Refresh playlists list
      mutate('/api/playlists');
      
      if (onPlaylistUpdated) {
        onPlaylistUpdated();
      }

      console.log('Playlist created:', newPlaylist);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create playlist');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdatePlaylist = async () => {
    if (!playlistId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/playlists/${playlistId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(editForm),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update playlist');
      }

      const updatedPlaylist = await response.json();
      setIsEditing(false);
      
      // Refresh current playlist data
      mutate(`/api/analytics/playlists/${playlistId}/stats`);
      
      if (onPlaylistUpdated) {
        onPlaylistUpdated();
      }

      console.log('Playlist updated:', updatedPlaylist);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update playlist');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeletePlaylist = async () => {
    if (!playlistId) return;
    
    const confirmed = window.confirm(
      'Are you sure you want to remove this playlist? This will unfollow it from your Spotify library and remove all local analysis data.'
    );
    
    if (!confirmed) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/playlists/${playlistId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete playlist');
      }

      // Refresh playlists list
      mutate('/api/playlists');
      
      if (onPlaylistUpdated) {
        onPlaylistUpdated();
      }

      // Redirect to main page
      window.location.href = '/';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete playlist');
    } finally {
      setIsLoading(false);
    }
  };

  const resetEditForm = () => {
    setEditForm({
      name: playlistName,
      description: playlistDescription,
      is_public: isPublic,
    });
    setIsEditing(false);
    setError(null);
  };

  const resetCreateForm = () => {
    setCreateForm({ name: '', description: '', is_public: true });
    setIsCreating(false);
    setError(null);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Playlist Management
        </h3>
        
        <div className="flex space-x-2">
          {!isCreating && (
            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              disabled={isLoading}
            >
              <Plus className="w-4 h-4 mr-1" />
              New Playlist
            </button>
          )}
          
          {playlistId && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              disabled={isLoading}
            >
              <Edit3 className="w-4 h-4 mr-1" />
              Edit
            </button>
          )}
          
          {playlistId && !isEditing && (
            <button
              onClick={handleDeletePlaylist}
              className="flex items-center px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              disabled={isLoading}
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Delete
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Create New Playlist Form */}
      {isCreating && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <h4 className="font-medium text-green-900 mb-3">Create New Playlist</h4>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <input
                type="text"
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="Enter playlist name"
                disabled={isLoading}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="Enter playlist description"
                rows={2}
                disabled={isLoading}
              />
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="create-public"
                checked={createForm.is_public}
                onChange={(e) => setCreateForm({ ...createForm, is_public: e.target.checked })}
                className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                disabled={isLoading}
              />
              <label htmlFor="create-public" className="ml-2 block text-sm text-gray-700">
                Make playlist public
              </label>
            </div>
          </div>
          
          <div className="flex justify-end space-x-2 mt-4">
            <button
              onClick={resetCreateForm}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              disabled={isLoading}
            >
              <X className="w-4 h-4 mr-1 inline" />
              Cancel
            </button>
            <button
              onClick={handleCreatePlaylist}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
              disabled={isLoading || !createForm.name.trim()}
            >
              {isLoading ? (
                <RefreshCw className="w-4 h-4 mr-1 inline animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-1 inline" />
              )}
              Create
            </button>
          </div>
        </div>
      )}

      {/* Edit Existing Playlist Form */}
      {isEditing && playlistId && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
          <h4 className="font-medium text-blue-900 mb-3">Edit Playlist</h4>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <input
                type="text"
                value={editForm.name || ''}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter playlist name"
                disabled={isLoading}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={editForm.description || ''}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter playlist description"
                rows={2}
                disabled={isLoading}
              />
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="edit-public"
                checked={editForm.is_public || false}
                onChange={(e) => setEditForm({ ...editForm, is_public: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={isLoading}
              />
              <label htmlFor="edit-public" className="ml-2 block text-sm text-gray-700">
                Make playlist public
              </label>
            </div>
          </div>
          
          <div className="flex justify-end space-x-2 mt-4">
            <button
              onClick={resetEditForm}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              disabled={isLoading}
            >
              <X className="w-4 h-4 mr-1 inline" />
              Cancel
            </button>
            <button
              onClick={handleUpdatePlaylist}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              disabled={isLoading}
            >
              {isLoading ? (
                <RefreshCw className="w-4 h-4 mr-1 inline animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-1 inline" />
              )}
              Save Changes
            </button>
          </div>
        </div>
      )}

      {/* Current Playlist Info */}
      {playlistId && !isEditing && (
        <div className="text-sm text-gray-600">
          <p><strong>Current:</strong> {playlistName}</p>
          {playlistDescription && <p><strong>Description:</strong> {playlistDescription}</p>}
          <p><strong>Visibility:</strong> {isPublic ? 'Public' : 'Private'}</p>
        </div>
      )}
    </div>
  );
}
