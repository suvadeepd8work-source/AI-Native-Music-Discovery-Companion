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
from lastfm_client import LastFMClient, MockLastFMClient
from review_client import ReviewEngineClient, MockReviewEngineClient
from storage import RecommendationStorage, MockRecommendationStorage
from explainability_engine import ExplainabilityEngine, MockExplainabilityEngine


# Configuration
class Settings(BaseSettings):
    lastfm_api_key: str = os.getenv("LASTFM_API_KEY", "")
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
            lastfm_client = MockLastFMClient()
            review_client = MockReviewEngineClient()
            storage = MockRecommendationStorage()
            explainability_engine = MockExplainabilityEngine()
            recommendation_engine = MockRecommendationEngine()
        else:
            logger.info("Using production implementations")
            lastfm_client = LastFMClient(
                api_key=settings.lastfm_api_key,
                timeout=config["lastfm"]["timeout"],
                max_retries=config["lastfm"]["max_retries"]
            )
            review_client = ReviewEngineClient(
                base_url=settings.review_engine_url,
                timeout=config["review_engine"]["timeout"],
                max_retries=config["review_engine"]["max_retries"]
            )
            
            storage = RecommendationStorage()
            explainability_engine = ExplainabilityEngine()
            recommendation_engine = RecommendationEngine(
                lastfm_client=lastfm_client,
                review_client=review_client,
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
        dependencies["lastfm_api"] = "configured" if settings.lastfm_api_key else "not_configured"
        dependencies["review_engine"] = settings.review_engine_url
    
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
