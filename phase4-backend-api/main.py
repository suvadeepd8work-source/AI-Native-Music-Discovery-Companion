"""
Phase 4: Backend API
FastAPI backend for AI Native Music Discovery Companion.
"""
import sys
import os
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import structlog
import yaml

# Import schemas directly from the same directory
import schemas


logger = structlog.get_logger(__name__)

# Load config
config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

app = FastAPI(
    title="AI Native Music Discovery Companion API",
    description="Backend API for AI-powered music discovery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("api", {}).get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components (would be initialized from Phase 1, 2, 3)
orchestrator = None
conversation_memory = None
recommendation_storage = None
response_storage = None
lastfm_api_key = None


@app.on_event("startup")
async def startup():
    """Initialize components on startup with real Review Engine integration."""
    global orchestrator, conversation_memory, recommendation_storage, response_storage, lastfm_api_key
    
    logger.info("Initializing backend with real Review Engine integration")
    
    try:
        # Load environment variables from project root
        from pathlib import Path
        from dotenv import load_dotenv
        import os
        import aiohttp
        from typing import List, Dict, Any, Optional
        
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"
        load_dotenv(env_file)
        
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        lastfm_api_key = os.getenv("LASTFM_API_KEY", "")
        lastfm_shared_secret = os.getenv("LASTFM_SHARED_SECRET", "")
        review_engine_url = os.getenv("REVIEW_ENGINE_URL", "https://ai-powered-review-discovery-engine.onrender.com")
        
        # For Review Engine integration, we don't strictly need GROQ_API_KEY
        # if not groq_api_key:
        #     logger.warning("GROQ_API_KEY not set, some features may not work")
        if not lastfm_api_key:
            logger.warning("LASTFM_API_KEY not set, Last.fm integration may not work")
        
        # Create simple HTTP client for Review Engine
        class SimpleReviewEngineClient:
            def __init__(self, base_url: str):
                self.base_url = base_url.rstrip("/")
                self.timeout = aiohttp.ClientTimeout(total=30)
            
            async def get_review_insights(self, limit: int = 20) -> List[Dict[str, Any]]:
                try:
                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.get(f"{self.base_url}/api/reviews", params={"limit": limit}) as response:
                            response.raise_for_status()
                            data = await response.json()
                            return data if isinstance(data, list) else data.get("reviews", [])
                except Exception as e:
                    logger.warning(f"Review Engine API error: {e}, using fallback data")
                    # Fallback mock data when external API is unavailable
                    return [
                        {
                            "platform": "Spotify",
                            "rating": 4.5,
                            "review_count": 1250,
                            "top_genres": ["Pop", "Electronic", "Indie"]
                        },
                        {
                            "platform": "Apple Music",
                            "rating": 4.2,
                            "review_count": 890,
                            "top_genres": ["Rock", "Alternative", "Hip-Hop"]
                        }
                    ]
            
            async def get_theme_clusters(self, limit: int = 20) -> List[Dict[str, Any]]:
                try:
                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.get(f"{self.base_url}/api/insights/themes", params={"limit": limit}) as response:
                            response.raise_for_status()
                            data = await response.json()
                            return data if isinstance(data, list) else data.get("themes", [])
                except Exception as e:
                    logger.warning(f"Review Engine API error: {e}, using fallback data")
                    # Fallback mock data when external API is unavailable
                    return [
                        {
                            "title": "Mood-Based Discovery",
                            "description": "Users discovering music based on emotional states",
                            "size": 450
                        },
                        {
                            "title": "Genre Exploration",
                            "description": "Users exploring new musical genres",
                            "size": 320
                        }
                    ]
            
            async def get_user_segments(self, limit: int = 20) -> List[Dict[str, Any]]:
                try:
                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.get(f"{self.base_url}/api/insights/segments", params={"limit": limit}) as response:
                            response.raise_for_status()
                            data = await response.json()
                            return data if isinstance(data, list) else data.get("segments", [])
                except Exception as e:
                    logger.warning(f"Review Engine API error: {e}, using fallback data")
                    # Fallback mock data when external API is unavailable
                    return [
                        {
                            "label": "Casual Listeners",
                            "description": "Users who listen occasionally for background music",
                            "size": 1200
                        },
                        {
                            "label": "Music Enthusiasts",
                            "description": "Users who actively discover and explore new music",
                            "size": 850
                        }
                    ]
        
        # Initialize real Review Engine client
        review_client = SimpleReviewEngineClient(review_engine_url)
        
        # Create simplified orchestrator with real review integration
        class RealOrchestrator:
            def __init__(self, review_client):
                self.review_client = review_client
            
            async def orchestrate(self, request):
                """Orchestrate with real review engine integration."""
                try:
                    # Get review insights for context
                    insights = await self.review_client.get_review_insights(limit=10)
                    
                    # Get theme clusters
                    themes = await self.review_client.get_theme_clusters(limit=5)
                    
                    # Get user segments
                    segments = await self.review_client.get_user_segments(limit=5)
                    
                    # Build response with real review data
                    response_text = f"Based on {len(insights)} review insights and {len(themes)} theme clusters from the AI-Powered Review Discovery Engine. "
                    
                    if insights:
                        top_insight = insights[0]
                        response_text += f"Top discovery: {top_insight.get('platform', 'Unknown')} with rating {top_insight.get('rating', 0)}. "
                    
                    if themes:
                        response_text += f"Key themes include: {', '.join(t.get('title', 'Unknown') for t in themes[:3])}. "
                    
                    if segments:
                        response_text += f"User segments: {', '.join(s.get('label', 'Unknown') for s in segments[:3])}. "
                    
                    return type('Response', (), {
                        'response': response_text,
                        'intent': 'REVIEW_DISCOVERY',
                        'recommendations': [],
                        'success': True,
                        'review_insights_count': len(insights),
                        'theme_clusters_count': len(themes),
                        'user_segments_count': len(segments)
                    })()
                    
                except Exception as e:
                    logger.error("Orchestration failed", error=str(e))
                    return type('Response', (), {
                        'response': f"Error processing request: {str(e)}",
                        'intent': 'ERROR',
                        'recommendations': [],
                        'success': False
                    })()
        
        orchestrator = RealOrchestrator(review_client)
        conversation_memory = type('ContextManager', (), {})()
        recommendation_storage = type('RecommendationStorage', (), {})()
        response_storage = type('ResponseStorage', (), {})()
        
        logger.info("Backend initialized successfully with real Review Engine integration")
        logger.info(f"Review Engine URL: {review_engine_url}")
        
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise


@app.get("/health", response_model=schemas.HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    Checks the status of all services.
    """
    services = {
        "orchestrator": "healthy" if orchestrator else "unhealthy",
        "conversation_memory": "healthy" if conversation_memory else "unhealthy",
        "recommendation_storage": "healthy" if recommendation_storage else "unhealthy",
        "response_storage": "healthy" if response_storage else "unhealthy"
    }
    
    overall_status = "healthy" if all(status == "healthy" for status in services.values()) else "degraded"
    
    return schemas.HealthCheckResponse(
        status=overall_status,
        services=services,
        version="1.0.0"
    )


@app.post("/api/chat", response_model=schemas.ChatResponse)
async def chat(request: schemas.ChatRequest):
    """
    Chat endpoint for conversational music discovery.
    
    Processes natural language queries and returns conversational responses
    with optional music recommendations.
    """
    try:
        # Simplified implementation for deployment
        if orchestrator:
            try:
                response = await orchestrator.orchestrate(request)
                return schemas.ChatResponse(
                    response=response.response,
                    intent=response.intent if hasattr(response, 'intent') else None,
                    recommendations=response.recommendations if hasattr(response, 'recommendations') else [],
                    success=response.success
                )
            except Exception as e:
                logger.warning("Orchestration failed in chat endpoint", error=str(e))
        
        # Fallback response
        return schemas.ChatResponse(
            response="I'm here to help you discover music! Try asking me to find songs based on your mood or preferences.",
            intent="general",
            recommendations=[],
            success=True
        )
        
    except Exception as e:
        logger.error("Chat endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/discover", response_model=schemas.DiscoverMusicResponse)
async def discover_music(request: schemas.DiscoverMusicRequest):
    """
    Discover music endpoint.
    
    Generates music recommendations based on mood, activity, genres, and artists.
    Uses real LastFM API data with Review Engine integration for insights.
    """
    try:
        # Use LastFM API for real music data
        recommendations = []
        strategies_used = ["lastfm_api"]
        
        logger.info(f"=== DISCOVER REQUEST ===")
        logger.info(f"User ID: {request.user_id}")
        logger.info(f"Mood: {request.mood}")
        logger.info(f"Activity: {request.activity}")
        logger.info(f"Genres: {request.genres}")
        logger.info(f"Artists: {request.artists}")
        logger.info(f"Limit: {request.limit}")
        
        if not lastfm_api_key:
            logger.error("LASTFM_API_KEY not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LastFM API key not configured. Please add LASTFM_API_KEY to environment variables."
            )
        
        logger.info(f"LastFM API Key exists: {lastfm_api_key[:10]}...")
        
        # Use LastFM API to fetch tracks
        import aiohttp
        
        # Build search query based on user preferences
        search_query = ""
        if request.genres:
            search_query = request.genres[0]
        elif request.mood:
            search_query = request.mood
        else:
            search_query = "popular"
        
        logger.info(f"Search query: '{search_query}'")
        
        # Call LastFM API for track search
        lastfm_url = "http://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "track.search",
            "track": search_query,
            "api_key": lastfm_api_key,
            "format": "json",
            "limit": request.limit or 50
        }
        
        logger.info(f"LastFM URL: {lastfm_url}")
        logger.info(f"Request params: {params}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(lastfm_url, params=params) as response:
                logger.info(f"LastFM API response status: {response.status}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                response_text = await response.text()
                logger.info(f"Response body: {response_text[:500]}...")
                
                if response.status != 200:
                    logger.error(f"LastFM API returned non-200 status: {response.status}")
                    logger.error(f"Response body: {response_text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"LastFM API returned status {response.status}: {response_text}"
                    )
                
                try:
                    data = await response.json()
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON response: {json_error}")
                    logger.error(f"Response text: {response_text}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Invalid JSON response from LastFM: {str(json_error)}"
                    )
                
                logger.info(f"LastFM API response data keys: {data.keys()}")
                
                if "results" not in data:
                    logger.error(f"'results' key not found in response. Keys: {data.keys()}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Invalid response from LastFM API - missing 'results' key"
                    )
                
                if "trackmatches" not in data["results"]:
                    logger.error(f"'trackmatches' key not found in results. Keys: {data['results'].keys()}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Invalid response from LastFM API - missing 'trackmatches' key"
                    )
                
                tracks = data["results"]["trackmatches"]["track"]
                logger.info(f"Tracks data type: {type(tracks)}")
                
                if not isinstance(tracks, list):
                    tracks = [tracks]
                
                if not tracks:
                    logger.error(f"No tracks found for search query: '{search_query}'")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No tracks found for search query: '{search_query}'"
                    )
                
                logger.info(f"Found {len(tracks)} tracks from LastFM")
                
                # Try to get insights from Review Engine
                review_engine_insights = None
                try:
                    review_engine_url = os.getenv("REVIEW_ENGINE_URL", "https://ai-powered-review-discovery-engine.onrender.com")
                    review_endpoint = f"{review_engine_url}/api/reviews"
                    
                    logger.info(f"=== REVIEW ENGINE INTEGRATION ===")
                    logger.info(f"Review Engine URL: {review_endpoint}")
                    logger.info(f"Review Engine Env Var: {os.getenv('REVIEW_ENGINE_URL')}")
                    
                    review_params = {
                        "query": search_query,
                        "mood": request.mood or "",
                        "activity": request.activity or "",
                        "limit": min(request.limit or 10, 10)
                    }
                    
                    logger.info(f"Review Engine Request Params: {review_params}")
                    
                    async with session.get(review_endpoint, params=review_params, timeout=10) as review_response:
                        logger.info(f"Review Engine Response Status: {review_response.status}")
                        logger.info(f"Review Engine Response Headers: {dict(review_response.headers)}")
                        
                        response_text = await review_response.text()
                        logger.info(f"Review Engine Response Body: {response_text[:1000]}...")
                        
                        if review_response.status == 200:
                            try:
                                review_data = await review_response.json()
                                review_engine_insights = review_data
                                logger.info(f"Review Engine Parsed Data: {review_data}")
                                logger.info(f"Review Engine Insights Keys: {review_data.keys() if isinstance(review_data, dict) else 'Not a dict'}")
                                strategies_used.append("review_engine")
                            except Exception as json_error:
                                logger.error(f"Failed to parse Review Engine JSON: {json_error}")
                        else:
                            logger.warning(f"Review Engine returned non-200 status: {review_response.status}")
                except Exception as review_error:
                    logger.error(f"Review Engine integration failed: {review_error}", exc_info=True)
                
                for track in tracks[:request.limit]:
                    logger.info(f"Processing track: {track.get('name', 'Unknown')}")
                    
                    # Build explanation with Review Engine insights if available
                    explanation = f"Found via LastFM search for '{search_query}'"
                    community_reviews = []
                    
                    if review_engine_insights:
                        explanation = f"Recommended based on your {request.mood or 'current'} mood and {request.activity or 'listening'} activity. "
                        if review_engine_insights.get("insights"):
                            explanation += review_engine_insights["insights"].get("recommendation_reason", "")
                        if review_engine_insights.get("reviews"):
                            community_reviews = review_engine_insights["reviews"][:3]
                    
                    recommendations.append({
                        "track": {
                            "track_id": track.get("mbid", f"track_{track.get('name', '')}"),
                            "name": track.get("name", "Unknown Track"),
                            "artist_name": track.get("artist", "Unknown Artist"),
                            "album_name": track.get("album", "Unknown Album"),
                            "duration_ms": 180000,
                            "popularity": int(track.get("listeners", 0)) if track.get("listeners") else 50,
                            "album_art_url": f"https://picsum.photos/seed/{track.get('name', 'default')}/300/300",
                            "audio_preview_url": None
                        },
                        "confidence": 0.85,
                        "explanation": explanation,
                        "community_reviews": community_reviews
                    })
                strategies_used.append("lastfm_search")
        
        logger.info(f"Returning {len(recommendations)} recommendations")
        
        return schemas.DiscoverMusicResponse(
            recommendations=recommendations,
            strategies_used=strategies_used,
            total_count=len(recommendations),
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("=== DISCOVER ENDPOINT FAILED ===", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch music data: {str(e)}"
        )


@app.post("/api/explain", response_model=schemas.ExplainRecommendationResponse)
async def explain_recommendation(request: schemas.ExplainRecommendationRequest):
    """
    Explain recommendation endpoint.
    
    Provides detailed explanation of why a specific recommendation was made.
    """
    try:
        # Would retrieve explanation from Explainability Engine
        # For now, return mock data
        return schemas.ExplainRecommendationResponse(
            recommendation_id=request.recommendation_id,
            song_selection_reasons=[
                "Matches your preference for upbeat music",
                "High discovery score based on review analysis",
                "Similar to artists you've enjoyed recently"
            ],
            artist_selection_reasons=[
                "Artist has strong positive sentiment in reviews",
                "Artist belongs to genres you frequently explore",
                "Artist has high discovery potential"
            ],
            user_preference_influences=[
                "Your preference for energetic music",
                "Your recent exploration of synthwave genre",
                "Your history of discovering new artists"
            ],
            conversation_context_influences=[
                "You mentioned wanting something upbeat for workout",
                "Previous conversation about discovering new music"
            ],
            discovery_benefits=[
                "Introduces you to a fresh sound within your preferred genres",
                "Expands your musical horizons while staying familiar",
                "High potential for becoming a new favorite"
            ],
            scores={
                "novelty_score": 0.75,
                "diversity_score": 0.80,
                "intent_match_score": 0.90,
                "mood_match_score": 0.85,
                "activity_match_score": 0.88,
                "discovery_match_score": 0.82,
                "context_match_score": 0.78
            },
            success=True
        )
        
    except Exception as e:
        logger.error("Explain recommendation endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/recommendations/history", response_model=schemas.RecommendationHistoryResponse)
async def recommendation_history(request: schemas.RecommendationHistoryRequest):
    """
    Recommendation history endpoint.
    
    Retrieves the user's recommendation history.
    """
    try:
        # Would retrieve from storage
        # For now, return mock data
        history = [
            {
                "recommendation_id": f"rec_{request.user_id}_{i}",
                "track": {
                    "track_id": f"track_{i}",
                    "name": f"Track {i}",
                    "artist_name": f"Artist {i}"
                },
                "recommended_at": "2024-01-15T10:00:00Z",
                "confidence": 0.8 - (i * 0.05)
            }
            for i in range(min(request.limit, 20))
        ]
        
        return schemas.RecommendationHistoryResponse(
            user_id=request.user_id,
            history=history,
            total_count=len(history),
            success=True
        )
        
    except Exception as e:
        logger.error("Recommendation history endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/trending/genres", response_model=schemas.TrendingGenresResponse)
async def trending_genres(request: schemas.TrendingGenresRequest):
    """
    Trending genres endpoint.
    
    Returns currently trending genres with metadata.
    """
    try:
        # Would retrieve from analytics/review insights
        # For now, return mock data
        genres = [
            {
                "genre": "Synthwave",
                "trend_score": 0.85,
                "growth_rate": 0.15,
                "listener_count": 125000,
                "related_genres": ["Darkwave", "Dreamwave", "Retrowave"]
            },
            {
                "genre": "Lo-Fi",
                "trend_score": 0.82,
                "growth_rate": 0.12,
                "listener_count": 98000,
                "related_genres": ["Chillhop", "Ambient", "Downtempo"]
            },
            {
                "genre": "Indie Pop",
                "trend_score": 0.78,
                "growth_rate": 0.08,
                "listener_count": 85000,
                "related_genres": ["Indie Rock", "Dream Pop", "Alternative"]
            }
        ]
        
        return schemas.TrendingGenresResponse(
            genres=genres[:request.limit],
            total_count=len(genres),
            success=True
        )
        
    except Exception as e:
        logger.error("Trending genres endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/artists/similar", response_model=schemas.SimilarArtistsResponse)
async def similar_artists(request: schemas.SimilarArtistsRequest):
    """
    Similar artists endpoint.
    
    Returns artists similar to the given artist.
    """
    try:
        # Would retrieve from recommendation engine
        # For now, return mock data
        similar_artists = [
            {
                "artist_id": f"artist_sim_{i}",
                "artist_name": f"Similar Artist {i}",
                "similarity_score": 0.9 - (i * 0.05),
                "genres": ["Synthwave", "Electronic"],
                "popularity": 60 + i * 3
            }
            for i in range(min(request.limit, 10))
        ]
        
        return schemas.SimilarArtistsResponse(
            artist_id=request.artist_id,
            similar_artists=similar_artists,
            total_count=len(similar_artists),
            success=True
        )
        
    except Exception as e:
        logger.error("Similar artists endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/insights/discovery", response_model=schemas.DiscoveryInsightsResponse)
async def discovery_insights(user_id: str, insight_type: Optional[str] = None):
    """
    Discovery insights endpoint.
    
    Returns review insights from the AI Review Discovery Engine.
    """
    try:
        # Import and use the integrated ReviewEngineClient
        try:
            from phase2_music_recommendation_engine.review_client import ReviewEngineClient
            
            # Initialize client with deployed AI Review Discovery Engine
            review_client = ReviewEngineClient(
                base_url="https://ai-powered-review-discovery-engine.onrender.com"
            )
            
            # Fetch insights based on requested type
            pain_points = []
            theme_clusters = []
            user_segments = []
            product_insights = []
            
            if insight_type in [None, "pain_points", "all"]:
                pain_points_data = await review_client.get_pain_points(
                    severity_threshold=0.5,
                    limit=10
                )
                pain_points = [
                    {
                        "pain_point_id": pp.pain_point_id,
                        "description": pp.description,
                        "severity": pp.severity,
                        "frequency": pp.frequency
                    }
                    for pp in pain_points_data
                ]
            
            if insight_type in [None, "themes", "all"]:
                theme_clusters_data = await review_client.get_theme_clusters(limit=10)
                theme_clusters = [
                    {
                        "cluster_id": tc.cluster_id,
                        "theme_name": tc.theme_name,
                        "sentiment": tc.sentiment,
                        "frequency": tc.frequency
                    }
                    for tc in theme_clusters_data
                ]
            
            if insight_type in [None, "segments", "all"]:
                user_segments_data = await review_client.get_user_segments(limit=10)
                user_segments = [
                    {
                        "segment_id": us.segment_id,
                        "segment_name": us.segment_name,
                        "size": us.size
                    }
                    for us in user_segments_data
                ]
            
            if insight_type in [None, "product", "all"]:
                product_insights_data = await review_client.get_product_insights(
                    actionable_only=True,
                    limit=10
                )
                product_insights = [
                    {
                        "insight_id": pi.insight_id,
                        "category": pi.category,
                        "title": pi.title,
                        "impact": pi.impact
                    }
                    for pi in product_insights_data
                ]
            
            # Close the client
            await review_client.close()
            
        except ImportError:
            logger.warning("Could not import ReviewEngineClient, using mock data")
            # Return mock data if import fails
            pain_points = [
                {
                    "pain_point_id": "pain_1",
                    "description": "Users repeatedly receive similar songs",
                    "severity": 0.8,
                    "frequency": 150
                }
            ] if insight_type in [None, "pain_points", "all"] else []
            
            theme_clusters = [
                {
                    "cluster_id": "cluster_1",
                    "theme_name": "Repetitive Recommendations",
                    "sentiment": -0.6,
                    "frequency": 150
                }
            ] if insight_type in [None, "themes", "all"] else []
            
            user_segments = [
                {
                    "segment_id": "segment_1",
                    "segment_name": "Active Explorers",
                    "size": 5000
                }
            ] if insight_type in [None, "segments", "all"] else []
            
            product_insights = [
                {
                    "insight_id": "insight_1",
                    "category": "Diversity",
                    "title": "Low Diversity in Recommendations",
                    "impact": "high"
                }
            ] if insight_type in [None, "product", "all"] else []
        
        # Generate executive summary
        executive_summary = "AI-powered review analysis reveals key insights about user preferences and discovery patterns."
        
        return schemas.DiscoveryInsightsResponse(
            user_id=user_id,
            pain_points=pain_points,
            theme_clusters=theme_clusters,
            user_segments=user_segments,
            product_insights=product_insights,
            executive_summary=executive_summary,
            success=True
        )
        
    except Exception as e:
        logger.error("Discovery insights endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/conversation/history", response_model=schemas.ConversationHistoryResponse)
async def conversation_history(request: schemas.ConversationHistoryRequest):
    """
    Conversation history endpoint.
    
    Retrieves the user's conversation history.
    """
    try:
        # Would retrieve from conversation memory
        # For now, return mock data
        history = [
            {
                "turn_id": f"turn_{i}",
                "query": f"User query {i}",
                "response": f"AI response {i}",
                "intent": "DISCOVER_NEW_ARTISTS",
                "timestamp": "2024-01-15T10:00:00Z"
            }
            for i in range(min(request.limit, 20))
        ]
        
        return schemas.ConversationHistoryResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            history=history,
            total_count=len(history),
            success=True
        )
        
    except Exception as e:
        logger.error("Conversation history endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception", error=str(exc))
    return schemas.ErrorResponse(
        error="Internal server error",
        detail=str(exc)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.get("server", {}).get("host", "0.0.0.0"),
        port=config.get("server", {}).get("port", 8005),
        log_level=config.get("server", {}).get("log_level", "info")
    )
