"""Integration tests for Phase 4: Backend API"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add phase4 to path
PHASE4_PATH = Path(__file__).parent.parent / "phase4-backend-api"
sys.path.insert(0, str(PHASE4_PATH))


@pytest.mark.phase4
@pytest.mark.api
@pytest.mark.integration
class TestAPIHealthCheck:
    """Test API healthcheck endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, api_client):
        """Test health check endpoint returns 200"""
        response = await api_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_check_service_status(self, api_client):
        """Test health check includes service status"""
        response = await api_client.get("/health")
        data = response.json()
        
        assert "services" in data
        assert isinstance(data["services"], dict)

    @pytest.mark.asyncio
    async def test_health_check_timestamp(self, api_client):
        """Test health check includes timestamp"""
        response = await api_client.get("/health")
        data = response.json()
        
        assert "timestamp" in data


@pytest.mark.phase4
@pytest.mark.api
@pytest.mark.integration
class TestChatAPI:
    """Test chat API endpoint"""

    @pytest.mark.asyncio
    async def test_chat_endpoint_basic(self, api_client, sample_query_data):
        """Test basic chat endpoint"""
        payload = {
            "user_id": sample_user_data["user_id"] if 'sample_user_data' in locals() else "test_user",
            "session_id": "test_session",
            "query": sample_query_data["query"],
            "conversation_history": [],
            "enable_recommendations": True,
            "enable_explanations": True,
            "max_recommendations": 5
        }
        
        response = await api_client.post("/api/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "success" in data

    @pytest.mark.asyncio
    async def test_chat_with_conversation_history(self, api_client):
        """Test chat with conversation history"""
        payload = {
            "user_id": "test_user",
            "session_id": "test_session",
            "query": "What about something more chill?",
            "conversation_history": [
                {"role": "user", "content": "I want energetic music"},
                {"role": "assistant", "content": "Here are some energetic tracks"}
            ],
            "enable_recommendations": True,
            "max_recommendations": 5
        }
        
        response = await api_client.post("/api/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.asyncio
    async def test_chat_without_recommendations(self, api_client):
        """Test chat without recommendations"""
        payload = {
            "user_id": "test_user",
            "session_id": "test_session",
            "query": "What is synthwave?",
            "enable_recommendations": False,
            "max_recommendations": 0
        }
        
        response = await api_client.post("/api/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.asyncio
    async def test_chat_invalid_payload(self, api_client):
        """Test chat with invalid payload"""
        payload = {
            "user_id": "test_user",
            # Missing required fields
        }
        
        response = await api_client.post("/api/chat", json=payload)
        
        # Should return 400 or 422
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_chat_rate_limiting(self, api_client):
        """Test chat rate limiting"""
        payload = {
            "user_id": "test_user",
            "session_id": "test_session",
            "query": "Test query",
            "max_recommendations": 5
        }
        
        # Make multiple requests
        responses = []
        for _ in range(11):  # Assuming rate limit is 10
            response = await api_client.post("/api/chat", json=payload)
            responses.append(response)
        
        # Check if rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        # If rate limiting is implemented, at least one should be 429


@pytest.mark.phase4
@pytest.mark.api
@pytest.mark.integration
class TestDiscoverAPI:
    """Test discover music API endpoint"""

    @pytest.mark.asyncio
    async def test_discover_music_basic(self, api_client):
        """Test basic music discovery"""
        payload = {
            "user_id": "test_user",
            "session_id": "test_session",
            "mood": "energetic",
            "activity": "coding",
            "genres": ["electronic"],
            "discovery_preference": "balanced",
            "limit": 10
        }
        
        response = await api_client.post("/api/discover", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "success" in data

    @pytest.mark.asyncio
    async def test_discover_with_mood_only(self, api_client):
        """Test discovery with mood only"""
        payload = {
            "user_id": "test_user",
            "session_id": "test_session",
            "mood": "chill",
            "limit": 5
        }
        
        response = await api_client.post("/api/discover", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    @pytest.mark.asyncio
    async def test_discover_with_genres(self, api_client):
        """Test discovery with genres"""
        payload = {
            "user_id": "test_user",
            "session_id": "test_session",
            "genres": ["electronic", "indie", "rock"],
            "limit": 10
        }
        
        response = await api_client.post("/api/discover", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    @pytest.mark.asyncio
    async def test_discover_strategies_used(self, api_client):
        """Test that discovery returns strategies used"""
        payload = {
            "user_id": "test_user",
            "session_id": "test_session",
            "mood": "energetic",
            "limit": 5
        }
        
        response = await api_client.post("/api/discover", json=payload)
        data = response.json()
        
        assert "strategies_used" in data
        assert isinstance(data["strategies_used"], list)

    @pytest.mark.asyncio
    async def test_discover_limit_parameter(self, api_client):
        """Test discovery limit parameter"""
        payload = {
            "user_id": "test_user",
            "session_id": "test_session",
            "mood": "energetic",
            "limit": 3
        }
        
        response = await api_client.post("/api/discover", json=payload)
        data = response.json()
        
        assert len(data["recommendations"]) <= 3


@pytest.mark.phase4
@pytest.mark.api
@pytest.mark.integration
class TestExplainAPI:
    """Test explanation API endpoint"""

    @pytest.mark.asyncio
    async def test_explain_recommendation_basic(self, api_client):
        """Test basic recommendation explanation"""
        payload = {
            "user_id": "test_user",
            "recommendation_id": "rec_001"
        }
        
        response = await api_client.post("/api/explain", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    @pytest.mark.asyncio
    async def test_explanation_content(self, api_client):
        """Test explanation content structure"""
        payload = {
            "user_id": "test_user",
            "recommendation_id": "rec_001"
        }
        
        response = await api_client.post("/api/explain", json=payload)
        data = response.json()
        
        if data.get("success"):
            # Check for expected fields
            expected_fields = [
                "song_selection_reasons",
                "artist_selection_reasons",
                "user_preference_influences",
                "scores"
            ]
            for field in expected_fields:
                assert field in data

    @pytest.mark.asyncio
    async def test_explanation_scores_range(self, api_client):
        """Test that explanation scores are in valid range"""
        payload = {
            "user_id": "test_user",
            "recommendation_id": "rec_001"
        }
        
        response = await api_client.post("/api/explain", json=payload)
        data = response.json()
        
        if data.get("success") and "scores" in data:
            for key, value in data["scores"].items():
                assert 0 <= value <= 1.0

    @pytest.mark.asyncio
    async def test_explain_invalid_recommendation_id(self, api_client):
        """Test explanation with invalid recommendation ID"""
        payload = {
            "user_id": "test_user",
            "recommendation_id": "invalid_id"
        }
        
        response = await api_client.post("/api/explain", json=payload)
        
        # Should handle gracefully
        assert response.status_code in [200, 404]


@pytest.mark.phase4
@pytest.mark.api
@pytest.mark.integration
class TestRecommendationHistoryAPI:
    """Test recommendation history API endpoint"""

    @pytest.mark.asyncio
    async def test_get_recommendation_history(self, api_client):
        """Test getting recommendation history"""
        params = {
            "user_id": "test_user",
            "limit": 10
        }
        
        response = await api_client.get("/api/recommendations/history", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "total_count" in data

    @pytest.mark.asyncio
    async def test_history_pagination(self, api_client):
        """Test history pagination with limit"""
        params = {
            "user_id": "test_user",
            "limit": 5
        }
        
        response = await api_client.get("/api/recommendations/history", params=params)
        data = response.json()
        
        assert len(data["history"]) <= 5

    @pytest.mark.asyncio
    async def test_history_structure(self, api_client):
        """Test history item structure"""
        params = {
            "user_id": "test_user",
            "limit": 1
        }
        
        response = await api_client.get("/api/recommendations/history", params=params)
        data = response.json()
        
        if data["history"]:
            item = data["history"][0]
            expected_fields = ["track", "confidence", "explanation"]
            for field in expected_fields:
                assert field in item


@pytest.mark.phase4
@pytest.mark.api
@pytest.mark.integration
class TestSimilarArtistsAPI:
    """Test similar artists API endpoint"""

    @pytest.mark.asyncio
    async def test_get_similar_artists_by_id(self, api_client, sample_artist_data):
        """Test getting similar artists by ID"""
        params = {
            "artist_id": sample_artist_data["artist_id"],
            "limit": 5
        }
        
        response = await api_client.get("/api/artists/similar", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "similar_artists" in data or "artists" in data

    @pytest.mark.asyncio
    async def test_get_similar_artists_by_name(self, api_client):
        """Test getting similar artists by name"""
        params = {
            "artist_name": "Daft Punk",
            "limit": 5
        }
        
        response = await api_client.get("/api/artists/similar", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "similar_artists" in data or "artists" in data

    @pytest.mark.asyncio
    async def test_similar_artists_limit(self, api_client):
        """Test similar artists limit parameter"""
        params = {
            "artist_name": "Test Artist",
            "limit": 3
        }
        
        response = await api_client.get("/api/artists/similar", params=params)
        data = response.json()
        
        artists = data.get("similar_artists", data.get("artists", []))
        assert len(artists) <= 3


@pytest.mark.phase4
@pytest.mark.api
@pytest.mark.integration
class TestDiscoveryInsightsAPI:
    """Test discovery insights API endpoint"""

    @pytest.mark.asyncio
    async def test_get_discovery_insights(self, api_client):
        """Test getting discovery insights"""
        params = {
            "user_id": "test_user"
        }
        
        response = await api_client.get("/api/insights/discovery", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    @pytest.mark.asyncio
    async def test_insights_structure(self, api_client):
        """Test insights data structure"""
        params = {
            "user_id": "test_user"
        }
        
        response = await api_client.get("/api/insights/discovery", params=params)
        data = response.json()
        
        if data.get("success"):
            expected_sections = [
                "pain_points",
                "theme_clusters",
                "user_segments",
                "product_insights"
            ]
            for section in expected_sections:
                assert section in data

    @pytest.mark.asyncio
    async def test_insights_by_type(self, api_client):
        """Test filtering insights by type"""
        params = {
            "user_id": "test_user",
            "insight_type": "pain_points"
        }
        
        response = await api_client.get("/api/insights/discovery", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    @pytest.mark.asyncio
    async def test_insights_executive_summary(self, api_client):
        """Test executive summary in insights"""
        params = {
            "user_id": "test_user"
        }
        
        response = await api_client.get("/api/insights/discovery", params=params)
        data = response.json()
        
        if data.get("success"):
            # Executive summary may or may not be present
            if "executive_summary" in data:
                assert isinstance(data["executive_summary"], str)


@pytest.mark.phase4
@pytest.mark.api
@pytest.mark.integration
class TestConversationHistoryAPI:
    """Test conversation history API endpoint"""

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, api_client):
        """Test getting conversation history"""
        params = {
            "user_id": "test_user",
            "limit": 10
        }
        
        response = await api_client.get("/api/conversation/history", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "total_count" in data

    @pytest.mark.asyncio
    async def test_conversation_history_by_session(self, api_client):
        """Test getting conversation history by session"""
        params = {
            "user_id": "test_user",
            "session_id": "test_session",
            "limit": 10
        }
        
        response = await api_client.get("/api/conversation/history", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data

    @pytest.mark.asyncio
    async def test_conversation_history_structure(self, api_client):
        """Test conversation history item structure"""
        params = {
            "user_id": "test_user",
            "limit": 1
        }
        
        response = await api_client.get("/api/conversation/history", params=params)
        data = response.json()
        
        if data["history"]:
            item = data["history"][0]
            expected_fields = ["query", "response", "intent"]
            for field in expected_fields:
                assert field in item


@pytest.mark.phase4
@pytest.mark.api
@pytest.mark.integration
@pytest.mark.slow
class TestPhase4EndToEnd:
    """End-to-end tests for Phase 4 API"""

    @pytest.mark.asyncio
    async def test_complete_user_flow(self, api_client):
        """Test complete user flow through API"""
        user_id = "test_user_e2e"
        session_id = "test_session_e2e"
        
        # Step 1: Chat request
        chat_payload = {
            "user_id": user_id,
            "session_id": session_id,
            "query": "I want energetic music for coding",
            "enable_recommendations": True,
            "max_recommendations": 3
        }
        chat_response = await api_client.post("/api/chat", json=chat_payload)
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        
        # Step 2: Get recommendations from discovery
        if chat_data.get("recommendations"):
            rec_id = chat_data["recommendations"][0].get("id", "rec_001")
            
            # Step 3: Get explanation
            explain_payload = {
                "user_id": user_id,
                "recommendation_id": rec_id
            }
            explain_response = await api_client.post("/api/explain", json=explain_payload)
            assert explain_response.status_code == 200
        
        # Step 4: Get recommendation history
        history_response = await api_client.get(
            "/api/recommendations/history",
            params={"user_id": user_id, "limit": 5}
        )
        assert history_response.status_code == 200
        
        # Step 5: Get conversation history
        conv_history_response = await api_client.get(
            "/api/conversation/history",
            params={"user_id": user_id, "session_id": session_id, "limit": 5}
        )
        assert conv_history_response.status_code == 200

    @pytest.mark.asyncio
    async def test_multi_session_flow(self, api_client):
        """Test multi-session conversation flow"""
        user_id = "test_user_multi"
        sessions = ["session_1", "session_2"]
        
        for session_id in sessions:
            chat_payload = {
                "user_id": user_id,
                "session_id": session_id,
                "query": f"Query for {session_id}",
                "enable_recommendations": True,
                "max_recommendations": 2
            }
            response = await api_client.post("/api/chat", json=chat_payload)
            assert response.status_code == 200
        
        # Get combined history
        history_response = await api_client.get(
            "/api/conversation/history",
            params={"user_id": user_id, "limit": 20}
        )
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data["total_count"] >= 2

    @pytest.mark.asyncio
    async def test_error_handling_flow(self, api_client):
        """Test error handling across endpoints"""
        # Test invalid chat payload
        invalid_chat = await api_client.post(
            "/api/chat",
            json={"user_id": "test"}  # Missing required fields
        )
        assert invalid_chat.status_code in [400, 422]
        
        # Test invalid recommendation ID
        invalid_explain = await api_client.post(
            "/api/explain",
            json={"user_id": "test", "recommendation_id": "nonexistent"}
        )
        # Should handle gracefully
        assert invalid_explain.status_code in [200, 404]
        
        # Test non-existent user history
        no_history = await api_client.get(
            "/api/recommendations/history",
            params={"user_id": "nonexistent_user", "limit": 10}
        )
        assert no_history.status_code == 200
        data = no_history.json()
        assert data.get("total_count", 0) == 0

    @pytest.mark.asyncio
    async def test_api_performance(self, api_client, performance_thresholds):
        """Test API response times"""
        import time
        
        # Test chat endpoint performance
        start = time.time()
        chat_response = await api_client.post(
            "/api/chat",
            json={
                "user_id": "test_user",
                "session_id": "test_session",
                "query": "Test query",
                "max_recommendations": 5
            }
        )
        chat_time = (time.time() - start) * 1000  # Convert to ms
        
        assert chat_response.status_code == 200
        assert chat_time < performance_thresholds["api_response_time_ms"]
        
        # Test discover endpoint performance
        start = time.time()
        discover_response = await api_client.post(
            "/api/discover",
            json={
                "user_id": "test_user",
                "session_id": "test_session",
                "mood": "energetic",
                "limit": 5
            }
        )
        discover_time = (time.time() - start) * 1000
        
        assert discover_response.status_code == 200
        assert discover_time < performance_thresholds["api_response_time_ms"]
