from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Recommendation(BaseModel):
    """Schema for a music recommendation."""
    artist: str
    track: Optional[str] = None
    album: Optional[str] = None
    explanation: str
    spotify_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeneratedResponse(BaseModel):
    """Schema for a generated AI response."""
    content: str
    recommendations: List[Recommendation] = Field(default_factory=list)
    intent: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
