/**
 * Playlist card component for displaying playlist information in the dashboard.
 */
import { Music, Play, BarChart3 } from 'lucide-react';
import { IPlaylist } from '@/types/playlist';

interface IPlaylistCardProps {
  playlist: IPlaylist;
  onSelect: (playlist: IPlaylist) => void;
  selected?: boolean;
}

export default function PlaylistCard({
  playlist,
  onSelect,
  selected = false,
}: IPlaylistCardProps) {
  const handleClick = () => {
    onSelect(playlist);
  };

  return (
    <div
      onClick={handleClick}
      className={`
        relative p-6 rounded-xl border transition-all duration-200 cursor-pointer
        ${
          selected
            ? 'bg-spotify-green/10 border-spotify-green shadow-lg shadow-spotify-green/20'
            : 'bg-spotify-gray-800/50 border-spotify-gray-700 hover:bg-spotify-gray-700/50 hover:border-spotify-gray-600'
        }
        backdrop-blur-sm group
      `}>
      {/* Playlist Info */}
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          <div className="w-16 h-16 bg-gradient-to-br from-spotify-green to-spotify-green/70 rounded-lg flex items-center justify-center">
            <Music className="h-8 w-8 text-white" />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-white truncate">
            {playlist.name}
          </h3>

          {playlist.description && (
            <p className="text-spotify-gray-400 text-sm mt-1 line-clamp-2">
              {playlist.description}
            </p>
          )}

          <div className="flex items-center space-x-4 mt-3">
            <div className="flex items-center space-x-1">
              <Music className="h-4 w-4 text-spotify-gray-500" />
              <span className="text-spotify-gray-400 text-sm">
                {playlist.total_tracks} tracks
              </span>
            </div>

            <div className="flex items-center space-x-1">
              <div
                className={`w-2 h-2 rounded-full ${
                  playlist.is_public ? 'bg-green-500' : 'bg-yellow-500'
                }`}
              />
              <span className="text-spotify-gray-400 text-sm">
                {playlist.is_public ? 'Public' : 'Private'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-4 flex items-center justify-between">
        <div className="text-spotify-gray-500 text-xs">
          Created: {new Date(playlist.created_at).toLocaleDateString()}
        </div>

        <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="p-2 bg-spotify-gray-700 hover:bg-spotify-gray-600 text-white rounded-lg transition-colors">
            <Play className="h-4 w-4" />
          </button>

          <button className="p-2 bg-spotify-green hover:bg-spotify-green/90 text-white rounded-lg transition-colors">
            <BarChart3 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Selection Indicator */}
      {selected && (
        <div className="absolute top-3 right-3">
          <div className="w-3 h-3 bg-spotify-green rounded-full" />
        </div>
      )}
    </div>
  );
}
