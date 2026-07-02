"""Integration tests for Agent Outputs"""

import pytest
import asyncio
import sys
from pathlib import Path

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
from mood_activity_matching.mood_activity_matcher import MoodActivityMatcher
from genre_exploration.genre_explorer import GenreExplorer
from similarity_search.similarity_searcher import SimilaritySearcher
from review_based_discovery.review_discovery import ReviewDiscoveryEngine
from habit_breaking.habit_breaker import HabitBreaker
from recommendation_fusion.recommendation_fuser import RecommendationFuser
from explanation_generator.explanation_generator import ExplanationGenerator


@pytest.mark.agent
@pytest.mark.integration
class TestIntentRecognitionOutputs:
    """Test intent recognition agent outputs"""

    @pytest.fixture
    def intent_recognizer(self):
        """Create IntentRecognizer instance"""
        return IntentRecognizer()

    @pytest.mark.asyncio
    async def test_intent_output_format(self, intent_recognizer):
        """Test that intent output has correct format"""
        query = "I want energetic music for coding"
        intent, confidence = intent_recognizer.recognize(query)
        
        assert isinstance(intent, str)
        assert isinstance(confidence, (int, float))
        assert 0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_intent_output_consistency(self, intent_recognizer):
        """Test that intent outputs are consistent for similar queries"""
        queries = [
            "I want energetic music",
            "Show me energetic tracks",
            "Give me energetic songs"
        ]
        
        intents = []
        for query in queries:
            intent, _ = intent_recognizer.recognize(query)
            intents.append(intent)
        
        # All should have similar intents
        assert all(i == intents[0] for i in intents) or len(set(intents)) <= 2

    @pytest.mark.asyncio
    async def test_intent_confidence_calibration(self, intent_recognizer):
        """Test that confidence scores are well-calibrated"""
        clear_queries = [
            "I want music recommendations",
            "What's trending?",
            "Tell me about this artist"
        ]
        
        ambiguous_queries = [
            "Hello",
            "Okay",
            "Maybe"
        ]
        
        clear_confidences = []
        ambiguous_confidences = []
        
        for query in clear_queries:
            _, confidence = intent_recognizer.recognize(query)
            clear_confidences.append(confidence)
        
        for query in ambiguous_queries:
            _, confidence = intent_recognizer.recognize(query)
            ambiguous_confidences.append(confidence)
        
        # Clear queries should have higher confidence on average
        if clear_confidences and ambiguous_confidences:
            avg_clear = sum(clear_confidences) / len(clear_confidences)
            avg_ambiguous = sum(ambiguous_confidences) / len(ambiguous_confidences)
            assert avg_clear >= avg_ambiguous


@pytest.mark.agent
@pytest.mark.integration
class TestQueryParserOutputs:
    """Test query parser agent outputs"""

    @pytest.fixture
    def query_parser(self):
        """Create QueryParser instance"""
        return QueryParser()

    @pytest.mark.asyncio
    async def test_parser_output_structure(self, query_parser):
        """Test that parser output has correct structure"""
        query = "I want energetic electronic music for coding"
        parsed = query_parser.parse(query)
        
        # Should have expected fields
        expected_fields = ["mood", "activity", "genres", "energy_level"]
        for field in expected_fields:
            assert hasattr(parsed, field) or field in parsed

    @pytest.mark.asyncio
    async def test_parser_output_accuracy(self, query_parser):
        """Test that parser output accurately reflects query"""
        query = "I want energetic electronic music for coding"
        parsed = query_parser.parse(query)
        
        # Check extracted values
        mood = getattr(parsed, "mood", None) or parsed.get("mood", "")
        activity = getattr(parsed, "activity", None) or parsed.get("activity", "")
        genres = getattr(parsed, "genres", None) or parsed.get("genres", [])
        
        assert "energetic" in str(mood).lower()
        assert "coding" in str(activity).lower()
        assert "electronic" in str(genres).lower()

    @pytest.mark.asyncio
    async def test_parser_output_handling_missing_info(self, query_parser):
        """Test parser output when information is missing"""
        query = "I want music"
        parsed = query_parser.parse(query)
        
        # Should not crash, should return defaults
        assert parsed is not None


@pytest.mark.agent
@pytest.mark.integration
class TestResponseGeneratorOutputs:
    """Test response generator agent outputs"""

    @pytest.fixture
    def response_generator(self):
        """Create ResponseGenerator instance"""
        return ResponseGenerator()

    @pytest.mark.asyncio
    async def test_response_output_format(self, response_generator):
        """Test that response output has correct format"""
        query = "I want energetic music"
        intent = "music_recommendation"
        
        response = response_generator.generate(
            query, intent, [], [], {}
        )
        
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_response_output_relevance(self, response_generator):
        """Test that response is relevant to query"""
        query = "I want energetic music for coding"
        intent = "music_recommendation"
        context = {"mood": "energetic", "activity": "coding"}
        
        response = response_generator.generate(
            query, intent, [], [], context
        )
        
        # Response should mention key terms
        response_lower = response.lower()
        assert "energetic" in response_lower or "coding" in response_lower

    @pytest.mark.asyncio
    async def test_response_output_with_recommendations(self, response_generator):
        """Test response output with recommendations"""
        query = "I want energetic music"
        intent = "music_recommendation"
        recommendations = [
            {
                "track": {"name": "Test Song", "artist_name": "Test Artist"},
                "confidence": 0.85
            }
        ]
        
        response = response_generator.generate(
            query, intent, recommendations, [], {}
        )
        
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_response_output_with_explanations(self, response_generator):
        """Test response output with explanations"""
        query = "Why this song?"
        intent = "explanation"
        explanations = ["Matches your mood preference"]
        
        response = response_generator.generate(
            query, intent, [], explanations, {}
        )
        
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.agent
@pytest.mark.integration
class TestMoodMatcherOutputs:
    """Test mood matcher agent outputs"""

    @pytest.fixture
    def mood_matcher(self):
        """Create MoodActivityMatcher instance"""
        return MoodActivityMatcher()

    @pytest.mark.asyncio
    async def test_mood_output_characteristics(self, mood_matcher):
        """Test that mood output has correct characteristics"""
        mood = "energetic"
        characteristics = mood_matcher.match_mood(mood)
        
        assert characteristics is not None
        assert isinstance(characteristics, dict)

    @pytest.mark.asyncio
    async def test_mood_output_values(self, mood_matcher):
        """Test that mood output values are in valid range"""
        mood = "energetic"
        characteristics = mood_matcher.match_mood(mood)
        
        for key, value in characteristics.items():
            if isinstance(value, (int, float)):
                assert 0 <= value <= 1.0

    @pytest.mark.asyncio
    async def test_activity_output_characteristics(self, mood_matcher):
        """Test that activity output has correct characteristics"""
        activity = "coding"
        characteristics = mood_matcher.match_activity(activity)
        
        assert characteristics is not None
        assert isinstance(characteristics, dict)


@pytest.mark.agent
@pytest.mark.integration
class TestGenreExplorerOutputs:
    """Test genre explorer agent outputs"""

    @pytest.fixture
    def genre_explorer(self):
        """Create GenreExplorer instance"""
        return GenreExplorer()

    @pytest.mark.asyncio
    async def test_genre_output_structure(self, genre_explorer):
        """Test that genre output has correct structure"""
        genre = "electronic"
        characteristics = genre_explorer.explore_genre(genre)
        
        assert characteristics is not None
        assert isinstance(characteristics, dict)

    @pytest.mark.asyncio
    async def test_similar_genres_output(self, genre_explorer):
        """Test similar genres output"""
        genre = "synthwave"
        similar = genre_explorer.find_similar_genres(genre, limit=5)
        
        assert isinstance(similar, list)
        assert len(similar) <= 5

    @pytest.mark.asyncio
    async def test_genre_trends_output(self, genre_explorer):
        """Test genre trends output"""
        trends = genre_explorer.get_genre_trends(limit=10)
        
        assert isinstance(trends, list)
        assert len(trends) <= 10


@pytest.mark.agent
@pytest.mark.integration
class TestSimilaritySearcherOutputs:
    """Test similarity searcher agent outputs"""

    @pytest.fixture
    def similarity_searcher(self):
        """Create SimilaritySearcher instance"""
        return SimilaritySearcher()

    @pytest.mark.asyncio
    async def test_similar_tracks_output(self, similarity_searcher):
        """Test similar tracks output"""
        track_id = "test_track_001"
        similar = similarity_searcher.find_similar_tracks(track_id, limit=5)
        
        assert isinstance(similar, list)
        assert len(similar) <= 5

    @pytest.mark.asyncio
    async def test_similar_tracks_similarity_scores(self, similarity_searcher):
        """Test that similarity scores are valid"""
        track_id = "test_track_001"
        similar = similarity_searcher.find_similar_tracks(track_id, limit=10)
        
        for track in similar:
            if "similarity" in track:
                assert 0 <= track["similarity"] <= 1.0

    @pytest.mark.asyncio
    async def test_similar_artists_output(self, similarity_searcher):
        """Test similar artists output"""
        artist_id = "test_artist_001"
        similar = similarity_searcher.find_similar_artists(artist_id, limit=5)
        
        assert isinstance(similar, list)
        assert len(similar) <= 5


@pytest.mark.agent
@pytest.mark.integration
class TestReviewDiscoveryOutputs:
    """Test review discovery agent outputs"""

    @pytest.fixture
    def review_discovery(self):
        """Create ReviewDiscoveryEngine instance"""
        return ReviewDiscoveryEngine()

    @pytest.mark.asyncio
    async def test_sentiment_discovery_output(self, review_discovery):
        """Test sentiment discovery output"""
        tracks = review_discovery.discover_by_sentiment("positive", limit=5)
        
        assert isinstance(tracks, list)
        assert len(tracks) <= 5

    @pytest.mark.asyncio
    async def test_theme_discovery_output(self, review_discovery):
        """Test theme discovery output"""
        tracks = review_discovery.discover_by_theme("energetic", limit=5)
        
        assert isinstance(tracks, list)
        assert len(tracks) <= 5

    @pytest.mark.asyncio
    async def test_review_summary_output(self, review_discovery):
        """Test review summary output"""
        artist_id = "test_artist_001"
        summary = review_discovery.get_artist_review_summary(artist_id)
        
        assert summary is not None
        assert isinstance(summary, dict)


@pytest.mark.agent
@pytest.mark.integration
class TestHabitBreakerOutputs:
    """Test habit breaker agent outputs"""

    @pytest.fixture
    def habit_breaker(self):
        """Create HabitBreaker instance"""
        return HabitBreaker()

    @pytest.mark.asyncio
    async def test_listening_history_output(self, habit_breaker):
        """Test listening history output"""
        user_id = "test_user"
        history = habit_breaker.get_listening_history(user_id, limit=20)
        
        assert isinstance(history, list)
        assert len(history) <= 20

    @pytest.mark.asyncio
    async def test_habits_output(self, habit_breaker):
        """Test habits identification output"""
        user_id = "test_user"
        habits = habit_breaker.identify_habits(user_id)
        
        assert habits is not None
        assert isinstance(habits, (dict, list))

    @pytest.mark.asyncio
    async def test_diversity_score_output(self, habit_breaker):
        """Test diversity score output"""
        user_id = "test_user"
        score = habit_breaker.calculate_diversity_score(user_id)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 1.0


@pytest.mark.agent
@pytest.mark.integration
class TestRecommendationFuserOutputs:
    """Test recommendation fuser agent outputs"""

    @pytest.fixture
    def recommendation_fuser(self):
        """Create RecommendationFuser instance"""
        return RecommendationFuser()

    @pytest.mark.asyncio
    async def test_fused_output_structure(self, recommendation_fuser):
        """Test that fused output has correct structure"""
        source1 = [{"track_id": "t1", "confidence": 0.8}]
        source2 = [{"track_id": "t2", "confidence": 0.7}]
        
        fused = recommendation_fuser.fuse_recommendations(
            [source1, source2], limit=5
        )
        
        assert isinstance(fused, list)
        assert len(fused) <= 5

    @pytest.mark.asyncio
    async def test_fused_output_scores(self, recommendation_fuser):
        """Test that fused recommendations have combined scores"""
        source1 = [{"track_id": "t1", "confidence": 0.8}]
        source2 = [{"track_id": "t2", "confidence": 0.7}]
        
        fused = recommendation_fuser.fuse_recommendations(
            [source1, source2], limit=5
        )
        
        for rec in fused:
            assert "confidence" in rec or "combined_score" in rec

    @pytest.mark.asyncio
    async def test_deduplicated_output(self, recommendation_fuser):
        """Test that output is deduplicated"""
        recommendations = [
            {"track_id": "t1", "confidence": 0.8},
            {"track_id": "t1", "confidence": 0.7},
            {"track_id": "t2", "confidence": 0.9}
        ]
        
        deduped = recommendation_fuser.deduplicate(recommendations)
        
        track_ids = [r["track_id"] for r in deduped]
        assert len(track_ids) == len(set(track_ids))


@pytest.mark.agent
@pytest.mark.integration
class TestExplanationGeneratorOutputs:
    """Test explanation generator agent outputs"""

    @pytest.fixture
    def explanation_generator(self):
        """Create ExplanationGenerator instance"""
        return ExplanationGenerator()

    @pytest.mark.asyncio
    async def test_mood_explanation_output(self, explanation_generator):
        """Test mood explanation output"""
        recommendation = {"track": {"name": "Test"}}
        mood = "energetic"
        
        explanation = explanation_generator.generate_mood_explanation(
            recommendation, mood
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert mood in explanation.lower()

    @pytest.mark.asyncio
    async def test_similarity_explanation_output(self, explanation_generator):
        """Test similarity explanation output"""
        recommendation = {"track": {"name": "Test"}}
        similar_tracks = ["Track A", "Track B"]
        
        explanation = explanation_generator.generate_similarity_explanation(
            recommendation, similar_tracks
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0

    @pytest.mark.asyncio
    async def test_comprehensive_explanation_output(self, explanation_generator):
        """Test comprehensive explanation output"""
        recommendation = {"track": {"name": "Test"}}
        factors = {
            "mood": "energetic",
            "similarity": 0.85,
            "review_sentiment": "positive"
        }
        
        explanation = explanation_generator.generate_comprehensive_explanation(
            recommendation, factors
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        # Should be longer for comprehensive explanation
        assert len(explanation.split()) > 10


@pytest.mark.agent
@pytest.mark.integration
@pytest.mark.slow
class TestAgentOutputConsistency:
    """Test consistency across agent outputs"""

    @pytest.mark.asyncio
    async def test_intent_to_parser_consistency(self):
        """Test consistency between intent and parser outputs"""
        intent_recognizer = IntentRecognizer()
        query_parser = QueryParser()
        
        query = "I want energetic electronic music for coding"
        
        intent, _ = intent_recognizer.recognize(query)
        parsed = query_parser.parse(query)
        
        # If intent is music_recommendation, parser should extract mood/activity
        if "recommendation" in intent.lower():
            mood = getattr(parsed, "mood", None) or parsed.get("mood", "")
            activity = getattr(parsed, "activity", None) or parsed.get("activity", "")
            
            # Should have extracted something
            assert mood or activity or parsed.get("genres")

    @pytest.mark.asyncio
    async def test_parser_to_recommendation_consistency(self):
        """Test consistency between parser and recommendation outputs"""
        query_parser = QueryParser()
        mood_matcher = MoodActivityMatcher()
        
        query = "I want energetic music for coding"
        parsed = query_parser.parse(query)
        
        mood = getattr(parsed, "mood", None) or parsed.get("mood", "")
        activity = getattr(parsed, "activity", None) or parsed.get("activity", "")
        
        if mood:
            characteristics = mood_matcher.match_mood(mood)
            assert characteristics is not None

    @pytest.mark.asyncio
    async def test_recommendation_to_explanation_consistency(self):
        """Test consistency between recommendation and explanation outputs"""
        recommendation_fuser = RecommendationFuser()
        explanation_generator = ExplanationGenerator()
        
        source1 = [{"track_id": "t1", "confidence": 0.8, "track": {"name": "Test Song"}}]
        fused = recommendation_fuser.fuse_recommendations([source1], limit=1)
        
        if fused:
            explanation = explanation_generator.generate_mood_explanation(
                fused[0], "energetic"
            )
            assert isinstance(explanation, str)
            assert len(explanation) > 0

    @pytest.mark.asyncio
    async def test_multi_agent_pipeline_consistency(self):
        """Test consistency across full multi-agent pipeline"""
        intent_recognizer = IntentRecognizer()
        query_parser = QueryParser()
        mood_matcher = MoodActivityMatcher()
        response_generator = ResponseGenerator()
        
        query = "I want energetic music for coding"
        
        # Step 1: Intent
        intent, _ = intent_recognizer.recognize(query)
        
        # Step 2: Parse
        parsed = query_parser.parse(query)
        
        # Step 3: Match
        mood = getattr(parsed, "mood", None) or parsed.get("mood", "")
        characteristics = mood_matcher.match_mood(mood) if mood else None
        
        # Step 4: Generate response
        response = response_generator.generate(
            query, intent, [], [], {"mood": mood, "characteristics": characteristics}
        )
        
        # All steps should complete successfully
        assert intent is not None
        assert parsed is not None
        assert response is not None
        assert len(response) > 0
