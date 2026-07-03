import asyncio
import structlog
from typing import Optional, List, Dict, Any
from groq import Groq
from .response_schemas import GeneratedResponse, Recommendation
from .response_prompts import RESPONSE_GENERATION_PROMPT
from .response_storage import ResponseStorage, MockResponseStorage
from ..prompt_builder import PromptBuilder, PromptContext, PromptMemory, PromptReviewInsights, PromptMusicMetadata


logger = structlog.get_logger(__name__)


class ResponseGenerator:
    """
    Generates natural, conversational responses using Groq LLM.
    """
    
    def __init__(
        self,
        groq_api_key: str,
        primary_model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 30,
        prompt_builder: Optional[PromptBuilder] = None,
        storage: Optional[ResponseStorage] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.groq = Groq(api_key=groq_api_key)
        self.primary_model = primary_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.prompt_builder = prompt_builder or PromptBuilder(config or {})
        self.storage = storage or ResponseStorage(config.get("response_storage", {}) if config else {})
        self.config = config or {}
    
    async def generate(
        self,
        query: str,
        intent: str,
        context: Dict[str, Any],
        recommendations: Optional[List[Recommendation]] = None,
        memory: Optional[Dict[str, Any]] = None,
        review_insights: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> GeneratedResponse:
        """
        Generate a natural response to the user's query.
        
        Args:
            query: The user's original query
            intent: The detected intent
            context: User context (mood, goal, genres, artists)
            recommendations: Optional list of recommendations to include
            memory: Optional conversation memory
            review_insights: Optional review insights from Phase 2
            user_id: Optional user identifier for storage
            session_id: Optional session identifier for storage
            
        Returns:
            GeneratedResponse with the conversational response
        """
        try:
            # Build prompt context
            prompt_context = PromptContext(
                intent=intent,
                mood=context.get("current_mood"),
                activity=context.get("current_activity"),
                discovery_goal=context.get("current_goal"),
                preferred_genres=context.get("recent_genres", []),
                preferred_artists=context.get("recent_artists", []),
                energy_level=context.get("energy_level"),
                popularity_filter=context.get("popularity_filter")
            )
            
            # Build prompt memory
            prompt_memory = None
            if memory:
                prompt_memory = PromptMemory(
                    previously_recommended_songs=memory.get("previously_recommended_songs", []),
                    previously_recommended_artists=memory.get("previously_recommended_artists", []),
                    discovery_history=memory.get("discovery_history", []),
                    recently_discussed_genres=memory.get("recently_discussed_genres", []),
                    user_segment=memory.get("user_segment")
                )
            
            # Build review insights
            prompt_review_insights = None
            if review_insights:
                prompt_review_insights = PromptReviewInsights(
                    pain_points=review_insights.get("pain_points", []),
                    theme_clusters=review_insights.get("theme_clusters", []),
                    product_insights=review_insights.get("product_insights", []),
                    executive_summary=review_insights.get("executive_summary")
                )
            
            # Build music metadata
            prompt_music_metadata = None
            if recommendations:
                tracks = [f"{rec.artist}: {rec.track}" for rec in recommendations]
                artists = [rec.artist for rec in recommendations]
                prompt_music_metadata = PromptMusicMetadata(
                    recommended_tracks=tracks,
                    recommended_artists=artists
                )
            
            # Build prompt using Prompt Builder
            prompt = self.prompt_builder.build_prompt(
                user_query=query,
                context=prompt_context,
                memory=prompt_memory,
                review_insights=prompt_review_insights,
                music_metadata=prompt_music_metadata,
                intent=intent
            )
            
            # Try primary model
            response_text = await self._generate_with_model(
                prompt,
                self.primary_model
            )
            
            generated_response = GeneratedResponse(
                content=response_text or "I understand. Let me help you with that.",
                recommendations=recommendations or [],
                intent=intent,
                confidence=0.8
            )
            
            # Store response if user_id and session_id provided
            if user_id and session_id:
                response_id = f"resp_{user_id}_{session_id}_{int(asyncio.get_event_loop().time())}"
                self.storage.store_response(
                    user_id=user_id,
                    session_id=session_id,
                    response_id=response_id,
                    query=query,
                    intent=intent,
                    response_content=generated_response.content,
                    recommendations=[{"artist": r.artist, "track": r.track, "explanation": r.explanation} for r in (recommendations or [])],
                    context=context,
                    memory=memory,
                    confidence=generated_response.confidence
                )
            
            return generated_response
            
        except Exception as e:
            logger.error(
                "Response generation failed",
                query=query,
                error=str(e)
            )
            # Return fallback response
            return GeneratedResponse(
                content="I apologize, but I encountered an error generating a response. Please try again.",
                recommendations=recommendations or [],
                intent=intent,
                confidence=0.0
            )
    
    async def _generate_with_model(
        self,
        prompt: str,
        model: str
    ) -> Optional[str]:
        """
        Generate response using a specific model.
        
        Args:
            prompt: The formatted prompt
            model: The Groq model to use
            
        Returns:
            Generated response text or None on failure
        """
        try:
            response = await asyncio.to_thread(
                self.groq.chat.completions.create,
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(
                "Model generation failed",
                model=model,
                error=str(e)
            )
            return None


class MockResponseGenerator:
    """Mock implementation for testing without Groq API."""
    
    def __init__(self):
        self.storage = MockResponseStorage()
    
    async def generate(
        self,
        query: str,
        intent: str,
        context: Dict[str, Any],
        recommendations: Optional[List[Recommendation]] = None,
        memory: Optional[Dict[str, Any]] = None,
        review_insights: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> GeneratedResponse:
        """Mock response generation based on intent."""
        
        responses = {
            "DISCOVER_NEW_ARTISTS": "I'd love to help you discover some new artists! Based on your preferences, I can suggest some hidden gems that might surprise you.",
            "MOOD_BASED": f"I understand you're feeling {context.get('current_mood', 'a certain way')}. Let me find some music that matches that mood.",
            "ACTIVITY_BASED": f"Perfect! I can help you find great music for {context.get('current_goal', 'your activity')}.",
            "GENRE_EXPLORATION": "Genre exploration is a great way to discover new music! What genres are you curious about?",
            "ARTIST_EXPLORATION": "I can help you explore artists similar to your favorites. Let me find some great matches.",
            "ESCAPE_REPETITIVE": "I totally understand - it's easy to get stuck in a music rut. Let me help you break out of your usual patterns with some fresh recommendations.",
            "INSTRUMENTAL_MUSIC": "Instrumental music can be perfect for focus and relaxation. Let me find some great instrumental tracks for you.",
            "CODING_MUSIC": "Coding music should help you stay in the flow state. I'll find some tracks that are great for programming.",
            "WORKOUT_MUSIC": "High-energy music is essential for a good workout! Let me find some tracks to keep you motivated.",
            "RELAXATION_MUSIC": "Relaxation music can help you unwind. Let me find some calming tracks for you.",
            "CLARIFICATION": "I'd be happy to clarify! Could you tell me more about what you're looking for?",
            "FEEDBACK": "Thank you for your feedback! I'll use that to improve my recommendations.",
            "GENERAL_CHAT": "Hello! I'm your AI music discovery assistant. How can I help you find great music today?"
        }
        
        response_text = responses.get(intent, responses["GENERAL_CHAT"])
        
        # Add conversational context based on memory
        if memory and memory.get("recently_discussed_genres"):
            genres = memory.get("recently_discussed_genres", [])[:2]
            if genres:
                response_text = f"I noticed you've been exploring {', '.join(genres)} recently. {response_text}"
        
        # Add recommendations if provided
        if recommendations:
            response_text += " Here are some recommendations for you:"
            for rec in recommendations[:3]:
                response_text += f" {rec.artist} - {rec.explanation}"
        
        generated_response = GeneratedResponse(
            content=response_text,
            recommendations=recommendations or [],
            intent=intent,
            confidence=0.75
        )
        
        # Store response if user_id and session_id provided
        if user_id and session_id:
            response_id = f"resp_{user_id}_{session_id}_{int(asyncio.get_event_loop().time())}"
            self.storage.store_response(
                user_id=user_id,
                session_id=session_id,
                response_id=response_id,
                query=query,
                intent=intent,
                response_content=generated_response.content,
                recommendations=[{"artist": r.artist, "track": r.track, "explanation": r.explanation} for r in (recommendations or [])],
                context=context,
                memory=memory,
                confidence=generated_response.confidence
            )
        
        return generated_response
