"""
CRUD router for playlist and track management via Spotify API.
Implements create/update/delete operations and optional DB refresh.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import httpx
from pydantic import BaseModel

from backend.dependencies import (
    get_database, get_current_user, get_audio_features_service
)
from backend.models import User, Playlist, Track
from backend.schemas import (
    PlaylistResponse,
    TrackResponse
)
from ..services.audio_features import AudioFeaturesService

router = APIRouter()

class PlaylistCreateInput(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True

class PlaylistUpdateInput(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class AddTracksRequest(BaseModel):
    track_ids: List[str]

@router.get("/search")
async def search_tracks(
    q: str = Query(..., description="Search query"),
    type: str = Query("track", description="Search type"),
    limit: int = Query(20, description="Number of results"),
    current_user: User = Depends(get_current_user)
):
    """
    Search for tracks using Spotify API.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Authorization": f"Bearer {current_user.access_token}"}
        
        try:
            response = await client.get(
                "https://api.spotify.com/v1/search",
                headers=headers,
                params={
                    "q": q,
                    "type": type,
                    "limit": limit
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Spotify search failed: {response.text}"
                )
            
            return response.json()
        except Exception as e:
            if "timeout" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail="Search request timed out - please try again"
                )
            elif "json" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid response from Spotify API"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search failed: {str(e)}"
            )

async def _refresh_playlist_in_db(
    playlist: Playlist,
    current_user: User,
    db: Session,
    audio_features_service: AudioFeaturesService
) -> List[Track]:
    """Fetch playlist tracks and features from Spotify and upsert into DB."""
    import logging
    logger = logging.getLogger(__name__)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        access_token = current_user.access_token
        headers = {"Authorization": f"Bearer {access_token}"}

        # Fetch all tracks using pagination
        all_tracks_items = []
        offset = 0
        limit = 100

        try:
            while True:
                tracks_response = await client.get(
                    f"https://api.spotify.com/v1/playlists/{playlist.spotify_playlist_id}/tracks",
                    headers=headers,
                    params={
                        "limit": limit,
                        "offset": offset,
                        "fields": "items(track(id,name,artists,album,duration_ms,popularity)),next"
                    }
                )

                if tracks_response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to fetch tracks from Spotify: {tracks_response.text}"
                    )

                try:
                    batch_data = tracks_response.json()
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to parse Spotify response: {str(e)}"
                    )
                    
                items = batch_data.get("items", [])
                all_tracks_items.extend(items)

                if not batch_data.get("next") or len(items) < limit:
                    break

                offset += limit
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail="Timeout fetching tracks from Spotify")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")

    # Count before refresh
    existing_tracks = db.query(Track).filter(Track.playlist_id == playlist.id).all()
    db_before_count = len(existing_tracks)
    spotify_count = len(all_tracks_items)
    
    logger.info(f"Refreshing playlist {playlist.id}: Spotify has {spotify_count} tracks, DB has {db_before_count}")
    
    # Delete existing tracks for this playlist and replace with fresh set
    for t in existing_tracks:
        db.delete(t)
    db.commit()

    new_tracks: List[Track] = []
    for item in all_tracks_items:
        track_data = item.get("track")
        if not track_data or not track_data.get("id") or not track_data.get("name"):
            continue

        track = Track(
            spotify_track_id=track_data["id"],
            name=track_data["name"],
            artist=", ".join([a["name"] for a in track_data.get("artists", [])]),
            album=track_data.get("album", {}).get("name"),
            duration_ms=track_data.get("duration_ms"),
            popularity=track_data.get("popularity"),
            playlist_id=playlist.id,
        )
        db.add(track)
        new_tracks.append(track)

    db.commit()

    # Fetch and impute missing audio features
    try:
        await audio_features_service.fetch_and_impute_features(new_tracks, db)
        db.commit()
        for track in new_tracks:
            db.refresh(track)
    except Exception as e:
        logger.warning(f"Failed to fetch audio features for playlist {playlist.id}: {str(e)}")
    
    # Update playlist count and log final state
    playlist.total_tracks = len(new_tracks)
    db.commit()
    db.refresh(playlist)
    
    logger.info(f"Playlist {playlist.id} refresh complete: {len(new_tracks)} tracks in DB (was {db_before_count})")
    return new_tracks

@router.post("/playlists/{playlist_id}/sync", response_model=List[TrackResponse])
async def sync_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    audio_features_service: AudioFeaturesService = Depends(get_audio_features_service)
):
    """
    Force a full sync of playlist tracks from Spotify to local DB.
    Useful for manual refresh when tracks may be out of sync.
    """
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id, 
        Playlist.user_id == current_user.id
    ).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    return await _refresh_playlist_in_db(playlist, current_user, db, audio_features_service)

@router.post("/playlists", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    body: PlaylistCreateInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Create a new playlist on Spotify and persist minimal metadata in DB.
    """
    # Create on Spotify
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {current_user.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "name": body.name,
                "description": body.description or "",
                "public": body.is_public,
            }
            resp = await client.post(
                f"https://api.spotify.com/v1/users/{current_user.spotify_user_id}/playlists",
                headers=headers,
                json=payload,
            )
            if resp.status_code not in (200, 201):
                raise HTTPException(status_code=resp.status_code, detail=f"Spotify create failed: {resp.text}")
            sp = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout communicating with Spotify API")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating playlist: {str(e)}")

    # Upsert in DB
    playlist = Playlist(
        spotify_playlist_id=sp["id"],
        name=sp.get("name", body.name),
        description=sp.get("description") or body.description,
        user_id=current_user.id,
        total_tracks=sp.get("tracks", {}).get("total", 0),
        is_public=sp.get("public", body.is_public),
    )
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    return playlist

@router.get("/playlists/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Get playlist metadata by ID."""
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id, 
        Playlist.user_id == current_user.id
    ).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    return playlist

@router.put("/playlists/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: int,
    body: PlaylistUpdateInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Update playlist metadata on Spotify and in DB."""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {current_user.access_token}",
                "Content-Type": "application/json",
            }
            payload = {}
            if body.name:
                payload["name"] = body.name
            if body.description is not None:
                payload["description"] = body.description
            if body.is_public is not None:
                payload["public"] = body.is_public

            if payload:
                resp = await client.put(
                    f"https://api.spotify.com/v1/playlists/{playlist.spotify_playlist_id}",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code not in (200, 201, 202, 204):
                    raise HTTPException(status_code=resp.status_code, detail=f"Spotify update failed: {resp.text}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout communicating with Spotify API")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating playlist: {str(e)}")

    # Update DB
    if body.name:
        playlist.name = body.name
    if body.description is not None:
        playlist.description = body.description
    if body.is_public is not None:
        playlist.is_public = bool(body.is_public)
    db.commit()
    db.refresh(playlist)
    return playlist

@router.delete("/playlists/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Remove a playlist from the user's library (unfollow) and delete from local DB.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {current_user.access_token}"}
            resp = await client.delete(
                f"https://api.spotify.com/v1/playlists/{playlist.spotify_playlist_id}/followers",
                headers=headers,
            )
            if resp.status_code not in (200, 202, 204):
                # Still try to remove locally if Spotify rejected (e.g., not owner)
                pass
    except Exception:
        # Continue with local deletion even if Spotify operation fails
        pass

    # Remove from DB
    # Delete tracks first
    for t in db.query(Track).filter(Track.playlist_id == playlist.id).all():
        db.delete(t)
    db.delete(playlist)
    db.commit()
    return {"message": "Playlist removed", "playlist_id": playlist_id}

@router.post("/playlists/{playlist_id}/tracks", response_model=List[TrackResponse])
async def add_tracks_to_playlist(
    playlist_id: int,
    req: AddTracksRequest,
    refresh: bool = Query(True, description="Refresh DB after adding"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    audio_features_service: AudioFeaturesService = Depends(get_audio_features_service)
):
    """
    Add tracks to a playlist on Spotify. Provide a list of Spotify track IDs.
    Optionally refresh local DB to reflect changes and return updated tracks.
    Checks for duplicates and only adds tracks that don't already exist in the playlist.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if not req.track_ids:
        raise HTTPException(status_code=400, detail="No track IDs provided")

    # Single async context manager for all HTTP operations
    timeout_config = httpx.Timeout(30.0)
    headers = {"Authorization": f"Bearer {current_user.access_token}"}
    
    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            # Step 1: Fetch existing tracks to check for duplicates
            existing_track_ids = set()
            offset = 0
            limit = 100
            
            while True:
                try:
                    resp = await client.get(
                        f"https://api.spotify.com/v1/playlists/{playlist.spotify_playlist_id}/tracks",
                        headers=headers,
                        params={"limit": limit, "offset": offset, "fields": "items(track(id)),total,next"}
                    )
                    if resp.status_code != 200:
                        break
                        
                    data = resp.json()
                    for item in data.get("items", []):
                        if item.get("track") and item["track"].get("id"):
                            existing_track_ids.add(item["track"]["id"])
                    
                    if not data.get("next"):
                        break
                    offset += limit
                except Exception:
                    break

            # Step 2: Filter out duplicate tracks
            new_track_ids = [tid for tid in req.track_ids if tid not in existing_track_ids]
            
            # Step 3: Add new tracks if any
            if new_track_ids:
                uris = [f"spotify:track:{tid}" for tid in new_track_ids]
                resp = await client.post(
                    f"https://api.spotify.com/v1/playlists/{playlist.spotify_playlist_id}/tracks",
                    headers={
                        "Authorization": f"Bearer {current_user.access_token}",
                        "Content-Type": "application/json",
                    },
                    json={"uris": uris},
                )
                if resp.status_code not in (200, 201):
                    raise HTTPException(status_code=resp.status_code, detail=f"Spotify add tracks failed: {resp.text}")
                    
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Request timed out - please try again")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    # Handle refresh and return logic
    if refresh:
        try:
            current_tracks = await _refresh_playlist_in_db(playlist, current_user, db, audio_features_service)
            return current_tracks
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to refresh playlist data: {str(e)}")
    
    # Return current tracks without refresh
    return db.query(Track).filter(Track.playlist_id == playlist.id).all()

@router.delete("/playlists/{playlist_id}/tracks/{spotify_track_id}")
async def remove_track_from_playlist(
    playlist_id: int,
    spotify_track_id: str,
    refresh: bool = Query(True, description="Refresh DB after removal"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    audio_features_service: AudioFeaturesService = Depends(get_audio_features_service)
):
    """
    Remove all occurrences of a track from a playlist on Spotify by track ID.
    Optionally refresh local DB.
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {current_user.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "tracks": [{"uri": f"spotify:track:{spotify_track_id}"}]
            }
            resp = await client.request(
                method="DELETE",
                url=f"https://api.spotify.com/v1/playlists/{playlist.spotify_playlist_id}/tracks",
                headers=headers,
                json=payload,
            )
            if resp.status_code not in (200, 201, 202):
                raise HTTPException(status_code=resp.status_code, detail=f"Spotify remove track failed: {resp.text}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout communicating with Spotify API")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing track: {str(e)}")

    if refresh:
        await _refresh_playlist_in_db(playlist, current_user, db, audio_features_service)
    return {"message": "Track removed", "playlist_id": playlist_id, "spotify_track_id": spotify_track_id}
