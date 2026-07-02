"""Integration tests for Phase 1: AI Conversation Engine"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add phase1 to path
PHASE1_PATH = Path(__file__).parent.parent / "phase1-ai-conversation-engine"
sys.path.insert(0, str(PHASE1_PATH))

from intent_recognition.intent_recognizer import IntentRecognizer
from query_parser.query_parser import QueryParser
from response_generator.response_generator import ResponseGenerator
from context_manager.context_manager import ContextManager
from prompt_builder.prompt_builder import PromptBuilder


@pytest.mark.phase1
@pytest.mark.integration
class TestIntentRecognition:
    """Test intent recognition integration"""

    @pytest.fixture
    def intent_recognizer(self):
        """Create IntentRecognizer instance"""
        return IntentRecognizer()

    @pytest.mark.asyncio
    async def test_recognize_music_recommendation_intent(self, intent_recognizer):
        """Test recognizing music recommendation intent"""
        query = "I want some energetic music for coding"
        intent, confidence = intent_recognizer.recognize(query)
        
        assert intent in ["music_recommendation", "discovery", "recommendation"]
        assert confidence > 0.5
        assert confidence <= 1.0

    @pytest.mark.asyncio
    async def test_recognize_trending_query_intent(self, intent_recognizer):
        """Test recognizing trending query intent"""
        query = "What's trending in electronic music?"
        intent, confidence = intent_recognizer.recognize(query)
        
        assert intent in ["trending_query", "trending", "discovery"]
        assert confidence > 0.5

    @pytest.mark.asyncio
    async def test_recognize_explanation_intent(self, intent_recognizer):
        """Test recognizing explanation intent"""
        query = "Why did you recommend this song?"
        intent, confidence = intent_recognizer.recognize(query)
        
        assert intent in ["explanation", "why", "reasoning"]
        assert confidence > 0.5

    @pytest.mark.asyncio
    async def test_recognize_artist_query_intent(self, intent_recognizer):
        """Test recognizing artist query intent"""
        query = "Tell me about Daft Punk"
        intent, confidence = intent_recognizer.recognize(query)
        
        assert intent in ["artist_query", "artist_info", "artist"]
        assert confidence > 0.5

    @pytest.mark.asyncio
    async def test_recognize_genre_query_intent(self, intent_recognizer):
        """Test recognizing genre query intent"""
        query = "What is synthwave music?"
        intent, confidence = intent_recognizer.recognize(query)
        
        assert intent in ["genre_query", "genre_info", "genre"]
        assert confidence > 0.5

    @pytest.mark.asyncio
    async def test_recognize_low_confidence_query(self, intent_recognizer):
        """Test handling of low confidence queries"""
        query = "Hello"
        intent, confidence = intent_recognizer.recognize(query)
        
        assert confidence < 0.5
        assert intent in ["greeting", "unknown", "general"]


@pytest.mark.phase1
@pytest.mark.integration
class TestQueryParsing:
    """Test query parsing integration"""

    @pytest.fixture
    def query_parser(self):
        """Create QueryParser instance"""
        return QueryParser()

    @pytest.mark.asyncio
    async def test_parse_mood_query(self, query_parser):
        """Test parsing mood from query"""
        query = "I want energetic music"
        parsed = query_parser.parse(query)
        
        assert parsed.mood == "energetic"
        assert parsed.activity is None or parsed.activity == ""

    @pytest.mark.asyncio
    async def test_parse_activity_query(self, query_parser):
        """Test parsing activity from query"""
        query = "Music for coding"
        parsed = query_parser.parse(query)
        
        assert parsed.activity == "coding"
        assert parsed.mood is None or parsed.mood == ""

    @pytest.mark.asyncio
    async def test_parse_genre_query(self, query_parser):
        """Test parsing genres from query"""
        query = "I like electronic and indie music"
        parsed = query_parser.parse(query)
        
        assert "electronic" in parsed.genres or "electronic" in str(parsed.genres)
        assert "indie" in parsed.genres or "indie" in str(parsed.genres)

    @pytest.mark.asyncio
    async def test_parse_complex_query(self, query_parser):
        """Test parsing complex query with multiple parameters"""
        query = "I want energetic electronic music for coding"
        parsed = query_parser.parse(query)
        
        assert parsed.mood == "energetic"
        assert parsed.activity == "coding"
        assert "electronic" in parsed.genres or "electronic" in str(parsed.genres)

    @pytest.mark.asyncio
    async def test_parse_energy_level(self, query_parser):
        """Test parsing energy level from query"""
        query = "I want high energy music"
        parsed = query_parser.parse(query)
        
        assert parsed.energy_level == "high" or parsed.energy_level > 0.7

    @pytest.mark.asyncio
    async def test_parse_popularity_filter(self, query_parser):
        """Test parsing popularity filter from query"""
        query = "Show me popular songs"
        parsed = query_parser.parse(query)
        
        assert parsed.popularity_filter == "popular" or parsed.popularity_filter == "high"


@pytest.mark.phase1
@pytest.mark.integration
class TestResponseGeneration:
    """Test response generation integration"""

    @pytest.fixture
    def response_generator(self):
        """Create ResponseGenerator instance"""
        return ResponseGenerator()

    @pytest.mark.asyncio
    async def test_generate_music_recommendation_response(self, response_generator):
        """Test generating response for music recommendation"""
        query = "I want energetic music for coding"
        intent = "music_recommendation"
        recommendations = [
            {
                "track": {"name": "Test Song", "artist_name": "Test Artist"},
                "confidence": 0.85,
                "explanation": "Matches your energetic mood"
            }
        ]
        explanations = ["This track is high energy"]
        context = {"mood": "energetic", "activity": "coding"}
        
        response = response_generator.generate(
            query, intent, recommendations, explanations, context
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "energetic" in response.lower() or "coding" in response.lower()

    @pytest.mark.asyncio
    async def test_generate_trending_response(self, response_generator):
        """Test generating response for trending query"""
        query = "What's trending?"
        intent = "trending_query"
        recommendations = []
        explanations = []
        context = {}
        
        response = response_generator.generate(
            query, intent, recommendations, explanations, context
        )
        
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_explanation_response(self, response_generator):
        """Test generating explanation response"""
        query = "Why this song?"
        intent = "explanation"
        recommendations = []
        explanations = ["Based on your mood preference"]
        context = {"previous_recommendation": "Test Song"}
        
        response = response_generator.generate(
            query, intent, recommendations, explanations, context
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "mood" in response.lower() or "preference" in response.lower()


@pytest.mark.phase1
@pytest.mark.integration
class TestContextManagement:
    """Test context management integration"""

    @pytest.fixture
    def context_manager(self):
        """Create ContextManager instance"""
        return ContextManager()

    @pytest.mark.asyncio
    async def test_add_conversation_turn(self, context_manager):
        """Test adding conversation turn to context"""
        user_id = "test_user"
        session_id = "test_session"
        query = "I want energetic music"
        response = "Here are some energetic tracks"
        
        await context_manager.add_turn(user_id, session_id, query, response)
        
        context = await context_manager.get_context(user_id, session_id)
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_get_conversation_context(self, context_manager):
        """Test retrieving conversation context"""
        user_id = "test_user"
        session_id = "test_session"
        
        # Add some turns first
        await context_manager.add_turn(user_id, session_id, "Query 1", "Response 1")
        await context_manager.add_turn(user_id, session_id, "Query 2", "Response 2")
        
        context = await context_manager.get_context(user_id, session_id)
        
        assert len(context) >= 2
        assert context[-1]["query"] == "Query 2"
        assert context[-1]["response"] == "Response 2"

    @pytest.mark.asyncio
    async def test_clear_conversation_context(self, context_manager):
        """Test clearing conversation context"""
        user_id = "test_user"
        session_id = "test_session"
        
        # Add turns
        await context_manager.add_turn(user_id, session_id, "Query", "Response")
        
        # Clear context
        await context_manager.clear_context(user_id, session_id)
        
        context = await context_manager.get_context(user_id, session_id)
        assert len(context) == 0

    @pytest.mark.asyncio
    async def test_context_limit(self, context_manager):
        """Test context limit enforcement"""
        user_id = "test_user"
        session_id = "test_session"
        
        # Add many turns
        for i in range(20):
            await context_manager.add_turn(user_id, session_id, f"Query {i}", f"Response {i}")
        
        context = await context_manager.get_context(user_id, session_id)
        
        # Should be limited to last N turns (typically 10)
        assert len(context) <= 10


@pytest.mark.phase1
@pytest.mark.integration
class TestPromptBuilder:
    """Test prompt builder integration"""

    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance"""
        return PromptBuilder()

    def test_build_intent_prompt(self, prompt_builder):
        """Test building intent recognition prompt"""
        query = "I want energetic music for coding"
        
        prompt = prompt_builder.build_intent_prompt(query)
        
        assert isinstance(prompt, str)
        assert query in prompt
        assert len(prompt) > 0

    def test_build_parser_prompt(self, prompt_builder):
        """Test building query parser prompt"""
        query = "I want energetic electronic music"
        
        prompt = prompt_builder.build_parser_prompt(query)
        
        assert isinstance(prompt, str)
        assert query in prompt
        assert len(prompt) > 0

    def test_build_response_prompt(self, prompt_builder):
        """Test building response generation prompt"""
        query = "I want energetic music"
        intent = "music_recommendation"
        recommendations = [{"track": {"name": "Test"}}]
        context = {"mood": "energetic"}
        
        prompt = prompt_builder.build_response_prompt(
            query, intent, recommendations, context
        )
        
        assert isinstance(prompt, str)
        assert query in prompt
        assert intent in prompt
        assert len(prompt) > 0

    def test_build_explanation_prompt(self, prompt_builder):
        """Test building explanation prompt"""
        recommendation_id = "rec_001"
        context = {"user_preferences": {"mood": "energetic"}}
        
        prompt = prompt_builder.build_explanation_prompt(recommendation_id, context)
        
        assert isinstance(prompt, str)
        assert recommendation_id in prompt
        assert len(prompt) > 0


@pytest.mark.phase1
@pytest.mark.integration
@pytest.mark.slow
class TestPhase1EndToEnd:
    """End-to-end tests for Phase 1"""

    @pytest.fixture
    def conversation_components(self):
        """Create all Phase 1 components"""
        return {
            "intent_recognizer": IntentRecognizer(),
            "query_parser": QueryParser(),
            "response_generator": ResponseGenerator(),
            "context_manager": ContextManager(),
            "prompt_builder": PromptBuilder()
        }

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, conversation_components):
        """Test complete conversation flow"""
        user_id = "test_user"
        session_id = "test_session"
        
        # Step 1: User query
        query = "I want energetic electronic music for coding"
        
        # Step 2: Recognize intent
        intent, confidence = conversation_components["intent_recognizer"].recognize(query)
        assert confidence > 0.5
        
        # Step 3: Parse query
        parsed = conversation_components["query_parser"].parse(query)
        assert parsed.mood == "energetic"
        
        # Step 4: Generate response
        response = conversation_components["response_generator"].generate(
            query, intent, [], [], {"mood": parsed.mood, "activity": parsed.activity}
        )
        assert len(response) > 0
        
        # Step 5: Add to context
        await conversation_components["context_manager"].add_turn(
            user_id, session_id, query, response
        )
        
        # Step 6: Verify context
        context = await conversation_components["context_manager"].get_context(
            user_id, session_id
        )
        assert len(context) > 0
        assert context[0]["query"] == query

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, conversation_components):
        """Test multi-turn conversation with context"""
        user_id = "test_user"
        session_id = "test_session"
        
        queries = [
            "I want energetic music",
            "What about something more chill?",
            "Show me indie rock recommendations"
        ]
        
        for query in queries:
            intent, _ = conversation_components["intent_recognizer"].recognize(query)
            parsed = conversation_components["query_parser"].parse(query)
            response = conversation_components["response_generator"].generate(
                query, intent, [], [], {"mood": parsed.mood}
            )
            await conversation_components["context_manager"].add_turn(
                user_id, session_id, query, response
            )
        
        context = await conversation_components["context_manager"].get_context(
            user_id, session_id
        )
        assert len(context) == 3

    @pytest.mark.asyncio
    async def test_context_aware_response(self, conversation_components):
        """Test that responses use conversation context"""
        user_id = "test_user"
        session_id = "test_session"
        
        # First query
        query1 = "I like electronic music"
        await conversation_components["context_manager"].add_turn(
            user_id, session_id, query1, "Noted your preference for electronic music"
        )
        
        # Second query that references previous context
        query2 = "What about rock?"
        intent, _ = conversation_components["intent_recognizer"].recognize(query2)
        context = await conversation_components["context_manager"].get_context(user_id, session_id)
        
        response = conversation_components["response_generator"].generate(
            query2, intent, [], [], {"conversation_history": context}
        )
        
        # Response should acknowledge the context
        assert len(response) > 0
