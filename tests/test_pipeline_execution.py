"""Integration tests for Pipeline Execution"""

import pytest
import asyncio
import sys
from pathlib import Path
import time

# Add phases to path
PHASE1_PATH = Path(__file__).parent.parent / "phase1-ai-conversation-engine"
PHASE2_PATH = Path(__file__).parent.parent / "phase2-music-recommendation-engine"
PHASE3_PATH = Path(__file__).parent.parent / "phase3-ai-orchestration"
sys.path.insert(0, str(PHASE1_PATH))
sys.path.insert(0, str(PHASE2_PATH))
sys.path.insert(0, str(PHASE3_PATH))

from intent_recognition.intent_recognizer import IntentRecognizer
from query_parser.query_parser import QueryParser
from response_generator.response_generator import ResponseGenerator
from context_manager.context_manager import ContextManager
from mood_activity_matching.mood_activity_matcher import MoodActivityMatcher
from genre_exploration.genre_explorer import GenreExplorer
from similarity_search.similarity_searcher import SimilaritySearcher
from review_based_discovery.review_discovery import ReviewDiscoveryEngine
from habit_breaking.habit_breaker import HabitBreaker
from recommendation_fusion.recommendation_fuser import RecommendationFuser
from explanation_generator.explanation_generator import ExplanationGenerator
from orchestration_controller.orchestration_controller import OrchestrationController
from fallback_manager.fallback_manager import FallbackManager
from performance_monitor.performance_monitor import PerformanceMonitor


@pytest.mark.pipeline
@pytest.mark.integration
class TestConversationPipeline:
    """Test conversation pipeline execution"""

    @pytest.fixture
    def pipeline_components(self):
        """Create all pipeline components"""
        return {
            "intent_recognizer": IntentRecognizer(),
            "query_parser": QueryParser(),
            "response_generator": ResponseGenerator(),
            "context_manager": ContextManager()
        }

    @pytest.mark.asyncio
    async def test_conversation_pipeline_single_turn(self, pipeline_components):
        """Test single-turn conversation pipeline"""
        user_id = "test_user"
        session_id = "test_session"
        query = "I want energetic music for coding"
        
        # Step 1: Recognize intent
        intent, confidence = pipeline_components["intent_recognizer"].recognize(query)
        assert confidence > 0.5
        
        # Step 2: Parse query
        parsed = pipeline_components["query_parser"].parse(query)
        assert parsed is not None
        
        # Step 3: Generate response
        response = pipeline_components["response_generator"].generate(
            query, intent, [], [], {"mood": getattr(parsed, "mood", "")}
        )
        assert len(response) > 0
        
        # Step 4: Add to context
        await pipeline_components["context_manager"].add_turn(
            user_id, session_id, query, response
        )
        
        # Verify context
        context = await pipeline_components["context_manager"].get_context(
            user_id, session_id
        )
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_conversation_pipeline_multi_turn(self, pipeline_components):
        """Test multi-turn conversation pipeline"""
        user_id = "test_user"
        session_id = "test_session"
        
        queries = [
            "I want energetic music",
            "What about something more chill?",
            "Show me indie rock recommendations"
        ]
        
        for i, query in enumerate(queries):
            # Execute pipeline steps
            intent, _ = pipeline_components["intent_recognizer"].recognize(query)
            parsed = pipeline_components["query_parser"].parse(query)
            response = pipeline_components["response_generator"].generate(
                query, intent, [], [], {"mood": getattr(parsed, "mood", "")}
            )
            await pipeline_components["context_manager"].add_turn(
                user_id, session_id, query, response
            )
        
        # Verify all turns in context
        context = await pipeline_components["context_manager"].get_context(
            user_id, session_id
        )
        assert len(context) == 3

    @pytest.mark.asyncio
    async def test_conversation_pipeline_with_context(self, pipeline_components):
        """Test conversation pipeline with context awareness"""
        user_id = "test_user"
        session_id = "test_session"
        
        # First query
        query1 = "I like electronic music"
        intent1, _ = pipeline_components["intent_recognizer"].recognize(query1)
        response1 = pipeline_components["response_generator"].generate(
            query1, intent1, [], [], {}
        )
        await pipeline_components["context_manager"].add_turn(
            user_id, session_id, query1, response1
        )
        
        # Second query with context
        query2 = "What about rock?"
        context = await pipeline_components["context_manager"].get_context(user_id, session_id)
        intent2, _ = pipeline_components["intent_recognizer"].recognize(query2)
        response2 = pipeline_components["response_generator"].generate(
            query2, intent2, [], [], {"conversation_history": context}
        )
        
        assert len(response2) > 0


@pytest.mark.pipeline
@pytest.mark.integration
class TestRecommendationPipeline:
    """Test recommendation pipeline execution"""

    @pytest.fixture
    def recommendation_pipeline(self):
        """Create recommendation pipeline components"""
        return {
            "mood_matcher": MoodActivityMatcher(),
            "genre_explorer": GenreExplorer(),
            "similarity_searcher": SimilaritySearcher(),
            "review_discovery": ReviewDiscoveryEngine(),
            "recommendation_fuser": RecommendationFuser(),
            "explanation_generator": ExplanationGenerator()
        }

    @pytest.mark.asyncio
    async def test_recommendation_pipeline_mood_based(self, recommendation_pipeline):
        """Test mood-based recommendation pipeline"""
        mood = "energetic"
        activity = "coding"
        
        # Step 1: Match mood and activity
        characteristics = recommendation_pipeline["mood_matcher"].match_combined(
            mood, activity
        )
        assert characteristics is not None
        
        # Step 2: Get genre recommendations
        genre_recs = recommendation_pipeline["genre_explorer"].explore_genre("electronic")
        
        # Step 3: Fuse recommendations
        if genre_recs:
            fused = recommendation_pipeline["recommendation_fuser"].fuse_recommendations(
                [genre_recs[:5]], limit=5
            )
            assert isinstance(fused, list)
        
        # Step 4: Generate explanation
        if genre_recs:
            explanation = recommendation_pipeline["explanation_generator"].generate_mood_explanation(
                genre_recs[0], mood
            )
            assert len(explanation) > 0

    @pytest.mark.asyncio
    async def test_recommendation_pipeline_multi_source(self, recommendation_pipeline):
        """Test multi-source recommendation pipeline"""
        # Get recommendations from multiple sources
        mood_recs = [{"track_id": "m1", "confidence": 0.8}]
        similarity_recs = [{"track_id": "s1", "confidence": 0.7}]
        review_recs = [{"track_id": "r1", "confidence": 0.9}]
        
        # Fuse all sources
        fused = recommendation_pipeline["recommendation_fuser"].fuse_recommendations(
            [mood_recs, similarity_recs, review_recs], limit=10
        )
        
        assert isinstance(fused, list)
        assert len(fused) <= 10
        
        # Verify deduplication
        track_ids = [r.get("track_id") for r in fused]
        assert len(track_ids) == len(set(track_ids))

    @pytest.mark.asyncio
    async def test_recommendation_pipeline_with_explanation(self, recommendation_pipeline):
        """Test recommendation pipeline with explanation generation"""
        recommendation = {
            "track": {"name": "Test Song", "artist_name": "Test Artist"},
            "confidence": 0.85
        }
        factors = {
            "mood": "energetic",
            "similarity": 0.9,
            "review_sentiment": "positive"
        }
        
        # Generate comprehensive explanation
        explanation = recommendation_pipeline["explanation_generator"].generate_comprehensive_explanation(
            recommendation, factors
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert len(explanation.split()) > 10


@pytest.mark.pipeline
@pytest.mark.integration
class TestOrchestrationPipeline:
    """Test orchestration pipeline execution"""

    @pytest.fixture
    def orchestration_pipeline(self):
        """Create orchestration pipeline components"""
        return {
            "orchestration_controller": OrchestrationController(),
            "fallback_manager": FallbackManager(),
            "performance_monitor": PerformanceMonitor()
        }

    @pytest.mark.asyncio
    async def test_orchestration_pipeline_success(self, orchestration_pipeline):
        """Test successful orchestration pipeline"""
        query = "I want energetic music for coding"
        user_id = "test_user"
        session_id = "test_session"
        
        # Track performance
        start_time = time.time()
        
        # Process request
        result = await orchestration_pipeline["orchestration_controller"].process_request(
            query, user_id, session_id
        )
        
        # Track latency
        latency = (time.time() - start_time) * 1000
        orchestration_pipeline["performance_monitor"].track_latency(
            "orchestration", latency
        )
        
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_orchestration_pipeline_with_fallback(self, orchestration_pipeline):
        """Test orchestration pipeline with fallback"""
        query = "I want music recommendations"
        user_id = "test_user"
        session_id = "test_session"
        
        try:
            result = await orchestration_pipeline["orchestration_controller"].process_request(
                query, user_id, session_id
            )
        except Exception as e:
            # Use fallback
            result = orchestration_pipeline["fallback_manager"].handle_llm_failure(e, query)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_orchestration_pipeline_performance(self, orchestration_pipeline, performance_thresholds):
        """Test orchestration pipeline performance"""
        query = "I want energetic music"
        user_id = "test_user"
        session_id = "test_session"
        
        start_time = time.time()
        
        result = await orchestration_pipeline["orchestration_controller"].process_request(
            query, user_id, session_id
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        assert result is not None
        assert execution_time < performance_thresholds["pipeline_execution_time_ms"]


@pytest.mark.pipeline
@pytest.mark.integration
class TestEndToEndPipeline:
    """Test end-to-end pipeline execution across all phases"""

    @pytest.fixture
    def full_pipeline(self):
        """Create full pipeline components"""
        return {
            # Phase 1
            "intent_recognizer": IntentRecognizer(),
            "query_parser": QueryParser(),
            "response_generator": ResponseGenerator(),
            "context_manager": ContextManager(),
            # Phase 2
            "mood_matcher": MoodActivityMatcher(),
            "genre_explorer": GenreExplorer(),
            "similarity_searcher": SimilaritySearcher(),
            "review_discovery": ReviewDiscoveryEngine(),
            "recommendation_fuser": RecommendationFuser(),
            "explanation_generator": ExplanationGenerator(),
            # Phase 3
            "orchestration_controller": OrchestrationController(),
            "fallback_manager": FallbackManager(),
            "performance_monitor": PerformanceMonitor()
        }

    @pytest.mark.asyncio
    async def test_full_music_discovery_pipeline(self, full_pipeline):
        """Test complete music discovery pipeline"""
        user_id = "test_user"
        session_id = "test_session"
        query = "I want energetic electronic music for coding"
        
        # Phase 1: Conversation Processing
        intent, confidence = full_pipeline["intent_recognizer"].recognize(query)
        assert confidence > 0.5
        
        parsed = full_pipeline["query_parser"].parse(query)
        assert parsed is not None
        
        # Phase 2: Recommendation Generation
        mood = getattr(parsed, "mood", None) or parsed.get("mood", "")
        activity = getattr(parsed, "activity", None) or parsed.get("activity", "")
        
        characteristics = full_pipeline["mood_matcher"].match_combined(mood, activity)
        assert characteristics is not None
        
        genre_recs = full_pipeline["genre_explorer"].explore_genre("electronic")
        
        if genre_recs:
            fused = full_pipeline["recommendation_fuser"].fuse_recommendations(
                [genre_recs[:5]], limit=5
            )
            assert isinstance(fused, list)
            
            explanation = full_pipeline["explanation_generator"].generate_mood_explanation(
                genre_recs[0], mood
            )
            assert len(explanation) > 0
        
        # Phase 3: Response Generation
        response = full_pipeline["response_generator"].generate(
            query, intent, genre_recs[:3] if genre_recs else [], [], {"mood": mood}
        )
        assert len(response) > 0
        
        # Add to context
        await full_pipeline["context_manager"].add_turn(
            user_id, session_id, query, response
        )
        
        # Verify complete flow
        context = await full_pipeline["context_manager"].get_context(user_id, session_id)
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_with_explanation_request(self, full_pipeline):
        """Test full pipeline with explanation request"""
        user_id = "test_user"
        session_id = "test_session"
        
        # First request: Get recommendations
        query1 = "I want energetic music"
        intent1, _ = full_pipeline["intent_recognizer"].recognize(query1)
        parsed1 = full_pipeline["query_parser"].parse(query1)
        response1 = full_pipeline["response_generator"].generate(
            query1, intent1, [], [], {"mood": getattr(parsed1, "mood", "")}
        )
        await full_pipeline["context_manager"].add_turn(
            user_id, session_id, query1, response1
        )
        
        # Second request: Ask for explanation
        query2 = "Why did you recommend those songs?"
        intent2, _ = full_pipeline["intent_recognizer"].recognize(query2)
        context = await full_pipeline["context_manager"].get_context(user_id, session_id)
        
        response2 = full_pipeline["response_generator"].generate(
            query2, intent2, [], [], {"conversation_history": context}
        )
        
        assert len(response2) > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_error_recovery(self, full_pipeline):
        """Test full pipeline error recovery"""
        user_id = "test_user"
        session_id = "test_session"
        query = "I want music recommendations"
        
        try:
            # Attempt full pipeline
            intent, _ = full_pipeline["intent_recognizer"].recognize(query)
            parsed = full_pipeline["query_parser"].parse(query)
            response = full_pipeline["response_generator"].generate(
                query, intent, [], [], {}
            )
            assert len(response) > 0
        except Exception as e:
            # Use fallback
            fallback_response = full_pipeline["fallback_manager"].handle_llm_failure(e, query)
            assert fallback_response is not None

    @pytest.mark.asyncio
    async def test_full_pipeline_performance_tracking(self, full_pipeline, performance_thresholds):
        """Test full pipeline with performance tracking"""
        user_id = "test_user"
        session_id = "test_session"
        query = "I want energetic music"
        
        # Track overall pipeline time
        start_time = time.time()
        
        # Execute pipeline
        intent, _ = full_pipeline["intent_recognizer"].recognize(query)
        parsed = full_pipeline["query_parser"].parse(query)
        response = full_pipeline["response_generator"].generate(
            query, intent, [], [], {}
        )
        
        total_time = (time.time() - start_time) * 1000
        
        # Track individual components
        full_pipeline["performance_monitor"].track_latency("intent_recognition", 100)
        full_pipeline["performance_monitor"].track_latency("query_parsing", 50)
        full_pipeline["performance_monitor"].track_latency("response_generation", 200)
        
        # Get summary
        summary = full_pipeline["performance_monitor"].get_summary()
        assert summary is not None
        
        # Verify performance
        assert total_time < performance_thresholds["pipeline_execution_time_ms"]

    @pytest.mark.asyncio
    async def test_full_pipeline_multi_user(self, full_pipeline):
        """Test full pipeline with multiple users"""
        users = ["user_1", "user_2", "user_3"]
        
        for user_id in users:
            session_id = f"{user_id}_session"
            query = f"I want music for {user_id}"
            
            intent, _ = full_pipeline["intent_recognizer"].recognize(query)
            parsed = full_pipeline["query_parser"].parse(query)
            response = full_pipeline["response_generator"].generate(
                query, intent, [], [], {}
            )
            
            await full_pipeline["context_manager"].add_turn(
                user_id, session_id, query, response
            )
        
        # Verify each user has their own context
        for user_id in users:
            context = await full_pipeline["context_manager"].get_context(
                user_id, f"{user_id}_session"
            )
            assert len(context) > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_concurrent_requests(self, full_pipeline):
        """Test full pipeline with concurrent requests"""
        async def process_request(user_id):
            query = f"I want music for {user_id}"
            session_id = f"{user_id}_session"
            
            intent, _ = full_pipeline["intent_recognizer"].recognize(query)
            parsed = full_pipeline["query_parser"].parse(query)
            response = full_pipeline["response_generator"].generate(
                query, intent, [], [], {}
            )
            
            await full_pipeline["context_manager"].add_turn(
                user_id, session_id, query, response
            )
            
            return response
        
        # Process concurrent requests
        users = [f"user_{i}" for i in range(5)]
        responses = await asyncio.gather(*[
            process_request(user_id) for user_id in users
        ])
        
        # All should complete successfully
        assert len(responses) == 5
        assert all(len(r) > 0 for r in responses)


@pytest.mark.pipeline
@pytest.mark.integration
@pytest.mark.slow
class TestPipelineStressTests:
    """Stress tests for pipeline execution"""

    @pytest.fixture
    def pipeline_components(self):
        """Create pipeline components"""
        return {
            "intent_recognizer": IntentRecognizer(),
            "query_parser": QueryParser(),
            "response_generator": ResponseGenerator(),
            "context_manager": ContextManager()
        }

    @pytest.mark.asyncio
    async def test_pipeline_high_volume_requests(self, pipeline_components):
        """Test pipeline with high volume of requests"""
        user_id = "test_user"
        session_id = "test_session"
        
        # Process 50 requests
        for i in range(50):
            query = f"I want music request {i}"
            
            intent, _ = pipeline_components["intent_recognizer"].recognize(query)
            parsed = pipeline_components["query_parser"].parse(query)
            response = pipeline_components["response_generator"].generate(
                query, intent, [], [], {}
            )
            
            await pipeline_components["context_manager"].add_turn(
                user_id, session_id, query, response
            )
        
        # Verify context limit
        context = await pipeline_components["context_manager"].get_context(
            user_id, session_id
        )
        # Should be limited (typically to last 10)
        assert len(context) <= 10

    @pytest.mark.asyncio
    async def test_pipeline_long_conversation(self, pipeline_components):
        """Test pipeline with long conversation"""
        user_id = "test_user"
        session_id = "test_session"
        
        # Simulate long conversation
        queries = [
            "I want energetic music",
            "What about chill?",
            "Show me rock",
            "How about indie?",
            "Electronic please",
            "Synthwave?",
            "Lo-fi hip hop",
            "Classical music",
            "Jazz recommendations",
            "Blues tracks",
            "Country music",
            "Pop songs",
            "R&B tracks",
            "Hip hop",
            "Reggae music"
        ]
        
        for query in queries:
            intent, _ = pipeline_components["intent_recognizer"].recognize(query)
            response = pipeline_components["response_generator"].generate(
                query, intent, [], [], {}
            )
            await pipeline_components["context_manager"].add_turn(
                user_id, session_id, query, response
            )
        
        # Verify context management
        context = await pipeline_components["context_manager"].get_context(
            user_id, session_id
        )
        assert len(context) <= 10  # Should be limited

    @pytest.mark.asyncio
    async def test_pipeline_memory_management(self, pipeline_components):
        """Test pipeline memory management"""
        user_id = "test_user"
        
        # Create multiple sessions
        sessions = [f"session_{i}" for i in range(10)]
        
        for session_id in sessions:
            query = f"Query for {session_id}"
            intent, _ = pipeline_components["intent_recognizer"].recognize(query)
            response = pipeline_components["response_generator"].generate(
                query, intent, [], [], {}
            )
            await pipeline_components["context_manager"].add_turn(
                user_id, session_id, query, response
            )
        
        # Clear one session
        await pipeline_components["context_manager"].clear_context(
            user_id, sessions[0]
        )
        
        # Verify cleared session
        context = await pipeline_components["context_manager"].get_context(
            user_id, sessions[0]
        )
        assert len(context) == 0
        
        # Verify other sessions still exist
        for session_id in sessions[1:]:
            context = await pipeline_components["context_manager"].get_context(
                user_id, session_id
            )
            assert len(context) > 0
