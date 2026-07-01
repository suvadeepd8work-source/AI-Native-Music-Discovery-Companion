from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


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


class IntentResult(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
