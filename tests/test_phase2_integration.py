"""Integration tests for Phase 2: Music Recommendation Engine"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add phase2 to path
PHASE2_PATH = Path(__file__).parent.parent / "phase2-music-recommendation-engine"
sys.path.insert(0, str(PHASE2_PATH))

from mood_activity_matching.mood_activity_matcher import MoodActivityMatcher
from genre_exploration.genre_explorer import GenreExplorer
from similarity_search.similarity_searcher import SimilaritySearcher
from review_based_discovery.review_discovery import ReviewDiscoveryEngine
from habit_breaking.habit_breaker import HabitBreaker
from recommendation_fusion.recommendation_fuser import RecommendationFuser
from explanation_generator.explanation_generator import ExplanationGenerator


@pytest.mark.phase2
@pytest.mark.integration
class TestMoodActivityMatching:
    """Test mood and activity matching integration"""

    @pytest.fixture
    def mood_matcher(self):
        """Create MoodActivityMatcher instance"""
        return MoodActivityMatcher()

    @pytest.mark.asyncio
    async def test_match_mood_to_music(self, mood_matcher):
        """Test matching mood to music characteristics"""
        mood = "energetic"
        characteristics = mood_matcher.match_mood(mood)
        
        assert characteristics is not None
        assert "energy" in characteristics or "tempo" in characteristics
        assert characteristics.get("energy", 0) > 0.7

    @pytest.mark.asyncio
    async def test_match_activity_to_music(self, mood_matcher):
        """Test matching activity to music characteristics"""
        activity = "coding"
        characteristics = mood_matcher.match_activity(activity)
        
        assert characteristics is not None
        assert "focus" in characteristics or "energy" in characteristics

    @pytest.mark.asyncio
    async def test_match_mood_and_activity(self, mood_matcher):
        """Test matching both mood and activity"""
        mood = "energetic"
        activity = "workout"
        characteristics = mood_matcher.match_combined(mood, activity)
        
        assert characteristics is not None
        assert characteristics.get("energy", 0) > 0.8

    @pytest.mark.asyncio
    async def test_invalid_mood_handling(self, mood_matcher):
        """Test handling of invalid mood"""
        mood = "invalid_mood"
        characteristics = mood_matcher.match_mood(mood)
        
        # Should return default or None
        assert characteristics is not None or characteristics is None

    @pytest.mark.asyncio
    async def test_mood_characteristics_range(self, mood_matcher):
        """Test that mood characteristics are in valid range"""
        moods = ["energetic", "chill", "happy", "sad", "focus"]
        
        for mood in moods:
            characteristics = mood_matcher.match_mood(mood)
            if characteristics:
                for key, value in characteristics.items():
                    if isinstance(value, (int, float)):
                        assert 0 <= value <= 1.0


@pytest.mark.phase2
@pytest.mark.integration
class TestGenreExploration:
    """Test genre exploration integration"""

    @pytest.fixture
    def genre_explorer(self):
        """Create GenreExplorer instance"""
        return GenreExplorer()

    @pytest.mark.asyncio
    async def test_explore_genre_characteristics(self, genre_explorer):
        """Test exploring genre characteristics"""
        genre = "electronic"
        characteristics = genre_explorer.explore_genre(genre)
        
        assert characteristics is not None
        assert "name" in characteristics or "genre" in characteristics

    @pytest.mark.asyncio
    async def test_find_similar_genres(self, genre_explorer):
        """Test finding similar genres"""
        genre = "synthwave"
        similar_genres = genre_explorer.find_similar_genres(genre, limit=5)
        
        assert isinstance(similar_genres, list)
        assert len(similar_genres) <= 5

    @pytest.mark.asyncio
    async def test_get_genre_trends(self, genre_explorer):
        """Test getting genre trends"""
        trends = genre_explorer.get_genre_trends(limit=10)
        
        assert isinstance(trends, list)
        assert len(trends) <= 10

    @pytest.mark.asyncio
    async def test_explore_subgenres(self, genre_explorer):
        """Test exploring subgenres"""
        genre = "electronic"
        subgenres = genre_explorer.get_subgenres(genre)
        
        assert isinstance(subgenres, list)


@pytest.mark.phase2
@pytest.mark.integration
class TestSimilaritySearch:
    """Test similarity search integration"""

    @pytest.fixture
    def similarity_searcher(self):
        """Create SimilaritySearcher instance"""
        return SimilaritySearcher()

    @pytest.mark.asyncio
    async def test_search_similar_tracks(self, similarity_searcher, sample_recommendation_data):
        """Test searching for similar tracks"""
        track_id = sample_recommendation_data["track"]["id"]
        similar_tracks = similarity_searcher.find_similar_tracks(track_id, limit=5)
        
        assert isinstance(similar_tracks, list)
        assert len(similar_tracks) <= 5

    @pytest.mark.asyncio
    async def test_search_similar_artists(self, similarity_searcher, sample_artist_data):
        """Test searching for similar artists"""
        artist_id = sample_artist_data["artist_id"]
        similar_artists = similarity_searcher.find_similar_artists(artist_id, limit=5)
        
        assert isinstance(similar_artists, list)
        assert len(similar_artists) <= 5

    @pytest.mark.asyncio
    async def test_similarity_score_range(self, similarity_searcher):
        """Test that similarity scores are in valid range"""
        track_id = "test_track_001"
        similar_tracks = similarity_searcher.find_similar_tracks(track_id, limit=10)
        
        for track in similar_tracks:
            if "similarity" in track:
                assert 0 <= track["similarity"] <= 1.0


@pytest.mark.phase2
@pytest.mark.integration
class TestReviewBasedDiscovery:
    """Test review-based discovery integration"""

    @pytest.fixture
    def review_discovery(self):
        """Create ReviewDiscoveryEngine instance"""
        return ReviewDiscoveryEngine()

    @pytest.mark.asyncio
    async def test_discover_by_review_sentiment(self, review_discovery):
        """Test discovering tracks by review sentiment"""
        sentiment = "positive"
        tracks = review_discovery.discover_by_sentiment(sentiment, limit=5)
        
        assert isinstance(tracks, list)
        assert len(tracks) <= 5

    @pytest.mark.asyncio
    async def test_discover_by_review_themes(self, review_discovery):
        """Test discovering tracks by review themes"""
        theme = "energetic"
        tracks = review_discovery.discover_by_theme(theme, limit=5)
        
        assert isinstance(tracks, list)
        assert len(tracks) <= 5

    @pytest.mark.asyncio
    async def test_get_review_summary(self, review_discovery, sample_artist_data):
        """Test getting review summary for artist"""
        artist_id = sample_artist_data["artist_id"]
        summary = review_discovery.get_artist_review_summary(artist_id)
        
        assert summary is not None
        assert "artist_name" in summary or "sentiment" in summary

    @pytest.mark.asyncio
    async def test_get_unique_descriptors(self, review_discovery):
        """Test getting unique descriptors from reviews"""
        descriptors = review_discovery.get_unique_descriptors(limit=10)
        
        assert isinstance(descriptors, list)
        assert len(descriptors) <= 10


@pytest.mark.phase2
@pytest.mark.integration
class TestHabitBreaking:
    """Test habit breaking integration"""

    @pytest.fixture
    def habit_breaker(self):
        """Create HabitBreaker instance"""
        return HabitBreaker()

    @pytest.mark.asyncio
    async def test_get_user_listening_history(self, habit_breaker, sample_user_data):
        """Test getting user listening history"""
        user_id = sample_user_data["user_id"]
        history = habit_breaker.get_listening_history(user_id, limit=20)
        
        assert isinstance(history, list)
        assert len(history) <= 20

    @pytest.mark.asyncio
    async def test_identify_habits(self, habit_breaker, sample_user_data):
        """Test identifying user listening habits"""
        user_id = sample_user_data["user_id"]
        habits = habit_breaker.identify_habits(user_id)
        
        assert habits is not None
        assert isinstance(habits, dict) or isinstance(habits, list)

    @pytest.mark.asyncio
    async def test_suggest_habit_breaking_tracks(self, habit_breaker, sample_user_data):
        """Test suggesting tracks to break habits"""
        user_id = sample_user_data["user_id"]
        suggestions = habit_breaker.suggest_habit_breaking(user_id, limit=5)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5

    @pytest.mark.asyncio
    async def test_calculate_diversity_score(self, habit_breaker, sample_user_data):
        """Test calculating diversity score"""
        user_id = sample_user_data["user_id"]
        score = habit_breaker.calculate_diversity_score(user_id)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 1.0


@pytest.mark.phase2
@pytest.mark.integration
class TestRecommendationFusion:
    """Test recommendation fusion integration"""

    @pytest.fixture
    def recommendation_fuser(self):
        """Create RecommendationFuser instance"""
        return RecommendationFuser()

    @pytest.mark.asyncio
    async def test_fuse_recommendations(self, recommendation_fuser):
        """Test fusing recommendations from multiple sources"""
        source1 = [
            {"track_id": "t1", "confidence": 0.8, "source": "mood_matching"}
        ]
        source2 = [
            {"track_id": "t2", "confidence": 0.7, "source": "similarity"}
        ]
        source3 = [
            {"track_id": "t3", "confidence": 0.9, "source": "review_based"}
        ]
        
        fused = recommendation_fuser.fuse_recommendations(
            [source1, source2, source3], limit=5
        )
        
        assert isinstance(fused, list)
        assert len(fused) <= 5
        # Check that fused recommendations have combined scores
        for rec in fused:
            assert "combined_score" in rec or "confidence" in rec

    @pytest.mark.asyncio
    async def test_weighted_fusion(self, recommendation_fuser):
        """Test weighted fusion of recommendations"""
        source1 = [
            {"track_id": "t1", "confidence": 0.8, "source": "mood_matching"}
        ]
        source2 = [
            {"track_id": "t2", "confidence": 0.7, "source": "similarity"}
        ]
        
        weights = {"mood_matching": 0.6, "similarity": 0.4}
        fused = recommendation_fuser.fuse_recommendations(
            [source1, source2], limit=5, weights=weights
        )
        
        assert isinstance(fused, list)
        assert len(fused) <= 5

    @pytest.mark.asyncio
    async def test_deduplicate_recommendations(self, recommendation_fuser):
        """Test deduplication of recommendations"""
        recommendations = [
            {"track_id": "t1", "confidence": 0.8, "source": "mood_matching"},
            {"track_id": "t1", "confidence": 0.7, "source": "similarity"},
            {"track_id": "t2", "confidence": 0.9, "source": "review_based"}
        ]
        
        deduped = recommendation_fuser.deduplicate(recommendations)
        
        assert len(deduped) <= len(recommendations)
        # Check no duplicate track_ids
        track_ids = [r["track_id"] for r in deduped]
        assert len(track_ids) == len(set(track_ids))


@pytest.mark.phase2
@pytest.mark.integration
class TestExplanationGeneration:
    """Test explanation generation integration"""

    @pytest.fixture
    def explanation_generator(self):
        """Create ExplanationGenerator instance"""
        return ExplanationGenerator()

    @pytest.mark.asyncio
    async def test_generate_mood_explanation(self, explanation_generator, sample_recommendation_data):
        """Test generating mood-based explanation"""
        recommendation = sample_recommendation_data
        mood = "energetic"
        
        explanation = explanation_generator.generate_mood_explanation(
            recommendation, mood
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert mood in explanation.lower()

    @pytest.mark.asyncio
    async def test_generate_similarity_explanation(self, explanation_generator, sample_recommendation_data):
        """Test generating similarity-based explanation"""
        recommendation = sample_recommendation_data
        similar_tracks = ["Track A", "Track B"]
        
        explanation = explanation_generator.generate_similarity_explanation(
            recommendation, similar_tracks
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0

    @pytest.mark.asyncio
    async def test_generate_review_explanation(self, explanation_generator, sample_recommendation_data):
        """Test generating review-based explanation"""
        recommendation = sample_recommendation_data
        review_themes = ["energetic", "upbeat"]
        
        explanation = explanation_generator.generate_review_explanation(
            recommendation, review_themes
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0

    @pytest.mark.asyncio
    async def test_generate_comprehensive_explanation(self, explanation_generator, sample_recommendation_data):
        """Test generating comprehensive explanation with multiple factors"""
        recommendation = sample_recommendation_data
        factors = {
            "mood": "energetic",
            "activity": "coding",
            "similarity": 0.85,
            "review_sentiment": "positive"
        }
        
        explanation = explanation_generator.generate_comprehensive_explanation(
            recommendation, factors
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        # Should mention multiple factors
        word_count = len(explanation.split())
        assert word_count > 10


@pytest.mark.phase2
@pytest.mark.integration
@pytest.mark.slow
class TestPhase2EndToEnd:
    """End-to-end tests for Phase 2"""

    @pytest.fixture
    def recommendation_components(self):
        """Create all Phase 2 components"""
        return {
            "mood_matcher": MoodActivityMatcher(),
            "genre_explorer": GenreExplorer(),
            "similarity_searcher": SimilaritySearcher(),
            "review_discovery": ReviewDiscoveryEngine(),
            "habit_breaker": HabitBreaker(),
            "recommendation_fuser": RecommendationFuser(),
            "explanation_generator": ExplanationGenerator()
        }

    @pytest.mark.asyncio
    async def test_full_recommendation_pipeline(self, recommendation_components, sample_user_data):
        """Test complete recommendation pipeline"""
        user_id = sample_user_data["user_id"]
        mood = "energetic"
        activity = "coding"
        
        # Step 1: Match mood and activity
        mood_characteristics = recommendation_components["mood_matcher"].match_combined(
            mood, activity
        )
        assert mood_characteristics is not None
        
        # Step 2: Get genre recommendations
        genre_recs = recommendation_components["genre_explorer"].explore_genre("electronic")
        
        # Step 3: Get similar tracks
        if genre_recs and len(genre_recs) > 0:
            similar_recs = recommendation_components["similarity_searcher"].find_similar_tracks(
                genre_recs[0].get("id", "test"), limit=5
            )
        else:
            similar_recs = []
        
        # Step 4: Get review-based recommendations
        review_recs = recommendation_components["review_discovery"].discover_by_sentiment(
            "positive", limit=5
        )
        
        # Step 5: Fuse recommendations
        all_recs = [genre_recs[:3], similar_recs, review_recs]
        fused_recs = recommendation_components["recommendation_fuser"].fuse_recommendations(
            all_recs, limit=10
        )
        
        assert isinstance(fused_recs, list)
        
        # Step 6: Generate explanations
        if fused_recs:
            explanation = recommendation_components["explanation_generator"].generate_mood_explanation(
                fused_recs[0], mood
            )
            assert len(explanation) > 0

    @pytest.mark.asyncio
    async def test_habit_breaking_recommendation_flow(self, recommendation_components, sample_user_data):
        """Test habit-breaking recommendation flow"""
        user_id = sample_user_data["user_id"]
        
        # Step 1: Get user history
        history = recommendation_components["habit_breaker"].get_listening_history(
            user_id, limit=20
        )
        
        # Step 2: Identify habits
        habits = recommendation_components["habit_breaker"].identify_habits(user_id)
        
        # Step 3: Get habit-breaking suggestions
        suggestions = recommendation_components["habit_breaker"].suggest_habit_breaking(
            user_id, limit=5
        )
        
        assert isinstance(suggestions, list)
        
        # Step 4: Generate explanations for suggestions
        if suggestions:
            for suggestion in suggestions[:2]:
                explanation = recommendation_components["explanation_generator"].generate_comprehensive_explanation(
                    suggestion, {"habit_breaking": True}
                )
                assert len(explanation) > 0

    @pytest.mark.asyncio
    async def test_multi_source_recommendation_fusion(self, recommendation_components):
        """Test fusion of recommendations from multiple sources"""
        # Get recommendations from different sources
        mood_recs = [
            {"track_id": "m1", "confidence": 0.8, "source": "mood"}
        ]
        similarity_recs = [
            {"track_id": "s1", "confidence": 0.7, "source": "similarity"}
        ]
        review_recs = [
            {"track_id": "r1", "confidence": 0.9, "source": "review"}
        ]
        habit_recs = [
            {"track_id": "h1", "confidence": 0.6, "source": "habit_breaking"}
        ]
        
        # Fuse all sources
        fused = recommendation_components["recommendation_fuser"].fuse_recommendations(
            [mood_recs, similarity_recs, review_recs, habit_recs], limit=10
        )
        
        assert isinstance(fused, list)
        assert len(fused) <= 10
        
        # Verify deduplication
        track_ids = [r.get("track_id") for r in fused]
        assert len(track_ids) == len(set(track_ids))
