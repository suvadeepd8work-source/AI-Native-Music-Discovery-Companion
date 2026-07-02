"""Test configuration and fixtures for integration tests"""

import pytest
import asyncio
import os
from pathlib import Path
from typing import Dict, Any
import httpx

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
PHASE1_PATH = PROJECT_ROOT / "phase1-ai-conversation-engine"
PHASE2_PATH = PROJECT_ROOT / "phase2-music-recommendation-engine"
PHASE3_PATH = PROJECT_ROOT / "phase3-ai-orchestration"
PHASE4_PATH = PROJECT_ROOT / "phase4-backend-api"

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8005")
API_TIMEOUT = 30.0


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def api_client():
    """HTTP client for API testing"""
    return httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "user_id": "test_user_001",
        "session_id": "test_session_001",
        "preferences": {
            "genres": ["electronic", "indie", "rock"],
            "moods": ["energetic", "chill"],
            "activities": ["coding", "workout"]
        }
    }


@pytest.fixture
def sample_query_data():
    """Sample query data for testing"""
    return {
        "query": "I want some energetic music for coding",
        "expected_intent": "music_recommendation",
        "expected_mood": "energetic",
        "expected_activity": "coding"
    }


@pytest.fixture
def sample_recommendation_data():
    """Sample recommendation data for testing"""
    return {
        "track": {
            "id": "track_001",
            "name": "Test Song",
            "artist_name": "Test Artist",
            "album": "Test Album",
            "duration_ms": 180000,
            "external_url": "https://example.com/track"
        },
        "confidence": 0.85,
        "explanation": "This track matches your energetic mood preference"
    }


@pytest.fixture
def sample_artist_data():
    """Sample artist data for testing"""
    return {
        "artist_id": "artist_001",
        "name": "Test Artist",
        "genres": ["electronic", "synthwave"],
        "popularity": 75,
        "followers": 1000000,
        "external_url": "https://example.com/artist"
    }


@pytest.fixture
def sample_insight_data():
    """Sample insight data for testing"""
    return {
        "pain_points": [
            {
                "description": "Users struggle to discover new music",
                "severity": 0.8,
                "frequency": 150
            }
        ],
        "theme_clusters": [
            {
                "theme_name": "Energetic Coding Music",
                "sentiment": 0.9,
                "frequency": 200
            }
        ],
        "user_segments": [
            {
                "segment_name": "Developers",
                "size": 50000
            }
        ],
        "product_insights": [
            {
                "title": "Improve discovery algorithm",
                "category": "Algorithm",
                "impact": "high"
            }
        ]
    }


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing"""
    return [
        {
            "query": "I want some chill music",
            "response": "Here are some chill recommendations",
            "intent": "music_recommendation",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        {
            "query": "What's trending in electronic music?",
            "response": "Here are the trending electronic tracks",
            "intent": "trending_query",
            "timestamp": "2024-01-01T12:05:00Z"
        }
    ]


@pytest.fixture
async def health_check(api_client):
    """Perform health check before tests"""
    try:
        response = await api_client.get("/health")
        assert response.status_code == 200
        return response.json()
    except Exception as e:
        pytest.skip(f"API health check failed: {e}")


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "choices": [
            {
                "message": {
                    "content": "music_recommendation|0.95"
                }
            }
        ]
    }


@pytest.fixture
def mock_lastfm_response():
    """Mock Last.fm API response for testing"""
    return {
        "results": {
            "trackmatches": {
                "track": [
                    {
                        "name": "Test Song",
                        "artist": "Test Artist",
                        "url": "https://www.last.fm/music/Test+Artist/_/Test+Song",
                        "listeners": 1000000,
                        "mbid": "track_001"
                    }
                ]
            }
        }
    }


@pytest.fixture
def test_environment():
    """Test environment configuration"""
    return {
        "testing": True,
        "mock_external_apis": True,
        "database_url": "sqlite:///test.db",
        "redis_url": "redis://localhost:6379/1"
    }


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing"""
    return {
        "api_response_time_ms": 1000,
        "llm_response_time_ms": 5000,
        "database_query_time_ms": 100,
        "pipeline_execution_time_ms": 10000
    }


# Custom markers
pytest.mark.phase1 = pytest.mark.phase1
pytest.mark.phase2 = pytest.mark.phase2
pytest.mark.phase3 = pytest.mark.phase3
pytest.mark.phase4 = pytest.mark.phase4
pytest.mark.phase5 = pytest.mark.phase5
pytest.mark.api = pytest.mark.api
pytest.mark.agent = pytest.mark.agent
pytest.mark.pipeline = pytest.mark.pipeline
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
