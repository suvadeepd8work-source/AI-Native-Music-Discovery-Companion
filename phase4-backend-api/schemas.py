"""
API Schemas for Phase 4: Backend API.
Request and response models for all endpoints.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# Chat API
class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="User's natural language query")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Conversation history")
    enable_recommendations: bool = Field(default=True, description="Whether to generate recommendations")
    enable_explanations: bool = Field(default=True, description="Whether to generate explanations")
    enable_review_insights: bool = Field(default=True, description="Whether to use review insights")
    max_recommendations: int = Field(default=10, ge=1, le=20, description="Maximum recommendations")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str = Field(..., description="Conversational response")
    intent: Optional[str] = Field(None, description="Detected intent")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="Music recommendations")
    success: bool = Field(..., description="Whether the request succeeded")


# Discover Music API
class DiscoverMusicRequest(BaseModel):
    """Request for discover music endpoint."""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    mood: Optional[str] = Field(None, description="Requested mood")
    activity: Optional[str] = Field(None, description="Requested activity")
    genres: Optional[List[str]] = Field(default_factory=list, description="Preferred genres")
    artists: Optional[List[str]] = Field(default_factory=list, description="Preferred artists")
    discovery_preference: str = Field(default="balanced", description="Discovery preference (novel, familiar, balanced)")
    limit: int = Field(default=10, ge=1, le=20, description="Number of recommendations")


class DiscoverMusicResponse(BaseModel):
    """Response from discover music endpoint."""
    recommendations: List[Dict[str, Any]] = Field(..., description="Music recommendations")
    strategies_used: List[str] = Field(..., description="Strategies that contributed")
    total_count: int = Field(..., description="Total number of recommendations")
    success: bool = Field(..., description="Whether the request succeeded")


# Explain Recommendation API
class ExplainRecommendationRequest(BaseModel):
    """Request for explain recommendation endpoint."""
    user_id: str = Field(..., description="User identifier")
    recommendation_id: str = Field(..., description="Recommendation identifier")


class ExplainRecommendationResponse(BaseModel):
    """Response from explain recommendation endpoint."""
    recommendation_id: str = Field(..., description="Recommendation identifier")
    song_selection_reasons: List[str] = Field(..., description="Why the song was selected")
    artist_selection_reasons: List[str] = Field(..., description="Why the artist was selected")
    user_preference_influences: List[str] = Field(..., description="Which user preferences influenced it")
    conversation_context_influences: List[str] = Field(..., description="Which conversation context influenced it")
    discovery_benefits: List[str] = Field(..., description="How it helps users discover new music")
    scores: Dict[str, float] = Field(..., description="Scoring factors")
    success: bool = Field(..., description="Whether the request succeeded")


# Recommendation History API
class RecommendationHistoryRequest(BaseModel):
    """Request for recommendation history endpoint."""
    user_id: str = Field(..., description="User identifier")
    limit: int = Field(default=50, ge=1, le=100, description="Number of history items")


class RecommendationHistoryResponse(BaseModel):
    """Response from recommendation history endpoint."""
    user_id: str = Field(..., description="User identifier")
    history: List[Dict[str, Any]] = Field(..., description="Recommendation history")
    total_count: int = Field(..., description="Total number of items")
    success: bool = Field(..., description="Whether the request succeeded")


# Trending Genres API
class TrendingGenresRequest(BaseModel):
    """Request for trending genres endpoint."""
    limit: int = Field(default=20, ge=1, le=50, description="Number of genres")


class TrendingGenresResponse(BaseModel):
    """Response from trending genres endpoint."""
    genres: List[Dict[str, Any]] = Field(..., description="Trending genres with metadata")
    total_count: int = Field(..., description="Total number of genres")
    success: bool = Field(..., description="Whether the request succeeded")


# Similar Artists API
class SimilarArtistsRequest(BaseModel):
    """Request for similar artists endpoint."""
    artist_id: str = Field(..., description="Artist identifier")
    limit: int = Field(default=10, ge=1, le=20, description="Number of similar artists")


class SimilarArtistsResponse(BaseModel):
    """Response from similar artists endpoint."""
    artist_id: str = Field(..., description="Original artist identifier")
    similar_artists: List[Dict[str, Any]] = Field(..., description="Similar artists")
    total_count: int = Field(..., description="Total number of similar artists")
    success: bool = Field(..., description="Whether the request succeeded")


# Discovery Insights API
class DiscoveryInsightsRequest(BaseModel):
    """Request for discovery insights endpoint."""
    user_id: str = Field(..., description="User identifier")
    insight_type: Optional[str] = Field(None, description="Type of insights (all, pain_points, themes, segments)")


class DiscoveryInsightsResponse(BaseModel):
    """Response from discovery insights endpoint."""
    user_id: str = Field(..., description="User identifier")
    pain_points: List[Dict[str, Any]] = Field(default_factory=list, description="Identified pain points")
    theme_clusters: List[Dict[str, Any]] = Field(default_factory=list, description="Theme clusters")
    user_segments: List[Dict[str, Any]] = Field(default_factory=list, description="User segments")
    product_insights: List[Dict[str, Any]] = Field(default_factory=list, description="Product insights")
    executive_summary: Optional[str] = Field(None, description="Executive summary")
    success: bool = Field(..., description="Whether the request succeeded")


# Conversation History API
class ConversationHistoryRequest(BaseModel):
    """Request for conversation history endpoint."""
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier (optional)")
    limit: int = Field(default=50, ge=1, le=100, description="Number of history items")


class ConversationHistoryResponse(BaseModel):
    """Response from conversation history endpoint."""
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    history: List[Dict[str, Any]] = Field(..., description="Conversation history")
    total_count: int = Field(..., description="Total number of items")
    success: bool = Field(..., description="Whether the request succeeded")


# Health Check API
class HealthCheckResponse(BaseModel):
    """Response from health check endpoint."""
    status: str = Field(..., description="Overall health status")
    services: Dict[str, str] = Field(..., description="Individual service statuses")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


# Error Response
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
