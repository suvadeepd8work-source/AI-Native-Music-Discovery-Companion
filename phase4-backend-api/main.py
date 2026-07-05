"""
Phase 4: Backend API
FastAPI backend for AI Native Music Discovery Companion.
"""
import sys
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


@app.on_event("startup")
async def startup():
    """Initialize components on startup with real Phase 1, 2, 3 components."""
    global orchestrator, conversation_memory, recommendation_storage, response_storage
    
    use_mocks = config.get("use_mocks", False)
    
    if use_mocks:
        logger.info("Initializing components with mocks")
        
        # Simple mock orchestrator
        orchestrator = type('MockOrchestrator', (), {
            'orchestrate': lambda x: type('Response', (), {
                'response': 'Mock response',
                'intent': 'GENERAL_CHAT',
                'recommendations': [],
                'success': True
            })()
        })()
        
        # Simple mock context manager
        conversation_memory = type('MockContextManager', (), {})()
        
        # Simple mock storage
        recommendation_storage = type('MockRecommendationStorage', (), {})()
        response_storage = type('MockResponseStorage', (), {})()
        
        logger.info("Mock components initialized successfully")
    else:
        logger.info("Initializing real Phase 1, 2, 3 components")
        
        try:
            # Import Phase 3 Orchestrator
            from phase3_ai_orchestration.orchestrator import Orchestrator
            from phase3_ai_orchestration.orchestration_logger import OrchestrationLogger
            
            # Import Phase 1 components
            from phase1_ai_conversation_engine.intent_recognition.intent_recognizer import IntentRecognizer
            from phase1_ai_conversation_engine.query_parser.query_parser import QueryParser
            from phase1_ai_conversation_engine.combined_processor import CombinedIntentParser
            from phase1_ai_conversation_engine.response_generator.response_generator import ResponseGenerator
            from phase1_ai_conversation_engine.context_manager.context_manager import ContextManager
            
            # Import Phase 2 components
            from phase2_music_recommendation_engine.recommendation_engine import RecommendationEngine
            from phase2_music_recommendation_engine.lastfm_client import LastFMClient
            from phase2_music_recommendation_engine.review_client import ReviewEngineClient
            from phase2_music_recommendation_engine.storage import RecommendationStorage
            from phase2_music_recommendation_engine.explainability_engine import ExplainabilityEngine
            
            # Import Phase 1 storage
            from phase1_ai_conversation_engine.response_storage.response_storage import ResponseStorage
            
            # Get API keys from environment
            import os
            groq_api_key = os.getenv("GROQ_API_KEY", "")
            lastfm_api_key = os.getenv("LASTFM_API_KEY", "")
            lastfm_shared_secret = os.getenv("LASTFM_SHARED_SECRET", "")
            review_engine_url = os.getenv("REVIEW_ENGINE_URL", "https://ai-powered-review-discovery-engine.onrender.com")
            
            # Initialize Phase 1 components
            intent_recognizer = IntentRecognizer(groq_api_key=groq_api_key)
            query_parser = QueryParser(groq_api_key=groq_api_key)
            combined_parser = CombinedIntentParser(groq_api_key=groq_api_key)
            response_generator = ResponseGenerator(groq_api_key=groq_api_key)
            context_manager = ContextManager()
            
            # Initialize Phase 2 components
            lastfm_client = LastFMClient(api_key=lastfm_api_key, shared_secret=lastfm_shared_secret)
            review_client = ReviewEngineClient(base_url=review_engine_url)
            recommendation_storage = RecommendationStorage()
            explainability_engine = ExplainabilityEngine()
            recommendation_engine = RecommendationEngine(
                lastfm_client=lastfm_client,
                review_client=review_client,
                storage=recommendation_storage,
                explainability_engine=explainability_engine
            )
            
            # Initialize Phase 1 storage
            response_storage = ResponseStorage()
            
            # Initialize Phase 3 Orchestrator with combined parser
            conversation_engine = {
                "intent_recognizer": intent_recognizer,
                "query_parser": query_parser,
                "combined_parser": combined_parser
            }
            
            orchestrator = Orchestrator(
                conversation_engine=conversation_engine,
                conversation_memory=context_manager,
                review_client=review_client,
                recommendation_engine=recommendation_engine,
                explainability_engine=explainability_engine,
                response_generator=response_generator,
                orchestration_logger=OrchestrationLogger(config.get("orchestration_logger", {})),
                config=config
            )
            
            conversation_memory = context_manager
            
            logger.info("Real components initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Failed to import real components, falling back to mocks: {e}")
            
            # Fallback to mocks
            orchestrator = type('MockOrchestrator', (), {
                'orchestrate': lambda x: type('Response', (), {
                    'response': 'Mock response (import failed)',
                    'intent': 'GENERAL_CHAT',
                    'recommendations': [],
                    'success': True
                })()
            })()
            
            conversation_memory = type('MockContextManager', (), {})()
            recommendation_storage = type('MockRecommendationStorage', (), {})()
            response_storage = type('MockResponseStorage', (), {})()
            
            logger.info("Fallback mock components initialized")


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
        from phase3_ai_orchestration.orchestrator_schemas import OrchestrationRequest
        
        orchestration_request = OrchestrationRequest(
            user_id=request.user_id,
            session_id=request.session_id,
            query=request.query,
            conversation_history=request.conversation_history,
            enable_recommendations=request.enable_recommendations,
            enable_explanations=request.enable_explanations,
            enable_review_insights=request.enable_review_insights,
            max_recommendations=request.max_recommendations
        )
        
        response = await orchestrator.orchestrate(orchestration_request)
        
        return schemas.ChatResponse(
            response=response.response,
            intent=response.intent,
            recommendations=response.recommendations,
            success=response.success
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
    """
    try:
        from phase2_music_recommendation_engine.schemas import RecommendationRequest, DiscoveryPreferenceType
        
        # Build recommendation request
        rec_request = RecommendationRequest(
            user_id=request.user_id,
            session_id=request.session_id,
            user_intent="discovery",
            mood=request.mood,
            activity=request.activity,
            discovery_goal=request.discovery_preference,
            preferred_genres=request.genres or [],
            preferred_artists=request.artists or [],
            limit=request.limit,
            review_insights_enabled=True
        )
        
        # Generate recommendations (would use real recommendation engine)
        # For now, return mock data
        recommendations = [
            {
                "track": {
                    "track_id": f"track_{i}",
                    "name": f"Track {i}",
                    "artist_name": f"Artist {i}",
                    "album_name": f"Album {i}",
                    "duration_ms": 180000,
                    "popularity": 50 + i * 5
                },
                "confidence": 0.8 - (i * 0.05),
                "explanation": f"Based on your preferences for {request.genres or 'various genres'}"
            }
            for i in range(min(request.limit, 10))
        ]
        
        return schemas.DiscoverMusicResponse(
            recommendations=recommendations,
            strategies_used=["review_based", "mood_activity", "similarity_search"],
            total_count=len(recommendations),
            success=True
        )
        
    except Exception as e:
        logger.error("Discover music endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
