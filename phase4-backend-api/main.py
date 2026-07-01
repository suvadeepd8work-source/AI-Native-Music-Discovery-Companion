"""
Phase 4: Backend API
FastAPI backend for AI Native Music Discovery Companion.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import structlog
import yaml
from pathlib import Path

from .schemas import (
    ChatRequest, ChatResponse,
    DiscoverMusicRequest, DiscoverMusicResponse,
    ExplainRecommendationRequest, ExplainRecommendationResponse,
    RecommendationHistoryRequest, RecommendationHistoryResponse,
    TrendingGenresRequest, TrendingGenresResponse,
    SimilarArtistsRequest, SimilarArtistsResponse,
    DiscoveryInsightsRequest, DiscoveryInsightsResponse,
    ConversationHistoryRequest, ConversationHistoryResponse,
    HealthCheckResponse, ErrorResponse
)


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
    """Initialize components on startup."""
    global orchestrator, conversation_memory, recommendation_storage, response_storage
    
    use_mocks = config.get("use_mocks", True)
    
    if use_mocks:
        logger.info("Using mock implementations")
        # Import mock implementations
        from phase3_ai_orchestration import MockOrchestrator
        from phase1_ai_conversation_engine.context_manager import MockContextManager
        from phase2_music_recommendation_engine.storage import MockRecommendationStorage
        from phase1_ai_conversation_engine.response_generator.response_storage import MockResponseStorage
        
        orchestrator = MockOrchestrator()
        conversation_memory = MockContextManager()
        recommendation_storage = MockRecommendationStorage()
        response_storage = MockResponseStorage()
    else:
        logger.info("Initializing production components")
        # Would initialize real components from Phase 1, 2, 3
        # For now, use mocks
        from phase3_ai_orchestration import MockOrchestrator
        from phase1_ai_conversation_engine.context_manager import MockContextManager
        from phase2_music_recommendation_engine.storage import MockRecommendationStorage
        from phase1_ai_conversation_engine.response_generator.response_storage import MockResponseStorage
        
        orchestrator = MockOrchestrator()
        conversation_memory = MockContextManager()
        recommendation_storage = MockRecommendationStorage()
        response_storage = MockResponseStorage()
        logger.warning("Production components not fully implemented, using mocks")


@app.get("/health", response_model=HealthCheckResponse)
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
    
    return HealthCheckResponse(
        status=overall_status,
        services=services,
        version="1.0.0"
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
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
        
        return ChatResponse(
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


@app.post("/api/discover", response_model=DiscoverMusicResponse)
async def discover_music(request: DiscoverMusicRequest):
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
        
        return DiscoverMusicResponse(
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


@app.post("/api/explain", response_model=ExplainRecommendationResponse)
async def explain_recommendation(request: ExplainRecommendationRequest):
    """
    Explain recommendation endpoint.
    
    Provides detailed explanation of why a specific recommendation was made.
    """
    try:
        # Would retrieve explanation from Explainability Engine
        # For now, return mock data
        return ExplainRecommendationResponse(
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


@app.get("/api/recommendations/history", response_model=RecommendationHistoryResponse)
async def recommendation_history(request: RecommendationHistoryRequest):
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
        
        return RecommendationHistoryResponse(
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


@app.get("/api/trending/genres", response_model=TrendingGenresResponse)
async def trending_genres(request: TrendingGenresRequest):
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
        
        return TrendingGenresResponse(
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


@app.get("/api/artists/similar", response_model=SimilarArtistsResponse)
async def similar_artists(request: SimilarArtistsRequest):
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
        
        return SimilarArtistsResponse(
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


@app.get("/api/insights/discovery", response_model=DiscoveryInsightsResponse)
async def discovery_insights(request: DiscoveryInsightsRequest):
    """
    Discovery insights endpoint.
    
    Returns review insights from the Review Discovery Engine.
    """
    try:
        # Would retrieve from Review Client
        # For now, return mock data
        pain_points = [
            {
                "pain_point_id": "pain_1",
                "description": "Users repeatedly receive similar songs",
                "severity": 0.8,
                "frequency": 150
            }
        ]
        
        theme_clusters = [
            {
                "cluster_id": "cluster_1",
                "theme_name": "Repetitive Recommendations",
                "sentiment": -0.6,
                "frequency": 150
            }
        ]
        
        user_segments = [
            {
                "segment_id": "segment_1",
                "segment_name": "Active Explorers",
                "size": 5000
            }
        ]
        
        product_insights = [
            {
                "insight_id": "insight_1",
                "category": "Diversity",
                "title": "Low Diversity in Recommendations",
                "impact": "high"
            }
        ]
        
        # Filter by insight type if specified
        if request.insight_type == "pain_points":
            return DiscoveryInsightsResponse(
                user_id=request.user_id,
                pain_points=pain_points,
                theme_clusters=[],
                user_segments=[],
                product_insights=[],
                success=True
            )
        elif request.insight_type == "themes":
            return DiscoveryInsightsResponse(
                user_id=request.user_id,
                pain_points=[],
                theme_clusters=theme_clusters,
                user_segments=[],
                product_insights=[],
                success=True
            )
        elif request.insight_type == "segments":
            return DiscoveryInsightsResponse(
                user_id=request.user_id,
                pain_points=[],
                theme_clusters=[],
                user_segments=user_segments,
                product_insights=[],
                success=True
            )
        
        return DiscoveryInsightsResponse(
            user_id=request.user_id,
            pain_points=pain_points,
            theme_clusters=theme_clusters,
            user_segments=user_segments,
            product_insights=product_insights,
            executive_summary="User feedback indicates need for improved diversity and better mood matching.",
            success=True
        )
        
    except Exception as e:
        logger.error("Discovery insights endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/conversation/history", response_model=ConversationHistoryResponse)
async def conversation_history(request: ConversationHistoryRequest):
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
        
        return ConversationHistoryResponse(
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
    return ErrorResponse(
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
