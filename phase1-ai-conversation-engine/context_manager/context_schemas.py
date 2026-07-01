from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MoodType(str, Enum):
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


class ListeningGoalType(str, Enum):
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
    FAMILIAR = "familiar"
    BALANCED = "balanced"
    NOVEL = "novel"
    EXPERIMENTAL = "experimental"


class IntentType(str, Enum):
    DISCOVER_NEW_ARTISTS = "DISCOVER_NEW_ARTISTS"
    MOOD_BASED = "MOOD_BASED"
    ACTIVITY_BASED = "ACTIVITY_BASED"
    GENRE_EXPLORATION = "GENRE_EXPLORATION"
    ARTIST_EXPLORATION = "ARTIST_EXPLORATION"
    ESCAPE_REPETITIVE = "ESCAPE_REPETITIVE"
    INSTRUMENTAL_MUSIC = "INSTRUMENTAL_MUSIC"
    CODING_MUSIC = "CODING_MUSIC"
    WORKOUT_MUSIC = "WORKOUT_MUSIC"
    RELAXATION_MUSIC = "RELAXATION_MUSIC"
    CLARIFICATION = "CLARIFICATION"
    FEEDBACK = "FEEDBACK"
    GENERAL_CHAT = "GENERAL_CHAT"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ConversationMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StructuredConversationContext(BaseModel):
    """Structured information extracted from conversation."""
    user_intent: Optional[IntentType] = None
    mood: Optional[MoodType] = None
    activity: Optional[ListeningGoalType] = None
    preferred_genres: List[str] = Field(default_factory=list)
    preferred_artists: List[str] = Field(default_factory=list)
    discovery_goal: DiscoveryPreferenceType = DiscoveryPreferenceType.BALANCED
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class UserContext(BaseModel):
    user_id: str
    current_mood: Optional[MoodType] = None
    current_goal: Optional[ListeningGoalType] = None
    discovery_preference: DiscoveryPreferenceType = DiscoveryPreferenceType.BALANCED
    recent_genres: List[str] = Field(default_factory=list)
    recent_artists: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Enhanced with structured conversation context
    structured_context: StructuredConversationContext = Field(default_factory=StructuredConversationContext)


class ConversationHistory(BaseModel):
    user_id: str
    session_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    context: UserContext
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendedSong(BaseModel):
    """Schema for a recommended song."""
    song_id: str
    song_name: str
    artist: str
    album: Optional[str] = None
    recommended_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    feedback: Optional[str] = None  # "liked", "disliked", "neutral"


class RecommendedArtist(BaseModel):
    """Schema for a recommended artist."""
    artist_id: str
    artist_name: str
    recommended_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    feedback: Optional[str] = None


class DiscoveryHistory(BaseModel):
    """Schema for discovery history."""
    discovery_type: str  # "genre", "artist", "mood", "activity"
    discovered_item: str
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    confidence: float = 0.5


class UserMemory(BaseModel):
    """Schema for user memory tracking recommendations and discovery history."""
    user_id: str
    previously_recommended_songs: List[RecommendedSong] = Field(default_factory=list)
    previously_recommended_artists: List[RecommendedArtist] = Field(default_factory=list)
    recently_discussed_genres: List[str] = Field(default_factory=list)
    discovery_history: List[DiscoveryHistory] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
