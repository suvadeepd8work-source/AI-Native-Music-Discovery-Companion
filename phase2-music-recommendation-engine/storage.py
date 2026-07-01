"""
Structured recommendation storage for Phase 2: Music Recommendation Engine.
Stores recommendations with full metadata for analysis and tracking.
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog
from .schemas import StoredRecommendation, Track, Artist, Album


logger = structlog.get_logger(__name__)


class RecommendationStorage:
    """
    Storage manager for structured recommendations.
    Uses JSON files for persistence.
    """
    
    def __init__(self, storage_dir: str = "./data/recommendations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_dir(self, user_id: str) -> Path:
        """Get storage directory for a specific user."""
        user_dir = self.storage_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _get_recommendation_file_path(self, user_id: str, recommendation_id: str) -> Path:
        """Get file path for a specific recommendation."""
        user_dir = self._get_user_dir(user_id)
        return user_dir / f"{recommendation_id}.json"
    
    def _get_history_file_path(self, user_id: str) -> Path:
        """Get file path for recommendation history."""
        user_dir = self._get_user_dir(user_id)
        return user_dir / "recommendation_history.json"
    
    def _generate_recommendation_id(self) -> str:
        """Generate a unique recommendation ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"rec_{timestamp}"
    
    def store_recommendation(
        self,
        recommendation: StoredRecommendation
    ) -> bool:
        """
        Store a recommendation with full metadata.
        
        Args:
            recommendation: StoredRecommendation object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_recommendation_file_path(
                recommendation.user_id,
                recommendation.recommendation_id
            )
            
            data = {
                "recommendation_id": recommendation.recommendation_id,
                "user_id": recommendation.user_id,
                "session_id": recommendation.session_id,
                "track": recommendation.track.model_dump(),
                "artist": recommendation.artist.model_dump(),
                "album": recommendation.album.model_dump() if recommendation.album else None,
                "confidence": recommendation.confidence,
                "explanation": recommendation.explanation,
                "strategies_used": recommendation.strategies_used,
                "generated_at": recommendation.generated_at.isoformat(),
                "user_feedback": recommendation.user_feedback,
                "was_played": recommendation.was_played,
                "play_duration_ms": recommendation.play_duration_ms
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Update history
            self._update_history(recommendation)
            
            logger.info(
                "Recommendation stored",
                recommendation_id=recommendation.recommendation_id,
                user_id=recommendation.user_id,
                track_name=recommendation.track.track_name
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to store recommendation",
                recommendation_id=recommendation.recommendation_id,
                error=str(e)
            )
            return False
    
    def get_recommendation(
        self,
        user_id: str,
        recommendation_id: str
    ) -> Optional[StoredRecommendation]:
        """
        Retrieve a stored recommendation.
        
        Args:
            user_id: User ID
            recommendation_id: Recommendation ID
            
        Returns:
            StoredRecommendation or None if not found
        """
        try:
            file_path = self._get_recommendation_file_path(user_id, recommendation_id)
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return StoredRecommendation(
                recommendation_id=data["recommendation_id"],
                user_id=data["user_id"],
                session_id=data["session_id"],
                track=Track(**data["track"]),
                artist=Artist(**data["artist"]),
                album=Album(**data["album"]) if data.get("album") else None,
                confidence=data["confidence"],
                explanation=data["explanation"],
                strategies_used=data["strategies_used"],
                generated_at=datetime.fromisoformat(data["generated_at"]),
                user_feedback=data.get("user_feedback"),
                was_played=data.get("was_played", False),
                play_duration_ms=data.get("play_duration_ms")
            )
            
        except Exception as e:
            logger.error(
                "Failed to retrieve recommendation",
                recommendation_id=recommendation_id,
                error=str(e)
            )
            return None
    
    def update_recommendation_feedback(
        self,
        user_id: str,
        recommendation_id: str,
        feedback: str,
        was_played: bool = False,
        play_duration_ms: Optional[int] = None
    ) -> bool:
        """
        Update recommendation with user feedback.
        
        Args:
            user_id: User ID
            recommendation_id: Recommendation ID
            feedback: User feedback (liked, disliked, neutral)
            was_played: Whether track was played
            play_duration_ms: Play duration in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            recommendation = self.get_recommendation(user_id, recommendation_id)
            
            if not recommendation:
                logger.warning(
                    "Recommendation not found for feedback update",
                    recommendation_id=recommendation_id
                )
                return False
            
            recommendation.user_feedback = feedback
            recommendation.was_played = was_played
            recommendation.play_duration_ms = play_duration_ms
            
            return self.store_recommendation(recommendation)
            
        except Exception as e:
            logger.error(
                "Failed to update recommendation feedback",
                recommendation_id=recommendation_id,
                error=str(e)
            )
            return False
    
    def get_user_recommendations(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[StoredRecommendation]:
        """
        Get all recommendations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations to return
            
        Returns:
            List of StoredRecommendation
        """
        try:
            user_dir = self._get_user_dir(user_id)
            
            if not user_dir.exists():
                return []
            
            recommendations = []
            
            for file_path in user_dir.glob("rec_*.json"):
                if file_path.name == "recommendation_history.json":
                    continue
                
                recommendation_id = file_path.stem
                recommendation = self.get_recommendation(user_id, recommendation_id)
                
                if recommendation:
                    recommendations.append(recommendation)
            
            # Sort by generation time (newest first)
            recommendations.sort(key=lambda r: r.generated_at, reverse=True)
            
            if limit:
                recommendations = recommendations[:limit]
            
            return recommendations
            
        except Exception as e:
            logger.error(
                "Failed to get user recommendations",
                user_id=user_id,
                error=str(e)
            )
            return []
    
    def _update_history(self, recommendation: StoredRecommendation) -> None:
        """Update recommendation history file."""
        try:
            history_file = self._get_history_file_path(recommendation.user_id)
            
            # Load existing history
            history = []
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # Add new entry
            history_entry = {
                "recommendation_id": recommendation.recommendation_id,
                "track_id": recommendation.track.track_id,
                "track_name": recommendation.track.track_name,
                "artist_id": recommendation.artist.artist_id,
                "artist_name": recommendation.artist.artist_name,
                "confidence": recommendation.confidence,
                "generated_at": recommendation.generated_at.isoformat(),
                "strategies_used": recommendation.strategies_used
            }
            
            history.append(history_entry)
            
            # Keep only last 1000 entries

            if len(history) > 1000:
                history = history[-1000:]
            
            # Save history
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(
                "Failed to update recommendation history",
                user_id=recommendation.user_id,
                error=str(e)
            )
    
    def get_recommendation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get recommendation history for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of history entries
        """
        try:
            history_file = self._get_history_file_path(user_id)
            
            if not history_file.exists():
                return []
            
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            return history
            
        except Exception as e:
            logger.error(
                "Failed to get recommendation history",
                user_id=user_id,
                error=str(e)
            )
            return []
    
    def get_recommendation_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about recommendations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        try:
            recommendations = self.get_user_recommendations(user_id)
            
            if not recommendations:
                return {
                    "total_recommendations": 0,
                    "played_count": 0,
                    "liked_count": 0,
                    "disliked_count": 0,
                    "neutral_count": 0,
                    "average_confidence": 0.0,
                    "top_artists": [],
                    "top_genres": []
                }
            
            played_count = sum(1 for r in recommendations if r.was_played)
            liked_count = sum(1 for r in recommendations if r.user_feedback == "liked")
            disliked_count = sum(1 for r in recommendations if r.user_feedback == "disliked")
            neutral_count = sum(1 for r in recommendations if r.user_feedback == "neutral")
            
            avg_confidence = sum(r.confidence for r in recommendations) / len(recommendations)
            
            # Count artists
            artist_counts = {}
            for r in recommendations:
                artist_name = r.artist.artist_name
                artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
            
            top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Count genres
            genre_counts = {}
            for r in recommendations:
                for genre in r.track.genres:
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "total_recommendations": len(recommendations),
                "played_count": played_count,
                "liked_count": liked_count,
                "disliked_count": disliked_count,
                "neutral_count": neutral_count,
                "average_confidence": avg_confidence,
                "top_artists": [{"artist": k, "count": v} for k, v in top_artists],
                "top_genres": [{"genre": k, "count": v} for k, v in top_genres]
            }
            
        except Exception as e:
            logger.error(
                "Failed to get recommendation statistics",
                user_id=user_id,
                error=str(e)
            )
            return {}


class MockRecommendationStorage:
    """Mock implementation for testing."""
    
    def __init__(self):
        self._recommendations: Dict[str, StoredRecommendation] = {}
        self._histories: Dict[str, List[Dict]] = {}
    
    def _generate_recommendation_id(self) -> str:
        """Generate a unique recommendation ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"rec_{timestamp}"
    
    def store_recommendation(
        self,
        recommendation: StoredRecommendation
    ) -> bool:
        """Store a recommendation."""
        key = f"{recommendation.user_id}:{recommendation.recommendation_id}"
        self._recommendations[key] = recommendation
        return True
    
    def get_recommendation(
        self,
        user_id: str,
        recommendation_id: str
    ) -> Optional[StoredRecommendation]:
        """Retrieve a stored recommendation."""
        key = f"{user_id}:{recommendation_id}"
        return self._recommendations.get(key)
    
    def update_recommendation_feedback(
        self,
        user_id: str,
        recommendation_id: str,
        feedback: str,
        was_played: bool = False,
        play_duration_ms: Optional[int] = None
    ) -> bool:
        """Update recommendation with user feedback."""
        key = f"{user_id}:{recommendation_id}"
        recommendation = self._recommendations.get(key)
        
        if recommendation:
            recommendation.user_feedback = feedback
            recommendation.was_played = was_played
            recommendation.play_duration_ms = play_duration_ms
            return True
        
        return False
    
    def get_user_recommendations(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[StoredRecommendation]:
        """Get all recommendations for a user."""
        recommendations = [
            r for k, r in self._recommendations.items()
            if k.startswith(f"{user_id}:")
        ]
        
        recommendations.sort(key=lambda r: r.generated_at, reverse=True)
        
        if limit:
            recommendations = recommendations[:limit]
        
        return recommendations
    
    def get_recommendation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recommendation history for a user."""
        return self._histories.get(user_id, [])
    
    def get_recommendation_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about recommendations for a user."""
        recommendations = self.get_user_recommendations(user_id)
        
        if not recommendations:
            return {
                "total_recommendations": 0,
                "played_count": 0,
                "liked_count": 0,
                "disliked_count": 0,
                "neutral_count": 0,
                "average_confidence": 0.0,
                "top_artists": [],
                "top_genres": []
            }
        
        played_count = sum(1 for r in recommendations if r.was_played)
        liked_count = sum(1 for r in recommendations if r.user_feedback == "liked")
        disliked_count = sum(1 for r in recommendations if r.user_feedback == "disliked")
        neutral_count = sum(1 for r in recommendations if r.user_feedback == "neutral")
        
        avg_confidence = sum(r.confidence for r in recommendations) / len(recommendations)
        
        return {
            "total_recommendations": len(recommendations),
            "played_count": played_count,
            "liked_count": liked_count,
            "disliked_count": disliked_count,
            "neutral_count": neutral_count,
            "average_confidence": avg_confidence,
            "top_artists": [],
            "top_genres": []
        }
