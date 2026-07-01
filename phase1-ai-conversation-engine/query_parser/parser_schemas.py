from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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


class PopularityFilterType(str, Enum):
    MAINSTREAM = "mainstream"
    INDIE = "indie"
    UNDERGROUND = "underground"


class ParsedQuery(BaseModel):
    """Structured representation of a parsed user query."""
    
    # Core parameters
    mood: Optional[MoodType] = None
    goal: Optional[ListeningGoalType] = None
    genres: List[str] = Field(default_factory=list)
    artists: List[str] = Field(default_factory=list)
    
    # Discovery preferences
    discovery_preference: DiscoveryPreferenceType = DiscoveryPreferenceType.BALANCED
    popularity_filter: Optional[PopularityFilterType] = None
    
    # Constraints
    instrumental_only: bool = False
    energy_level: Optional[int] = Field(None, ge=0, le=100)  # 0-100
    tempo: Optional[str] = None  # slow, medium, fast
    
    # Additional extracted information
    keywords: List[str] = Field(default_factory=list)
    entities: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    raw_query: str = ""
