"""
Jamendo API client for Phase 2: Music Recommendation Engine.
"""
import asyncio
import time
from typing import Optional, List
import structlog
import httpx
from .schemas import Track, Artist, Album, AudioFeatures


logger = structlog.get_logger(__name__)


class JamendoClient:
    """
    Client for Jamendo API.
    Requires client ID for authentication.
    """
    
    def __init__(
        self,
        client_id: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = "https://api.jamendo.com/v3.0"
        self.client_id = client_id
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def _execute_with_retry(self, func):
        """Execute API call with retry logic."""
        for attempt in range(self.max_retries):
            try:
                return await func()
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    if attempt == self.max_retries - 1:
                        raise
                    delay = 2 ** attempt
                    logger.warning(f"Server error, retrying in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
            except httpx.RequestError as e:
                if attempt == self.max_retries - 1:
                    raise
                delay = 2 ** attempt
                logger.warning(f"Request error, retrying in {delay}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)
    
    async def get_artist(self, artist_id: str) -> Optional[Artist]:
        """Get artist information by ID."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "client_id": self.client_id,
                "id": artist_id,
                "imagesize": 500
            }
            
            response = await client.get(
                f"{self.base_url}/artists",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return None
            
            artist_data = results[0]
            
            return Artist(
                artist_id=str(artist_data["id"]),
                source="jamendo",
                artist_name=artist_data["name"],
                genres=artist_data.get("genres", []),
                popularity=min(artist_data.get("fans", 0) // 100, 100),
                followers=artist_data.get("fans", 0),
                external_url=artist_data.get("shareurl"),
                image_url=artist_data.get("image"),
                similar_artists=[],
                biography=artist_data.get("shortbio") or artist_data.get("bio"),
                country=artist_data.get("country"),
                formation_year=None,
                albums=[],
                top_tracks=[]
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get Jamendo artist", artist_id=artist_id, error=str(e))
            return None
    
    async def get_track(self, track_id: str) -> Optional[Track]:
        """Get track information by ID."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "client_id": self.client_id,
                "id": track_id,
                "imagesize": 500
            }
            
            response = await client.get(
                f"{self.base_url}/tracks",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return None
            
            track_data = results[0]
            artist_data = track_data.get("artist", {})
            album_data = track_data.get("album", {})
            
            # Extract release year
            release_date = track_data.get("releasedate", "")
            release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
            
            return Track(
                track_id=str(track_data["id"]),
                source="jamendo",
                track_name=track_data["name"],
                artist_id=str(artist_data.get("id", "")),
                artist_name=artist_data.get("name", ""),
                album_name=album_data.get("name") if album_data else None,
                album_id=str(album_data.get("id", "")) if album_data else None,
                duration_ms=track_data["duration"] * 1000 if track_data.get("duration") else 0,
                popularity=min(track_data.get("fans", 0) // 10, 100),
                audio_features=None,
                external_url=track_data.get("shareurl"),
                preview_url=track_data.get("audio"),
                image_url=track_data.get("image"),
                release_date=release_date,
                release_year=release_year,
                genres=track_data.get("genres", []),
                explicit=False,  # Jamendo doesn't have explicit flag
                track_number=track_data.get("position"),
                isrc=None
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get Jamendo track", track_id=track_id, error=str(e))
            return None
    
    async def get_album(self, album_id: str) -> Optional[Album]:
        """Get album information by ID."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "client_id": self.client_id,
                "id": album_id,
                "imagesize": 500
            }
            
            response = await client.get(
                f"{self.base_url}/albums",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return None
            
            album_data = results[0]
            artist_data = album_data.get("artist", {})
            
            # Extract release year
            release_date = album_data.get("releasedate", "")
            release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
            
            return Album(
                album_id=str(album_data["id"]),
                source="jamendo",
                album_name=album_data["name"],
                artist_id=str(artist_data.get("id", "")),
                artist_name=artist_data.get("name", ""),
                release_date=release_date,
                release_year=release_year,
                total_tracks=album_data.get("tracks", 0),
                genres=album_data.get("genres", []),
                popularity=min(album_data.get("fans", 0) // 100, 100),
                external_url=album_data.get("shareurl"),
                image_url=album_data.get("image"),
                label=album_data.get("label"),
                tracks=[]  # Need separate call to get tracks
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get Jamendo album", album_id=album_id, error=str(e))
            return None
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 10,
        genres: Optional[List[str]] = None
    ) -> List[Track]:
        """Search for tracks."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "client_id": self.client_id,
                "name": query,
                "limit": limit,
                "imagesize": 500
            }
            
            if genres:
                params["tag_id"] = ",".join(genres)
            
            response = await client.get(
                f"{self.base_url}/tracks",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            tracks_data = data.get("results", [])
            
            tracks = []
            for track_data in tracks_data[:limit]:
                artist_data = track_data.get("artist", {})
                album_data = track_data.get("album", {})
                
                release_date = track_data.get("releasedate", "")
                release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
                
                track = Track(
                    track_id=str(track_data["id"]),
                    source="jamendo",
                    track_name=track_data["name"],
                    artist_id=str(artist_data.get("id", "")),
                    artist_name=artist_data.get("name", ""),
                    album_name=album_data.get("name") if album_data else None,
                    album_id=str(album_data.get("id", "")) if album_data else None,
                    duration_ms=track_data["duration"] * 1000 if track_data.get("duration") else 0,
                    popularity=min(track_data.get("fans", 0) // 10, 100),
                    audio_features=None,
                    external_url=track_data.get("shareurl"),
                    preview_url=track_data.get("audio"),
                    image_url=track_data.get("image"),
                    release_date=release_date,
                    release_year=release_year,
                    genres=track_data.get("genres", []),
                    explicit=False,
                    track_number=track_data.get("position"),
                    isrc=None
                )
                tracks.append(track)
            
            return tracks
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to search Jamendo tracks", query=query, error=str(e))
            return []
    
    async def search_artists(
        self,
        query: str,
        limit: int = 10,
        genres: Optional[List[str]] = None
    ) -> List[Artist]:
        """Search for artists."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "client_id": self.client_id,
                "name": query,
                "limit": limit,
                "imagesize": 500
            }
            
            if genres:
                params["tag_id"] = ",".join(genres)
            
            response = await client.get(
                f"{self.base_url}/artists",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            artists_data = data.get("results", [])
            
            artists = []
            for artist_data in artists_data[:limit]:
                artist = Artist(
                    artist_id=str(artist_data["id"]),
                    source="jamendo",
                    artist_name=artist_data["name"],
                    genres=artist_data.get("genres", []),
                    popularity=min(artist_data.get("fans", 0) // 100, 100),
                    followers=artist_data.get("fans", 0),
                    external_url=artist_data.get("shareurl"),
                    image_url=artist_data.get("image"),
                    similar_artists=[],
                    biography=artist_data.get("shortbio") or artist_data.get("bio"),
                    country=artist_data.get("country"),
                    formation_year=None,
                    albums=[],
                    top_tracks=[]
                )
                artists.append(artist)
            
            return artists
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to search Jamendo artists", query=query, error=str(e))
            return []
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class MockJamendoClient:
    """Mock implementation for testing."""
    
    def __init__(self):
        self._artists = {
            "jamendo_artist_1": Artist(
                artist_id="jamendo_artist_1",
                source="jamendo",
                artist_name="Independent Artist",
                genres=["indie", "alternative", "electronic"],
                popularity=45,
                followers=50000,
                external_url="https://www.jamendo.com/artist/artist1",
                image_url="https://usercontent.jamendo.com?type=artist&id=1&width=500&height=500",
                similar_artists=[],
                biography="Independent artist creating original music",
                country="USA",
                formation_year=2015,
                albums=[],
                top_tracks=[]
            )
        }
        
        self._tracks = {
            "jamendo_track_1": Track(
                track_id="jamendo_track_1",
                source="jamendo",
                track_name="Original Song",
                artist_id="jamendo_artist_1",
                artist_name="Independent Artist",
                album_name="Debut Album",
                album_id="jamendo_album_1",
                duration_ms=210000,
                popularity=50,
                audio_features=None,
                external_url="https://www.jamendo.com/track/track1",
                preview_url="https://usercontent.jamendo.com/?type=track&id=1&format=mp3",
                image_url="https://usercontent.jamendo.com?type=album&id=1&width=500&height=500",
                release_date="2023-01-15",
                release_year=2023,
                genres=["indie", "alternative"],
                explicit=False,
                track_number=1,
                isrc=None
            )
        }
    
    async def get_artist(self, artist_id: str) -> Optional[Artist]:
        """Get artist information by ID."""
        return self._artists.get(artist_id)
    
    async def get_track(self, track_id: str) -> Optional[Track]:
        """Get track information by ID."""
        return self._tracks.get(track_id)
    
    async def get_album(self, album_id: str) -> Optional[Album]:
        """Get album information by ID."""
        return None
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 10,
        genres: Optional[List[str]] = None
    ) -> List[Track]:
        """Search for tracks."""
        return list(self._tracks.values())[:limit]
    
    async def search_artists(
        self,
        query: str,
        limit: int = 10,
        genres: Optional[List[str]] = None
    ) -> List[Artist]:
        """Search for artists."""
        return list(self._artists.values())[:limit]
    
    async def close(self) -> None:
        """Close the client (no-op for mock)."""
        pass
