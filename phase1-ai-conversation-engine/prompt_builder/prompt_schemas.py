"""
Schemas for AI Prompt Builder.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PromptContext(BaseModel):
    """Conversation context for prompt building."""
    intent: Optional[str] = Field(None, description="Detected user intent")
    mood: Optional[str] = Field(None, description="Detected mood")
    activity: Optional[str] = Field(None, description="Detected activity")
    discovery_goal: Optional[str] = Field(None, description="Discovery goal")
    preferred_genres: List[str] = Field(default_factory=list, description="Preferred genres")
    preferred_artists: List[str] = Field(default_factory=list, description="Preferred artists")
    energy_level: Optional[str] = Field(None, description="Energy level")
    popularity_filter: Optional[str] = Field(None, description="Popularity filter")


class PromptMemory(BaseModel):
    """Conversation memory for prompt building."""
    previously_recommended_songs: List[str] = Field(default_factory=list, description="Previously recommended songs")
    previously_recommended_artists: List[str] = Field(default_factory=list, description="Previously recommended artists")
    discovery_history: List[str] = Field(default_factory=list, description="Discovery history")
    recently_discussed_genres: List[str] = Field(default_factory=list, description="Recently discussed genres")
    user_segment: Optional[str] = Field(None, description="User segment")


class PromptReviewInsights(BaseModel):
    """Review insights from Phase 2 for prompt building."""
    pain_points: List[str] = Field(default_factory=list, description="Identified pain points")
    theme_clusters: List[str] = Field(default_factory=list, description="Theme clusters")
    product_insights: List[str] = Field(default_factory=list, description="Product insights")
    executive_summary: Optional[str] = Field(None, description="Executive summary")


class PromptMusicMetadata(BaseModel):
    """Music metadata for prompt building."""
    recommended_tracks: List[str] = Field(default_factory=list, description="Recommended tracks")
    recommended_artists: List[str] = Field(default_factory=list, description="Recommended artists")
    genre_info: Optional[str] = Field(None, description="Genre information")
    audio_features: Optional[str] = Field(None, description="Audio features summary")
