"""
Phase 3: AI Orchestration API
FastAPI endpoint for the orchestration layer.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import structlog
import yaml
from pathlib import Path

from .orchestrator import Orchestrator, MockOrchestrator
from .orchestrator_schemas import OrchestrationRequest, OrchestrationResponse


logger = structlog.get_logger(__name__)

# Load config
config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

app = FastAPI(
    title="Phase 3: AI Orchestration API",
    description="Orchestration layer for AI music discovery pipeline",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("api", {}).get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator: Optional[Orchestrator] = None


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    user_id: str
    session_id: str
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = []
    enable_recommendations: bool = True
    enable_explanations: bool = True
    enable_review_insights: bool = True
    max_recommendations: int = 10


@app.on_event("startup")
async def startup():
    """Initialize orchestrator on startup."""
    global orchestrator
    
    use_mocks = config.get("use_mocks", False)
    
    if use_mocks:
        logger.info("Using mock orchestrator")
        orchestrator = MockOrchestrator()
    else:
        logger.info("Initializing production orchestrator")
        # Initialize all components
        # This would typically involve importing from Phase 1 and Phase 2
        # For now, we'll use a placeholder
        orchestrator = MockOrchestrator()
        logger.warning("Production orchestrator not fully implemented, using mock")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "orchestrator_initialized": orchestrator is not None
    }


@app.post("/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(request: ChatRequest):
    """
    Execute the complete orchestration pipeline.
    
    Pipeline:
    1. Conversation Engine (Intent Recognition, Query Parsing)
    2. Conversation Memory (Retrieve context)
    3. Review Insight Retrieval (Fetch insights from Phase 2)
    4. Music Recommendation Engine (Generate recommendations)
    5. Explainability Engine (Generate explanations)
    6. Response Generator (Final conversational response)
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
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
        
        return response
        
    except Exception as e:
        logger.error("Orchestration failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Simplified chat endpoint that returns just the conversational response.
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
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
        
        return {
            "response": response.response,
            "intent": response.intent,
            "recommendations": response.recommendations,
            "success": response.success
        }
        
    except Exception as e:
        logger.error("Chat failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.get("server", {}).get("host", "0.0.0.0"),
        port=config.get("server", {}).get("port", 8004),
        log_level=config.get("server", {}).get("log_level", "info")
    )
