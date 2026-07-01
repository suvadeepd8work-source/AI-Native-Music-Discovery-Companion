"""
Shared schemas for Phase 2: Music Recommendation Engine.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MoodType(str, Enum):
    """Mood types for music matching."""
    ENERGETIC = "energetic"
    CALM = "calm"
    MELANCHOLIC = "melancholic"
    UPBEAT = "upbeat"
    FOCUS = "focus"
    RELAXED = "relaxed"
    HAPPY = "happy"
    SAD = "sad"
    ROMANTIC = "romantic"
    AGGRESSIVE = "aggressive"


class ActivityType(str, Enum):
    """Activity types for music matching."""
    CODING = "coding"
    WORKOUT = "workout"
    STUDYING = "studying"
    RELAXATION = "relaxation"
    SLEEP = "sleep"
    FOCUS = "focus"
    ENTERTAINMENT = "entertainment"
    BACKGROUND = "background"
    ACTIVE_LISTENING = "active_listening"
    SOCIAL = "social"


class DiscoveryPreferenceType(str, Enum):
    """Discovery preference types."""
    FAMILIAR = "familiar"
    BALANCED = "balanced"
    NOVEL = "novel"


class RecommendationRequest(BaseModel):
    """Request schema for music recommendations."""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Unique session identifier")
    
    # From Phase 1: Conversation Context
    user_intent: str = Field(..., description="Detected user intent")
    mood: Optional[MoodType] = Field(None, description="Detected mood")
    activity: Optional[ActivityType] = Field(None, description="Detected activity")
    preferred_genres: List[str] = Field(default_factory=list, description="Preferred genres")
    preferred_artists: List[str] = Field(default_factory=list, description="Preferred artists")
    discovery_goal: DiscoveryPreferenceType = Field(..., description="Discovery preference")
    
    # From Phase 1: Conversation Memory
    previously_recommended_songs: List[str] = Field(default_factory=list, description="Previously recommended song IDs")
    previously_recommended_artists: List[str] = Field(default_factory=list, description="Previously recommended artist IDs")
    recently_discussed_genres: List[str] = Field(default_factory=list, description="Recently discussed genres")
    
    # Additional parameters
    limit: int = Field(default=10, ge=1, le=20, description="Number of recommendations")
    include_explanations: bool = Field(default=True, description="Include explanations for recommendations")
    
    # Review Discovery Engine integration
    user_segment_id: Optional[str] = Field(None, description="User segment ID for personalization")
    review_insights_enabled: bool = Field(default=True, description="Whether to use review insights")


class AudioFeatures(BaseModel):
    """Audio features for tracks/artists."""
    energy: float = Field(..., ge=0.0, le=1.0, description="Energy level")
    valence: float = Field(..., ge=0.0, le=1.0, description="Musical positiveness")
    danceability: float = Field(..., ge=0.0, le=1.0, description="Danceability")
    acousticness: float = Field(..., ge=0.0, le=1.0, description="Acousticness")
    instrumentalness: float = Field(..., ge=0.0, le=1.0, description="Instrumentalness")
    speechiness: float = Field(..., ge=0.0, le=1.0, description="Speechiness")
    tempo: Optional[float] = Field(None, ge=0.0, description="Tempo in BPM")
    loudness: Optional[float] = Field(None, description="Loudness in dB")
    mode: Optional[int] = Field(None, ge=0, le=1, description="Mode (0=minor, 1=major)")
    key: Optional[int] = Field(None, ge=-1, le=11, description="Key")
    liveness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Liveness")


class Track(BaseModel):
    """Track information."""
    track_id: str = Field(..., description="Track ID")
    source: str = Field(..., description="Source API (spotify, deezer, lastfm, jamendo)")
    track_name: str = Field(..., description="Track name")
    artist_id: str = Field(..., description="Artist ID")
    artist_name: str = Field(..., description="Artist name")
    album_name: Optional[str] = Field(None, description="Album name")
    album_id: Optional[str] = Field(None, description="Album ID")
    duration_ms: int = Field(..., description="Duration in milliseconds")
    popularity: int = Field(..., ge=0, le=100, description="Popularity score")
    audio_features: Optional[AudioFeatures] = Field(None, description="Audio features")
    external_url: Optional[str] = Field(None, description="External URL")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    image_url: Optional[str] = Field(None, description="Album image URL")
    release_date: Optional[str] = Field(None, description="Release date")
    release_year: Optional[int] = Field(None, description="Release year")
    genres: List[str] = Field(default_factory=list, description="Track genres")
    explicit: Optional[bool] = Field(None, description="Explicit content flag")
    track_number: Optional[int] = Field(None, description="Track number on album")
    isrc: Optional[str] = Field(None, description="ISRC code")


class Artist(BaseModel):
    """Artist information."""
    artist_id: str = Field(..., description="Artist ID")
    source: str = Field(..., description="Source API (spotify, deezer, lastfm, jamendo)")
    artist_name: str = Field(..., description="Artist name")
    genres: List[str] = Field(default_factory=list, description="Artist genres")
    popularity: int = Field(..., ge=0, le=100, description="Popularity score")
    followers: int = Field(..., ge=0, description="Number of followers")
    external_url: Optional[str] = Field(None, description="External URL")
    image_url: Optional[str] = Field(None, description="Artist image URL")
    similar_artists: List[str] = Field(default_factory=list, description="Similar artist IDs")
    biography: Optional[str] = Field(None, description="Artist biography")
    country: Optional[str] = Field(None, description="Artist country of origin")
    formation_year: Optional[int] = Field(None, description="Year artist was formed")
    albums: List[str] = Field(default_factory=list, description="Album IDs")
    top_tracks: List[str] = Field(default_factory=list, description="Top track IDs")


class Album(BaseModel):
    """Album information."""
    album_id: str = Field(..., description="Album ID")
    source: str = Field(..., description="Source API (spotify, deezer, lastfm, jamendo)")
    album_name: str = Field(..., description="Album name")
    artist_id: str = Field(..., description="Artist ID")
    artist_name: str = Field(..., description="Artist name")
    release_date: Optional[str] = Field(None, description="Release date")
    release_year: Optional[int] = Field(None, description="Release year")
    total_tracks: int = Field(..., ge=0, description="Total number of tracks")
    genres: List[str] = Field(default_factory=list, description="Album genres")
    popularity: int = Field(..., ge=0, le=100, description="Popularity score")
    external_url: Optional[str] = Field(None, description="External URL")
    image_url: Optional[str] = Field(None, description="Album image URL")
    label: Optional[str] = Field(None, description="Record label")
    tracks: List[str] = Field(default_factory=list, description="Track IDs")


class Genre(BaseModel):
    """Genre information."""
    genre_id: str = Field(..., description="Genre ID")
    source: str = Field(..., description="Source API")
    genre_name: str = Field(..., description="Genre name")
    parent_genre: Optional[str] = Field(None, description="Parent genre")
    sub_genres: List[str] = Field(default_factory=list, description="Sub-genres")
    description: Optional[str] = Field(None, description="Genre description")
    popularity: int = Field(..., ge=0, le=100, description="Genre popularity")


class StoredRecommendation(BaseModel):
    """Structured stored recommendation."""
    recommendation_id: str = Field(..., description="Unique recommendation ID")
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    track: Track = Field(..., description="Recommended track")
    artist: Artist = Field(..., description="Artist information")
    album: Optional[Album] = Field(None, description="Album information")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    explanation: str = Field(..., description="Explanation for recommendation")
    strategies_used: List[str] = Field(default_factory=list, description="Strategies used")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    user_feedback: Optional[str] = Field(None, description="User feedback")
    was_played: bool = Field(default=False, description="Whether track was played")
    play_duration_ms: Optional[int] = Field(None, description="Play duration in milliseconds")


class RecommendationCandidate(BaseModel):
    """A candidate recommendation before ranking."""
    item: Track = Field(..., description="Track or artist recommendation")
    strategy: str = Field(..., description="Strategy that generated this candidate")
    score: float = Field(..., ge=0.0, le=1.0, description="Strategy-specific score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    novelty_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Novelty score (how new/unusual)")
    diversity_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Diversity score (how different from others)")
    intent_match_score: float = Field(default=0.5, ge=0.0, le=1.0, description="User intent match score")
    mood_match_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Mood match score")
    activity_match_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Activity match score")
    discovery_match_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Discovery goal match score")
    context_match_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Listening context match score")


class Recommendation(BaseModel):
    """Final recommendation with explanation."""
    track: Track = Field(..., description="Recommended track")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    explanation: str = Field(..., description="Explanation for recommendation")
    strategies_used: List[str] = Field(default_factory=list, description="Strategies that contributed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    detailed_explanation: Optional[Dict[str, Any]] = Field(None, description="Detailed explanation factors")


class RecommendationResponse(BaseModel):
    """Response schema for music recommendations."""
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Unique session identifier")
    recommendations: List[Recommendation] = Field(..., description="List of recommendations")
    total_count: int = Field(..., description="Total number of recommendations")
    strategies_executed: List[str] = Field(..., description="Strategies that were executed")
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


class ReviewInsight(BaseModel):
    """Review insight from Review Discovery Engine."""
    artist_id: str = Field(..., description="Spotify artist ID")
    artist_name: str = Field(..., description="Artist name")
    review_sentiment: float = Field(..., ge=0.0, le=1.0, description="Review sentiment score")
    review_count: int = Field(..., ge=0, description="Number of reviews")
    genre_tags: List[str] = Field(default_factory=list, description="Genre tags")
    unique_descriptors: List[str] = Field(default_factory=list, description="Unique descriptors from reviews")
    discovery_score: float = Field(..., ge=0.0, le=1.0, description="Discovery score")
    last_updated: datetime = Field(..., description="Last update timestamp")
    themes: List[str] = Field(default_factory=list, description="Key themes from reviews")
    pain_points: List[str] = Field(default_factory=list, description="Common pain points mentioned")


class ThemeCluster(BaseModel):
    """Theme cluster from review analysis."""
    cluster_id: str = Field(..., description="Cluster ID")
    theme_name: str = Field(..., description="Theme name")
    description: str = Field(..., description="Theme description")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with theme")
    sentiment: float = Field(..., ge=-1.0, le=1.0, description="Average sentiment for this theme")
    frequency: int = Field(..., ge=0, description="Frequency of mentions")
    related_artists: List[str] = Field(default_factory=list, description="Artists associated with this theme")


class PainPoint(BaseModel):
    """Pain point identified from reviews."""
    pain_point_id: str = Field(..., description="Pain point ID")
    description: str = Field(..., description="Pain point description")
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity score")
    frequency: int = Field(..., ge=0, description="Frequency of mentions")
    affected_segments: List[str] = Field(default_factory=list, description="User segments affected")
    suggested_action: str = Field(..., description="Suggested action to mitigate")


class UserSegment(BaseModel):
    """User segment from review analysis."""
    segment_id: str = Field(..., description="Segment ID")
    segment_name: str = Field(..., description="Segment name")
    description: str = Field(..., description="Segment description")
    size: int = Field(..., ge=0, description="Number of users in segment")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Segment preferences")
    behaviors: List[str] = Field(default_factory=list, description="Common behaviors")
    pain_points: List[str] = Field(default_factory=list, description="Pain points for this segment")


class ProductInsight(BaseModel):
    """Product insight from executive report."""
    insight_id: str = Field(..., description="Insight ID")
    category: str = Field(..., description="Insight category")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Insight description")
    impact: str = Field(..., description="Impact level (high/medium/low)")
    actionable: bool = Field(..., description="Whether insight is actionable")
    recommendation: Optional[str] = Field(None, description="Recommended action")


class ExecutiveReport(BaseModel):
    """Executive report summary."""
    report_id: str = Field(..., description="Report ID")
    generated_at: str = Field(..., description="Report generation timestamp")
    summary: str = Field(..., description="Executive summary")
    key_findings: List[str] = Field(default_factory=list, description="Key findings")
    recommendations: List[str] = Field(default_factory=list, description="Top recommendations")
    theme_clusters: List[ThemeCluster] = Field(default_factory=list, description="Theme clusters")
    pain_points: List[PainPoint] = Field(default_factory=list, description="Identified pain points")
    user_segments: List[UserSegment] = Field(default_factory=list, description="User segments")
    product_insights: List[ProductInsight] = Field(default_factory=list, description="Product insights")


class StrategyResult(BaseModel):
    """Result from a recommendation strategy."""
    strategy_name: str = Field(..., description="Name of the strategy")
    candidates: List[RecommendationCandidate] = Field(default_factory=list, description="Generated candidates")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    success: bool = Field(..., description="Whether strategy succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
