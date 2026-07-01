from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    query: str = Field(..., description="User's natural language query")
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Unique session identifier")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    response: str = Field(..., description="AI-generated response")
    intent: str = Field(..., description="Detected user intent")
    confidence: float = Field(..., description="Intent confidence score")
    parsed_query: Dict[str, Any] = Field(..., description="Parsed query parameters")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Music recommendations")


class IntentRequest(BaseModel):
    """Request schema for intent recognition endpoint."""
    query: str = Field(..., description="User's natural language query")


class IntentResponse(BaseModel):
    """Response schema for intent recognition endpoint."""
    intent: str = Field(..., description="Detected intent")
    confidence: float = Field(..., description="Confidence score")
    reasoning: str = Field(..., description="Reasoning for classification")


class ParseRequest(BaseModel):
    """Request schema for query parsing endpoint."""
    query: str = Field(..., description="User's natural language query")
    intent: Optional[str] = Field(None, description="Optional intent for context")


class ParseResponse(BaseModel):
    """Response schema for query parsing endpoint."""
    parsed_query: Dict[str, Any] = Field(..., description="Parsed query parameters")
    confidence: float = Field(..., description="Parsing confidence")


class ContextRequest(BaseModel):
    """Request schema for context management endpoints."""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Unique session identifier")


class ContextResponse(BaseModel):
    """Response schema for context management endpoints."""
    context: Dict[str, Any] = Field(..., description="User context")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation messages")


class StructuredContextResponse(BaseModel):
    """Response schema for structured conversation context."""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Unique session identifier")
    user_intent: Optional[str] = Field(None, description="Detected user intent")
    mood: Optional[str] = Field(None, description="Detected mood")
    activity: Optional[str] = Field(None, description="Detected activity/goal")
    preferred_genres: List[str] = Field(default_factory=list, description="Preferred genres")
    preferred_artists: List[str] = Field(default_factory=list, description="Preferred artists")
    discovery_goal: str = Field(..., description="Discovery preference goal")
    extracted_at: str = Field(..., description="Timestamp of extraction")
    confidence: float = Field(..., description="Confidence score")
    message_count: int = Field(..., description="Number of messages in session")
    session_created_at: str = Field(..., description="Session creation timestamp")
    session_updated_at: str = Field(..., description="Session last update timestamp")


class ConversationHistoryResponse(BaseModel):
    """Response schema for full conversation history."""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Unique session identifier")
    created_at: str = Field(..., description="Session creation timestamp")
    updated_at: str = Field(..., description="Session last update timestamp")
    message_count: int = Field(..., description="Number of messages")
    messages: List[Dict[str, Any]] = Field(..., description="All messages")
    context: Dict[str, Any] = Field(..., description="Full context including structured context")


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency status")


class RecommendationRequest(BaseModel):
    """Request schema for adding recommendations."""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Unique session identifier")
    song_id: str = Field(..., description="Unique song identifier")
    song_name: str = Field(..., description="Song name")
    artist: str = Field(..., description="Artist name")
    album: Optional[str] = Field(None, description="Album name")
    feedback: Optional[str] = Field(None, description="User feedback")


class ArtistRecommendationRequest(BaseModel):
    """Request schema for adding artist recommendations."""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Unique session identifier")
    artist_id: str = Field(..., description="Unique artist identifier")
    artist_name: str = Field(..., description="Artist name")
    feedback: Optional[str] = Field(None, description="User feedback")


class UserMemoryResponse(BaseModel):
    """Response schema for user memory."""
    user_id: str = Field(..., description="Unique user identifier")
    previously_recommended_songs: List[Dict[str, Any]] = Field(default_factory=list, description="Previously recommended songs")
    previously_recommended_artists: List[Dict[str, Any]] = Field(default_factory=list, description="Previously recommended artists")
    recently_discussed_genres: List[str] = Field(default_factory=list, description="Recently discussed genres")
    discovery_history: List[Dict[str, Any]] = Field(default_factory=list, description="Discovery history")
    summary: Dict[str, int] = Field(default_factory=dict, description="Summary statistics")
