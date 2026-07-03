"""
Combined Intent Recognition and Query Parser
Processes both intent recognition and query parsing in a single Groq API call
to reduce API calls and improve performance.
"""
import asyncio
import json
import structlog
from typing import Optional, Dict, Any, List
from groq import Groq
from .intent_recognition.intent_schemas import IntentResult, IntentType
from .query_parser.parser_schemas import (
    ParsedQuery,
    MoodType,
    ListeningGoalType,
    DiscoveryPreferenceType,
    PopularityFilterType
)
from .prompt_builder import PromptBuilder


logger = structlog.get_logger(__name__)


class CombinedIntentParser:
    """
    Combined intent recognition and query parser using a single Groq API call.
    """
    
    def __init__(
        self,
        groq_api_key: str,
        primary_model: str = "llama-3.1-70b-versatile",
        fallback_model: str = "llama-3.1-8b",
        timeout: int = 30,
        prompt_builder: Optional[PromptBuilder] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.groq = Groq(api_key=groq_api_key)
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.timeout = timeout
        self.prompt_builder = prompt_builder or PromptBuilder(config or {})
        self.config = config or {}
        
        # Response cache
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 3600  # 1 hour cache
    
    async def process(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> tuple[IntentResult, ParsedQuery]:
        """
        Process query to recognize intent and parse parameters in a single API call.
        
        Args:
            query: The user's natural language query
            conversation_history: Optional conversation history for context
            
        Returns:
            Tuple of (IntentResult, ParsedQuery)
        """
        # Check cache
        cache_key = f"{query}_{str(conversation_history)}"
        if cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            if asyncio.get_event_loop().time() - cached_time < self._cache_ttl:
                logger.info("Using cached result", query=query)
                return cached_result
        
        try:
            # Build combined prompt
            prompt = self.prompt_builder.build_combined_intent_parse_prompt(
                user_query=query,
                conversation_history=conversation_history
            )
            
            # Try primary model
            result = await self._process_with_model(prompt, self.primary_model)
            
            # Cache result
            self._cache[cache_key] = (result, asyncio.get_event_loop().time())
            
            return result
            
        except Exception as e:
            logger.error(
                "Combined processing failed",
                query=query,
                error=str(e)
            )
            # Return fallback results
            return (
                IntentResult(intent=IntentType.GENERAL_CHAT, confidence=0.0),
                ParsedQuery(raw_query=query, confidence=0.0)
            )
    
    async def _process_with_model(
        self,
        prompt: str,
        model: str
    ) -> tuple[IntentResult, ParsedQuery]:
        """
        Process query using a specific model.
        
        Args:
            prompt: The combined prompt
            model: The Groq model to use
            
        Returns:
            Tuple of (IntentResult, ParsedQuery)
        """
        try:
            response = await asyncio.to_thread(
                self.groq.chat.completions.create,
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=400,
                response_format={"type": "json_object"},
                timeout=self.timeout
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            result_data = json.loads(response_text)
            
            # Extract intent result
            intent_str = result_data.get("intent", "GENERAL_CHAT")
            try:
                intent = IntentType(intent_str)
            except ValueError:
                logger.warning(
                    "Unknown intent returned, using fallback",
                    returned_intent=intent_str
                )
                intent = IntentType.GENERAL_CHAT
            
            intent_result = IntentResult(
                intent=intent,
                confidence=float(result_data.get("confidence", 0.5)),
                reasoning=result_data.get("reasoning", "")
            )
            
            # Extract parsed query
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
                keywords=result_data.get("keywords", []),
                entities=result_data.get("entities", {}),
                confidence=float(result_data.get("confidence", 0.5)),
                raw_query=prompt.split("USER QUERY: ")[1].split("\n")[0] if "USER QUERY:" in prompt else ""
            )
            
            return (intent_result, parsed_query)
            
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON response",
                response=response_text,
                error=str(e)
            )
            raise ValueError("Invalid JSON response from LLM")
            
        except Exception as e:
            logger.error(
                "Model processing failed",
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
    
    def clear_cache(self):
        """Clear the response cache."""
        self._cache.clear()
        logger.info("Cache cleared")


class MockCombinedIntentParser:
    """Mock implementation for testing without Groq API."""
    
    def __init__(self):
        pass
    
    async def process(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> tuple[IntentResult, ParsedQuery]:
        """Mock combined processing based on keyword matching."""
        query_lower = query.lower()
        
        # Intent detection
        intent_mapping = {
            "discover": IntentType.DISCOVER_NEW_ARTISTS,
            "new artist": IntentType.DISCOVER_NEW_ARTISTS,
            "underrated": IntentType.DISCOVER_NEW_ARTISTS,
            "hidden gem": IntentType.DISCOVER_NEW_ARTISTS,
            "feeling": IntentType.MOOD_BASED,
            "mood": IntentType.MOOD_BASED,
            "sad": IntentType.MOOD_BASED,
            "happy": IntentType.MOOD_BASED,
            "uplifting": IntentType.MOOD_BASED,
            "coding": IntentType.CODING_MUSIC,
            "programming": IntentType.CODING_MUSIC,
            "workout": IntentType.WORKOUT_MUSIC,
            "gym": IntentType.WORKOUT_MUSIC,
            "exercise": IntentType.WORKOUT_MUSIC,
            "relax": IntentType.RELAXATION_MUSIC,
            "calm": IntentType.RELAXATION_MUSIC,
            "sleep": IntentType.RELAXATION_MUSIC,
            "instrumental": IntentType.INSTRUMENTAL_MUSIC,
            "no vocals": IntentType.INSTRUMENTAL_MUSIC,
            "genre": IntentType.GENRE_EXPLORATION,
            "similar": IntentType.ARTIST_EXPLORATION,
            "like": IntentType.ARTIST_EXPLORATION,
            "repetitive": IntentType.ESCAPE_REPETITIVE,
            "same songs": IntentType.ESCAPE_REPETITIVE,
            "habit": IntentType.ESCAPE_REPETITIVE,
            "explain": IntentType.CLARIFICATION,
            "why": IntentType.CLARIFICATION,
            "don't like": IntentType.FEEDBACK,
            "great": IntentType.FEEDBACK,
            "hello": IntentType.GENERAL_CHAT,
            "hi": IntentType.GENERAL_CHAT,
            "how are you": IntentType.GENERAL_CHAT,
        }
        
        detected_intent = IntentType.GENERAL_CHAT
        for keyword, intent in intent_mapping.items():
            if keyword in query_lower:
                detected_intent = intent
                break
        
        intent_result = IntentResult(
            intent=detected_intent,
            confidence=0.85,
            reasoning=f"Matched keyword pattern"
        )
        
        # Query parsing
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
        
        return (intent_result, parsed)
