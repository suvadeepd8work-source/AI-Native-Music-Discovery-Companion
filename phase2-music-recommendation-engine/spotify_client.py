"""
Spotify API client for Phase 2: Music Recommendation Engine.
"""
import asyncio
import time
from typing import Optional, List, Dict, Any
import structlog
import httpx
from .schemas import Track, Artist, AudioFeatures


logger = structlog.get_logger(__name__)


class SpotifyRateLimitError(Exception):
    """Spotify API rate limit exceeded."""
    pass


class SpotifyServerError(Exception):
    """Spotify API server error."""
    pass


class SpotifyClient:
    """
    Client for Spotify Web API with retry logic and caching.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        timeout: int = 30,
        max_retries: int = 5,
        rate_limit_delay: int = 60
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def _ensure_token(self) -> str:
        """Ensure we have a valid access token."""
        current_time = time.time()
        
        if self._access_token and current_time < self._token_expires_at:
            return self._access_token
        
        # Get new token
        await self._refresh_token()
        return self._access_token
    
    async def _refresh_token(self) -> None:
        """Refresh the access token using client credentials flow."""
        client = await self._get_client()
        
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            logger.error("Failed to get Spotify access token", status=response.status_code)
            raise SpotifyServerError(f"Failed to get access token: {response.status_code}")
        
        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"] - 60  # Refresh 60s before expiry
        
        logger.info("Spotify access token refreshed")
    
    async def _execute_with_retry(self, func):
        """Execute API call with retry logic."""
        for attempt in range(self.max_retries):
            try:
                return await func()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", self.rate_limit_delay))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                elif e.response.status_code >= 500:
                    if attempt == self.max_retries - 1:
                        raise SpotifyServerError(f"Server error after {self.max_retries} retries")
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
            token = await self._ensure_token()
            client = await self._get_client()
            
            response = await client.get(
                f"https://api.spotify.com/v1/artists/{artist_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Get similar artists
            similar_response = await client.get(
                f"https://api.spotify.com/v1/artists/{artist_id}/related-artists",
                headers={"Authorization": f"Bearer {token}"}
            )
            similar_artists = []
            if similar_response.status_code == 200:
                similar_data = similar_response.json()
                similar_artists = [a["id"] for a in similar_data.get("artists", [])]
            
            # Get top tracks
            top_tracks_response = await client.get(
                f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
                headers={"Authorization": f"Bearer {token}"},
                params={"market": "US"}
            )
            top_tracks = []
            if top_tracks_response.status_code == 200:
                top_tracks_data = top_tracks_response.json()
                top_tracks = [t["id"] for t in top_tracks_data.get("tracks", [])]
            
            # Get albums
            albums_response = await client.get(
                f"https://api.spotify.com/v1/artists/{artist_id}/albums",
                headers={"Authorization": f"Bearer {token}"},
                params={"include_groups": "album,single", "limit": 10}
            )
            albums = []
            if albums_response.status_code == 200:
                albums_data = albums_response.json()
                albums = [a["id"] for a in albums_data.get("items", [])]
            
            return Artist(
                artist_id=data["id"],
                source="spotify",
                artist_name=data["name"],
                genres=data.get("genres", []),
                popularity=data["popularity"],
                followers=data["followers"]["total"],
                external_url=data.get("external_urls", {}).get("spotify"),
                image_url=data.get("images", [{}])[0].get("url") if data.get("images") else None,
                similar_artists=similar_artists,
                biography=None,  # Spotify doesn't provide biography
                country=None,  # Spotify doesn't provide country
                formation_year=None,  # Spotify doesn't provide formation year
                albums=albums,
                top_tracks=top_tracks
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get artist", artist_id=artist_id, error=str(e))
            return None
    
    async def get_track(self, track_id: str) -> Optional[Track]:
        """Get track information by ID."""
        async def _get():
            token = await self._ensure_token()
            client = await self._get_client()
            
            response = await client.get(
                f"https://api.spotify.com/v1/tracks/{track_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract release date and year
            album_data = data.get("album", {})
            release_date = album_data.get("release_date", "")
            release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
            
            # Get audio features
            audio_features = await self.get_audio_features(track_id)
            
            return Track(
                track_id=data["id"],
                source="spotify",
                track_name=data["name"],
                artist_id=data["artists"][0]["id"],
                artist_name=data["artists"][0]["name"],
                album_name=album_data.get("name"),
                album_id=album_data.get("id"),
                duration_ms=data["duration_ms"],
                popularity=data["popularity"],
                audio_features=audio_features,
                external_url=data.get("external_urls", {}).get("spotify"),
                preview_url=data.get("preview_url"),
                image_url=album_data.get("images", [{}])[0].get("url") if album_data.get("images") else None,
                release_date=release_date,
                release_year=release_year,
                genres=[],  # Genres are at artist level, not track level
                explicit=data.get("explicit", False),
                track_number=data.get("track_number"),
                isrc=data.get("external_ids", {}).get("isrc")
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get track", track_id=track_id, error=str(e))
            return None
    
    async def get_audio_features(self, track_id: str) -> Optional[AudioFeatures]:
        """Get audio features for a track."""
        async def _get():
            token = await self._ensure_token()
            client = await self._get_client()
            
            response = await client.get(
                f"https://api.spotify.com/v1/audio-features/{track_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            
            data = response.json()
            return AudioFeatures(
                energy=data["energy"],
                valence=data["valence"],
                danceability=data["danceability"],
                acousticness=data["acousticness"],
                instrumentalness=data["instrumentalness"],
                speechiness=data["speechiness"],
                tempo=data.get("tempo"),
                loudness=data.get("loudness"),
                mode=data.get("mode"),
                key=data.get("key"),
                liveness=data.get("liveness")
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get audio features", track_id=track_id, error=str(e))
            return None
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 10,
        seed_genres: Optional[List[str]] = None,
        seed_artists: Optional[List[str]] = None,
        target_energy: Optional[float] = None,
        target_valence: Optional[float] = None,
        target_danceability: Optional[float] = None,
        min_energy: Optional[float] = None,
        max_energy: Optional[float] = None,
        min_valence: Optional[float] = None,
        max_valence: Optional[float] = None,
        min_danceability: Optional[float] = None,
        max_danceability: Optional[float] = None,
        min_tempo: Optional[float] = None,
        max_tempo: Optional[float] = None
    ) -> List[Track]:
        """
        Search for tracks with optional audio feature constraints.
        Uses Spotify's recommendations endpoint for feature-based search.
        """
        async def _get():
            token = await self._ensure_token()
            client = await self._get_client()
            
            params = {"limit": limit}
            
            if seed_genres:
                params["seed_genres"] = ",".join(seed_genres)
            if seed_artists:
                params["seed_artists"] = ",".join(seed_artists)
            
            # Audio feature targets
            if target_energy is not None:
                params["target_energy"] = target_energy
            if target_valence is not None:
                params["target_valence"] = target_valence
            if target_danceability is not None:
                params["target_danceability"] = target_danceability
            
            # Audio feature ranges
            if min_energy is not None:
                params["min_energy"] = min_energy
            if max_energy is not None:
                params["max_energy"] = max_energy
            if min_valence is not None:
                params["min_valence"] = min_valence
            if max_valence is not None:
                params["max_valence"] = max_valence
            if min_danceability is not None:
                params["min_danceability"] = min_danceability
            if max_danceability is not None:
                params["max_danceability"] = max_danceability
            if min_tempo is not None:
                params["min_tempo"] = min_tempo
            if max_tempo is not None:
                params["max_tempo"] = max_tempo
            
            response = await client.get(
                "https://api.spotify.com/v1/recommendations",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            tracks = []
            
            for track_data in data.get("tracks", []):
                # Extract release date and year
                album_data = track_data.get("album", {})
                release_date = album_data.get("release_date", "")
                release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
                
                track = Track(
                    track_id=track_data["id"],
                    source="spotify",
                    track_name=track_data["name"],
                    artist_id=track_data["artists"][0]["id"],
                    artist_name=track_data["artists"][0]["name"],
                    album_name=album_data.get("name"),
                    album_id=album_data.get("id"),
                    duration_ms=track_data["duration_ms"],
                    popularity=track_data["popularity"],
                    audio_features=None,  # Audio features fetched separately
                    external_url=track_data.get("external_urls", {}).get("spotify"),
                    preview_url=track_data.get("preview_url"),
                    image_url=album_data.get("images", [{}])[0].get("url") if album_data.get("images") else None,
                    release_date=release_date,
                    release_year=release_year,
                    genres=[],
                    explicit=track_data.get("explicit", False),
                    track_number=track_data.get("track_number"),
                    isrc=track_data.get("external_ids", {}).get("isrc")
                )
                tracks.append(track)
            
            return tracks
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to search tracks", query=query, error=str(e))
            return []
    
    async def search_artists(
        self,
        query: str,
        limit: int = 10,
        genres: Optional[List[str]] = None
    ) -> List[Artist]:
        """Search for artists."""
        async def _get():
            token = await self._ensure_token()
            client = await self._get_client()
            
            params = {
                "q": query,
                "type": "artist",
                "limit": limit
            }
            
            if genres:
                params["q"] += f" genre:{','.join(genres)}"
            
            response = await client.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            artists = []
            
            for artist_data in data.get("artists", {}).get("items", []):
                artist = Artist(
                    artist_id=artist_data["id"],
                    source="spotify",
                    artist_name=artist_data["name"],
                    genres=artist_data.get("genres", []),
                    popularity=artist_data["popularity"],
                    followers=artist_data["followers"]["total"],
                    external_url=artist_data.get("external_urls", {}).get("spotify"),
                    image_url=artist_data.get("images", [{}])[0].get("url") if artist_data.get("images") else None,
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
            logger.error("Failed to search artists", query=query, error=str(e))
            return []
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class MockSpotifyClient:
    """Mock implementation for testing."""
    
    def __init__(self):
        self._artists = {
            "artist_1": Artist(
                artist_id="artist_1",
                artist_name="The Midnight",
                genres=["synthwave", "electronic", "retro"],
                popularity=65,
                followers=500000,
                external_url="https://open.spotify.com/artist/artist_1"
            ),
            "artist_2": Artist(
                artist_id="artist_2",
                artist_name="Carpenter Brut",
                genres=["synthwave", "electronic", "darkwave"],
                popularity=55,
                followers=300000,
                external_url="https://open.spotify.com/artist/artist_2"
            ),
            "artist_3": Artist(
                artist_id="artist_3",
                artist_name="Gunship",
                genres=["synthwave", "electronic", "cyberpunk"],
                popularity=60,
                followers=400000,
                external_url="https://open.spotify.com/artist/artist_3"
            )
        }
        
        self._tracks = {
            "track_1": Track(
                track_id="track_1",
                track_name="Los Angeles",
                artist_id="artist_1",
                artist_name="The Midnight",
                album_name="Endless Summer",
                album_id="album_1",
                duration_ms=240000,
                popularity=70,
                audio_features=AudioFeatures(
                    energy=0.7,
                    valence=0.8,
                    danceability=0.6,
                    acousticness=0.3,
                    instrumentalness=0.4,
                    speechiness=0.1,
                    tempo=120.0
                ),
                external_url="https://open.spotify.com/track/track_1"
            ),
            "track_2": Track(
                track_id="track_2",
                track_name="Nightcall",
                artist_id="artist_2",
                artist_name="Carpenter Brut",
                album_name="Trilogy",
                album_id="album_2",
                duration_ms=280000,
                popularity=65,
                audio_features=AudioFeatures(
                    energy=0.8,
                    valence=0.5,
                    danceability=0.5,
                    acousticness=0.2,
                    instrumentalness=0.6,
                    speechiness=0.05,
                    tempo=110.0
                ),
                external_url="https://open.spotify.com/track/track_2"
            ),
            "track_3": Track(
                track_id="track_3",
                track_name="Tech Noir",
                artist_id="artist_3",
                artist_name="Gunship",
                album_name="Gunship",
                album_id="album_3",
                duration_ms=260000,
                popularity=68,
                audio_features=AudioFeatures(
                    energy=0.75,
                    valence=0.7,
                    danceability=0.65,
                    acousticness=0.25,
                    instrumentalness=0.5,
                    speechiness=0.08,
                    tempo=115.0
                ),
                external_url="https://open.spotify.com/track/track_3"
            )
        }
    
    async def get_artist(self, artist_id: str) -> Optional[Artist]:
        """Get artist information by ID."""
        return self._artists.get(artist_id)
    
    async def get_track(self, track_id: str) -> Optional[Track]:
        """Get track information by ID."""
        return self._tracks.get(track_id)
    
    async def get_audio_features(self, track_id: str) -> Optional[AudioFeatures]:
        """Get audio features for a track."""
        track = self._tracks.get(track_id)
        return track.audio_features if track else None
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 10,
        seed_genres: Optional[List[str]] = None,
        seed_artists: Optional[List[str]] = None,
        **kwargs
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
