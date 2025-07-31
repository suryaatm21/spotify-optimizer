"""
ReccoBeats API service for audio features extraction.
This service replaces the deprecated Spotify audio features endpoint.
"""
from typing import List, Dict, Any, Optional
import httpx
import os
from dataclasses import dataclass

@dataclass
class ReccoBeatsConfig:
    """Configuration for ReccoBeats API."""
    base_url: str = "https://api.reccobeats.com/v1"
    api_key: Optional[str] = None  # Not required - API is public
    timeout: float = 30.0
    
    def __post_init__(self):
        """Load API key from environment if not provided (optional for ReccoBeats)."""
        if not self.api_key:
            self.api_key = os.getenv("RECCOBEATS_API_KEY")  # Optional


class ReccoBeatsService:
    """
    Service for interacting with ReccoBeats API to extract audio features.
    """
    
    def __init__(self, config: Optional[ReccoBeatsConfig] = None):
        """
        Initialize ReccoBeats service.
        
        Args:
            config: ReccoBeats configuration. If None, uses default config.
        """
        self.config = config or ReccoBeatsConfig()
        
        # API key is optional for ReccoBeats - no authentication required
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for ReccoBeats API requests.
        
        Returns:
            Dict[str, str]: Request headers
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Add API key to headers only if provided (authentication is optional)
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
            # Alternative: headers["X-API-Key"] = self.config.api_key
        
        return headers
    
    async def get_track_audio_features(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Get audio features for a single track from ReccoBeats API.
        
        ReccoBeats requires a two-step process:
        1. Get track info using Spotify ID to retrieve ReccoBeats internal UUID
        2. Use the UUID to fetch audio features
        
        Args:
            track_id: Spotify track ID or URI
        
        Returns:
            Dict[str, Any] | None: Audio features data if found, else None
        """
        # Step 1: Get ReccoBeats internal UUID using Spotify ID
        reccobeats_uuid = await self._get_reccobeats_uuid(track_id)
        if not reccobeats_uuid:
            return None
        
        # Step 2: Get audio features using the UUID
        url = f"{self.config.base_url}/track/{reccobeats_uuid}/audio-features"
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    print(f"❌ Audio features not found for ReccoBeats UUID: {reccobeats_uuid}")
                    return None
                else:
                    print(f"ReccoBeats audio features error {response.status_code}: {response.text[:200]}")
                    return None
                    
        except Exception as e:
            print(f"Error fetching audio features for {track_id}: {e}")
            return None

    async def _get_reccobeats_uuid(self, spotify_track_id: str) -> Optional[str]:
        """
        Get ReccoBeats internal UUID for a Spotify track ID.
        
        Args:
            spotify_track_id: Spotify track ID or URI
            
        Returns:
            str | None: ReccoBeats internal UUID if found, else None
        """
        # Clean the Spotify track ID
        clean_id = spotify_track_id.split(":")[-1]
        
        url = f"{self.config.base_url}/track"
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    url, 
                    params={"ids": clean_id},
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "content" in data and data["content"]:
                        # Return the ReccoBeats internal ID
                        return data["content"][0].get("id")
                    else:
                        print(f"❌ Track not found in ReccoBeats: {clean_id}")
                        return None
                else:
                    print(f"ReccoBeats track lookup error {response.status_code}: {response.text[:200]}")
                    return None
                    
        except Exception as e:
            print(f"Error getting ReccoBeats UUID for {spotify_track_id}: {e}")
            return None

    async def get_multiple_tracks_audio_features(self, track_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get audio features for multiple tracks from ReccoBeats API in bulk.

        Args:
            track_ids: A list of Spotify track IDs.

        Returns:
            A dictionary mapping Spotify track IDs to their audio features.
        """
        if not track_ids:
            return {}
        print(f"ReccoBeats: Getting audio features for {len(track_ids)} tracks.")

        # Step 1: Get ReccoBeats internal UUIDs for all Spotify IDs
        uuid_map = await self._get_multiple_reccobeats_uuids(track_ids)
        if not uuid_map:
            print("ReccoBeats: No UUIDs found, aborting audio feature fetch.")
            return {}
        print(f"ReccoBeats: UUID map received: {uuid_map}")

        reccobeats_uuids = list(uuid_map.values())
        print(f"ReccoBeats: Fetching features for UUIDs: {reccobeats_uuids}")
        
        # Step 2: Fetch audio features in bulk using the UUIDs
        url = f"{self.config.base_url}/audio-features"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    url,
                    params={"ids": ",".join(reccobeats_uuids)},
                    headers=self._get_headers()
                )
                print(f"ReccoBeats audio features response: {response.status_code}")

                if response.status_code != 200:
                    print(f"ReccoBeats bulk audio features error {response.status_code}: {response.text[:200]}")
                    return {}

                features_data = response.json().get("audio_features", [])
                print(f"ReccoBeats audio features response data: {features_data}")
                if not features_data:
                    return {}

                # Create a map from ReccoBeats UUID back to features
                features_by_uuid = {f["id"]: f for f in features_data if f}

                # Map features back to the original Spotify IDs
                result = {}
                for spotify_id, reccobeats_uuid in uuid_map.items():
                    if reccobeats_uuid in features_by_uuid:
                        result[spotify_id] = features_by_uuid[reccobeats_uuid]
                
                print(f"ReccoBeats: Successfully mapped {len(result)} features back to Spotify IDs.")
                return result

        except Exception as e:
            print(f"Error fetching bulk audio features: {e}")
            return {}

    async def _get_multiple_reccobeats_uuids(self, spotify_track_ids: List[str]) -> Dict[str, str]:
        """
        Get ReccoBeats internal UUIDs for a list of Spotify track IDs in bulk.

        Args:
            spotify_track_ids: A list of Spotify track IDs.

        Returns:
            A dictionary mapping Spotify track IDs to ReccoBeats internal UUIDs.
        """
        print(f"ReccoBeats: Getting UUIDs for {len(spotify_track_ids)} Spotify IDs.")
        clean_ids = list(set([tid.split(":")[-1] for tid in spotify_track_ids]))
        print(f"ReccoBeats: Cleaned IDs to fetch: {clean_ids}")
        url = f"{self.config.base_url}/track"
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    url,
                    params={"ids": ",".join(clean_ids)},
                    headers=self._get_headers()
                )
                print(f"ReccoBeats UUID lookup response: {response.status_code}")

                if response.status_code != 200:
                    print(f"ReccoBeats bulk track lookup error {response.status_code}: {response.text[:200]}")
                    return {}

                data = response.json()
                print(f"ReccoBeats UUID lookup response data: {data}")
                if "content" in data and data["content"]:
                    # The API returns a list, so we need to map IDs back
                    spotify_id_map = {item.get("spotify_id"): item.get("id") for item in data["content"] if item.get("spotify_id") and item.get("id")}
                    print(f"ReccoBeats: Found {len(spotify_id_map)} UUIDs.")
                    return spotify_id_map
                return {}

        except Exception as e:
            print(f"Error getting bulk ReccoBeats UUIDs: {e}")
            return {}

    def map_features_to_spotify_format(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps feature names from ReccoBeats format to Spotify/model format.
        Currently, the names are assumed to be identical.

        Args:
            features: A dictionary of audio features from ReccoBeats.

        Returns:
            A dictionary with keys matching the Track model fields.
        """
        # Assuming direct mapping for now as keys seem to match
        return features
    
    async def get_track_details(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Get track details from ReccoBeats API.
        
        Args:
            track_id: Spotify track ID
            
        Returns:
            Dict[str, Any]: Track details or None if request fails
        """
        url = f"{self.config.base_url}/track/{track_id}"
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"ReccoBeats track details error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error fetching track details for {track_id}: {e}")
            return None
    
    async def get_multiple_tracks_audio_features(self, track_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get audio features for multiple tracks using the two-step ReccoBeats process:
        1. Get track info with Spotify IDs to retrieve ReccoBeats UUIDs
        2. Use UUIDs to fetch audio features individually
        
        Args:
            track_ids: List of Spotify track IDs
            
        Returns:
            Dict[str, Dict[str, Any]]: Mapping of Spotify track_id to audio features
        """
        features_map = {}
        
        print(f"🎵 Fetching audio features for {len(track_ids)} tracks from ReccoBeats...")
        
        # Step 1: Get ReccoBeats UUIDs for all tracks in bulk
        print("� Step 1: Getting ReccoBeats UUIDs for all tracks...")
        uuid_mapping = await self._get_multiple_reccobeats_uuids(track_ids)
        
        if not uuid_mapping:
            print("❌ No tracks found in ReccoBeats")
            return {}
        
        print(f"✅ Found ReccoBeats UUIDs for {len(uuid_mapping)}/{len(track_ids)} tracks")
        
        # Step 2: Get audio features using the UUIDs
        print("🎶 Step 2: Fetching audio features using UUIDs...")
        
        # Process in chunks to avoid overwhelming the API
        CHUNK_SIZE = 10
        spotify_ids = list(uuid_mapping.keys())
        
        for i in range(0, len(spotify_ids), CHUNK_SIZE):
            chunk_spotify_ids = spotify_ids[i:i + CHUNK_SIZE]
            
            # Process chunk concurrently
            import asyncio
            tasks = []
            for spotify_id in chunk_spotify_ids:
                reccobeats_uuid = uuid_mapping[spotify_id]
                task = self._get_audio_features_by_uuid(reccobeats_uuid, spotify_id)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Map results back to Spotify track IDs
            for spotify_id, result in zip(chunk_spotify_ids, results):
                if isinstance(result, dict) and result:
                    features_map[spotify_id] = result
                elif isinstance(result, Exception):
                    print(f"Exception for track {spotify_id}: {result}")
            
            # Add delay between chunks to respect rate limits
            if i + CHUNK_SIZE < len(spotify_ids):
                await asyncio.sleep(0.1)  # 100ms delay
        
        print(f"✅ Successfully fetched audio features for {len(features_map)}/{len(track_ids)} tracks")
        return features_map

    async def _get_multiple_reccobeats_uuids(self, spotify_track_ids: List[str]) -> Dict[str, str]:
        """
        Get ReccoBeats UUIDs for multiple Spotify track IDs using bulk endpoint.
        
        Args:
            spotify_track_ids: List of Spotify track IDs
            
        Returns:
            Dict[str, str]: Mapping of Spotify track ID to ReccoBeats UUID
        """
        if not spotify_track_ids:
            return {}
        
        # Clean track IDs
        clean_ids = [tid.split(":")[-1] for tid in spotify_track_ids]
        ids_param = ",".join(clean_ids)
        
        url = f"{self.config.base_url}/track"
        uuid_mapping = {}
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    url, 
                    params={"ids": ids_param},
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "content" in data:
                        for track in data["content"]:
                            # Extract Spotify ID from href and map to ReccoBeats UUID
                            if "href" in track and "spotify.com/track/" in track["href"] and "id" in track:
                                spotify_id = track["href"].split("/")[-1]
                                reccobeats_uuid = track["id"]
                                uuid_mapping[spotify_id] = reccobeats_uuid
                    
                    return uuid_mapping
                else:
                    print(f"ReccoBeats bulk track lookup error: {response.status_code} - {response.text[:200]}")
                    return {}
                    
        except Exception as e:
            print(f"Error getting ReccoBeats UUIDs: {e}")
            return {}

    async def _get_audio_features_by_uuid(self, reccobeats_uuid: str, spotify_id: str) -> Optional[Dict[str, Any]]:
        """
        Get audio features using ReccoBeats internal UUID.
        
        Args:
            reccobeats_uuid: ReccoBeats internal UUID
            spotify_id: Original Spotify ID for logging
            
        Returns:
            Dict[str, Any] | None: Audio features if found, else None
        """
        url = f"{self.config.base_url}/track/{reccobeats_uuid}/audio-features"
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    print(f"❌ Audio features not available for {spotify_id} (UUID: {reccobeats_uuid})")
                    return None
                else:
                    print(f"ReccoBeats audio features error for {spotify_id}: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error fetching audio features for {spotify_id}: {e}")
            return None

    async def get_multiple_tracks_info(self, track_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get track information using the bulk endpoint (works without authentication).
        
        Args:
            track_ids: List of Spotify track IDs
            
        Returns:
            Dict[str, Dict[str, Any]]: Mapping of track_id to track data
        """
        if not track_ids:
            return {}
            
        # Clean track IDs
        clean_ids = [tid.split(":")[-1] for tid in track_ids]
        ids_param = ",".join(clean_ids)
        
        url = f"{self.config.base_url}/track"
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    url, 
                    params={"ids": ids_param},
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    tracks_data = {}
                    
                    # Map response content to track IDs
                    if "content" in data:
                        for track in data["content"]:
                            # Extract Spotify ID from href if available
                            if "href" in track and "spotify.com/track/" in track["href"]:
                                spotify_id = track["href"].split("/")[-1]
                                tracks_data[spotify_id] = track
                    
                    print(f"✅ Found {len(tracks_data)} tracks in ReccoBeats bulk endpoint")
                    return tracks_data
                else:
                    print(f"ReccoBeats bulk tracks error: {response.status_code} - {response.text[:200]}")
                    return {}
                    
        except Exception as e:
            print(f"Error fetching bulk tracks: {e}")
            return {}
    
    async def extract_audio_features(self, audio_data: Any) -> Optional[Dict[str, Any]]:
        """
        Extract audio features using ReccoBeats analysis endpoint.
        
        Args:
            audio_data: Audio data to analyze (format depends on API requirements)
            
        Returns:
            Dict[str, Any]: Extracted audio features or None if request fails
        """
        url = f"{self.config.base_url}/analysis/audio-features"
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    url, 
                    headers=self._get_headers(),
                    json=audio_data  # Adjust based on API requirements
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"ReccoBeats analysis error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error extracting audio features: {e}")
            return None
    
    def map_features_to_spotify_format(self, reccobeats_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map ReccoBeats audio features to Spotify-compatible format.
        
        Args:
            reccobeats_features: Audio features from ReccoBeats API
            
        Returns:
            Dict[str, Any]: Features mapped to match our database schema
        """
        # This mapping will need to be adjusted based on actual ReccoBeats response format
        # For now, assume similar structure to Spotify
        
        # Standard audio features we expect
        expected_features = [
            'danceability', 'energy', 'key', 'loudness', 'mode',
            'speechiness', 'acousticness', 'instrumentalness', 
            'liveness', 'valence', 'tempo'
        ]
        
        mapped_features = {}
        
        for feature in expected_features:
            # Try direct mapping first
            if feature in reccobeats_features:
                mapped_features[feature] = reccobeats_features[feature]
            # Add any custom mapping logic here based on ReccoBeats API response
            # e.g., if ReccoBeats uses different field names
        
        return mapped_features


# Example usage and testing
async def test_reccobeats_service():
    """Test function for ReccoBeats service."""
    try:
        service = ReccoBeatsService()
        
        # Test with Despacito - we know this works in ReccoBeats
        test_track_id = "6habFhsOp2NvshLv26DqMb"  # Despacito - verified working
        
        print(f"Testing ReccoBeats service with track ID: {test_track_id}")
        
        # Test audio features
        print("🎵 Testing single track audio features...")
        features = await service.get_track_audio_features(test_track_id)
        if features:
            print(f"✅ Audio features retrieved: {list(features.keys())}")
            mapped = service.map_features_to_spotify_format(features)
            print(f"✅ Mapped features: {mapped}")
        else:
            print("❌ Failed to retrieve audio features")
        
        # Test multiple tracks
        print("\n🎵 Testing multiple tracks audio features...")
        test_tracks = [test_track_id, "11dFghVXANMlKmJXsNCbNl"]  # Add another test track
        multi_features = await service.get_multiple_tracks_audio_features(test_tracks)
        if multi_features:
            print(f"✅ Multi-track audio features retrieved for {len(multi_features)} tracks")
            for track_id, features in multi_features.items():
                print(f"  - {track_id}: {list(features.keys())}")
        else:
            print("❌ Failed to retrieve multi-track audio features")
        
        # Test track info
        print("\n📋 Testing track info...")
        track_info = await service.get_multiple_tracks_info([test_track_id])
        if track_info:
            print(f"✅ Track info retrieved: {list(track_info.keys())}")
            for track_id, info in track_info.items():
                print(f"  - {track_id}: {info.get('trackTitle', 'Unknown')} by {info.get('artists', [{}])[0].get('artistName', 'Unknown')}")
        else:
            print("❌ Failed to retrieve track info")
            
    except Exception as e:
        print(f"❌ ReccoBeats service test failed: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_reccobeats_service())
