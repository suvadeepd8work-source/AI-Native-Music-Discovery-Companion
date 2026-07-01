"""
Last.fm API client for Phase 2: Music Recommendation Engine.
"""
import asyncio
import time
from typing import Optional, List
import structlog
import httpx
from .schemas import Track, Artist, Album, AudioFeatures


logger = structlog.get_logger(__name__)


class LastFMClient:
    """
    Client for Last.fm API.
    Requires API key for authentication.
    """
    
    def __init__(
        self,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = "https://ws.audioscrobbler.com/2.0"
        self.api_key = api_key
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
    
    async def get_artist(self, artist_name: str) -> Optional[Artist]:
        """Get artist information by name."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "method": "artist.getinfo",
                "artist": artist_name,
                "api_key": self.api_key,
                "format": "json"
            }
            
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            artist_data = data.get("artist", {})
            
            # Extract genres
            genres = []
            for tag in artist_data.get("tags", {}).get("tag", []):
                if isinstance(tag, dict):
                    genres.append(tag.get("name", ""))
                else:
                    genres.append(str(tag))
            
            return Artist(
                artist_id=artist_data.get("mbid", artist_name),
                source="lastfm",
                artist_name=artist_data.get("name", artist_name),
                genres=genres,
                popularity=min(artist_data.get("listeners", 0) // 10000, 100),
                followers=artist_data.get("listeners", 0),
                external_url=artist_data.get("url"),
                image_url=self._get_largest_image(artist_data.get("image", [])),
                similar_artists=[],
                biography=artist_data.get("bio", {}).get("content"),
                country=artist_data.get("country"),
                formation_year=None,
                albums=[],
                top_tracks=[]
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get Last.fm artist", artist_name=artist_name, error=str(e))
            return None
    
    async def get_track(self, track_name: str, artist_name: str) -> Optional[Track]:
        """Get track information by name and artist."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "method": "track.getinfo",
                "track": track_name,
                "artist": artist_name,
                "api_key": self.api_key,
                "format": "json"
            }
            
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            track_data = data.get("track", {})
            
            if not track_data:
                return None
            
            artist_data = track_data.get("artist", {})
            album_data = track_data.get("album", {})
            
            # Extract release year from album
            release_year = None
            if album_data:
                release_date = album_data.get("releasedate", "")
                if release_date:
                    try:
                        release_year = int(release_date[:4])
                    except (ValueError, IndexError):
                        pass
            
            return Track(
                track_id=track_data.get("mbid", f"{artist_name}:{track_name}"),
                source="lastfm",
                track_name=track_data.get("name", track_name),
                artist_id=artist_data.get("mbid", artist_name),
                artist_name=artist_data.get("name", artist_name),
                album_name=album_data.get("title") if album_data else None,
                album_id=album_data.get("mbid") if album_data else None,
                duration_ms=int(track_data.get("duration", 0)) if track_data.get("duration") else 0,
                popularity=min(track_data.get("listeners", 0) // 1000, 100),
                audio_features=None,
                external_url=track_data.get("url"),
                preview_url=None,
                image_url=self._get_largest_image(track_data.get("image", [])),
                release_date=album_data.get("releasedate") if album_data else None,
                release_year=release_year,
                genres=[],
                explicit=None,
                track_number=None,
                isrc=None
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get Last.fm track", track_name=track_name, artist_name=artist_name, error=str(e))
            return None
    
    async def get_similar_artists(self, artist_name: str, limit: int = 10) -> List[Artist]:
        """Get similar artists."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "method": "artist.getsimilar",
                "artist": artist_name,
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            similar_artists_data = data.get("similarartists", {}).get("artist", [])
            
            artists = []
            for artist_data in similar_artists_data[:limit]:
                artist = Artist(
                    artist_id=artist_data.get("mbid", artist_data.get("name", "")),
                    source="lastfm",
                    artist_name=artist_data.get("name", ""),
                    genres=[],
                    popularity=min(artist_data.get("match", 0) * 100, 100),
                    followers=0,
                    external_url=artist_data.get("url"),
                    image_url=self._get_largest_image(artist_data.get("image", [])),
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
            logger.error("Failed to get similar artists", artist_name=artist_name, error=str(e))
            return []
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 10
    ) -> List[Track]:
        """Search for tracks."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "method": "track.search",
                "track": query,
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results_data = data.get("results", {})
            tracks_data = results_data.get("trackmatches", {}).get("track", [])
            
            tracks = []
            for track_data in tracks_data[:limit]:
                artist_data = track_data.get("artist", "")
                if isinstance(artist_data, dict):
                    artist_name = artist_data.get("name", "")
                else:
                    artist_name = str(artist_data)
                
                track = Track(
                    track_id=track_data.get("mbid", f"{artist_name}:{track_data.get('name', '')}"),
                    source="lastfm",
                    track_name=track_data.get("name", ""),
                    artist_id="",
                    artist_name=artist_name,
                    album_name=None,
                    album_id=None,
                    duration_ms=0,
                    popularity=min(track_data.get("listeners", 0) // 1000, 100),
                    audio_features=None,
                    external_url=track_data.get("url"),
                    preview_url=None,
                    image_url=[],
                    release_date=None,
                    release_year=None,
                    genres=[],
                    explicit=None,
                    track_number=None,
                    isrc=None
                )
                tracks.append(track)
            
            return tracks
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to search Last.fm tracks", query=query, error=str(e))
            return []
    
    async def search_artists(
        self,
        query: str,
        limit: int = 10
    ) -> List[Artist]:
        """Search for artists."""
        async def _get():
            client = await self._get_client()
            
            params = {
                "method": "artist.search",
                "artist": query,
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results_data = data.get("results", {})
            artists_data = results_data.get("artistmatches", {}).get("artist", [])
            
            artists = []
            for artist_data in artists_data[:limit]:
                artist = Artist(
                    artist_id=artist_data.get("mbid", artist_data.get("name", "")),
                    source="lastfm",
                    artist_name=artist_data.get("name", ""),
                    genres=[],
                    popularity=min(artist_data.get("listeners", 0) // 10000, 100),
                    followers=artist_data.get("listeners", 0),
                    external_url=artist_data.get("url"),
                    image_url=self._get_largest_image(artist_data.get("image", [])),
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
            logger.error("Failed to search Last.fm artists", query=query, error=str(e))
            return []
    
    def _get_largest_image(self, images: list) -> Optional[str]:
        """Get the largest image from a list of images."""
        if not images:
            return None
        
        # Last.fm returns images in order: small, medium, large, extralarge
        # We want the largest available
        for image in reversed(images):
            if isinstance(image, dict):
                url = image.get("#text", "")
                if url:
                    return url
            elif isinstance(image, str) and image:
                return image
        
        return None
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class MockLastFMClient:
    """Mock implementation for testing."""
    
    def __init__(self):
        self._artists = {
            "radiohead": Artist(
                artist_id="a74b1b7f-71a5-4e19-9451-289b9e77f125",
                source="lastfm",
                artist_name="Radiohead",
                genres=["alternative rock", "art rock", "experimental rock"],
                popularity=90,
                followers=5000000,
                external_url="https://www.last.fm/music/Radiohead",
                image_url="https://lastfm.freetls.fastly.net/i/u/300x300/0efa1949b3b0fb7b8d4e0c9a1a6d5d5d.png",
                similar_artists=["coldplay", "muse"],
                biography="English rock band formed in Abingdon, Oxfordshire",
                country="UK",
                formation_year=1985,
                albums=[],
                top_tracks=[]
            )
        }
        
        self._tracks = {
            "radiohead:creep": Track(
                track_id="1b43d9d9-8b9e-4b8e-8b9e-1b43d9d9b8e9",
                source="lastfm",
                track_name="Creep",
                artist_id="a74b1b7f-71a5-4e19-9451-289b9e77f125",
                artist_name="Radiohead",
                album_name="Pablo Honey",
                album_id="1b43d9d9-8b9e-4b8e-8b9e-1b43d9d9b8e8",
                duration_ms=238000,
                popularity=95,
                audio_features=None,
                external_url="https://www.last.fm/music/Radiohead/_/Creep",
                preview_url=None,
                image_url="https://lastfm.freetls.fastly.net/i/u/300x300/0efa1949b3b0fb7b8d4e0c9a1a6d5d5d.png",
                release_date="1992-09-21",
                release_year=1992,
                genres=["alternative rock"],
                explicit=False,
                track_number=2,
                isrc="GBUSS19920002"
            )
        }
    
    async def get_artist(self, artist_name: str) -> Optional[Artist]:
        """Get artist information by name."""
        return self._artists.get(artist_name.lower())
    
    async def get_track(self, track_name: str, artist_name: str) -> Optional[Track]:
        """Get track information by name and artist."""
        key = f"{artist_name.lower()}:{track_name.lower()}"
        return self._tracks.get(key)
    
    async def get_similar_artists(self, artist_name: str, limit: int = 10) -> List[Artist]:
        """Get similar artists."""
        return list(self._artists.values())[:limit]
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 10
    ) -> List[Track]:
        """Search for tracks."""
        return list(self._tracks.values())[:limit]
    
    async def search_artists(
        self,
        query: str,
        limit: int = 10
    ) -> List[Artist]:
        """Search for artists."""
        return list(self._artists.values())[:limit]
    
    async def close(self) -> None:
        """Close the client (no-op for mock)."""
        pass
