"""
Explainability Engine for Phase 2: Music Recommendation Engine.
Generates detailed explanations for recommendations.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from .schemas import Recommendation, RecommendationRequest, RecommendationCandidate


logger = structlog.get_logger(__name__)


class ExplanationFactors:
    """Factors that influence a recommendation."""
    
    def __init__(self):
        self.song_selection_reasons: List[str] = []
        self.artist_selection_reasons: List[str] = []
        self.user_preference_influences: List[str] = []
        self.conversation_context_influences: List[str] = []
        self.discovery_benefits: List[str] = []
        self.scores: Dict[str, float] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "song_selection_reasons": self.song_selection_reasons,
            "artist_selection_reasons": self.artist_selection_reasons,
            "user_preference_influences": self.user_preference_influences,
            "conversation_context_influences": self.conversation_context_influences,
            "discovery_benefits": self.discovery_benefits,
            "scores": self.scores
        }


class ExplainabilityEngine:
    """
    Engine for generating detailed explanations for recommendations.
    """
    
    def __init__(self, storage_dir: str = "./data/explanations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.explanations_file = self.storage_dir / "recommendation_explanations.json"
    
    def generate_explanation(
        self,
        recommendation: Recommendation,
        candidate: RecommendationCandidate,
        request: RecommendationRequest
    ) -> Dict[str, Any]:
        """
        Generate detailed explanation for a recommendation.
        
        Args:
            recommendation: The recommendation
            candidate: The candidate with scores
            request: The original request
            
        Returns:
            Dictionary with detailed explanation factors
        """
        factors = ExplanationFactors()
        
        # Song selection reasons
        self._explain_song_selection(recommendation, candidate, factors)
        
        # Artist selection reasons
        self._explain_artist_selection(recommendation, candidate, factors)
        
        # User preference influences
        self._explain_user_preferences(recommendation, candidate, request, factors)
        
        # Conversation context influences
        self._explain_conversation_context(recommendation, candidate, request, factors)
        
        # Discovery benefits
        self._explain_discovery_benefits(recommendation, candidate, request, factors)
        
        # Store scores
        factors.scores = {
            "novelty_score": candidate.novelty_score,
            "diversity_score": candidate.diversity_score,
            "intent_match_score": candidate.intent_match_score,
            "mood_match_score": candidate.mood_match_score,
            "activity_match_score": candidate.activity_match_score,
            "discovery_match_score": candidate.discovery_match_score,
            "context_match_score": candidate.context_match_score,
            "final_confidence": recommendation.confidence
        }
        
        return factors.to_dict()
    
    def _explain_song_selection(
        self,
        recommendation: Recommendation,
        candidate: RecommendationCandidate,
        factors: ExplanationFactors
    ) -> None:
        """Explain why this song was selected."""
        track = recommendation.track
        
        # Strategy-based explanation
        strategy_explanations = {
            "review_based": "This song was selected because its artist has highly positive reviews and strong discovery potential.",
            "mood_activity": "This song was selected because its audio features match your requested mood and activity.",
            "similarity_search": "This song was selected because it's similar to artists you've shown interest in.",
            "habit_breaking": "This song was selected to help you break your usual listening patterns with something novel.",
            "genre_exploration": "This song was selected to explore genres you're interested in."
        }
        
        if candidate.strategy in strategy_explanations:
            factors.song_selection_reasons.append(strategy_explanations[candidate.strategy])
        
        # Audio features explanation
        if track.audio_features:
            if track.audio_features.energy > 0.7:
                factors.song_selection_reasons.append(f"High energy level ({track.audio_features.energy:.2f}) makes this track energetic and engaging.")
            if track.audio_features.valence > 0.7:
                factors.song_selection_reasons.append(f"Positive mood ({track.audio_features.valence:.2f}) creates an uplifting listening experience.")
            if track.audio_features.danceability > 0.7:
                factors.song_selection_reasons.append(f"High danceability ({track.audio_features.danceability:.2f}) makes this track great for movement.")
            if track.audio_features.acousticness > 0.6:
                factors.song_selection_reasons.append(f"Acoustic nature ({track.audio_features.acousticness:.2f}) provides a natural, organic sound.")
            if track.audio_features.instrumentalness > 0.6:
                factors.song_selection_reasons.append(f"Instrumental focus ({track.audio_features.instrumentalness:.2f}) makes this suitable for background listening.")
        
        # Release year explanation
        if track.release_year:
            if track.release_year >= 2023:
                factors.song_selection_reasons.append(f"Recent release ({track.release_year}) brings you fresh, contemporary music.")
            elif track.release_year >= 2010:
                factors.song_selection_reasons.append(f"Modern track from {track.release_year} with contemporary production.")
            else:
                factors.song_selection_reasons.append(f"Classic track from {track.release_year} with timeless appeal.")
    
    def _explain_artist_selection(
        self,
        recommendation: Recommendation,
        candidate: RecommendationCandidate,
        factors: ExplanationFactors
    ) -> None:
        """Explain why this artist was selected."""
        artist = recommendation.track.artist_name
        
        # Popularity explanation
        popularity = recommendation.track.popularity
        if popularity < 30:
            factors.artist_selection_reasons.append(f"{artist} is an emerging artist with unique sounds waiting to be discovered.")
        elif popularity < 60:
            factors.artist_selection_reasons.append(f"{artist} has a growing following and offers a balanced mix of familiarity and novelty.")
        elif popularity < 80:
            factors.artist_selection_reasons.append(f"{artist} is well-established with a proven track record of quality music.")
        else:
            factors.artist_selection_reasons.append(f"{artist} is highly popular and widely appreciated by listeners.")
        
        # Genre explanation
        if recommendation.track.genres:
            genres_str = ", ".join(recommendation.track.genres[:3])
            factors.artist_selection_reasons.append(f"{artist} specializes in {genres_str}, matching your musical interests.")
        
        # Similar artists explanation
        if recommendation.track.similar_artists:
            factors.artist_selection_reasons.append(f"{artist} is connected to other artists you might enjoy, expanding your musical network.")
    
    def _explain_user_preferences(
        self,
        recommendation: Recommendation,
        candidate: RecommendationCandidate,
        request: RecommendationRequest,
        factors: ExplanationFactors
    ) -> None:
        """Explain which user preferences influenced the recommendation."""
        # Mood preference
        if request.mood:
            factors.user_preference_influences.append(f"Your requested mood '{request.mood}' influenced this selection.")
        
        # Activity preference
        if request.activity:
            factors.user_preference_influences.append(f"Your activity '{request.activity}' was considered for this recommendation.")
        
        # Discovery preference
        if request.discovery_preference:
            if request.discovery_preference == "novel":
                factors.user_preference_influences.append("Your preference for novel discoveries led to this less familiar choice.")
            elif request.discovery_preference == "familiar":
                factors.user_preference_influences.append("Your preference for familiar music influenced this selection.")
            elif request.discovery_preference == "balanced":
                factors.user_preference_influences.append("Your balanced discovery preference guided this recommendation.")
        
        # Preferred genres
        if request.preferred_genres:
            matching_genres = [g for g in request.preferred_genres if g.lower() in [x.lower() for x in recommendation.track.genres]]
            if matching_genres:
                factors.user_preference_influences.append(f"Your preference for {', '.join(matching_genres)} influenced this choice.")
        
        # Preferred artists
        if request.preferred_artists and recommendation.track.artist_id in request.preferred_artists:
            factors.user_preference_influences.append("This artist is among your preferred artists.")
        
        # Energy level preference
        if request.energy_level:
            if recommendation.track.audio_features:
                energy = recommendation.track.audio_features.energy
                if request.energy_level == "high" and energy > 0.6:
                    factors.user_preference_influences.append("High energy level matches your preference.")
                elif request.energy_level == "low" and energy < 0.4:
                    factors.user_preference_influences.append("Low energy level matches your preference.")
                elif request.energy_level == "medium" and 0.4 <= energy <= 0.6:
                    factors.user_preference_influences.append("Medium energy level matches your preference.")
        
        # Popularity filter
        if request.popularity_filter:
            if request.popularity_filter == "popular" and recommendation.track.popularity > 70:
                factors.user_preference_influences.append("Popular track matches your preference.")
            elif request.popularity_filter == "niche" and recommendation.track.popularity < 30:
                factors.user_preference_influences.append("Niche track matches your preference.")
    
    def _explain_conversation_context(
        self,
        recommendation: Recommendation,
        candidate: RecommendationCandidate,
        request: RecommendationRequest,
        factors: ExplanationFactors
    ) -> None:
        """Explain which conversation context influenced the recommendation."""
        # User intent
        if request.user_intent:
            factors.conversation_context_influences.append(f"Your intent '{request.user_intent}' shaped this recommendation.")
        
        # Previously recommended songs (avoidance)
        if request.previously_recommended_songs:
            factors.conversation_context_influences.append("Your listening history was used to avoid repetitive recommendations.")
        
        # Discovery history
        if request.discovery_history:
            factors.conversation_context_influences.append("Your discovery patterns informed this recommendation to align with your exploration style.")
        
        # Recently discussed genres
        if request.recently_discussed_genres:
            matching_genres = [g for g in request.recently_discussed_genres if g.lower() in [x.lower() for x in recommendation.track.genres]]
            if matching_genres:
                factors.conversation_context_influences.append(f"Recently discussed genres {', '.join(matching_genres)} influenced this choice.")
        
        # Session context
        if request.session_id:
            factors.conversation_context_influences.append("Current session context was considered for personalized recommendations.")
    
    def _explain_discovery_benefits(
        self,
        recommendation: Recommendation,
        candidate: RecommendationCandidate,
        request: RecommendationRequest,
        factors: ExplanationFactors
    ) -> None:
        """Explain how this recommendation helps users discover new music."""
        # Novelty-based discovery
        if candidate.novelty_score > 0.7:
            factors.discovery_benefits.append("High novelty score indicates this track will introduce you to new sounds and artists.")
        elif candidate.novelty_score > 0.5:
            factors.discovery_benefits.append("Moderate novelty provides a balance between familiarity and discovery.")
        
        # Diversity-based discovery
        if candidate.diversity_score > 0.7:
            factors.discovery_benefits.append("High diversity score ensures this recommendation differs from your usual listening patterns.")
        
        # Genre exploration
        if recommendation.track.genres:
            factors.discovery_benefits.append(f"Exploring {', '.join(recommendation.track.genres[:2])} expands your musical horizons.")
        
        # Artist discovery
        if recommendation.track.popularity < 50:
            factors.discovery_benefits.append("Discovering emerging artists helps you find hidden gems before they become mainstream.")
        
        # Similar artists
        if recommendation.track.similar_artists:
            factors.discovery_benefits.append("This artist connects to a network of similar artists for further exploration.")
        
        # Strategy-specific discovery
        if candidate.strategy == "review_based":
            factors.discovery_benefits.append("Review-based discovery highlights artists with critical acclaim you might have missed.")
        elif candidate.strategy == "habit_breaking":
            factors.discovery_benefits.append("Habit-breaking recommendations challenge your usual patterns to broaden your taste.")
        elif candidate.strategy == "genre_exploration":
            factors.discovery_benefits.append("Genre exploration helps you dive deeper into musical styles you enjoy.")
    
    def store_explanation(
        self,
        user_id: str,
        session_id: str,
        recommendation_id: str,
        explanation: Dict[str, Any]
    ) -> bool:
        """
        Store explanation in recommendation_explanations.json.
        
        Args:
            user_id: User ID
            session_id: Session ID
            recommendation_id: Recommendation ID
            explanation: Explanation factors
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing explanations
            explanations = []
            if self.explanations_file.exists():
                with open(self.explanations_file, 'r', encoding='utf-8') as f:
                    explanations = json.load(f)
            
            # Add new explanation
            explanation_entry = {
                "user_id": user_id,
                "session_id": session_id,
                "recommendation_id": recommendation_id,
                "explanation": explanation,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            explanations.append(explanation_entry)
            
            # Keep only last 1000 explanations
            if len(explanations) > 1000:
                explanations = explanations[-1000:]
            
            # Save
            with open(self.explanations_file, 'w', encoding='utf-8') as f:
                json.dump(explanations, f, indent=2, ensure_ascii=False)
            
            logger.info(
                "Explanation stored",
                user_id=user_id,
                session_id=session_id,
                recommendation_id=recommendation_id
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to store explanation",
                user_id=user_id,
                recommendation_id=recommendation_id,
                error=str(e)
            )
            return False
    
    def get_user_explanations(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get explanations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of explanations to return
            
        Returns:
            List of explanations
        """
        try:
            if not self.explanations_file.exists():
                return []
            
            with open(self.explanations_file, 'r', encoding='utf-8') as f:
                explanations = json.load(f)
            
            # Filter by user
            user_explanations = [
                e for e in explanations
                if e.get("user_id") == user_id
            ]
            
            # Sort by generation time (newest first)
            user_explanations.sort(
                key=lambda x: x.get("generated_at", ""),
                reverse=True
            )
            
            if limit:
                user_explanations = user_explanations[:limit]
            
            return user_explanations
            
        except Exception as e:
            logger.error(
                "Failed to get user explanations",
                user_id=user_id,
                error=str(e)
            )
            return []


class MockExplainabilityEngine:
    """Mock implementation for testing."""
    
    def __init__(self):
        self._explanations: List[Dict[str, Any]] = []
    
    def generate_explanation(
        self,
        recommendation: Recommendation,
        candidate: RecommendationCandidate,
        request: RecommendationRequest
    ) -> Dict[str, Any]:
        """Generate mock explanation."""
        return {
            "song_selection_reasons": ["Mock song selection reason"],
            "artist_selection_reasons": ["Mock artist selection reason"],
            "user_preference_influences": ["Mock user preference influence"],
            "conversation_context_influences": ["Mock context influence"],
            "discovery_benefits": ["Mock discovery benefit"],
            "scores": {
                "novelty_score": 0.5,
                "diversity_score": 0.5,
                "intent_match_score": 0.5,
                "mood_match_score": 0.5,
                "activity_match_score": 0.5,
                "discovery_match_score": 0.5,
                "context_match_score": 0.5,
                "final_confidence": 0.5
            }
        }
    
    def store_explanation(
        self,
        user_id: str,
        session_id: str,
        recommendation_id: str,
        explanation: Dict[str, Any]
    ) -> bool:
        """Store explanation in memory."""
        self._explanations.append({
            "user_id": user_id,
            "session_id": session_id,
            "recommendation_id": recommendation_id,
            "explanation": explanation,
            "generated_at": datetime.utcnow().isoformat()
        })
        return True
    
    def get_user_explanations(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get user explanations from memory."""
        user_explanations = [
            e for e in self._explanations
            if e.get("user_id") == user_id
        ]
        
        user_explanations.sort(
            key=lambda x: x.get("generated_at", ""),
            reverse=True
        )
        
        if limit:
            user_explanations = user_explanations[:limit]
        
        return user_explanations
