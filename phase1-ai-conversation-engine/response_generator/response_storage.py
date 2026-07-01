"""
Response storage for Phase 1: AI Conversation Engine.
Stores generated conversational responses in responses.json.
"""
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import structlog


logger = structlog.get_logger(__name__)


class ResponseStorage:
    """Storage for generated conversational responses."""
    
    def __init__(self, storage_dir: str = "./data/responses", max_responses: int = 1000):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "responses.json"
        self.max_responses = max_responses
        self._responses: Dict[str, Dict[str, Any]] = {}
        
        # Load existing responses
        self._load_responses()
    
    def _load_responses(self) -> None:
        """Load responses from storage file."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self._responses = json.load(f)
                logger.info("Loaded responses from storage", count=len(self._responses))
            except Exception as e:
                logger.error("Failed to load responses", error=str(e))
                self._responses = {}
    
    def _save_responses(self) -> None:
        """Save responses to storage file."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self._responses, f, indent=2, ensure_ascii=False)
            logger.info("Saved responses to storage", count=len(self._responses))
        except Exception as e:
            logger.error("Failed to save responses", error=str(e))
    
    def store_response(
        self,
        user_id: str,
        session_id: str,
        response_id: str,
        query: str,
        intent: str,
        response_content: str,
        recommendations: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        memory: Optional[Dict[str, Any]] = None,
        confidence: float = 0.0
    ) -> None:
        """
        Store a generated response.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            response_id: Unique response identifier
            query: Original user query
            intent: Detected intent
            response_content: Generated response text
            recommendations: List of recommendations included
            context: Conversation context
            memory: Conversation memory used
            confidence: Response confidence score
        """
        response_data = {
            "response_id": response_id,
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "intent": intent,
            "response": response_content,
            "recommendations": recommendations or [],
            "context": context or {},
            "memory": memory or {},
            "confidence": confidence,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        self._responses[response_id] = response_data
        
        # Trim if exceeding max
        if len(self._responses) > self.max_responses:
            # Remove oldest responses
            sorted_responses = sorted(
                self._responses.items(),
                key=lambda x: x[1].get("generated_at", "")
            )
            for response_id, _ in sorted_responses[:len(self._responses) - self.max_responses]:
                del self._responses[response_id]
        
        self._save_responses()
        logger.info("Stored response", response_id=response_id, user_id=user_id)
    
    def get_response(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Get a stored response by ID."""
        return self._responses.get(response_id)
    
    def get_user_responses(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all responses for a user."""
        user_responses = [
            r for r in self._responses.values()
            if r.get("user_id") == user_id
        ]
        # Sort by generated_at descending
        user_responses.sort(
            key=lambda x: x.get("generated_at", ""),
            reverse=True
        )
        return user_responses[:limit]
    
    def get_session_responses(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all responses for a session."""
        session_responses = [
            r for r in self._responses.values()
            if r.get("session_id") == session_id
        ]
        # Sort by generated_at descending
        session_responses.sort(
            key=lambda x: x.get("generated_at", ""),
            reverse=True
        )
        return session_responses[:limit]
    
    def get_responses_by_intent(self, intent: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get responses by intent."""
        intent_responses = [
            r for r in self._responses.values()
            if r.get("intent") == intent
        ]
        # Sort by generated_at descending
        intent_responses.sort(
            key=lambda x: x.get("generated_at", ""),
            reverse=True
        )
        return intent_responses[:limit]
    
    def clear_old_responses(self, days: int = 30) -> int:
        """Clear responses older than specified days."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        old_count = 0
        to_delete = []
        
        for response_id, response_data in self._responses.items():
            generated_at = response_data.get("generated_at", "")
            if generated_at < cutoff_str:
                to_delete.append(response_id)
                old_count += 1
        
        for response_id in to_delete:
            del self._responses[response_id]
        
        if to_delete:
            self._save_responses()
            logger.info("Cleared old responses", count=old_count, days=days)
        
        return old_count


class MockResponseStorage:
    """Mock storage for testing."""
    
    def __init__(self):
        self._responses: Dict[str, Dict[str, Any]] = {}
    
    def store_response(
        self,
        user_id: str,
        session_id: str,
        response_id: str,
        query: str,
        intent: str,
        response_content: str,
        recommendations: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        memory: Optional[Dict[str, Any]] = None,
        confidence: float = 0.0
    ) -> None:
        """Mock store response."""
        self._responses[response_id] = {
            "response_id": response_id,
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "intent": intent,
            "response": response_content,
            "recommendations": recommendations or [],
            "context": context or {},
            "memory": memory or {},
            "confidence": confidence,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_response(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Mock get response."""
        return self._responses.get(response_id)
    
    def get_user_responses(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Mock get user responses."""
        return [r for r in self._responses.values() if r.get("user_id") == user_id][:limit]
    
    def get_session_responses(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Mock get session responses."""
        return [r for r in self._responses.values() if r.get("session_id") == session_id][:limit]
    
    def get_responses_by_intent(self, intent: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Mock get responses by intent."""
        return [r for r in self._responses.values() if r.get("intent") == intent][:limit]
    
    def clear_old_responses(self, days: int = 30) -> int:
        """Mock clear old responses."""
        return 0
