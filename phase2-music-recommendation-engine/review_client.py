"""
Review Engine API client for Phase 2: Music Recommendation Engine.
"""
import asyncio
from typing import Optional, List
import structlog
import httpx

try:
    from .schemas import ReviewInsight, ThemeCluster, PainPoint, UserSegment, ProductInsight, ExecutiveReport
except ImportError:
    from schemas import ReviewInsight, ThemeCluster, PainPoint, UserSegment, ProductInsight, ExecutiveReport


logger = structlog.get_logger(__name__)


class ReviewEngineClient:
    """
    Client for AI-Powered Review Discovery Engine API.
    Uses the deployed system at https://ai-powered-review-discovery-engine.onrender.com
    """
    
    def __init__(
        self,
        base_url: str = "https://ai-powered-review-discovery-engine.onrender.com",
        timeout: int = 10,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip("/")
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
    
    async def get_review_insights(
        self,
        genres: Optional[List[str]] = None,
        min_discovery_score: float = 0.5,
        limit: int = 20
    ) -> List[ReviewInsight]:
        """
        Get review insights for artists from AI review discovery system.
        
        Args:
            genres: Filter by genre tags
            min_discovery_score: Minimum discovery score
            limit: Maximum number of results
            
        Returns:
            List of review insights
        """
        async def _get():
            client = await self._get_client()
            
            params = {
                "min_discovery_score": min_discovery_score,
                "limit": limit
            }
            
            if genres:
                params["genres"] = ",".join(genres)
            
            response = await client.get(
                f"{self.base_url}/api/reviews",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            insights = []
            
            # Handle both list and dict responses
            reviews_data = data if isinstance(data, list) else data.get("reviews", [])
            
            for review_data in reviews_data:
                # Map review data to ReviewInsight schema with proper defaults
                insight = ReviewInsight(
                    artist_id=str(review_data.get("id", "")),
                    artist_name=review_data.get("platform") or "Unknown Platform",
                    review_sentiment=review_data.get("sentiment") or 0.5,
                    review_count=1,
                    genre_tags=[],
                    unique_descriptors=review_data.get("barriers") or [],
                    discovery_score=(review_data.get("rating") or 3) / 5.0,
                    last_updated="2024-01-01T00:00:00Z",
                    themes=[review_data.get("category")] if review_data.get("category") else [],
                    pain_points=[]
                )
                insights.append(insight)
            
            return insights
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get review insights", error=str(e))
            return []
    
    async def get_artist_review_insight(self, artist_id: str) -> Optional[ReviewInsight]:
        """
        Get review insight for a specific artist from AI review discovery system.
        
        Args:
            artist_id: Spotify artist ID
            
        Returns:
            Review insight or None if not found
        """
        async def _get():
            client = await self._get_client()
            
            response = await client.get(
                f"{self.base_url}/api/reviews/{artist_id}"
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            
            data = response.json()
            return ReviewInsight(
                artist_id=data["artist_id"],
                artist_name=data["artist_name"],
                review_sentiment=data["review_sentiment"],
                review_count=data["review_count"],
                genre_tags=data.get("genre_tags", []),
                unique_descriptors=data.get("unique_descriptors", []),
                discovery_score=data["discovery_score"],
                last_updated=data["last_updated"],
                themes=data.get("themes", []),
                pain_points=data.get("pain_points", [])
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get artist review insight", artist_id=artist_id, error=str(e))
            return None
    
    async def get_theme_clusters(
        self,
        limit: int = 20
    ) -> List[ThemeCluster]:
        """
        Get theme clusters from AI review discovery system.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of theme clusters
        """
        async def _get():
            client = await self._get_client()
            
            params = {"limit": limit}
            
            response = await client.get(
                f"{self.base_url}/api/insights/themes",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            clusters = []
            
            # Handle list response directly
            themes_data = data if isinstance(data, list) else data.get("themes", [])
            
            for theme_data in themes_data:
                cluster = ThemeCluster(
                    cluster_id=theme_data.get("theme_id", ""),
                    theme_name=theme_data.get("title", ""),
                    description=theme_data.get("description", ""),
                    keywords=theme_data.get("representative_reviews", [])[:3],  # Use first 3 reviews as keywords
                    sentiment=0.5,  # Default sentiment
                    frequency=theme_data.get("review_count", 0),
                    related_artists=[]
                )
                clusters.append(cluster)
            
            return clusters
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get theme clusters", error=str(e))
            return []
    
    async def get_pain_points(
        self,
        severity_threshold: float = 0.5,
        limit: int = 20
    ) -> List[PainPoint]:
        """
        Get pain points from AI review discovery system.
        Note: This endpoint is not available in the deployed system, returns empty list.
        
        Args:
            severity_threshold: Minimum severity score
            limit: Maximum number of results
            
        Returns:
            List of pain points
        """
        logger.warning("Pain points endpoint not available in deployed system")
        return []
    
    async def get_user_segments(
        self,
        limit: int = 20
    ) -> List[UserSegment]:
        """
        Get user segments from AI review discovery system.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of user segments
        """
        async def _get():
            client = await self._get_client()
            
            params = {"limit": limit}
            
            response = await client.get(
                f"{self.base_url}/api/insights/segments",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            segments = []
            
            # Handle list response directly
            segments_data = data if isinstance(data, list) else data.get("segments", [])
            
            for segment_data in segments_data:
                segment = UserSegment(
                    segment_id=segment_data.get("segment_id", ""),
                    segment_name=segment_data.get("label", ""),
                    description=", ".join(segment_data.get("traits", [])),
                    size=segment_data.get("review_count", 0),
                    preferences={},
                    behaviors=segment_data.get("listening_behaviors", []),
                    pain_points=segment_data.get("challenges", [])
                )
                segments.append(segment)
            
            return segments
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get user segments", error=str(e))
            return []
    
    async def get_user_segment(self, segment_id: str) -> Optional[UserSegment]:
        """
        Get a specific user segment from AI review discovery system.
        
        Args:
            segment_id: User segment ID
            
        Returns:
            User segment or None if not found
        """
        async def _get():
            client = await self._get_client()
            
            response = await client.get(
                f"{self.base_url}/api/insights/segments/{segment_id}"
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            
            data = response.json()
            return UserSegment(
                segment_id=data.get("segment_id", ""),
                segment_name=data.get("label", ""),
                description=", ".join(data.get("traits", [])),
                size=data.get("review_count", 0),
                preferences={},
                behaviors=data.get("listening_behaviors", []),
                pain_points=data.get("challenges", [])
            )
        
        try:
            return await self._execute_with_retry(_get)
        except Exception as e:
            logger.error("Failed to get user segment", segment_id=segment_id, error=str(e))
            return None
    
    async def get_product_insights(
        self,
        actionable_only: bool = False,
        limit: int = 20
    ) -> List[ProductInsight]:
        """
        Get product insights from AI review discovery system.
        Note: This endpoint is not available in the deployed system, returns empty list.
        
        Args:
            actionable_only: Filter for actionable insights only
            limit: Maximum number of results
            
        Returns:
            List of product insights
        """
        logger.warning("Product insights endpoint not available in deployed system")
        return []
    
    async def get_executive_report(self) -> Optional[ExecutiveReport]:
        """
        Get the executive report summary from AI review discovery system.
        Note: This endpoint is not available in the deployed system, returns None.
        
        Returns:
            Executive report or None if not available
        """
        logger.warning("Executive report endpoint not available in deployed system")
        return None
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class MockReviewEngineClient:
    """Mock implementation for testing."""
    
    def __init__(self):
        self._insights = {
            "artist_1": ReviewInsight(
                artist_id="artist_1",
                artist_name="The Midnight",
                review_sentiment=0.85,
                review_count=150,
                genre_tags=["synthwave", "electronic", "retro"],
                unique_descriptors=["nostalgic", "cinematic", "atmospheric"],
                discovery_score=0.75,
                last_updated="2024-01-15T00:00:00Z",
                themes=["retro aesthetics", "cinematic quality", "nostalgia"],
                pain_points=["limited mainstream appeal", "niche genre"]
            ),
            "artist_2": ReviewInsight(
                artist_id="artist_2",
                artist_name="Carpenter Brut",
                review_sentiment=0.80,
                review_count=120,
                genre_tags=["synthwave", "electronic", "darkwave"],
                unique_descriptors=["aggressive", "cinematic", "powerful"],
                discovery_score=0.70,
                last_updated="2024-01-10T00:00:00Z",
                themes=["dark atmosphere", "cinematic intensity", "aggressive sound"],
                pain_points=["too intense for casual listeners", "niche appeal"]
            ),
            "artist_3": ReviewInsight(
                artist_id="artist_3",
                artist_name="Gunship",
                review_sentiment=0.82,
                review_count=100,
                genre_tags=["synthwave", "electronic", "cyberpunk"],
                unique_descriptors=["futuristic", "immersive", "energetic"],
                discovery_score=0.72,
                last_updated="2024-01-12T00:00:00Z",
                themes=["cyberpunk aesthetics", "futuristic sound", "immersive experience"],
                pain_points=["niche genre", "limited mainstream recognition"]
            ),
            "artist_4": ReviewInsight(
                artist_id="artist_4",
                artist_name="Perturbator",
                review_sentiment=0.78,
                review_count=90,
                genre_tags=["synthwave", "darkwave", "electronic"],
                unique_descriptors=["dark", "intense", "atmospheric"],
                discovery_score=0.68,
                last_updated="2024-01-08T00:00:00Z",
                themes=["dark atmosphere", "intense soundscapes", "atmospheric depth"],
                pain_points=["too dark for some listeners", "niche appeal"]
            ),
            "artist_5": ReviewInsight(
                artist_id="artist_5",
                artist_name="Timecop1983",
                review_sentiment=0.88,
                review_count=180,
                genre_tags=["synthwave", "dreamwave", "electronic"],
                unique_descriptors=["dreamy", "emotional", "nostalgic"],
                discovery_score=0.78,
                last_updated="2024-01-14T00:00:00Z",
                themes=["dreamy atmosphere", "emotional depth", "nostalgic quality"],
                pain_points=["slow tempo", "niche genre"]
            )
        }
        
        # Mock theme clusters
        self._theme_clusters = {
            "cluster_1": ThemeCluster(
                cluster_id="cluster_1",
                theme_name="Repetitive Recommendations",
                description="Users complain about receiving similar songs repeatedly",
                keywords=["repetitive", "similar", "same", "boring", "predictable"],
                sentiment=-0.6,
                frequency=150,
                related_artists=["artist_1", "artist_2", "artist_3"]
            ),
            "cluster_2": ThemeCluster(
                cluster_id="cluster_2",
                theme_name="Genre Discovery",
                description="Users want to discover new genres and expand their musical taste",
                keywords=["discovery", "new", "explore", "genre", "variety"],
                sentiment=0.7,
                frequency=120,
                related_artists=["artist_4", "artist_5"]
            ),
            "cluster_3": ThemeCluster(
                cluster_id="cluster_3",
                theme_name="Mood Matching",
                description="Users want music that matches their current mood",
                keywords=["mood", "feeling", "emotional", "atmosphere", "vibe"],
                sentiment=0.5,
                frequency=100,
                related_artists=["artist_1", "artist_4"]
            )
        }
        
        # Mock pain points
        self._pain_points = {
            "pain_1": PainPoint(
                pain_point_id="pain_1",
                description="Users repeatedly receive similar songs",
                severity=0.8,
                frequency=150,
                affected_segments=["segment_1", "segment_2"],
                suggested_action="Increase diversity scoring and implement stronger deduplication"
            ),
            "pain_2": PainPoint(
                pain_point_id="pain_2",
                description="Recommendations don't match user's current mood",
                severity=0.6,
                frequency=80,
                affected_segments=["segment_1"],
                suggested_action="Improve mood-activity matching algorithm"
            ),
            "pain_3": PainPoint(
                pain_point_id="pain_3",
                description="Too many popular songs, not enough discovery",
                severity=0.5,
                frequency=60,
                affected_segments=["segment_3"],
                suggested_action="Adjust popularity filters and increase novelty weighting"
            )
        }
        
        # Mock user segments
        self._user_segments = {
            "segment_1": UserSegment(
                segment_id="segment_1",
                segment_name="Active Explorers",
                description="Users who actively seek new music and diverse recommendations",
                size=5000,
                preferences={
                    "discovery_preference": "novel",
                    "diversity_importance": 0.9,
                    "novelty_importance": 0.8
                },
                behaviors=["frequent_listening", "genre_exploration", "artist_discovery"],
                pain_points=["pain_1", "pain_2"]
            ),
            "segment_2": UserSegment(
                segment_id="segment_2",
                segment_name="Mood-Based Listeners",
                description="Users who primarily listen based on mood and activity",
                size=8000,
                preferences={
                    "discovery_preference": "balanced",
                    "mood_importance": 0.9,
                    "activity_importance": 0.8
                },
                behaviors=["mood_based_listening", "activity_based_listening"],
                pain_points=["pain_1"]
            ),
            "segment_3": UserSegment(
                segment_id="segment_3",
                segment_name="Familiarity Seekers",
                description="Users who prefer familiar music and popular tracks",
                size=3000,
                preferences={
                    "discovery_preference": "familiar",
                    "popularity_importance": 0.9,
                    "familiarity_importance": 0.8
                },
                behaviors=["repeat_listening", "popular_tracks"],
                pain_points=["pain_3"]
            )
        }
        
        # Mock product insights
        self._product_insights = {
            "insight_1": ProductInsight(
                insight_id="insight_1",
                category="Diversity",
                title="Low Diversity in Recommendations",
                description="Analysis shows 40% of users receive similar songs within 5 recommendations",
                impact="high",
                actionable=True,
                recommendation="Implement stronger diversity penalties and genre rotation"
            ),
            "insight_2": ProductInsight(
                insight_id="insight_2",
                category="Personalization",
                title="Mood Matching Accuracy",
                description="Mood-based recommendations have 65% user satisfaction rate",
                impact="medium",
                actionable=True,
                recommendation="Improve audio feature extraction for mood matching"
            ),
            "insight_3": ProductInsight(
                insight_id="insight_3",
                category="Discovery",
                title="Genre Exploration Success",
                description="Users who explore new genres show 30% higher engagement",
                impact="medium",
                actionable=True,
                recommendation="Encourage genre exploration through UI prompts"
            )
        }
        
        # Mock executive report
        self._executive_report = ExecutiveReport(
            report_id="report_2024_01",
            generated_at="2024-01-15T00:00:00Z",
            summary="User feedback indicates need for improved diversity and better mood matching. Active explorers show highest engagement but report repetitive recommendations.",
            key_findings=[
                "40% of users experience repetitive recommendations",
                "Mood-based recommendations have 65% satisfaction",
                "Genre exploration increases engagement by 30%",
                "Active explorers are the most engaged segment"
            ],
            recommendations=[
                "Increase diversity scoring in recommendation fusion",
                "Improve mood-activity matching algorithm",
                "Add genre exploration prompts in UI",
                "Implement user segment-based personalization"
            ],
            theme_clusters=list(self._theme_clusters.values()),
            pain_points=list(self._pain_points.values()),
            user_segments=list(self._user_segments.values()),
            product_insights=list(self._product_insights.values())
        )
    
    async def get_review_insights(
        self,
        genres: Optional[List[str]] = None,
        min_discovery_score: float = 0.5,
        limit: int = 20
    ) -> List[ReviewInsight]:
        """Get review insights for artists."""
        insights = list(self._insights.values())
        
        # Filter by discovery score
        insights = [i for i in insights if i.discovery_score >= min_discovery_score]
        
        # Filter by genres
        if genres:
            insights = [
                i for i in insights
                if any(g in i.genre_tags for g in genres)
            ]
        
        return insights[:limit]
    
    async def get_artist_review_insight(self, artist_id: str) -> Optional[ReviewInsight]:
        """Get review insight for a specific artist."""
        return self._insights.get(artist_id)
    
    async def get_theme_clusters(
        self,
        limit: int = 20
    ) -> List[ThemeCluster]:
        """Get theme clusters from review analysis."""
        return list(self._theme_clusters.values())[:limit]
    
    async def get_pain_points(
        self,
        severity_threshold: float = 0.5,
        limit: int = 20
    ) -> List[PainPoint]:
        """Get pain points from review analysis."""
        pain_points = [
            pp for pp in self._pain_points.values()
            if pp.severity >= severity_threshold
        ]
        return sorted(pain_points, key=lambda x: x.severity, reverse=True)[:limit]
    
    async def get_user_segments(
        self,
        limit: int = 20
    ) -> List[UserSegment]:
        """Get user segments from review analysis."""
        return list(self._user_segments.values())[:limit]
    
    async def get_user_segment(self, segment_id: str) -> Optional[UserSegment]:
        """Get a specific user segment."""
        return self._user_segments.get(segment_id)
    
    async def get_product_insights(
        self,
        actionable_only: bool = False,
        limit: int = 20
    ) -> List[ProductInsight]:
        """Get product insights from executive report."""
        insights = list(self._product_insights.values())
        
        if actionable_only:
            insights = [i for i in insights if i.actionable]
        
        return insights[:limit]
    
    async def get_executive_report(self) -> Optional[ExecutiveReport]:
        """Get the executive report summary."""
        return self._executive_report
    
    async def close(self) -> None:
        """Close the client (no-op for mock)."""
        pass
