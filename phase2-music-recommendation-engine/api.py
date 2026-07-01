"""
FastAPI server for Phase 2: Music Recommendation Engine.
Exposes recommendation endpoints for Phase 1 to consume.
"""
import os
import yaml
import structlog
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from schemas import RecommendationRequest, RecommendationResponse
from recommendation_engine import RecommendationEngine, MockRecommendationEngine
from spotify_client import SpotifyClient, MockSpotifyClient
from review_client import ReviewEngineClient, MockReviewEngineClient
from deezer_client import DeezerClient, MockDeezerClient
from lastfm_client import LastFMClient, MockLastFMClient
from jamendo_client import JamendoClient, MockJamendoClient
from storage import RecommendationStorage, MockRecommendationStorage
from explainability_engine import ExplainabilityEngine, MockExplainabilityEngine


# Configuration
class Settings(BaseSettings):
    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    lastfm_api_key: str = os.getenv("LASTFM_API_KEY", "")
    jamendo_client_id: str = os.getenv("JAMENDO_CLIENT_ID", "")
    review_engine_url: str = os.getenv("REVIEW_ENGINE_URL", "http://localhost:8003")
    use_mocks: bool = os.getenv("USE_MOCKS", "false").lower() == "true"
    config_file: str = "config.yaml"


settings = Settings()

# Load configuration
with open(settings.config_file, 'r') as f:
    config = yaml.safe_load(f)

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


# Initialize components
recommendation_engine: Optional[RecommendationEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global recommendation_engine
    
    logger.info("Starting Phase 2: Music Recommendation Engine")
    
    try:
        # Initialize components
        if settings.use_mocks:
            logger.info("Using mock implementations")
            spotify_client = MockSpotifyClient()
            review_client = MockReviewEngineClient()
            deezer_client = MockDeezerClient()
            lastfm_client = MockLastFMClient()
            jamendo_client = MockJamendoClient()
            storage = MockRecommendationStorage()
            explainability_engine = MockExplainabilityEngine()
            recommendation_engine = MockRecommendationEngine()
        else:
            logger.info("Using production implementations")
            spotify_client = SpotifyClient(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret,
                timeout=config["spotify"]["timeout"],
                max_retries=config["spotify"]["max_retries"],
                rate_limit_delay=config["spotify"]["rate_limit_delay"]
            )
            review_client = ReviewEngineClient(
                base_url=settings.review_engine_url,
                timeout=config["review_engine"]["timeout"],
                max_retries=config["review_engine"]["max_retries"]
            )
            
            # Initialize optional API clients
            deezer_client = None
            if config.get("deezer", {}).get("enabled", False):
                deezer_client = DeezerClient(
                    timeout=config["deezer"]["timeout"],
                    max_retries=config["deezer"]["max_retries"]
                )
            
            lastfm_client = None
            if config.get("lastfm", {}).get("enabled", False) and settings.lastfm_api_key:
                lastfm_client = LastFMClient(
                    api_key=settings.lastfm_api_key,
                    timeout=config["lastfm"]["timeout"],
                    max_retries=config["lastfm"]["max_retries"]
                )
            
            jamendo_client = None
            if config.get("jamendo", {}).get("enabled", False) and settings.jamendo_client_id:
                jamendo_client = JamendoClient(
                    client_id=settings.jamendo_client_id,
                    timeout=config["jamendo"]["timeout"],
                    max_retries=config["jamendo"]["max_retries"]
                )
            
            storage = RecommendationStorage()
            explainability_engine = ExplainabilityEngine()
            recommendation_engine = RecommendationEngine(
                spotify_client=spotify_client,
                review_client=review_client,
                deezer_client=deezer_client,
                lastfm_client=lastfm_client,
                jamendo_client=jamendo_client,
                storage=storage,
                explainability_engine=explainability_engine,
                config=config
            )
        
        logger.info("Phase 2 initialized successfully")
        yield
        
    except Exception as e:
        logger.error("Failed to initialize Phase 2", error=str(e))
        raise
    finally:
        logger.info("Shutting down Phase 2")
        if recommendation_engine:
            await recommendation_engine.close()


# Create FastAPI app
app = FastAPI(
    title="Music Recommendation Engine",
    description="Phase 2: Music Recommendation Engine for Music Discovery Companion",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["api"]["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    dependencies = {}
    
    if not settings.use_mocks:
        dependencies["spotify_api"] = "configured" if settings.spotify_client_id else "not_configured"
        dependencies["review_engine"] = settings.review_engine_url
        dependencies["deezer_api"] = "enabled" if config.get("deezer", {}).get("enabled", False) else "disabled"
        dependencies["lastfm_api"] = "enabled" if config.get("lastfm", {}).get("enabled", False) and settings.lastfm_api_key else "disabled"
        dependencies["jamendo_api"] = "enabled" if config.get("jamendo", {}).get("enabled", False) and settings.jamendo_client_id else "disabled"
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "mode": "mock" if settings.use_mocks else "production",
        "dependencies": dependencies
    }


@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Main recommendation endpoint.
    
    Receives conversation context and user memory from Phase 1,
    generates music recommendations using multiple strategies.
    
    Args:
        request: Recommendation request with context from Phase 1
        
    Returns:
        RecommendationResponse with ranked recommendations and explanations
    """
    try:
        logger.info(
            "Generating recommendations",
            user_id=request.user_id,
            session_id=request.session_id,
            intent=request.user_intent,
            mood=request.mood.value if request.mood else None,
            activity=request.activity.value if request.activity else None,
            discovery_goal=request.discovery_goal.value
        )
        
        response = await recommendation_engine.generate_recommendations(request)
        
        logger.info(
            "Recommendations generated",
            user_id=request.user_id,
            session_id=request.session_id,
            total_count=response.total_count,
            execution_time_ms=response.execution_time_ms,
            strategies_executed=response.strategies_executed
        )
        
        return response
        
    except Exception as e:
        logger.error("Failed to generate recommendations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        workers=config["server"]["workers"],
        log_level=config["server"]["log_level"]
    )
