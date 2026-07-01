import asyncio
import json
import structlog
from typing import Optional, Dict, Any
from groq import Groq
from .parser_schemas import (
    ParsedQuery,
    MoodType,
    ListeningGoalType,
    DiscoveryPreferenceType,
    PopularityFilterType
)
from .parser_prompts import QUERY_PARSER_PROMPT
from ..prompt_builder import PromptBuilder


logger = structlog.get_logger(__name__)


class QueryParser:
    """
    Parses natural language queries to extract structured parameters
    using Groq LLM for mood, goal, and discovery preference detection.
    """
    
    def __init__(
        self,
        groq_api_key: str,
        primary_model: str = "llama-3.1-70b-versatile",
        secondary_model: str = "mixtral-8x7b",
        timeout: int = 30,
        prompt_builder: Optional[PromptBuilder] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.groq = Groq(api_key=groq_api_key)
        self.primary_model = primary_model
        self.secondary_model = secondary_model
        self.timeout = timeout
        self.prompt_builder = prompt_builder or PromptBuilder(config or {})
        self.config = config or {}
    
    async def parse(
        self,
        query: str,
        intent: Optional[str] = None
    ) -> ParsedQuery:
        """
        Parse a natural language query to extract structured parameters.
        
        Args:
            query: The user's natural language query
            intent: Optional intent classification for context
            
        Returns:
            ParsedQuery with extracted parameters
        """
        try:
            # Build prompt using Prompt Builder
            prompt = self.prompt_builder.build_parser_prompt(
                user_query=query,
                intent=intent or "general"
            )
            
            # Try primary model first
            result = await self._parse_with_model(prompt, self.primary_model)
            
            # If confidence is low, try secondary model
            if result.confidence < 0.5:
                logger.warning(
                    "Primary model confidence low, trying secondary",
                    query=query,
                    confidence=result.confidence
                )
                result = await self._parse_with_model(prompt, self.secondary_model)
            
            return result
            
        except Exception as e:
            logger.error(
                "Query parsing failed",
                query=query,
                error=str(e)
            )
            # Return minimal parsed query on error
            return ParsedQuery(
                raw_query=query,
                confidence=0.0
            )
    
    async def _parse_with_model(
        self,
        prompt: str,
        model: str
    ) -> ParsedQuery:
        """
        Parse query using a specific model.
        
        Args:
            prompt: The prompt to send to the model
            model: The Groq model to use
            
        Returns:
            ParsedQuery with extracted parameters
        """
        try:
            response = await asyncio.to_thread(
                self.groq.chat.completions.create,
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"},
                timeout=self.timeout
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result_data = json.loads(response_text)
                
                # Convert string enums to actual enums
                parsed_query = ParsedQuery(
                    mood=self._parse_enum(result_data.get("mood"), MoodType),
                    goal=self._parse_enum(result_data.get("goal"), ListeningGoalType),
                    genres=result_data.get("genres", []),
                    artists=result_data.get("artists", []),
                    discovery_preference=self._parse_enum(
                        result_data.get("discovery_preference", "balanced"),
                        DiscoveryPreferenceType
                    ),
                    popularity_filter=self._parse_enum(
                        result_data.get("popularity_filter"),
                        PopularityFilterType
                    ),
                    instrumental_only=result_data.get("instrumental_only", False),
                    energy_level=result_data.get("energy_level"),
                    tempo=result_data.get("tempo"),
                    keywords=result_data.get("keywords", []),
                    entities=result_data.get("entities", {}),
                    confidence=result_data.get("confidence", 0.5),
                    raw_query=query
                )
                
                return parsed_query
                
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse JSON response",
                    response=response_text,
                    error=str(e)
                )
                raise ValueError("Invalid JSON response from LLM")
                
        except Exception as e:
            logger.error(
                "Model parsing failed",
                model=model,
                error=str(e)
            )
            raise
    
    def _parse_enum(self, value: Optional[str], enum_class):
        """Parse a string value to an enum, returning None if invalid."""
        if value is None:
            return None
        try:
            return enum_class(value)
        except ValueError:
            logger.warning(
                f"Invalid enum value: {value} for {enum_class.__name__}"
            )
            return None


class MockQueryParser:
    """Mock implementation for testing without Groq API."""
    
    def __init__(self):
        pass
    
    async def parse(
        self,
        query: str,
        intent: Optional[str] = None
    ) -> ParsedQuery:
        """Mock query parsing based on keyword matching."""
        query_lower = query.lower()
        
        parsed = ParsedQuery(
            raw_query=query,
            confidence=0.75
        )
        
        # Mood detection
        mood_keywords = {
            "energetic": MoodType.ENERGETIC,
            "upbeat": MoodType.UPBEAT,
            "happy": MoodType.HAPPY,
            "sad": MoodType.SAD,
            "melancholic": MoodType.MELANCHOLIC,
            "calm": MoodType.CALM,
            "relaxed": MoodType.RELAXED,
            "focus": MoodType.FOCUS,
            "romantic": MoodType.ROMANTIC,
            "aggressive": MoodType.AGGRESSIVE
        }
        
        for keyword, mood in mood_keywords.items():
            if keyword in query_lower:
                parsed.mood = mood
                parsed.keywords.append(keyword)
                break
        
        # Goal detection
        goal_keywords = {
            "coding": ListeningGoalType.CODING,
            "programming": ListeningGoalType.CODING,
            "workout": ListeningGoalType.WORKOUT,
            "gym": ListeningGoalType.WORKOUT,
            "exercise": ListeningGoalType.WORKOUT,
            "studying": ListeningGoalType.STUDYING,
            "study": ListeningGoalType.STUDYING,
            "relax": ListeningGoalType.RELAXATION,
            "relaxation": ListeningGoalType.RELAXATION,
            "sleep": ListeningGoalType.SLEEP,
            "focus": ListeningGoalType.FOCUS
        }
        
        for keyword, goal in goal_keywords.items():
            if keyword in query_lower:
                parsed.goal = goal
                parsed.keywords.append(keyword)
                break
        
        # Instrumental detection
        if "instrumental" in query_lower or "no vocals" in query_lower:
            parsed.instrumental_only = True
            parsed.keywords.append("instrumental")
        
        # Discovery preference
        if "new" in query_lower or "discover" in query_lower:
            parsed.discovery_preference = DiscoveryPreferenceType.NOVEL
        elif "familiar" in query_lower:
            parsed.discovery_preference = DiscoveryPreferenceType.FAMILIAR
        
        # Popularity filter
        if "indie" in query_lower:
            parsed.popularity_filter = PopularityFilterType.INDIE
        elif "mainstream" in query_lower:
            parsed.popularity_filter = PopularityFilterType.MAINSTREAM
        elif "underground" in query_lower:
            parsed.popularity_filter = PopularityFilterType.UNDERGROUND
        
        return parsed
