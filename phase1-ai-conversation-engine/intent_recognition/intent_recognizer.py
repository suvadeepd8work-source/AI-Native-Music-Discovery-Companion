import asyncio
import json
import structlog
from typing import Optional, Dict, Any, List
from groq import Groq
from .intent_schemas import IntentResult, IntentType
from .intent_prompts import INTENT_CLASSIFICATION_PROMPT
from ..prompt_builder import PromptBuilder


logger = structlog.get_logger(__name__)


class IntentRecognizer:
    def __init__(
        self,
        groq_api_key: str,
        primary_model: str = "llama-3.1-70b-versatile",
        fallback_model: str = "llama-3.1-8b",
        confidence_threshold: float = 0.7,
        fallback_intent: str = "GENERAL_CHAT",
        timeout: int = 30,
        prompt_builder: Optional[PromptBuilder] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.groq = Groq(api_key=groq_api_key)
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.confidence_threshold = confidence_threshold
        self.fallback_intent = fallback_intent
        self.timeout = timeout
        self.prompt_builder = prompt_builder or PromptBuilder(config or {})
        self.config = config or {}

    async def recognize(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> IntentResult:
        """
        Recognize the intent of a user query using Groq LLM.
        
        Args:
            query: The user's natural language query
            conversation_history: Optional conversation history for context
            
        Returns:
            IntentResult containing the classified intent and confidence
        """
        try:
            # Build prompt using Prompt Builder
            prompt = self.prompt_builder.build_intent_prompt(
                user_query=query,
                conversation_history=conversation_history
            )
            
            # Try primary model
            result = await self._recognize_with_model(prompt, self.primary_model)
            
            # If confidence is below threshold, use fallback
            if result.confidence < self.confidence_threshold:
                logger.warning(
                    "Primary model confidence below threshold, using fallback",
                    query=query,
                    confidence=result.confidence
                )
                result = IntentResult(
                    intent=self.fallback_intent,
                    confidence=0.5
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "Intent recognition failed",
                query=query,
                error=str(e)
            )
            # Return fallback intent
            return IntentResult(
                intent=self.fallback_intent,
                confidence=0.0
            )

    async def _recognize_with_model(
        self,
        prompt: str,
        model: str
    ) -> IntentResult:
        """
        Recognize intent using a specific model.
        
        Args:
            prompt: The prompt to send to the model
            model: The Groq model to use
            
        Returns:
            IntentResult with classification
        """
        try:
            response = await asyncio.to_thread(
                self.groq.chat.completions.create,
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200,
                timeout=self.timeout
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                # Extract JSON from response (in case there's extra text)
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    result_data = json.loads(json_text)
                else:
                    result_data = json.loads(response_text)
                
                # Validate intent
                intent_str = result_data.get("intent", "GENERAL_CHAT")
                try:
                    intent = IntentType(intent_str)
                except ValueError:
                    logger.warning(
                        "Unknown intent returned, using fallback",
                        returned_intent=intent_str
                    )
                    intent = IntentType.GENERAL_CHAT
                
                confidence = float(result_data.get("confidence", 0.5))
                reasoning = result_data.get("reasoning", "")
                
                return IntentResult(
                    intent=intent,
                    confidence=confidence,
                    reasoning=reasoning
                )
                
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse JSON response",
                    response=response_text,
                    error=str(e)
                )
                raise ValueError("Invalid JSON response from LLM")
                
        except Exception as e:
            logger.error(
                "Model recognition failed",
                model=model,
                error=str(e)
            )
            raise


class MockIntentRecognizer:
    """Mock implementation for testing without Groq API."""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
    
    async def recognize(self, query: str) -> IntentResult:
        """Mock intent recognition based on keyword matching."""
        query_lower = query.lower()
        
        # Simple keyword-based mock classification
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
        
        for keyword, intent in intent_mapping.items():
            if keyword in query_lower:
                return IntentResult(
                    intent=intent,
                    confidence=0.85,
                    reasoning=f"Matched keyword: {keyword}"
                )
        
        # Default fallback
        return IntentResult(
            intent=IntentType.GENERAL_CHAT,
            confidence=0.5,
            reasoning="No keyword match, using default"
        )
