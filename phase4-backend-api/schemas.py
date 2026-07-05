"""
API Schemas for Phase 4: Backend API.
Request and response models for all endpoints.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


# Chat API
@dataclass
class ChatRequest:
    """Request for chat endpoint."""
    user_id: str
    session_id: str
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    enable_recommendations: bool = True
    enable_explanations: bool = True
    enable_review_insights: bool = True
    max_recommendations: int = 10

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.max_recommendations < 1:
            self.max_recommendations = 1
        elif self.max_recommendations > 20:
            self.max_recommendations = 20


@dataclass
class ChatResponse:
    """Response from chat endpoint."""
    response: str
    intent: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    success: bool = True


# Discover Music API
@dataclass
class DiscoverMusicRequest:
    """Request for discover music endpoint."""
    user_id: str
    session_id: str
    mood: Optional[str] = None
    activity: Optional[str] = None
    genres: Optional[List[str]] = None
    artists: Optional[List[str]] = None
    discovery_preference: str = "balanced"
    limit: int = 10

    def __post_init__(self):
        if self.genres is None:
            self.genres = []
        if self.artists is None:
            self.artists = []
        if self.limit < 1:
            self.limit = 1
        elif self.limit > 20:
            self.limit = 20


@dataclass
class DiscoverMusicResponse:
    """Response from discover music endpoint."""
    recommendations: List[Dict[str, Any]]
    strategies_used: List[str]
    total_count: int
    success: bool = True


# Explain Recommendation API
@dataclass
class ExplainRecommendationRequest:
    """Request for explain recommendation endpoint."""
    user_id: str
    recommendation_id: str


@dataclass
class ExplainRecommendationResponse:
    """Response from explain recommendation endpoint."""
    recommendation_id: str
    song_selection_reasons: List[str]
    artist_selection_reasons: List[str]
    user_preference_influences: List[str]
    conversation_context_influences: List[str]
    discovery_benefits: List[str]
    scores: Dict[str, float]
    success: bool = True


# Recommendation History API
@dataclass
class RecommendationHistoryRequest:
    """Request for recommendation history endpoint."""
    user_id: str
    limit: int = 50

    def __post_init__(self):
        if self.limit < 1:
            self.limit = 1
        elif self.limit > 100:
            self.limit = 100


@dataclass
class RecommendationHistoryResponse:
    """Response from recommendation history endpoint."""
    user_id: str
    history: List[Dict[str, Any]]
    total_count: int
    success: bool = True


# Trending Genres API
@dataclass
class TrendingGenresRequest:
    """Request for trending genres endpoint."""
    limit: int = 20

    def __post_init__(self):
        if self.limit < 1:
            self.limit = 1
        elif self.limit > 50:
            self.limit = 50


@dataclass
class TrendingGenresResponse:
    """Response from trending genres endpoint."""
    genres: List[Dict[str, Any]]
    total_count: int
    success: bool = True


# Similar Artists API
@dataclass
class SimilarArtistsRequest:
    """Request for similar artists endpoint."""
    artist_id: str
    limit: int = 10

    def __post_init__(self):
        if self.limit < 1:
            self.limit = 1
        elif self.limit > 20:
            self.limit = 20


@dataclass
class SimilarArtistsResponse:
    """Response from similar artists endpoint."""
    artist_id: str
    similar_artists: List[Dict[str, Any]]
    total_count: int
    success: bool = True


# Discovery Insights API
@dataclass
class DiscoveryInsightsRequest:
    """Request for discovery insights endpoint."""
    user_id: str
    insight_type: Optional[str] = None


@dataclass
class DiscoveryInsightsResponse:
    """Response from discovery insights endpoint."""
    user_id: str
    pain_points: List[Dict[str, Any]] = field(default_factory=list)
    theme_clusters: List[Dict[str, Any]] = field(default_factory=list)
    user_segments: List[Dict[str, Any]] = field(default_factory=list)
    product_insights: List[Dict[str, Any]] = field(default_factory=list)
    executive_summary: Optional[str] = None
    success: bool = True


# Conversation History API
@dataclass
class ConversationHistoryRequest:
    """Request for conversation history endpoint."""
    user_id: str
    session_id: Optional[str] = None
    limit: int = 50

    def __post_init__(self):
        if self.limit < 1:
            self.limit = 1
        elif self.limit > 100:
            self.limit = 100


@dataclass
class ConversationHistoryResponse:
    """Response from conversation history endpoint."""
    user_id: str
    history: List[Dict[str, Any]]
    total_count: int
    session_id: Optional[str] = None
    success: bool = True


# Health Check API
@dataclass
class HealthCheckResponse:
    """Response from health check endpoint."""
    status: str
    services: Dict[str, str]
    version: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


# Error Response
@dataclass
class ErrorResponse:
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
