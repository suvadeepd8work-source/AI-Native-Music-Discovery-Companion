"""
AI Prompt Builder for Phase 1: AI Conversation Engine.
Generates optimized prompts for Groq by combining user query, context, memory, review insights, and music metadata.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from .prompt_schemas import PromptContext, PromptMemory, PromptReviewInsights, PromptMusicMetadata


logger = structlog.get_logger(__name__)


class PromptBuilder:
    """
    Builder for generating optimized prompts for Groq.
    Combines user query, conversation context, memory, review insights, and music metadata.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_context_length = self.config.get("max_context_length", 4000)
        self.max_memory_items = self.config.get("max_memory_items", 10)
        self.max_review_insights = self.config.get("max_review_insights", 5)
        self.max_music_metadata = self.config.get("max_music_metadata", 3)
    
    def build_prompt(
        self,
        user_query: str,
        context: PromptContext,
        memory: Optional[PromptMemory] = None,
        review_insights: Optional[PromptReviewInsights] = None,
        music_metadata: Optional[PromptMusicMetadata] = None,
        intent: Optional[str] = None
    ) -> str:
        """
        Build the final prompt for Groq.
        
        Args:
            user_query: The user's query
            context: Conversation context (intent, mood, activity, etc.)
            memory: Conversation memory (previous recommendations, history)
            review_insights: Review insights from Phase 2
            music_metadata: Music metadata for recommendations
            intent: Detected user intent (optional, overrides context.intent)
            
        Returns:
            Optimized prompt string for Groq
        """
        # Build prompt sections
        sections = []
        
        # System instruction
        sections.append(self._build_system_instruction())
        
        # User query
        sections.append(self._build_user_query_section(user_query))
        
        # Conversation context
        sections.append(self._build_context_section(context, intent))
        
        # Conversation memory
        if memory:
            sections.append(self._build_memory_section(memory))
        
        # Review insights
        if review_insights:
            sections.append(self._build_review_insights_section(review_insights))
        
        # Music metadata
        if music_metadata:
            sections.append(self._build_music_metadata_section(music_metadata))
        
        # Response format instruction
        sections.append(self._build_response_format_instruction())
        
        # Combine sections
        prompt = "\n\n".join(sections)
        
        # Truncate if too long
        if len(prompt) > self.max_context_length:
            prompt = self._truncate_prompt(prompt, self.max_context_length)
            logger.warning("Prompt truncated to fit context window", original_length=len(prompt))
        
        logger.info(
            "Built prompt",
            user_query_length=len(user_query),
            context_included=context is not None,
            memory_included=memory is not None,
            review_insights_included=review_insights is not None,
            music_metadata_included=music_metadata is not None,
            final_length=len(prompt)
        )
        
        return prompt
    
    def _build_system_instruction(self) -> str:
        """Build the system instruction section."""
        return """You are an AI music discovery assistant. Your goal is to help users discover new music that matches their preferences, mood, and context. Be conversational, helpful, and informative. Provide specific recommendations with explanations of why they match the user's request."""
    
    def _build_user_query_section(self, user_query: str) -> str:
        """Build the user query section."""
        return f"USER QUERY:\n{user_query}"
    
    def _build_context_section(self, context: PromptContext, intent: Optional[str] = None) -> str:
        """Build the conversation context section."""
        sections = ["CONVERSATION CONTEXT:"]
        
        # Intent
        detected_intent = intent or context.intent
        if detected_intent:
            sections.append(f"- User Intent: {detected_intent}")
        
        # Mood
        if context.mood:
            sections.append(f"- Current Mood: {context.mood}")
        
        # Activity
        if context.activity:
            sections.append(f"- Current Activity: {context.activity}")
        
        # Discovery goal
        if context.discovery_goal:
            sections.append(f"- Discovery Goal: {context.discovery_goal}")
        
        # Preferred genres
        if context.preferred_genres:
            genres_str = ", ".join(context.preferred_genres[:5])
            sections.append(f"- Preferred Genres: {genres_str}")
        
        # Preferred artists
        if context.preferred_artists:
            artists_str = ", ".join(context.preferred_artists[:5])
            sections.append(f"- Preferred Artists: {artists_str}")
        
        # Energy level
        if context.energy_level:
            sections.append(f"- Energy Level: {context.energy_level}")
        
        # Popularity filter
        if context.popularity_filter:
            sections.append(f"- Popularity Preference: {context.popularity_filter}")
        
        return "\n".join(sections)
    
    def _build_memory_section(self, memory: PromptMemory) -> str:
        """Build the conversation memory section."""
        sections = ["CONVERSATION MEMORY:"]
        
        # Previously recommended songs
        if memory.previously_recommended_songs:
            songs = memory.previously_recommended_songs[:self.max_memory_items]
            sections.append(f"- Previously Recommended Songs ({len(songs)}):")
            for song in songs:
                sections.append(f"  * {song}")
        
        # Previously recommended artists
        if memory.previously_recommended_artists:
            artists = memory.previously_recommended_artists[:self.max_memory_items]
            sections.append(f"- Previously Recommended Artists ({len(artists)}):")
            for artist in artists:
                sections.append(f"  * {artist}")
        
        # Discovery history
        if memory.discovery_history:
            discoveries = memory.discovery_history[:self.max_memory_items]
            sections.append(f"- Discovery History ({len(discoveries)}):")
            for discovery in discoveries:
                sections.append(f"  * {discovery}")
        
        # Recently discussed genres
        if memory.recently_discussed_genres:
            genres = memory.recently_discussed_genres[:self.max_memory_items]
            sections.append(f"- Recently Discussed Genres: {', '.join(genres)}")
        
        # User segment
        if memory.user_segment:
            sections.append(f"- User Segment: {memory.user_segment}")
        
        return "\n".join(sections)
    
    def _build_review_insights_section(self, review_insights: PromptReviewInsights) -> str:
        """Build the review insights section."""
        sections = ["REVIEW INSIGHTS:"]
        
        # Pain points
        if review_insights.pain_points:
            pain_points = review_insights.pain_points[:self.max_review_insights]
            sections.append(f"- Identified Pain Points ({len(pain_points)}):")
            for pain_point in pain_points:
                sections.append(f"  * {pain_point}")
        
        # Theme clusters
        if review_insights.theme_clusters:
            clusters = review_insights.theme_clusters[:self.max_review_insights]
            sections.append(f"- Theme Clusters ({len(clusters)}):")
            for cluster in clusters:
                sections.append(f"  * {cluster}")
        
        # Product insights
        if review_insights.product_insights:
            insights = review_insights.product_insights[:self.max_review_insights]
            sections.append(f"- Product Insights ({len(insights)}):")
            for insight in insights:
                sections.append(f"  * {insight}")
        
        # Executive summary
        if review_insights.executive_summary:
            sections.append(f"- Executive Summary: {review_insights.executive_summary}")
        
        return "\n".join(sections)
    
    def _build_music_metadata_section(self, music_metadata: PromptMusicMetadata) -> str:
        """Build the music metadata section."""
        sections = ["MUSIC METADATA:"]
        
        # Recommended tracks
        if music_metadata.recommended_tracks:
            tracks = music_metadata.recommended_tracks[:self.max_music_metadata]
            sections.append(f"- Recommended Tracks ({len(tracks)}):")
            for track in tracks:
                sections.append(f"  * {track}")
        
        # Recommended artists
        if music_metadata.recommended_artists:
            artists = music_metadata.recommended_artists[:self.max_music_metadata]
            sections.append(f"- Recommended Artists ({len(artists)}):")
            for artist in artists:
                sections.append(f"  * {artist}")
        
        # Genre information
        if music_metadata.genre_info:
            sections.append(f"- Genre Information: {music_metadata.genre_info}")
        
        # Audio features
        if music_metadata.audio_features:
            sections.append(f"- Audio Features: {music_metadata.audio_features}")
        
        return "\n".join(sections)
    
    def _build_response_format_instruction(self) -> str:
        """Build the response format instruction section."""
        return """RESPONSE FORMAT:
Provide a conversational response that:
1. Acknowledges the user's query and context
2. Explains the recommendations and why they match
3. Highlights interesting aspects of the recommended music
4. Encourages further exploration
5. Is concise but informative (2-4 sentences per recommendation)"""
    
    def _truncate_prompt(self, prompt: str, max_length: int) -> str:
        """Truncate prompt to fit within max length while preserving structure."""
        # Simple truncation - in production, use smarter section-based truncation
        if len(prompt) <= max_length:
            return prompt
        
        # Truncate from the middle, keeping start and end
        keep_start = max_length // 2 - 100
        keep_end = max_length // 2 - 100
        
        truncated = prompt[:keep_start] + "\n\n... [Context truncated due to length] ...\n\n" + prompt[-keep_end:]
        
        return truncated
    
    def build_intent_prompt(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Build a prompt for intent recognition.
        
        Args:
            user_query: The user's query
            conversation_history: Optional conversation history for context
            
        Returns:
            Prompt for intent recognition
        """
        sections = [
            "Identify the user's intent from the following query.",
            "",
            "Possible intents:",
            "- discovery: User wants to discover new music",
            "- familiar: User wants familiar music they know",
            "- mood: User wants music matching a specific mood",
            "- activity: User wants music for a specific activity",
            "- genre: User wants music from a specific genre",
            "- artist: User wants music from a specific artist",
            "- general: General conversation about music",
            "",
            f"USER QUERY: {user_query}"
        ]
        
        if conversation_history:
            sections.append("")
            sections.append("CONVERSATION HISTORY:")
            for turn in conversation_history[-3:]:  # Last 3 turns
                sections.append(f"User: {turn.get('user', '')}")
                sections.append(f"Assistant: {turn.get('assistant', '')}")
        
        sections.append("")
        sections.append("Respond with the intent only, in format: intent|confidence")
        
        return "\n".join(sections)
    
    def build_combined_intent_parse_prompt(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Build a combined prompt for intent recognition and query parsing in a single call.
        
        Args:
            user_query: The user's query
            conversation_history: Optional conversation history for context
            
        Returns:
            Combined prompt for both intent recognition and query parsing
        """
        sections = [
            "Analyze the user's query to determine their intent and extract structured parameters.",
            "",
            "Possible intents:",
            "- DISCOVER_NEW_ARTISTS: User wants to discover new music/hidden gems",
            "- MOOD_BASED: User wants music matching a specific mood",
            "- CODING_MUSIC: User wants music for coding/programming",
            "- WORKOUT_MUSIC: User wants music for workout/exercise",
            "- RELAXATION_MUSIC: User wants music for relaxation/sleep",
            "- INSTRUMENTAL_MUSIC: User wants instrumental music",
            "- GENRE_EXPLORATION: User wants to explore specific genres",
            "- ARTIST_EXPLORATION: User wants music similar to specific artists",
            "- ESCAPE_REPETITIVE: User wants to break out of repetitive patterns",
            "- CLARIFICATION: User is asking for clarification",
            "- FEEDBACK: User is providing feedback",
            "- GENERAL_CHAT: General conversation",
            "",
            f"USER QUERY: {user_query}"
        ]
        
        if conversation_history:
            sections.append("")
            sections.append("CONVERSATION HISTORY (last 3 turns):")
            for turn in conversation_history[-3:]:
                sections.append(f"User: {turn.get('user', '')}")
                sections.append(f"Assistant: {turn.get('assistant', '')}")
        
        sections.append("")
        sections.append("Extract the following parameters if present:")
        sections.append("- mood: The mood the user wants (energetic, calm, melancholic, upbeat, happy, sad, focus, romantic, aggressive)")
        sections.append("- activity: The activity the user is doing (coding, workout, studying, relaxation, sleep, focus)")
        sections.append("- genres: List of genres mentioned")
        sections.append("- artists: List of artists mentioned")
        sections.append("- energy_level: high, medium, or low")
        sections.append("- popularity_filter: mainstream, indie, or underground")
        sections.append("- discovery_preference: novel, familiar, or balanced")
        sections.append("- instrumental_only: true if user wants instrumental music")
        sections.append("")
        sections.append("Respond with a JSON object containing:")
        sections.append("- intent: the detected intent")
        sections.append("- confidence: confidence score (0.0-1.0)")
        sections.append("- reasoning: brief reasoning for the intent")
        sections.append("- mood: extracted mood (or null)")
        sections.append("- goal: extracted activity (or null)")
        sections.append("- genres: list of genres (or empty array)")
        sections.append("- artists: list of artists (or empty array)")
        sections.append("- discovery_preference: preference (or null)")
        sections.append("- popularity_filter: filter (or null)")
        sections.append("- instrumental_only: boolean")
        sections.append("- energy_level: energy level (or null)")
        sections.append("- keywords: list of keywords mentioned (or empty array)")
        
        return "\n".join(sections)

    def build_parser_prompt(
        self,
        user_query: str,
        intent: str
    ) -> str:
        """
        Build a prompt for query parsing.
        
        Args:
            user_query: The user's query
            intent: Detected user intent
            
        Returns:
            Prompt for query parsing
        """
        sections = [
            "Extract structured parameters from the user's query.",
            "",
            f"USER INTENT: {intent}",
            f"USER QUERY: {user_query}",
            "",
            "Extract the following parameters if present:",
            "- mood: The mood the user wants (energetic, calm, melancholic, upbeat, etc.)",
            "- activity: The activity the user is doing (workout, studying, social, sleep, etc.)",
            "- genres: List of genres mentioned",
            "- artists: List of artists mentioned",
            "- energy_level: high, medium, or low",
            "- popularity_filter: popular, niche, or all",
            "- discovery_preference: novel, familiar, or balanced",
            "",
            "Respond with a JSON object containing the extracted parameters."
        ]
        
        return "\n".join(sections)


class MockPromptBuilder:
    """Mock implementation for testing."""
    
    def __init__(self):
        pass
    
    def build_prompt(
        self,
        user_query: str,
        context: Optional[PromptContext] = None,
        memory: Optional[PromptMemory] = None,
        review_insights: Optional[PromptReviewInsights] = None,
        music_metadata: Optional[PromptMusicMetadata] = None,
        intent: Optional[str] = None
    ) -> str:
        """Build a mock prompt."""
        sections = [f"USER QUERY: {user_query}"]
        
        if context:
            sections.append(f"INTENT: {context.intent}")
            if context.mood:
                sections.append(f"MOOD: {context.mood}")
        
        return "\n".join(sections)
    
    def build_intent_prompt(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build a mock intent prompt."""
        return f"Detect intent for: {user_query}"
    
    def build_parser_prompt(
        self,
        user_query: str,
        intent: str
    ) -> str:
        """Build a mock parser prompt."""
        return f"Parse query with intent {intent}: {user_query}"
