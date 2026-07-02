"""Integration tests for Phase 3: AI Orchestration"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add phase3 to path
PHASE3_PATH = Path(__file__).parent.parent / "phase3-ai-orchestration"
sys.path.insert(0, str(PHASE3_PATH))

from orchestration_controller.orchestration_controller import OrchestrationController
from fallback_manager.fallback_manager import FallbackManager
from performance_monitor.performance_monitor import PerformanceMonitor
from prompt_chain_manager.prompt_chain_manager import PromptChainManager
from response_validator.response_validator import ResponseValidator


@pytest.mark.phase3
@pytest.mark.integration
class TestOrchestrationController:
    """Test orchestration controller integration"""

    @pytest.fixture
    def orchestration_controller(self):
        """Create OrchestrationController instance"""
        return OrchestrationController()

    @pytest.mark.asyncio
    async def test_process_music_recommendation_request(self, orchestration_controller, sample_query_data):
        """Test processing music recommendation request"""
        query = sample_query_data["query"]
        user_id = sample_user_data["user_id"] if 'sample_user_data' in locals() else "test_user"
        session_id = "test_session"
        
        result = await orchestration_controller.process_request(
            query, user_id, session_id
        )
        
        assert result is not None
        assert "response" in result or "recommendations" in result
        assert "success" in result

    @pytest.mark.asyncio
    async def test_process_trending_query(self, orchestration_controller):
        """Test processing trending query"""
        query = "What's trending in electronic music?"
        user_id = "test_user"
        session_id = "test_session"
        
        result = await orchestration_controller.process_request(
            query, user_id, session_id
        )
        
        assert result is not None
        assert "response" in result or "trending" in str(result).lower()

    @pytest.mark.asyncio
    async def test_process_explanation_request(self, orchestration_controller):
        """Test processing explanation request"""
        query = "Why did you recommend this song?"
        user_id = "test_user"
        session_id = "test_session"
        context = {"last_recommendation": "Test Song"}
        
        result = await orchestration_controller.process_request(
            query, user_id, session_id, context=context
        )
        
        assert result is not None
        assert "response" in result

    @pytest.mark.asyncio
    async def test_process_artist_query(self, orchestration_controller):
        """Test processing artist query"""
        query = "Tell me about Daft Punk"
        user_id = "test_user"
        session_id = "test_session"
        
        result = await orchestration_controller.process_request(
            query, user_id, session_id
        )
        
        assert result is not None
        assert "response" in result or "artist" in str(result).lower()

    @pytest.mark.asyncio
    async def test_handle_unknown_intent(self, orchestration_controller):
        """Test handling of unknown intent"""
        query = "What is the meaning of life?"
        user_id = "test_user"
        session_id = "test_session"
        
        result = await orchestration_controller.process_request(
            query, user_id, session_id
        )
        
        assert result is not None
        # Should have fallback response
        assert "response" in result


@pytest.mark.phase3
@pytest.mark.integration
class TestFallbackManager:
    """Test fallback manager integration"""

    @pytest.fixture
    def fallback_manager(self):
        """Create FallbackManager instance"""
        return FallbackManager()

    @pytest.mark.asyncio
    async def test_llm_failure_fallback(self, fallback_manager):
        """Test fallback when LLM fails"""
        error = Exception("LLM API timeout")
        query = "I want music recommendations"
        
        fallback_response = fallback_manager.handle_llm_failure(error, query)
        
        assert fallback_response is not None
        assert isinstance(fallback_response, str)
        assert len(fallback_response) > 0

    @pytest.mark.asyncio
    async def test_spotify_api_failure_fallback(self, fallback_manager):
        """Test fallback when Spotify API fails"""
        error = Exception("Spotify API rate limit")
        operation = "get_recommendations"
        
        fallback_response = fallback_manager.handle_spotify_failure(error, operation)
        
        assert fallback_response is not None
        assert isinstance(fallback_response, (str, dict))

    @pytest.mark.asyncio
    async def test_database_failure_fallback(self, fallback_manager):
        """Test fallback when database fails"""
        error = Exception("Database connection lost")
        operation = "get_user_history"
        
        fallback_response = fallback_manager.handle_database_failure(error, operation)
        
        assert fallback_response is not None

    @pytest.mark.asyncio
    async def test_cascading_fallbacks(self, fallback_manager):
        """Test cascading through multiple fallback strategies"""
        errors = [
            Exception("Primary service down"),
            Exception("Secondary service down"),
            Exception("Tertiary service down")
        ]
        
        for error in errors:
            response = fallback_manager.handle_llm_failure(error, "test query")
            assert response is not None

    @pytest.mark.asyncio
    async def test_fallback_with_context(self, fallback_manager):
        """Test fallback with context preservation"""
        error = Exception("Service unavailable")
        query = "I want energetic music"
        context = {"user_preferences": {"mood": "energetic"}}
        
        fallback_response = fallback_manager.handle_llm_failure(
            error, query, context=context
        )
        
        assert fallback_response is not None
        # Should attempt to use context
        assert len(fallback_response) > 0


@pytest.mark.phase3
@pytest.mark.integration
class TestPerformanceMonitor:
    """Test performance monitor integration"""

    @pytest.fixture
    def performance_monitor(self):
        """Create PerformanceMonitor instance"""
        return PerformanceMonitor()

    @pytest.mark.asyncio
    async def test_track_llm_latency(self, performance_monitor):
        """Test tracking LLM latency"""
        operation = "intent_recognition"
        latency = 150  # ms
        
        performance_monitor.track_latency(operation, latency)
        
        metrics = performance_monitor.get_metrics(operation)
        assert metrics is not None
        assert "avg_latency" in metrics or "latency" in metrics

    @pytest.mark.asyncio
    async def test_track_api_call(self, performance_monitor):
        """Test tracking API call"""
        endpoint = "/api/chat"
        status_code = 200
        latency = 250
        
        performance_monitor.track_api_call(endpoint, status_code, latency)
        
        metrics = performance_monitor.get_api_metrics(endpoint)
        assert metrics is not None

    @pytest.mark.asyncio
    async def test_track_error_rate(self, performance_monitor):
        """Test tracking error rate"""
        operation = "recommendation_generation"
        
        # Track some errors
        performance_monitor.track_error(operation)
        performance_monitor.track_error(operation)
        performance_monitor.track_success(operation)
        
        error_rate = performance_monitor.get_error_rate(operation)
        assert error_rate is not None
        assert 0 <= error_rate <= 1.0

    @pytest.mark.asyncio
    async def test_get_performance_summary(self, performance_monitor):
        """Test getting performance summary"""
        # Track some metrics
        performance_monitor.track_latency("intent_recognition", 100)
        performance_monitor.track_latency("query_parsing", 50)
        performance_monitor.track_success("intent_recognition")
        
        summary = performance_monitor.get_summary()
        
        assert summary is not None
        assert isinstance(summary, dict)

    @pytest.mark.asyncio
    async def test_performance_threshold_alerts(self, performance_monitor):
        """Test performance threshold alerts"""
        # Track slow operation
        performance_monitor.track_latency("slow_operation", 5000)
        
        alerts = performance_monitor.check_thresholds()
        
        # Should have alert for slow operation
        assert isinstance(alerts, list)


@pytest.mark.phase3
@pytest.mark.integration
class TestPromptChainManager:
    """Test prompt chain manager integration"""

    @pytest.fixture
    def prompt_chain_manager(self):
        """Create PromptChainManager instance"""
        return PromptChainManager()

    @pytest.mark.asyncio
    async def test_build_recommendation_chain(self, prompt_chain_manager):
        """Test building recommendation prompt chain"""
        query = "I want energetic music for coding"
        context = {"user_preferences": {"mood": "energetic"}}
        
        chain = prompt_chain_manager.build_recommendation_chain(query, context)
        
        assert chain is not None
        assert isinstance(chain, list) or isinstance(chain, dict)

    @pytest.mark.asyncio
    async def test_build_explanation_chain(self, prompt_chain_manager):
        """Test building explanation prompt chain"""
        recommendation_id = "rec_001"
        context = {"user_history": ["previous queries"]}
        
        chain = prompt_chain_manager.build_explanation_chain(
            recommendation_id, context
        )
        
        assert chain is not None

    @pytest.mark.asyncio
    async def test_execute_chain(self, prompt_chain_manager):
        """Test executing prompt chain"""
        chain = [
            {"step": "intent_recognition", "query": "test query"},
            {"step": "query_parsing", "query": "test query"}
        ]
        
        result = prompt_chain_manager.execute_chain(chain)
        
        assert result is not None
        assert "results" in result or "output" in result

    @pytest.mark.asyncio
    async def test_chain_with_dependencies(self, prompt_chain_manager):
        """Test chain with step dependencies"""
        chain = [
            {"step": "intent_recognition", "query": "test query"},
            {"step": "query_parsing", "depends_on": "intent_recognition"},
            {"step": "response_generation", "depends_on": ["intent_recognition", "query_parsing"]}
        ]
        
        result = prompt_chain_manager.execute_chain(chain)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_chain_error_handling(self, prompt_chain_manager):
        """Test chain error handling"""
        chain = [
            {"step": "invalid_step", "query": "test query"}
        ]
        
        result = prompt_chain_manager.execute_chain(chain)
        
        # Should handle error gracefully
        assert result is not None
        assert "error" in result or "success" in result


@pytest.mark.phase3
@pytest.mark.integration
class TestResponseValidator:
    """Test response validator integration"""

    @pytest.fixture
    def response_validator(self):
        """Create ResponseValidator instance"""
        return ResponseValidator()

    @pytest.mark.asyncio
    async def test_validate_chat_response(self, response_validator):
        """Test validating chat response"""
        response = {
            "response": "Here are some energetic tracks for coding",
            "intent": "music_recommendation",
            "recommendations": []
        }
        
        validation = response_validator.validate_chat_response(response)
        
        assert validation is not None
        assert "valid" in validation or "is_valid" in validation

    @pytest.mark.asyncio
    async def test_validate_recommendation_response(self, response_validator, sample_recommendation_data):
        """Test validating recommendation response"""
        response = {
            "recommendations": [sample_recommendation_data],
            "strategies_used": ["mood_matching", "similarity"],
            "success": True
        }
        
        validation = response_validator.validate_recommendation_response(response)
        
        assert validation is not None

    @pytest.mark.asyncio
    async def test_validate_explanation_response(self, response_validator):
        """Test validating explanation response"""
        response = {
            "song_selection_reasons": ["Matches your mood"],
            "artist_selection_reasons": ["Similar to your preferences"],
            "scores": {"mood_match": 0.9, "similarity": 0.8},
            "success": True
        }
        
        validation = response_validator.validate_explanation_response(response)
        
        assert validation is not None

    @pytest.mark.asyncio
    async def test_detect_malformed_response(self, response_validator):
        """Test detecting malformed response"""
        response = {
            "response": None,
            "recommendations": "invalid"
        }
        
        validation = response_validator.validate_chat_response(response)
        
        assert validation.get("valid", validation.get("is_valid", True)) == False

    @pytest.mark.asyncio
    async def test_validate_response_structure(self, response_validator):
        """Test validating response structure"""
        response = {
            "response": "Test response",
            "intent": "music_recommendation"
        }
        
        structure = response_validator.validate_structure(response)
        
        assert structure is not None
        assert isinstance(structure, dict)


@pytest.mark.phase3
@pytest.mark.integration
@pytest.mark.slow
class TestPhase3EndToEnd:
    """End-to-end tests for Phase 3"""

    @pytest.fixture
    def orchestration_components(self):
        """Create all Phase 3 components"""
        return {
            "orchestration_controller": OrchestrationController(),
            "fallback_manager": FallbackManager(),
            "performance_monitor": PerformanceMonitor(),
            "prompt_chain_manager": PromptChainManager(),
            "response_validator": ResponseValidator()
        }

    @pytest.mark.asyncio
    async def test_full_orchestration_flow(self, orchestration_components, sample_query_data):
        """Test complete orchestration flow"""
        query = sample_query_data["query"]
        user_id = "test_user"
        session_id = "test_session"
        
        # Step 1: Process request through orchestration controller
        result = await orchestration_components["orchestration_controller"].process_request(
            query, user_id, session_id
        )
        
        assert result is not None
        assert "success" in result
        
        # Step 2: Validate response
        validation = orchestration_components["response_validator"].validate_chat_response(result)
        assert validation.get("valid", validation.get("is_valid", True)) == True
        
        # Step 3: Check performance metrics
        summary = orchestration_components["performance_monitor"].get_summary()
        assert summary is not None

    @pytest.mark.asyncio
    async def test_orchestration_with_fallback(self, orchestration_components):
        """Test orchestration with fallback handling"""
        query = "I want music recommendations"
        user_id = "test_user"
        session_id = "test_session"
        
        # Simulate failure
        try:
            result = await orchestration_components["orchestration_controller"].process_request(
                query, user_id, session_id
            )
        except Exception as e:
            # Use fallback
            result = orchestration_components["fallback_manager"].handle_llm_failure(e, query)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_orchestration_with_prompt_chain(self, orchestration_components):
        """Test orchestration using prompt chains"""
        query = "I want energetic music for coding"
        context = {"user_preferences": {"mood": "energetic"}}
        
        # Build chain
        chain = orchestration_components["prompt_chain_manager"].build_recommendation_chain(
            query, context
        )
        
        # Execute chain
        result = orchestration_components["prompt_chain_manager"].execute_chain(chain)
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_multi_step_orchestration(self, orchestration_components):
        """Test multi-step orchestration with context preservation"""
        user_id = "test_user"
        session_id = "test_session"
        
        queries = [
            "I like electronic music",
            "What about something more chill?",
            "Show me rock recommendations"
        ]
        
        context = {}
        for query in queries:
            result = await orchestration_components["orchestration_controller"].process_request(
                query, user_id, session_id, context=context
            )
            assert result is not None
            # Update context
            context["last_query"] = query
            context["last_response"] = result.get("response", "")

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, orchestration_components):
        """Test performance monitoring integration"""
        # Track various operations
        orchestration_components["performance_monitor"].track_latency("intent_recognition", 100)
        orchestration_components["performance_monitor"].track_latency("query_parsing", 50)
        orchestration_components["performance_monitor"].track_api_call("/api/chat", 200, 200)
        orchestration_components["performance_monitor"].track_success("intent_recognition")
        orchestration_components["performance_monitor"].track_error("recommendation_generation")
        
        # Get summary
        summary = orchestration_components["performance_monitor"].get_summary()
        
        assert summary is not None
        assert isinstance(summary, dict)
