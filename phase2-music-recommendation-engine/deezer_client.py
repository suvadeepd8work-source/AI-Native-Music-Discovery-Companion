"""
Deezer API client for Phase 2: Music Recommendation Engine.
"""
import asyncio
import time
from typing import Optional, List
import structlog
import httpx
from .schemas import Track, Artist, Album, AudioFeatures


logger = structlog.get_logger(__name__)


class DeezerClient:
    """
    Client for Deezer API.
    Deezer API doesn't require authentication for basic operations.
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = "https://api.deezer.com"
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
            
            response = await client.get(
                f"{self.base_url}/artist/{artist_id}"
            )
            response.raise_for_status()
            
            data = response.json()
            return Artist(
                artist_id=str(data["id"]),
                source="deezer",
                artist_name=data["name"],
                genres=[data.get("genre", {}).get("name", "")] if data.get("genre") else [],
                popularity=data.get("fans", 0) // 100,  # Normalize to 0-100
                followers=data.get("fans", 0),
                external_url=data.get("link"),
                image_url=data.get("picture_xl") or data.get("picture_medium"),
                similar_artists=[],  # Need separate call
                biography=data.get("biography"),
                country=data.get("country"),
                formation_year=None,  # Not provided by Deezer
                albums=[],
                top_tracks=[]
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get Deezer artist", artist_id=artist_id, error=str(e))
            return None
    
    async def get_track(self, track_id: str) -> Optional[Track]:
        """Get track information by ID."""
        async def _get():
            client = await self._get_client()
            
            response = await client.get(
                f"{self.base_url}/track/{track_id}"
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract release year from release_date
            release_date = data.get("release_date", "")
            release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
            
            return Track(
                track_id=str(data["id"]),
                source="deezer",
                track_name=data["title"],
                artist_id=str(data["artist"]["id"]),
                artist_name=data["artist"]["name"],
                album_name=data.get("album", {}).get("title"),
                album_id=str(data.get("album", {}).get("id", "")),
                duration_ms=data["duration"] * 1000 if data.get("duration") else 0,
                popularity=data.get("rank", 0) // 10,  # Normalize to 0-100
                audio_features=None,  # Deezer doesn't provide audio features
                external_url=data.get("link"),
                preview_url=data.get("preview"),
                image_url=data.get("album", {}).get("cover_xl") or data.get("album", {}).get("cover_medium"),
                release_date=release_date,
                release_year=release_year,
                genres=[],
                explicit=None,
                track_number=data.get("track_position"),
                isrc=data.get("isrc")
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get Deezer track", track_id=track_id, error=str(e))
            return None
    
    async def get_album(self, album_id: str) -> Optional[Album]:
        """Get album information by ID."""
        async def _get():
            client = await self._get_client()
            
            response = await client.get(
                f"{self.base_url}/album/{album_id}"
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract release year from release_date
            release_date = data.get("release_date", "")
            release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
            
            return Album(
                album_id=str(data["id"]),
                source="deezer",
                album_name=data["title"],
                artist_id=str(data["artist"]["id"]),
                artist_name=data["artist"]["name"],
                release_date=release_date,
                release_year=release_year,
                total_tracks=data.get("nb_tracks", 0),
                genres=[data.get("genre", {}).get("name", "")] if data.get("genre") else [],
                popularity=data.get("fans", 0) // 100,  # Normalize to 0-100
                external_url=data.get("link"),
                image_url=data.get("cover_xl") or data.get("cover_medium"),
                label=data.get("label"),
                tracks=[str(t["id"]) for t in data.get("tracks", {}).get("data", [])]
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get Deezer album", album_id=album_id, error=str(e))
            return None
    
    async def get_similar_artists(self, artist_id: str) -> List[Artist]:
        """Get similar artists."""
        async def _get():
            client = await self._get_client()
            
            response = await client.get(
                f"{self.base_url}/artist/{artist_id}/related"
            )
            response.raise_for_status()
            
            data = response.json()
            artists = []
            
            for artist_data in data.get("data", []):
                artist = Artist(
                    artist_id=str(artist_data["id"]),
                    source="deezer",
                    artist_name=artist_data["name"],
                    genres=[artist_data.get("genre", {}).get("name", "")] if artist_data.get("genre") else [],
                    popularity=artist_data.get("fans", 0) // 100,
                    followers=artist_data.get("fans", 0),
                    external_url=artist_data.get("link"),
                    image_url=artist_data.get("picture_xl") or artist_data.get("picture_medium"),
                    similar_artists=[],
                    biography=None,
                    country=None,
                    formation_year=None,
                    albums=[],
                    top_tracks=[]
                )
                artists.append(artist)
            
            return artists
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get similar artists", artist_id=artist_id, error=str(e))
            return []
    
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
                "q": query,
                "limit": limit
            }
            
            response = await client.get(
                f"{self.base_url}/search/track",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            tracks = []
            
            for track_data in data.get("data", []):
                release_date = track_data.get("release_date", "")
                release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
                
                track = Track(
                    track_id=str(track_data["id"]),
                    source="deezer",
                    track_name=track_data["title"],
                    artist_id=str(track_data["artist"]["id"]),
                    artist_name=track_data["artist"]["name"],
                    album_name=track_data.get("album", {}).get("title"),
                    album_id=str(track_data.get("album", {}).get("id", "")),
                    duration_ms=track_data["duration"] * 1000 if track_data.get("duration") else 0,
                    popularity=track_data.get("rank", 0) // 10,
                    audio_features=None,
                    external_url=track_data.get("link"),
                    preview_url=track_data.get("preview"),
                    image_url=track_data.get("album", {}).get("cover_xl") or track_data.get("album", {}).get("cover_medium"),
                    release_date=release_date,
                    release_year=release_year,
                    genres=[],
                    explicit=None,
                    track_number=track_data.get("track_position"),
                    isrc=track_data.get("isrc")
                )
                tracks.append(track)
            
            return tracks
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to search Deezer tracks", query=query, error=str(e))
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
                "q": query,
                "limit": limit
            }
            
            response = await client.get(
                f"{self.base_url}/search/artist",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            artists = []
            
            for artist_data in data.get("data", []):
                artist = Artist(
                    artist_id=str(artist_data["id"]),
                    source="deezer",
                    artist_name=artist_data["name"],
                    genres=[artist_data.get("genre", {}).get("name", "")] if artist_data.get("genre") else [],
                    popularity=artist_data.get("fans", 0) // 100,
                    followers=artist_data.get("fans", 0),
                    external_url=artist_data.get("link"),
                    image_url=artist_data.get("picture_xl") or artist_data.get("picture_medium"),
                    similar_artists=[],
                    biography=artist_data.get("biography"),
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
            logger.error("Failed to search Deezer artists", query=query, error=str(e))
            return []
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class MockDeezerClient:
    """Mock implementation for testing."""
    
    def __init__(self):
        self._artists = {
            "deezer_artist_1": Artist(
                artist_id="deezer_artist_1",
                source="deezer",
                artist_name="Daft Punk",
                genres=["electronic", "house", "french house"],
                popularity=85,
                followers=2000000,
                external_url="https://www.deezer.com/artist/27",
                image_url="https://e-cdns-images.dzcdn.net/images/artist/27/500x500-000000-80-0-0.jpg",
                similar_artists=["deezer_artist_2"],
                biography="French electronic music duo",
                country="France",
                formation_year=1993,
                albums=[],
                top_tracks=[]
            )
        }
        
        self._tracks = {
            "deezer_track_1": Track(
                track_id="deezer_track_1",
                source="deezer",
                track_name="One More Time",
                artist_id="deezer_artist_1",
                artist_name="Daft Punk",
                album_name="Discovery",
                album_id="deezer_album_1",
                duration_ms=320000,
                popularity=90,
                audio_features=None,
                external_url="https://www.deezer.com/track/3135556",
                preview_url="https://cdns-preview-a.dzcdn.net/stream/c-3135556-9f9b0e7d9a5e0b0b0b0b0b0b0b0b0b0b0.mp3",
                image_url="https://e-cdns-images.dzcdn.net/images/cover/500x500-000000-80-0-0-0.jpg",
                release_date="2001-03-12",
                release_year=2001,
                genres=["electronic", "house"],
                explicit=False,
                track_number=1,
                isrc="FRUM70000001"
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
    
    async def get_similar_artists(self, artist_id: str) -> List[Artist]:
        """Get similar artists."""
        return list(self._artists.values())[:5]
    
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
