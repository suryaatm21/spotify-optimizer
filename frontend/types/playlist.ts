/**
 * TypeScript interfaces for playlist and track data structures.
 */

export interface IUser {
  id: number;
  spotify_user_id: string;
  display_name?: string;
  email?: string;
  created_at: string;
  updated_at: string;
}

export interface IPlaylist {
  id: number;
  spotify_playlist_id: string;
  name: string;
  description?: string;
  user_id: number;
  total_tracks: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface ITrack {
  id: number;
  spotify_track_id: string;
  name: string;
  artist: string;
  album?: string;
  duration_ms?: number;
  popularity?: number;
  playlist_id: number;
  created_at: string;
  
  // Audio features
  danceability?: number;
  energy?: number;
  key?: number;
  loudness?: number;
  mode?: number;
  speechiness?: number;
  acousticness?: number;
  instrumentalness?: number;
  liveness?: number;
  valence?: number;
  tempo?: number;
}

export interface IClusterData {
  cluster_id: number;
  track_count: number;
  center_features: Record<string, number>;
  track_ids: number[];
}

export interface IAnalysisResult {
  id: number;
  playlist_id: number;
  cluster_count: number;
  cluster_method: string;
  silhouette_score?: number;
  clusters: IClusterData[];
  created_at: string;
}

export interface IPlaylistStats {
  total_tracks: number;
  avg_duration_ms: number;
  avg_popularity: number;
  avg_audio_features: Record<string, number>;
  feature_ranges: Record<string, {
    min: number;
    max: number;
    std: number;
  }>;
}

export interface IOptimizationSuggestion {
  suggestion_type: string;
  description: string;
  affected_tracks: number[];
  confidence_score: number;
}

export interface IOptimizationResponse {
  playlist_id: number;
  current_stats: IPlaylistStats;
  suggestions: IOptimizationSuggestion[];
  analysis_id: number;
}

export interface ITokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  scope?: string;
}

export interface IAuthContext {
  user: IUser | null;
  login: (token: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
}
