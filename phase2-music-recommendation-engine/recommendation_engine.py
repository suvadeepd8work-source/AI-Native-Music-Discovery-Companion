"""
Core Recommendation Engine for Phase 2: Music Recommendation Engine.
Integrates multiple recommendation strategies and fuses results.
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
import structlog
from .schemas import (
    RecommendationRequest,
    Recommendation,
    RecommendationCandidate,
    RecommendationResponse,
    StrategyResult,
    MoodType,
    ActivityType,
    DiscoveryPreferenceType
)
from .lastfm_client import LastFMClient, MockLastFMClient
from .review_client import ReviewEngineClient, MockReviewEngineClient
from .storage import RecommendationStorage, MockRecommendationStorage
from .explainability_engine import ExplainabilityEngine, MockExplainabilityEngine


logger = structlog.get_logger(__name__)


# Mood to audio feature mappings
MOOD_FEATURE_RANGES = {
    MoodType.ENERGETIC: {
        "energy": (0.7, 1.0),
        "valence": (0.6, 1.0),
        "tempo": (120, 160)
    },
    MoodType.CALM: {
        "energy": (0.2, 0.5),
        "valence": (0.4, 0.7),
        "tempo": (60, 100)
    },
    MoodType.MELANCHOLIC: {
        "energy": (0.2, 0.5),
        "valence": (0.1, 0.4),
        "acousticness": (0.5, 1.0)
    },
    MoodType.UPBEAT: {
        "energy": (0.6, 0.9),
        "valence": (0.7, 1.0),
        "tempo": (100, 140)
    },
    MoodType.FOCUS: {
        "energy": (0.3, 0.6),
        "instrumentalness": (0.6, 1.0),
        "speechiness": (0.0, 0.3)
    },
    MoodType.RELAXED: {
        "energy": (0.2, 0.5),
        "valence": (0.4, 0.7),
        "tempo": (60, 90)
    },
    MoodType.HAPPY: {
        "energy": (0.6, 0.9),
        "valence": (0.7, 1.0),
        "danceability": (0.6, 0.9)
    },
    MoodType.SAD: {
        "energy": (0.2, 0.4),
        "valence": (0.1, 0.4),
        "acousticness": (0.4, 0.8)
    },
    MoodType.ROMANTIC: {
        "energy": (0.3, 0.6),
        "valence": (0.5, 0.8),
        "acousticness": (0.3, 0.7)
    },
    MoodType.AGGRESSIVE: {
        "energy": (0.8, 1.0),
        "valence": (0.3, 0.6),
        "tempo": (130, 170)
    }
}

# Activity to audio feature mappings
ACTIVITY_FEATURE_RANGES = {
    ActivityType.CODING: {
        "energy": (0.4, 0.7),
        "instrumentalness": (0.5, 0.9),
        "tempo": (80, 120)
    },
    ActivityType.WORKOUT: {
        "energy": (0.8, 1.0),
        "tempo": (120, 160),
        "danceability": (0.7, 1.0)
    },
    ActivityType.STUDYING: {
        "energy": (0.2, 0.5),
        "instrumentalness": (0.7, 1.0),
        "speechiness": (0.0, 0.2)
    },
    ActivityType.RELAXATION: {
        "energy": (0.2, 0.5),
        "valence": (0.4, 0.7),
        "tempo": (60, 90)
    },
    ActivityType.SLEEP: {
        "energy": (0.1, 0.3),
        "valence": (0.3, 0.6),
        "tempo": (40, 70)
    },
    ActivityType.FOCUS: {
        "energy": (0.3, 0.6),
        "instrumentalness": (0.6, 1.0),
        "speechiness": (0.0, 0.3)
    },
    ActivityType.ENTERTAINMENT: {
        "energy": (0.5, 0.8),
        "valence": (0.6, 0.9),
        "danceability": (0.5, 0.8)
    },
    ActivityType.BACKGROUND: {
        "energy": (0.3, 0.6),
        "speechiness": (0.0, 0.4),
        "instrumentalness": (0.4, 0.8)
    },
    ActivityType.ACTIVE_LISTENING: {
        "energy": (0.4, 0.8),
        "valence": (0.5, 0.9),
        "danceability": (0.4, 0.8)
    },
    ActivityType.SOCIAL: {
        "energy": (0.5, 0.8),
        "valence": (0.6, 0.9),
        "danceability": (0.6, 0.9)
    }
}


class RecommendationEngine:
    """
    Main recommendation engine that integrates multiple strategies and APIs.
    """
    
    def __init__(
        self,
        lastfm_client: LastFMClient,
        review_client: ReviewEngineClient,
        storage: Optional[RecommendationStorage] = None,
        explainability_engine: Optional[ExplainabilityEngine] = None,
        config: Dict[str, Any] = None
    ):
        self.lastfm = lastfm_client
        self.review = review_client
        self.storage = storage or RecommendationStorage()
        self.explainability = explainability_engine or ExplainabilityEngine()
        self.config = config or {}
        
        self.strategies_config = self.config.get("recommendation", {}).get("strategies", {})
        self.fusion_config = self.config.get("recommendation", {}).get("fusion", {})
        self.api_config = self.config.get("api_sources", {})
        
        # Cache for reducing redundant API calls
        self._track_cache: Dict[str, Any] = {}
        self._artist_cache: Dict[str, Any] = {}
        self._cache_ttl = 1800  # 30 minutes cache
    
    def clear_cache(self):
        """Clear the recommendation engine cache."""
        self._track_cache.clear()
        self._artist_cache.clear()
        logger.info("Recommendation engine cache cleared")
    
    async def generate_recommendations(
        self,
        request: RecommendationRequest
    ) -> RecommendationResponse:
        """
        Generate music recommendations based on request.
        
        Args:
            request: Recommendation request with context from Phase 1
            
        Returns:
            RecommendationResponse with ranked recommendations
        """
        start_time = time.time()
        strategies_executed = []
        all_candidates: List[RecommendationCandidate] = []
        
        # Fetch review insights if enabled
        review_data = None
        if request.review_insights_enabled:
            review_data = await self._fetch_review_insights(request)
        
        # Apply insight-based adjustments
        if review_data:
            await self._apply_insight_adjustments(request, review_data)
        
        # Execute enabled strategies in parallel
        strategy_tasks = []
        
        if self.strategies_config.get("review_based", {}).get("enabled", True):
            strategy_tasks.append(self._review_based_discovery(request))
        
        if self.strategies_config.get("mood_activity", {}).get("enabled", True):
            strategy_tasks.append(self._mood_activity_matching(request))
        
        if self.strategies_config.get("similarity_search", {}).get("enabled", True):
            strategy_tasks.append(self._similarity_search(request))
        
        if self.strategies_config.get("habit_breaking", {}).get("enabled", True):
            strategy_tasks.append(self._habit_breaking(request))
        
        if self.strategies_config.get("genre_exploration", {}).get("enabled", True):
            strategy_tasks.append(self._genre_exploration(request))
        
        # Execute all strategies
        strategy_results = await asyncio.gather(*strategy_tasks, return_exceptions=True)
        
        # Collect results
        for result in strategy_results:
            if isinstance(result, Exception):
                logger.error("Strategy execution failed", error=str(result))
                continue
            
            if isinstance(result, StrategyResult):
                if result.success:
                    strategies_executed.append(result.strategy_name)
                    all_candidates.extend(result.candidates)
                else:
                    logger.warning(
                        "Strategy failed",
                        strategy=result.strategy_name,
                        error=result.error_message
                    )
        
        # Fuse and rank recommendations
        recommendations = await self._fuse_recommendations(
            all_candidates,
            request,
            strategies_executed,
            review_data
        )
        
        # Limit to requested number
        max_recommendations = self.fusion_config.get("max_recommendations", 10)
        recommendations = recommendations[:min(request.limit, max_recommendations)]
        
        # Store recommendations with full metadata
        await self._store_recommendations(request, recommendations)
        
        # Store explanations
        await self._store_explanations(request, recommendations)
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return RecommendationResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            recommendations=recommendations,
            total_count=len(recommendations),
            strategies_executed=strategies_executed,
            execution_time_ms=execution_time_ms
        )
    
    async def _store_recommendations(
        self,
        request: RecommendationRequest,
        recommendations: List[Recommendation]
    ) -> None:
        """Store recommendations with full metadata."""
        from .schemas import StoredRecommendation, Artist, Album
        
        for recommendation in recommendations:
            # Get full artist metadata
            artist = await self._get_artist_metadata(recommendation.track.artist_id)
            
            # Get full album metadata if available
            album = None
            if recommendation.track.album_id:
                album = await self._get_album_metadata(recommendation.track.album_id)
            
            # Create stored recommendation
            stored_rec = StoredRecommendation(
                recommendation_id=self.storage._generate_recommendation_id(),
                user_id=request.user_id,
                session_id=request.session_id,
                track=recommendation.track,
                artist=artist,
                album=album,
                confidence=recommendation.confidence,
                explanation=recommendation.explanation,
                strategies_used=recommendation.strategies_used,
                generated_at=datetime.utcnow()
            )
            
            # Store
            self.storage.store_recommendation(stored_rec)
    
    async def _store_explanations(
        self,
        request: RecommendationRequest,
        recommendations: List[Recommendation]
    ) -> None:
        """Store detailed explanations for recommendations."""
        for i, recommendation in enumerate(recommendations):
            if recommendation.detailed_explanation:
                recommendation_id = f"rec_{request.session_id}_{i}"
                self.explainability.store_explanation(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    recommendation_id=recommendation_id,
                    explanation=recommendation.detailed_explanation
                )
    
    async def _get_artist_metadata(self, artist_id: str) -> Artist:
        """Get artist metadata from available APIs."""
        # Try Last.fm first
        if self.lastfm:
            artist = await self.lastfm.get_artist(artist_id)
            if artist:
                return artist
        
        # Fallback to basic artist info
        return Artist(
            artist_id=artist_id,
            source="fallback",
            artist_name="Unknown",
            genres=[],
            popularity=0,
            followers=0,
            external_url=None,
            image_url=None,
            similar_artists=[],
            biography=None,
            country=None,
            formation_year=None,
            albums=[],
            top_tracks=[]
        )
    
    async def _get_album_metadata(self, album_id: str) -> Optional[Album]:
        """Get album metadata from available APIs."""
        # Last.fm doesn't have direct album metadata in current implementation
        return None
    
    async def _review_based_discovery(
        self,
        request: RecommendationRequest
    ) -> StrategyResult:
        """Strategy: Review-based artist discovery."""
        start_time = time.time()
        
        try:
            config = self.strategies_config.get("review_based", {})
            min_discovery_score = config.get("min_discovery_score", 0.5)
            max_results = config.get("max_results", 10)
            
            # Get review insights
            insights = await self.review.get_review_insights(
                genres=request.preferred_genres if request.preferred_genres else None,
                min_discovery_score=min_discovery_score,
                limit=max_results * 2
            )
            
            # Filter out previously recommended artists
            insights = [
                i for i in insights
                if i.artist_id not in request.previously_recommended_artists
            ]
            
            # Get Last.fm data for top insights
            candidates = []
            for insight in insights[:max_results]:
                artist = await self.lastfm.get_artist(insight.artist_id)
                if artist:
                    # Get top tracks for this artist
                    tracks = await self.lastfm.search_tracks(
                        query=artist.artist_name,
                        limit=1
                    )
                    
                    if tracks:
                        track = tracks[0]
                        score = self._calculate_review_score(insight, artist, request)
                        
                        candidate = RecommendationCandidate(
                            item=track,
                            strategy="review_based",
                            score=score,
                            metadata={
                                "review_sentiment": insight.review_sentiment,
                                "review_count": insight.review_count,
                                "discovery_score": insight.discovery_score,
                                "unique_descriptors": insight.unique_descriptors
                            }
                        )
                        candidates.append(candidate)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return StrategyResult(
                strategy_name="review_based",
                candidates=candidates,
                execution_time_ms=execution_time_ms,
                success=True
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return StrategyResult(
                strategy_name="review_based",
                candidates=[],
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )
    
    async def _mood_activity_matching(
        self,
        request: RecommendationRequest
    ) -> StrategyResult:
        """Strategy: Mood and activity-based matching."""
        start_time = time.time()
        
        try:
            config = self.strategies_config.get("mood_activity", {})
            max_results = config.get("max_results", 10)
            
            # Combine mood and activity features
            feature_ranges = {}
            
            if request.mood:
                mood_ranges = MOOD_FEATURE_RANGES.get(request.mood, {})
                feature_ranges.update(mood_ranges)
            
            if request.activity:
                activity_ranges = ACTIVITY_FEATURE_RANGES.get(request.activity, {})
                feature_ranges.update(activity_ranges)
            
            # Build search parameters
            search_params = {}
            
            if "energy" in feature_ranges:
                min_e, max_e = feature_ranges["energy"]
                search_params["min_energy"] = min_e
                search_params["max_energy"] = max_e
            
            if "valence" in feature_ranges:
                min_v, max_v = feature_ranges["valence"]
                search_params["min_valence"] = min_v
                search_params["max_valence"] = max_v
            
            if "danceability" in feature_ranges:
                min_d, max_d = feature_ranges["danceability"]
                search_params["min_danceability"] = min_d
                search_params["max_danceability"] = max_d
            
            if "tempo" in feature_ranges:
                min_t, max_t = feature_ranges["tempo"]
                search_params["min_tempo"] = min_t
                search_params["max_tempo"] = max_t
            
            if "instrumentalness" in feature_ranges:
                search_params["target_instrumentalness"] = feature_ranges["instrumentalness"][0]
            
            if "speechiness" in feature_ranges:
                search_params["max_speechiness"] = feature_ranges["speechiness"][1]
            
            # Search tracks using Last.fm
            # Last.fm doesn't support audio feature filtering, so we'll do basic search
            tracks = await self.lastfm.search_tracks(
                query=request.preferred_genres[0] if request.preferred_genres else "",
                limit=max_results * 2
            )
            
            # Filter out previously recommended songs
            tracks = [
                t for t in tracks
                if t.track_id not in request.previously_recommended_songs
            ]
            
            # Score candidates
            candidates = []
            for track in tracks[:max_results]:
                score = self._calculate_mood_score(track, feature_ranges, request)
                
                candidate = RecommendationCandidate(
                    item=track,
                    strategy="mood_activity",
                    score=score,
                    metadata={
                        "mood": request.mood.value if request.mood else None,
                        "activity": request.activity.value if request.activity else None,
                        "feature_ranges": feature_ranges
                    }
                )
                candidates.append(candidate)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return StrategyResult(
                strategy_name="mood_activity",
                candidates=candidates,
                execution_time_ms=execution_time_ms,
                success=True
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return StrategyResult(
                strategy_name="mood_activity",
                candidates=[],
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )
    
    async def _similarity_search(
        self,
        request: RecommendationRequest
    ) -> StrategyResult:
        """Strategy: Similarity search based on preferred artists with optimized API calls."""
        start_time = time.time()
        
        try:
            config = self.strategies_config.get("similarity_search", {})
            max_results = config.get("max_results", 10)
            min_similarity = config.get("min_similarity", 0.7)
            
            candidates = []
            
            # Collect all similar artist names first to batch track searches
            all_similar_artist_names = set()
            
            for artist_name in request.preferred_artists[:2]:
                # Get similar artists from Last.fm
                similar_artists = await self.lastfm.get_similar_artists(artist_name, limit=max_results)
                # Add artist names to set for deduplication
                all_similar_artist_names.update([sa.artist_name for sa in similar_artists])
            
            # Batch search for tracks from all similar artists at once
            # This reduces API calls from N*M to N+1 where N=artists, M=similar_artists_per_artist
            tracks = []
            artist_search_query = " OR ".join(list(all_similar_artist_names)[:5])  # Limit to 5 artists for search
            if artist_search_query:
                tracks = await self.lastfm.search_tracks(
                    query=artist_search_query,
                    limit=max_results * 3
                )
            
            # Filter out previously recommended
            tracks = [
                t for t in tracks
                if t.track_id not in request.previously_recommended_songs
                and t.artist_id not in request.previously_recommended_artists
            ]
            
            for track in tracks[:max_results]:
                # Simple similarity score based on genre overlap
                score = 0.8  # Base similarity score
                
                if track.artist_name not in request.preferred_artists:
                    score += 0.1  # Bonus for different artist
                
                candidate = RecommendationCandidate(
                    item=track,
                    strategy="similarity_search",
                    score=score,
                    metadata={
                        "reference_artists": request.preferred_artists[:2],
                        "similarity_score": score
                    }
                )
                candidates.append(candidate)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return StrategyResult(
                strategy_name="similarity_search",
                candidates=candidates[:max_results],
                execution_time_ms=execution_time_ms,
                success=True
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return StrategyResult(
                strategy_name="similarity_search",
                candidates=[],
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )
    
    async def _habit_breaking(
        self,
        request: RecommendationRequest
    ) -> StrategyResult:
        """Strategy: Habit breaking with novel recommendations."""
        start_time = time.time()
        
        try:
            config = self.strategies_config.get("habit_breaking", {})
            max_results = config.get("max_results", 5)
            novelty_threshold = config.get("novelty_threshold", 0.5)
            
            # If user wants novel recommendations, prioritize less popular artists
            if request.discovery_goal == DiscoveryPreferenceType.NOVEL:
                # Search for tracks with lower popularity using Last.fm
                tracks = await self.lastfm.search_tracks(
                    query=request.preferred_genres[0] if request.preferred_genres else "",
                    limit=max_results * 3
                )
                
                # Filter for lower popularity (more novel)
                novel_tracks = [
                    t for t in tracks
                    if t.popularity < 50
                    and t.track_id not in request.previously_recommended_songs
                    and t.artist_id not in request.previously_recommended_artists
                ]
                
                candidates = []
                for track in novel_tracks[:max_results]:
                    # Novelty score inversely related to popularity
                    novelty_score = 1.0 - (track.popularity / 100)
                    score = max(novelty_score, novelty_threshold)
                    
                    candidate = RecommendationCandidate(
                        item=track,
                        strategy="habit_breaking",
                        score=score,
                        metadata={
                            "novelty_score": novelty_score,
                            "popularity": track.popularity
                        }
                    )
                    candidates.append(candidate)
                
                execution_time_ms = (time.time() - start_time) * 1000
                
                return StrategyResult(
                    strategy_name="habit_breaking",
                    candidates=candidates,
                    execution_time_ms=execution_time_ms,
                    success=True
                )
            else:
                # Return empty if not seeking novelty
                execution_time_ms = (time.time() - start_time) * 1000
                return StrategyResult(
                    strategy_name="habit_breaking",
                    candidates=[],
                    execution_time_ms=execution_time_ms,
                    success=True
                )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return StrategyResult(
                strategy_name="habit_breaking",
                candidates=[],
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )
    
    async def _genre_exploration(
        self,
        request: RecommendationRequest
    ) -> StrategyResult:
        """Strategy: Genre exploration."""
        start_time = time.time()
        
        try:
            config = self.strategies_config.get("genre_exploration", {})
            max_results = config.get("max_results", 5)
            
            candidates = []
            
            # If user has preferred genres, search for tracks in those genres using Last.fm
            if request.preferred_genres:
                for genre in request.preferred_genres[:2]:
                    tracks = await self.lastfm.search_tracks(
                        query=genre,
                        limit=max_results
                    )
                    
                    # Filter out previously recommended
                    tracks = [
                        t for t in tracks
                        if t.track_id not in request.previously_recommended_songs
                        and t.artist_id not in request.previously_recommended_artists
                    ]
                    
                    for track in tracks[:max_results]:
                        score = 0.75  # Base genre match score
                        
                        candidate = RecommendationCandidate(
                            item=track,
                            strategy="genre_exploration",
                            score=score,
                            metadata={
                                "genre": genre,
                                "genre_match": True
                            }
                        )
                        candidates.append(candidate)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return StrategyResult(
                strategy_name="genre_exploration",
                candidates=candidates[:max_results],
                execution_time_ms=execution_time_ms,
                success=True
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return StrategyResult(
                strategy_name="genre_exploration",
                candidates=[],
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )
    
    async def _fuse_recommendations(
        self,
        candidates: List[RecommendationCandidate],
        request: RecommendationRequest,
        strategies_executed: List[str],
        review_data: Optional[Dict[str, Any]] = None
    ) -> List[Recommendation]:
        """Fuse and rank recommendations from all strategies using multi-factor scoring."""
        
        logger.info(
            "Fusing recommendations",
            total_candidates=len(candidates),
            strategies=strategies_executed
        )
        
        # Calculate scores for each candidate
        for candidate in candidates:
            # Calculate novelty score
            candidate.novelty_score = self._calculate_novelty_score(candidate, request)
            
            # Calculate diversity score
            candidate.diversity_score = self._calculate_diversity_score(candidate, candidates)
            
            # Calculate intent match score
            candidate.intent_match_score = self._calculate_intent_match_score(candidate, request)
            
            # Calculate mood match score
            candidate.mood_match_score = self._calculate_mood_match_score(candidate, request)
            
            # Calculate activity match score
            candidate.activity_match_score = self._calculate_activity_match_score(candidate, request)
            
            # Calculate discovery match score
            candidate.discovery_match_score = self._calculate_discovery_match_score(candidate, request)
            
            # Calculate context match score
            candidate.context_match_score = self._calculate_context_match_score(candidate, request)
        
        # Remove duplicates with advanced duplicate avoidance
        unique_candidates = self._advanced_duplicate_avoidance(candidates, request)
        
        logger.info(
            "After duplicate removal",
            unique_candidates=len(unique_candidates)
        )
        
        # Calculate final weighted scores
        ranking_weights = self.fusion_config.get("ranking_weights", {})
        for candidate in unique_candidates:
            final_score = (
                candidate.score * ranking_weights.get("strategy_score", 0.3) +
                candidate.novelty_score * ranking_weights.get("novelty_score", 0.2) +
                candidate.diversity_score * ranking_weights.get("diversity_score", 0.15) +
                candidate.intent_match_score * ranking_weights.get("intent_match_score", 0.15) +
                candidate.mood_match_score * ranking_weights.get("mood_match_score", 0.1) +
                candidate.activity_match_score * ranking_weights.get("activity_match_score", 0.05) +
                candidate.discovery_match_score * ranking_weights.get("discovery_match_score", 0.03) +
                candidate.context_match_score * ranking_weights.get("context_match_score", 0.02)
            )
            candidate.score = final_score
        
        # Sort by final score
        unique_candidates.sort(key=lambda x: x.score, reverse=True)
        
        # Apply popularity filters
        min_popularity = self.fusion_config.get("min_popularity", 10)
        max_popularity = self.fusion_config.get("max_popularity", 95)
        unique_candidates = [
            c for c in unique_candidates
            if min_popularity <= c.item.popularity <= max_popularity
        ]
        
        logger.info(
            "After popularity filter",
            filtered_candidates=len(unique_candidates)
        )
        
        # Generate recommendations with explanations
        recommendations = []
        for candidate in unique_candidates:
            explanation = await self._generate_explanation(candidate, request)
            
            recommendation = Recommendation(
                track=candidate.item,
                confidence=candidate.score,
                explanation=explanation,
                strategies_used=[candidate.strategy],
                metadata={
                    "novelty_score": candidate.novelty_score,
                    "diversity_score": candidate.diversity_score,
                    "intent_match_score": candidate.intent_match_score,
                    "mood_match_score": candidate.mood_match_score,
                    "activity_match_score": candidate.activity_match_score,
                    "discovery_match_score": candidate.discovery_match_score,
                    "context_match_score": candidate.context_match_score
                }
            )
            
            # Generate detailed explanation using explainability engine
            detailed_explanation = self.explainability.generate_explanation(
                recommendation=recommendation,
                candidate=candidate,
                request=request
            )
            recommendation.detailed_explanation = detailed_explanation
            
            recommendations.append(recommendation)
        
        # Log recommendation details
        self._log_recommendations(recommendations, request)
        
        return recommendations
    
    async def _fetch_review_insights(
        self,
        request: RecommendationRequest
    ) -> Optional[Dict[str, Any]]:
        """Fetch review insights from Review Discovery Engine."""
        try:
            # Get executive report
            executive_report = await self.review.get_executive_report()
            
            # Get pain points
            pain_points = await self.review.get_pain_points(severity_threshold=0.5)
            
            # Get user segments
            user_segments = await self.review.get_user_segments()
            
            # Get user's specific segment if provided
            user_segment = None
            if request.user_segment_id:
                user_segment = await self.review.get_user_segment(request.user_segment_id)
            
            # Get product insights
            product_insights = await self.review.get_product_insights(actionable_only=True)
            
            return {
                "executive_report": executive_report,
                "pain_points": pain_points,
                "user_segments": user_segments,
                "user_segment": user_segment,
                "product_insights": product_insights
            }
        except Exception as e:
            logger.error("Failed to fetch review insights", error=str(e))
            return None
    
    async def _apply_insight_adjustments(
        self,
        request: RecommendationRequest,
        review_data: Dict[str, Any]
    ) -> None:
        """Apply insight-based adjustments to recommendation parameters."""
        pain_points = review_data.get("pain_points", [])
        user_segment = review_data.get("user_segment")
        product_insights = review_data.get("product_insights", [])
        
        # Apply pain point mitigations
        for pain_point in pain_points:
            if "repetitive" in pain_point.description.lower() or "similar" in pain_point.description.lower():
                # Increase diversity penalty
                current_penalty = self.fusion_config.get("diversity_penalty", 0.1)
                self.fusion_config["diversity_penalty"] = min(0.3, current_penalty + 0.1)
                logger.info("Increased diversity penalty due to repetitive recommendations pain point")
            
            if "mood" in pain_point.description.lower():
                # Increase mood matching weight
                current_weight = self.fusion_config.get("ranking_weights", {}).get("mood_match_score", 0.1)
                self.fusion_config.setdefault("ranking_weights", {})["mood_match_score"] = min(0.2, current_weight + 0.05)
                logger.info("Increased mood matching weight due to mood matching pain point")
            
            if "popular" in pain_point.description.lower() or "discovery" in pain_point.description.lower():
                # Increase novelty weight
                current_weight = self.fusion_config.get("ranking_weights", {}).get("novelty_score", 0.2)
                self.fusion_config.setdefault("ranking_weights", {})["novelty_score"] = min(0.3, current_weight + 0.05)
                logger.info("Increased novelty weight due to discovery pain point")
        
        # Apply user segment preferences
        if user_segment:
            preferences = user_segment.preferences
            
            if "discovery_preference" in preferences:
                request.discovery_goal = preferences["discovery_preference"]
            
            if "diversity_importance" in preferences:
                current_weight = self.fusion_config.get("ranking_weights", {}).get("diversity_score", 0.15)
                self.fusion_config.setdefault("ranking_weights", {})["diversity_score"] = min(0.3, current_weight + 0.1)
            
            if "novelty_importance" in preferences:
                current_weight = self.fusion_config.get("ranking_weights", {}).get("novelty_score", 0.2)
                self.fusion_config.setdefault("ranking_weights", {})["novelty_score"] = min(0.3, current_weight + 0.1)
            
            if "mood_importance" in preferences:
                current_weight = self.fusion_config.get("ranking_weights", {}).get("mood_match_score", 0.1)
                self.fusion_config.setdefault("ranking_weights", {})["mood_match_score"] = min(0.2, current_weight + 0.05)
            
            logger.info("Applied user segment preferences", segment=user_segment.segment_name)
        
        # Apply product insights
        for insight in product_insights:
            if insight.actionable and insight.impact == "high":
                if "diversity" in insight.category.lower():
                    current_penalty = self.fusion_config.get("diversity_penalty", 0.1)
                    self.fusion_config["diversity_penalty"] = min(0.3, current_penalty + 0.05)
                    logger.info("Applied product insight: increase diversity")
                
                if "personalization" in insight.category.lower():
                    current_weight = self.fusion_config.get("ranking_weights", {}).get("context_match_score", 0.02)
                    self.fusion_config.setdefault("ranking_weights", {})["context_match_score"] = min(0.1, current_weight + 0.02)
                    logger.info("Applied product insight: increase personalization")
    
    def _calculate_novelty_score(
        self,
        candidate: RecommendationCandidate,
        request: RecommendationRequest
    ) -> float:
        """Calculate novelty score based on how new/unusual the track is."""
        novelty = 0.5
        
        # Penalize if track was previously recommended
        if candidate.item.track_id in request.previously_recommended_songs:
            novelty -= 0.3
        
        # Penalize if artist was previously recommended
        if candidate.item.artist_id in request.previously_recommended_artists:
            novelty -= 0.2
        
        # Boost if artist is less popular (more novel)
        if candidate.item.popularity < 50:
            novelty += 0.2
        
        # Boost if release year is recent (new music)
        if candidate.item.release_year and candidate.item.release_year >= 2023:
            novelty += 0.1
        
        return max(0.0, min(1.0, novelty))
    
    def _calculate_diversity_score(
        self,
        candidate: RecommendationCandidate,
        all_candidates: List[RecommendationCandidate]
    ) -> float:
        """Calculate diversity score based on how different from other candidates."""
        diversity = 0.5
        
        # Count how many candidates have same artist
        same_artist_count = sum(
            1 for c in all_candidates
            if c.item.artist_id == candidate.item.artist_id
        )
        
        # Penalize if many candidates from same artist
        if same_artist_count > 2:
            diversity -= 0.2 * (same_artist_count - 2)
        
        # Count how many candidates have same genre
        if candidate.item.genres:
            for genre in candidate.item.genres[:2]:
                same_genre_count = sum(
                    1 for c in all_candidates
                    if genre in c.item.genres
                )
                if same_genre_count > 5:
                    diversity -= 0.05 * (same_genre_count - 5)
        
        return max(0.0, min(1.0, diversity))
    
    def _calculate_intent_match_score(
        self,
        candidate: RecommendationCandidate,
        request: RecommendationRequest
    ) -> float:
        """Calculate how well the track matches user intent."""
        intent_score = 0.5
        
        # Boost if strategy matches intent
        if request.user_intent == "discovery" and candidate.strategy in ["review_based", "habit_breaking", "genre_exploration"]:
            intent_score += 0.3
        elif request.user_intent == "familiar" and candidate.strategy in ["similarity_search", "mood_activity"]:
            intent_score += 0.3
        elif request.user_intent == "mood" and candidate.strategy == "mood_activity":
            intent_score += 0.3
        
        return max(0.0, min(1.0, intent_score))
    
    def _calculate_mood_match_score(
        self,
        candidate: RecommendationCandidate,
        request: RecommendationRequest
    ) -> float:
        """Calculate how well the track matches requested mood."""
        if not request.mood or not candidate.item.audio_features:
            return 0.5
        
        mood_score = 0.5
        features = candidate.item.audio_features
        
        # Match mood to audio features
        mood_ranges = MOOD_FEATURE_RANGES.get(request.mood, {})
        
        for feature, (min_val, max_val) in mood_ranges.items():
            if hasattr(features, feature):
                value = getattr(features, feature)
                if min_val <= value <= max_val:
                    mood_score += 0.1
        
        return max(0.0, min(1.0, mood_score))
    
    def _calculate_activity_match_score(
        self,
        candidate: RecommendationCandidate,
        request: RecommendationRequest
    ) -> float:
        """Calculate how well the track matches requested activity."""
        if not request.activity or not candidate.item.audio_features:
            return 0.5
        
        activity_score = 0.5
        features = candidate.item.audio_features
        
        # Match activity to audio features
        activity_ranges = ACTIVITY_FEATURE_RANGES.get(request.activity, {})
        
        for feature, (min_val, max_val) in activity_ranges.items():
            if hasattr(features, feature):
                value = getattr(features, feature)
                if min_val <= value <= max_val:
                    activity_score += 0.15
        
        return max(0.0, min(1.0, activity_score))
    
    def _calculate_discovery_match_score(
        self,
        candidate: RecommendationCandidate,
        request: RecommendationRequest
    ) -> float:
        """Calculate how well the track matches discovery preference."""
        if not request.discovery_preference:
            return 0.5
        
        discovery_score = 0.5
        
        if request.discovery_preference == "novel":
            # Prefer less popular tracks
            if candidate.item.popularity < 30:
                discovery_score += 0.3
            elif candidate.item.popularity < 50:
                discovery_score += 0.15
        elif request.discovery_preference == "familiar":
            # Prefer more popular tracks
            if candidate.item.popularity > 70:
                discovery_score += 0.3
            elif candidate.item.popularity > 50:
                discovery_score += 0.15
        elif request.discovery_preference == "balanced":
            # Prefer mid-range popularity
            if 30 <= candidate.item.popularity <= 70:
                discovery_score += 0.2
        
        return max(0.0, min(1.0, discovery_score))
    
    def _calculate_context_match_score(
        self,
        candidate: RecommendationCandidate,
        request: RecommendationRequest
    ) -> float:
        """Calculate how well the track matches listening context."""
        context_score = 0.5
        
        # Check if track matches preferred genres
        if request.preferred_genres and candidate.item.genres:
            for genre in request.preferred_genres:
                if genre.lower() in [g.lower() for g in candidate.item.genres]:
                    context_score += 0.15
                    break
        
        # Check if track matches preferred artists
        if request.preferred_artists:
            if candidate.item.artist_id in request.preferred_artists:
                context_score += 0.2
        
        return max(0.0, min(1.0, context_score))
    
    def _advanced_duplicate_avoidance(
        self,
        candidates: List[RecommendationCandidate],
        request: RecommendationRequest
    ) -> List[RecommendationCandidate]:
        """Advanced duplicate avoidance considering multiple factors."""
        seen_track_ids = set(request.previously_recommended_songs)
        seen_artist_ids = set(request.previously_recommended_artists)
        unique_candidates = []
        
        repetition_penalty = self.fusion_config.get("repetition_penalty", 0.5)
        
        for candidate in candidates:
            # Skip if track was already recommended
            if candidate.item.track_id in seen_track_ids:
                candidate.score *= (1.0 - repetition_penalty)
                continue
            
            # Penalize if artist was recently recommended
            if candidate.item.artist_id in seen_artist_ids:
                candidate.score *= (1.0 - repetition_penalty * 0.5)
            
            # Add to seen sets
            seen_track_ids.add(candidate.item.track_id)
            seen_artist_ids.add(candidate.item.artist_id)
            unique_candidates.append(candidate)
        
        return unique_candidates
    
    def _log_recommendations(
        self,
        recommendations: List[Recommendation],
        request: RecommendationRequest
    ) -> None:
        """Log detailed recommendation information."""
        logger.info(
            "Recommendations generated",
            user_id=request.user_id,
            session_id=request.session_id,
            user_intent=request.user_intent,
            mood=request.mood,
            activity=request.activity,
            discovery_preference=request.discovery_preference,
            total_recommendations=len(recommendations),
            recommendations=[
                {
                    "track_id": r.track.track_id,
                    "track_name": r.track.track_name,
                    "artist_name": r.track.artist_name,
                    "confidence": r.confidence,
                    "strategy": r.strategies_used[0] if r.strategies_used else "unknown",
                    "novelty_score": r.metadata.get("novelty_score"),
                    "diversity_score": r.metadata.get("diversity_score"),
                    "intent_match_score": r.metadata.get("intent_match_score"),
                    "mood_match_score": r.metadata.get("mood_match_score"),
                    "activity_match_score": r.metadata.get("activity_match_score")
                }
                for r in recommendations
            ]
        )
    
    def _calculate_review_score(
        self,
        insight: Any,
        artist: Any,
        request: RecommendationRequest
    ) -> float:
        """Calculate score for review-based recommendation."""
        score = insight.discovery_score * 0.4
        score += insight.review_sentiment * 0.3
        score += (1 - artist.popularity / 100) * 0.2
        
        # Genre alignment bonus
        if request.preferred_genres:
            genre_match = any(g in insight.genre_tags for g in request.preferred_genres)
            if genre_match:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_mood_score(
        self,
        track: Any,
        feature_ranges: Dict[str, tuple],
        request: RecommendationRequest
    ) -> float:
        """Calculate score for mood-based recommendation."""
        score = 0.5  # Base score
        
        if track.audio_features:
            # Check energy alignment
            if "energy" in feature_ranges:
                min_e, max_e = feature_ranges["energy"]
                if min_e <= track.audio_features.energy <= max_e:
                    score += 0.15
            
            # Check valence alignment
            if "valence" in feature_ranges:
                min_v, max_v = feature_ranges["valence"]
                if min_v <= track.audio_features.valence <= max_v:
                    score += 0.15
            
            # Check danceability alignment
            if "danceability" in feature_ranges:
                min_d, max_d = feature_ranges["danceability"]
                if min_d <= track.audio_features.danceability <= max_d:
                    score += 0.1
            
            # Check instrumentalness alignment
            if "instrumentalness" in feature_ranges:
                target_i = feature_ranges["instrumentalness"][0]
                if abs(track.audio_features.instrumentalness - target_i) < 0.2:
                    score += 0.1
        
        return min(score, 1.0)
    
    def _generate_explanation(
        self,
        candidate: RecommendationCandidate,
        request: RecommendationRequest
    ) -> str:
        """Generate explanation for a recommendation."""
        strategy = candidate.strategy
        track = candidate.item
        metadata = candidate.metadata
        
        if strategy == "review_based":
            descriptors = metadata.get("unique_descriptors", [])[:2]
            desc_str = " and ".join(descriptors) if descriptors else "highly rated"
            return f"{track.artist_name} is {desc_str} in reviews, making it a great discovery for your {request.discovery_goal.value} preference."
        
        elif strategy == "mood_activity":
            mood = request.mood.value if request.mood else ""
            activity = request.activity.value if request.activity else ""
            context = f"{mood} {activity}" if mood and activity else mood or activity
            return f"Based on your {context} context, {track.artist_name}'s '{track.track_name}' matches the desired atmosphere perfectly."
        
        elif strategy == "similarity_search":
            ref_artist = metadata.get("reference_artist", "")
            return f"{track.artist_name} shares stylistic elements with your preference for {ref_artist}, offering a similar listening experience."
        
        elif strategy == "habit_breaking":
            novelty = metadata.get("novelty_score", 0)
            return f"To break repetitive patterns, {track.artist_name} offers fresh perspectives while maintaining appeal (novelty: {novelty:.1f})."
        
        elif strategy == "genre_exploration":
            genre = metadata.get("genre", "")
            return f"{track.artist_name} represents excellent {genre} music, expanding your exploration within this genre."
        
        else:
            return f"{track.artist_name}'s '{track.track_name}' is recommended based on your preferences and listening context."
    
    async def close(self) -> None:
        """Close all clients."""
        await self.lastfm.close()
        await self.review.close()


class MockRecommendationEngine:
    """Mock implementation for testing."""
    
    def __init__(self):
        self.lastfm = MockLastFMClient()
        self.review = MockReviewEngineClient()
        self.storage = MockRecommendationStorage()
        self.explainability = MockExplainabilityEngine()
    
    async def generate_recommendations(
        self,
        request: RecommendationRequest
    ) -> RecommendationResponse:
        """Generate mock recommendations."""
        start_time = time.time()
        
        # Get some mock tracks from Last.fm
        lastfm_tracks = await self.lastfm.search_tracks("", limit=request.limit)
        
        recommendations = []
        for i, track in enumerate(lastfm_tracks[:request.limit]):
            explanation = f"Mock recommendation {i+1} for {request.user_intent}"
            
            recommendation = Recommendation(
                track=track,
                confidence=0.8 - (i * 0.05),
                explanation=explanation,
                strategies_used=["mock"],
                metadata={"mock": True}
            )
            recommendations.append(recommendation)
        
        # Store recommendations
        await self._store_recommendations(request, recommendations)
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return RecommendationResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            recommendations=recommendations,
            total_count=len(recommendations),
            strategies_executed=["mock"],
            execution_time_ms=execution_time_ms
        )
    
    async def _store_recommendations(
        self,
        request: RecommendationRequest,
        recommendations: List[Recommendation]
    ) -> None:
        """Store recommendations with full metadata."""
        from .schemas import StoredRecommendation, Artist, Album
        
        for recommendation in recommendations:
            # Get full artist metadata
            artist = await self._get_artist_metadata(recommendation.track.artist_id)
            
            # Create stored recommendation
            stored_rec = StoredRecommendation(
                recommendation_id=self.storage._generate_recommendation_id(),
                user_id=request.user_id,
                session_id=request.session_id,
                track=recommendation.track,
                artist=artist,
                album=None,
                confidence=recommendation.confidence,
                explanation=recommendation.explanation,
                strategies_used=recommendation.strategies_used,
                generated_at=datetime.utcnow()
            )
            
            # Store
            self.storage.store_recommendation(stored_rec)
    
    async def _get_artist_metadata(self, artist_id: str) -> Artist:
        """Get artist metadata from available APIs."""
        # Try Last.fm
        artist = await self.lastfm.get_artist(artist_id)
        if artist:
            return artist
        
        # Fallback
        return Artist(
            artist_id=artist_id,
            source="fallback",
            artist_name="Unknown",
            genres=[],
            popularity=0,
            followers=0,
            external_url=None,
            image_url=None,
            similar_artists=[],
            biography=None,
            country=None,
            formation_year=None,
            albums=[],
            top_tracks=[]
        )
    
    async def _get_album_metadata(self, album_id: str) -> Optional[Album]:
        """Get album metadata from available APIs."""
        return None
    
    async def close(self) -> None:
        """Close clients."""
        await self.lastfm.close()
        await self.review.close()
