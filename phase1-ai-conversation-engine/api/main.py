import os
import yaml
import structlog
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from intent_recognition import IntentRecognizer, MockIntentRecognizer, IntentResult, IntentType
from context_manager import (
    ContextManager,
    MockContextManager,
    MoodType,
    ListeningGoalType,
    DiscoveryPreferenceType
)
from query_parser import QueryParser, MockQueryParser
from response_generator import ResponseGenerator, MockResponseGenerator
from combined_processor import CombinedIntentParser, MockCombinedIntentParser
from .schemas import (
    ChatRequest,
    ChatResponse,
    IntentRequest,
    IntentResponse,
    ParseRequest,
    ParseResponse,
    ContextRequest,
    ContextResponse,
    StructuredContextResponse,
    ConversationHistoryResponse,
    HealthResponse,
    RecommendationRequest,
    ArtistRecommendationRequest,
    UserMemoryResponse
)


# Configuration
class Settings(BaseSettings):
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
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
combined_processor: Optional[CombinedIntentParser] = None
context_manager: Optional[ContextManager] = None
response_generator: Optional[ResponseGenerator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global combined_processor, context_manager, response_generator
    
    logger.info("Starting Phase 1: AI Conversation Engine")
    
    try:
        # Initialize components
        if settings.use_mocks:
            logger.info("Using mock implementations")
            combined_processor = MockCombinedIntentParser()
            context_manager = MockContextManager(
                max_history_length=config["memory"]["max_history_length"]
            )
            response_generator = MockResponseGenerator()
        else:
            logger.info("Using production implementations")
            combined_processor = CombinedIntentParser(
                groq_api_key=settings.groq_api_key,
                primary_model=config["groq"]["primary_model"],
                fallback_model=config["groq"]["fallback_model"],
                timeout=config["groq"]["timeout"]
            )
            context_manager = ContextManager(
                storage_path=config["memory"]["storage_path"],
                max_history_length=config["memory"]["max_history_length"],
                max_context_exchanges=config["memory"]["max_context_exchanges"],
                auto_save=config["memory"]["auto_save"]
            )
            response_generator = ResponseGenerator(
                groq_api_key=settings.groq_api_key,
                primary_model=config["groq"]["primary_model"],
                secondary_model=config["groq"]["secondary_model"],
                temperature=config["groq"]["temperature"],
                max_tokens=config["groq"]["max_tokens"],
                timeout=config["groq"]["timeout"]
            )
        
        logger.info("Phase 1 initialized successfully")
        yield
        
    except Exception as e:
        logger.error("Failed to initialize Phase 1", error=str(e))
        raise
    finally:
        logger.info("Shutting down Phase 1")


# Create FastAPI app
app = FastAPI(
    title="AI Conversation Engine",
    description="Phase 1: AI Conversation Engine for Music Discovery Companion",
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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    dependencies = {}
    
    if not settings.use_mocks:
        dependencies["groq_api"] = "connected" if settings.groq_api_key else "not_configured"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        dependencies=dependencies
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that processes user queries and returns AI responses.
    
    This endpoint:
    1. Recognizes intent and parses query in a single combined call (optimized)
    2. Retrieves user context
    3. Generates a conversational response
    4. Updates conversation history
    """
    try:
        # Step 1: Combined intent recognition and query parsing (single API call)
        intent_result, parsed_query = await combined_processor.process(request.query)
        logger.info(
            "Combined processing complete",
            query=request.query,
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            mood=parsed_query.mood,
            goal=parsed_query.goal
        )
        
        # Step 2: Get user context
        user_context = await context_manager.get_context(
            request.user_id,
            request.session_id
        )
        
        # Update context based on parsed query
        if parsed_query.mood:
            await context_manager.set_mood(
                request.user_id,
                request.session_id,
                parsed_query.mood
            )
        
        if parsed_query.goal:
            await context_manager.set_goal(
                request.user_id,
                request.session_id,
                parsed_query.goal
            )
        
        for genre in parsed_query.genres:
            await context_manager.add_genre(
                request.user_id,
                request.session_id,
                genre
            )
        
        for artist in parsed_query.artists:
            await context_manager.add_artist(
                request.user_id,
                request.session_id,
                artist
            )
        
        # Step 3: Update structured context with extracted information
        await context_manager.update_structured_context(
            user_id=request.user_id,
            session_id=request.session_id,
            intent=intent_result.intent,
            mood=parsed_query.mood,
            activity=parsed_query.goal,
            genres=parsed_query.genres,
            artists=parsed_query.artists,
            discovery_goal=parsed_query.discovery_preference,
            confidence=max(intent_result.confidence, parsed_query.confidence)
        )
        
        # Step 4: Add user message to history
        await context_manager.add_message(
            request.user_id,
            request.session_id,
            role="user",
            content=request.query,
            metadata={"intent": intent_result.intent.value}
        )
        
        # Step 5: Generate response
        context_dict = {
            "current_mood": user_context.current_mood.value if user_context.current_mood else None,
            "current_goal": user_context.current_goal.value if user_context.current_goal else None,
            "recent_genres": user_context.recent_genres,
            "recent_artists": user_context.recent_artists,
            "discovery_preference": user_context.discovery_preference.value
        }
        
        generated_response = await response_generator.generate(
            query=request.query,
            intent=intent_result.intent.value,
            context=context_dict,
            recommendations=None  # Recommendations come from Phase 2
        )
        
        # Step 6: Add assistant message to history
        await context_manager.add_message(
            request.user_id,
            request.session_id,
            role="assistant",
            content=generated_response.content,
            metadata={"intent": intent_result.intent.value}
        )
        
        # Step 7: Generate structured JSON files
        await context_manager.generate_conversation_context_json(
            request.user_id,
            request.session_id
        )
        await context_manager.generate_conversation_history_json(
            request.user_id,
            request.session_id
        )
        
        # Step 8: Generate user memory JSON
        await context_manager.generate_user_memory_json(request.user_id)
        
        return ChatResponse(
            response=generated_response.content,
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            parsed_query=parsed_query.model_dump(),
            recommendations=[rec.model_dump() for rec in generated_response.recommendations]
        )
        
    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@app.post("/intent", response_model=IntentResponse)
async def recognize_intent(request: IntentRequest):
    """
    Intent recognition endpoint.
    Classifies the user's query into one of the supported intents.
    Uses combined processor for efficiency.
    """
    try:
        intent_result, _ = await combined_processor.process(request.query)
        
        return IntentResponse(
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            reasoning=intent_result.reasoning
        )
        
    except Exception as e:
        logger.error("Intent recognition failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recognize intent"
        )


@app.post("/parse", response_model=ParseResponse)
async def parse_query(request: ParseRequest):
    """
    Query parsing endpoint.
    Extracts structured parameters from natural language queries.
    Uses combined processor for efficiency.
    """
    try:
        _, parsed_query = await combined_processor.process(
            request.query,
            conversation_history=None
        )
        
        return ParseResponse(
            parsed_query=parsed_query.model_dump(),
            confidence=parsed_query.confidence
        )
        
    except Exception as e:
        logger.error("Query parsing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse query"
        )


@app.get("/context", response_model=ContextResponse)
async def get_context(request: ContextRequest):
    """
    Get user context endpoint.
    Returns the user's current context and conversation history.
    """
    try:
        history = await context_manager.get_history(
            request.user_id,
            request.session_id
        )
        
        return ContextResponse(
            context=history.context.model_dump(),
            messages=[msg.model_dump() for msg in history.messages]
        )
        
    except Exception as e:
        logger.error("Failed to get context", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve context"
        )


@app.delete("/context")
async def clear_context(request: ContextRequest):
    """
    Clear conversation history endpoint.
    Clears the conversation history for a user session.
    """
    try:
        await context_manager.clear_history(
            request.user_id,
            request.session_id
        )
        
        return {"status": "success", "message": "Context cleared"}
        
    except Exception as e:
        logger.error("Failed to clear context", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear context"
        )


@app.get("/sessions/{user_id}")
async def get_sessions(user_id: str):
    """
    Get all sessions for a user.
    Returns a list of session IDs for the user.
    """
    try:
        sessions = await context_manager.get_all_sessions(user_id)
        return {"user_id": user_id, "sessions": sessions}
        
    except Exception as e:
        logger.error("Failed to get sessions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@app.get("/structured-context", response_model=StructuredContextResponse)
async def get_structured_context(request: ContextRequest):
    """
    Get structured conversation context endpoint.
    Returns the structured conversation context with extracted information.
    """
    try:
        context_data = await context_manager.generate_conversation_context_json(
            request.user_id,
            request.session_id
        )
        
        return StructuredContextResponse(**context_data)
        
    except Exception as e:
        logger.error("Failed to get structured context", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve structured context"
        )


@app.get("/conversation-history", response_model=ConversationHistoryResponse)
async def get_conversation_history(request: ContextRequest):
    """
    Get full conversation history endpoint.
    Returns the complete conversation history with all messages and context.
    """
    try:
        history_data = await context_manager.generate_conversation_history_json(
            request.user_id,
            request.session_id
        )
        
        return ConversationHistoryResponse(**history_data)
        
    except Exception as e:
        logger.error("Failed to get conversation history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )


@app.post("/recommendations/song")
async def add_song_recommendation(request: RecommendationRequest):
    """
    Add a song recommendation to user memory.
    Tracks the song to avoid duplicate recommendations.
    """
    try:
        recommended_song = await context_manager.add_recommended_song(
            user_id=request.user_id,
            session_id=request.session_id,
            song_id=request.song_id,
            song_name=request.song_name,
            artist=request.artist,
            album=request.album,
            feedback=request.feedback
        )
        
        # Generate updated user memory JSON
        await context_manager.generate_user_memory_json(request.user_id)
        
        return {
            "status": "success",
            "message": "Song recommendation added",
            "song_id": recommended_song.song_id,
            "already_recommended": False
        }
        
    except Exception as e:
        logger.error("Failed to add song recommendation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add song recommendation"
        )


@app.post("/recommendations/artist")
async def add_artist_recommendation(request: ArtistRecommendationRequest):
    """
    Add an artist recommendation to user memory.
    Tracks the artist to avoid duplicate recommendations.
    """
    try:
        recommended_artist = await context_manager.add_recommended_artist(
            user_id=request.user_id,
            session_id=request.session_id,
            artist_id=request.artist_id,
            artist_name=request.artist_name,
            feedback=request.feedback
        )
        
        # Generate updated user memory JSON
        await context_manager.generate_user_memory_json(request.user_id)
        
        return {
            "status": "success",
            "message": "Artist recommendation added",
            "artist_id": recommended_artist.artist_id,
            "already_recommended": False
        }
        
    except Exception as e:
        logger.error("Failed to add artist recommendation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add artist recommendation"
        )


@app.get("/memory/{user_id}", response_model=UserMemoryResponse)
async def get_user_memory(user_id: str):
    """
    Get user memory endpoint.
    Returns the user's recommendation history and discovery history.
    """
    try:
        memory_data = await context_manager.generate_user_memory_json(user_id)
        
        return UserMemoryResponse(**memory_data)
        
    except Exception as e:
        logger.error("Failed to get user memory", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user memory"
        )


@app.get("/memory/{user_id}/songs")
async def get_recommended_songs(user_id: str):
    """
    Get list of previously recommended song IDs for a user.
    Used for duplicate avoidance in recommendation engines.
    """
    try:
        song_ids = await context_manager.get_recommended_song_ids(user_id)
        return {"user_id": user_id, "song_ids": song_ids}
        
    except Exception as e:
        logger.error("Failed to get recommended songs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recommended songs"
        )


@app.get("/memory/{user_id}/artists")
async def get_recommended_artists(user_id: str):
    """
    Get list of previously recommended artist IDs for a user.
    Used for duplicate avoidance in recommendation engines.
    """
    try:
        artist_ids = await context_manager.get_recommended_artist_ids(user_id)
        return {"user_id": user_id, "artist_ids": artist_ids}
        
    except Exception as e:
        logger.error("Failed to get recommended artists", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recommended artists"
        )


@app.get("/memory/{user_id}/check/song/{song_id}")
async def check_song_recommended(user_id: str, song_id: str):
    """
    Check if a song has been previously recommended to a user.
    """
    try:
        is_recommended = await context_manager.is_song_recommended(user_id, song_id)
        return {"user_id": user_id, "song_id": song_id, "is_recommended": is_recommended}
        
    except Exception as e:
        logger.error("Failed to check song recommendation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check song recommendation"
        )


@app.get("/memory/{user_id}/check/artist/{artist_id}")
async def check_artist_recommended(user_id: str, artist_id: str):
    """
    Check if an artist has been previously recommended to a user.
    """
    try:
        is_recommended = await context_manager.is_artist_recommended(user_id, artist_id)
        return {"user_id": user_id, "artist_id": artist_id, "is_recommended": is_recommended}
        
    except Exception as e:
        logger.error("Failed to check artist recommendation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check artist recommendation"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        workers=config["server"]["workers"],
        log_level=config["server"]["log_level"]
    )
