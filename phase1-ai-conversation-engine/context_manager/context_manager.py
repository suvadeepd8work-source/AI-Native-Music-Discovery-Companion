import asyncio
import json
import os
import structlog
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from .context_schemas import (
    UserContext,
    ConversationHistory,
    ConversationMessage,
    MessageRole,
    MoodType,
    ListeningGoalType,
    DiscoveryPreferenceType,
    StructuredConversationContext,
    IntentType,
    UserMemory,
    RecommendedSong,
    RecommendedArtist,
    DiscoveryHistory
)


logger = structlog.get_logger(__name__)


class ContextManager:
    """
    Manages conversation context and history for users.
    Stores conversation history in phase1/data/chat_history/
    """
    
    def __init__(
        self,
        storage_path: str = "./data/chat_history",
        max_history_length: int = 10,
        max_context_exchanges: int = 50,
        auto_save: bool = True
    ):
        self.storage_path = Path(storage_path)
        self.max_history_length = max_history_length
        self.max_context_exchanges = max_context_exchanges
        self.auto_save = auto_save
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for active sessions
        self._cache: dict[str, ConversationHistory] = {}
        
        # In-memory cache for user memory
        self._memory_cache: dict[str, UserMemory] = {}
    
    async def get_context(self, user_id: str, session_id: str) -> UserContext:
        """
        Get or create user context for a session.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            UserContext with current context
        """
        history = await self._get_or_create_history(user_id, session_id)
        return history.context
    
    async def get_history(
        self,
        user_id: str,
        session_id: str
    ) -> ConversationHistory:
        """
        Get conversation history for a session.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            ConversationHistory with messages and context
        """
        return await self._get_or_create_history(user_id, session_id)
    
    async def add_message(
        self,
        user_id: str,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: dict = None
    ) -> ConversationMessage:
        """
        Add a message to the conversation history.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            role: Message role (user or assistant)
            content: Message content
            metadata: Optional metadata for the message
            
        Returns:
            The added ConversationMessage
        """
        history = await self._get_or_create_history(user_id, session_id)
        
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        history.messages.append(message)
        
        # Trim history if too long
        if len(history.messages) > self.max_history_length:
            history.messages = history.messages[-self.max_history_length:]
        
        history.updated_at = datetime.utcnow()
        
        if self.auto_save:
            await self._save_history(history)
        
        return message
    
    async def update_context(
        self,
        user_id: str,
        session_id: str,
        context_updates: dict
    ) -> UserContext:
        """
        Update user context with new information.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            context_updates: Dictionary of context fields to update
            
        Returns:
            Updated UserContext
        """
        history = await self._get_or_create_history(user_id, session_id)
        
        # Update context fields
        for key, value in context_updates.items():
            if hasattr(history.context, key):
                setattr(history.context, key, value)
            else:
                # Add to metadata if not a direct field
                history.context.metadata[key] = value
        
        history.updated_at = datetime.utcnow()
        
        if self.auto_save:
            await self._save_history(history)
        
        return history.context
    
    async def set_mood(
        self,
        user_id: str,
        session_id: str,
        mood: MoodType
    ) -> UserContext:
        """
        Set the user's current mood.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            mood: The user's current mood
            
        Returns:
            Updated UserContext
        """
        return await self.update_context(
            user_id,
            session_id,
            {"current_mood": mood}
        )
    
    async def set_goal(
        self,
        user_id: str,
        session_id: str,
        goal: ListeningGoalType
    ) -> UserContext:
        """
        Set the user's current listening goal.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            goal: The user's listening goal
            
        Returns:
            Updated UserContext
        """
        return await self.update_context(
            user_id,
            session_id,
            {"current_goal": goal}
        )
    
    async def add_genre(
        self,
        user_id: str,
        session_id: str,
        genre: str
    ) -> UserContext:
        """
        Add a genre to the user's recent genres.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            genre: Genre to add
            
        Returns:
            Updated UserContext
        """
        history = await self._get_or_create_history(user_id, session_id)
        
        if genre not in history.context.recent_genres:
            history.context.recent_genres.append(genre)
        
        # Keep only recent genres
        if len(history.context.recent_genres) > 20:
            history.context.recent_genres = history.context.recent_genres[-20:]
        
        history.updated_at = datetime.utcnow()
        
        if self.auto_save:
            await self._save_history(history)
        
        return history.context
    
    async def add_artist(
        self,
        user_id: str,
        session_id: str,
        artist: str
    ) -> UserContext:
        """
        Add an artist to the user's recent artists.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            artist: Artist to add
            
        Returns:
            Updated UserContext
        """
        history = await self._get_or_create_history(user_id, session_id)
        
        if artist not in history.context.recent_artists:
            history.context.recent_artists.append(artist)
        
        # Keep only recent artists
        if len(history.context.recent_artists) > 20:
            history.context.recent_artists = history.context.recent_artists[-20:]
        
        history.updated_at = datetime.utcnow()
        
        if self.auto_save:
            await self._save_history(history)
        
        return history.context
    
    async def clear_history(
        self,
        user_id: str,
        session_id: str
    ) -> None:
        """
        Clear conversation history for a session.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
        """
        cache_key = f"{user_id}:{session_id}"
        
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        # Delete file if exists
        file_path = self._get_file_path(user_id, session_id)
        if file_path.exists():
            file_path.unlink()
        
        logger.info(
            "Cleared conversation history",
            user_id=user_id,
            session_id=session_id
        )
    
    async def _get_or_create_history(
        self,
        user_id: str,
        session_id: str
    ) -> ConversationHistory:
        """
        Get existing history or create new one.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            ConversationHistory
        """
        cache_key = f"{user_id}:{session_id}"
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try to load from file
        file_path = self._get_file_path(user_id, session_id)
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                history = ConversationHistory(**data)
                self._cache[cache_key] = history
                return history
            except Exception as e:
                logger.error(
                    "Failed to load history from file",
                    file_path=str(file_path),
                    error=str(e)
                )
        
        # Create new history
        history = ConversationHistory(
            user_id=user_id,
            session_id=session_id,
            context=UserContext(user_id=user_id)
        )
        self._cache[cache_key] = history
        
        if self.auto_save:
            await self._save_history(history)
        
        return history
    
    async def _save_history(self, history: ConversationHistory) -> None:
        """
        Save conversation history to file.
        
        Args:
            history: ConversationHistory to save
        """
        file_path = self._get_file_path(history.user_id, history.session_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    history.model_dump(mode='json'),
                    f,
                    indent=2,
                    default=str
                )
        except Exception as e:
            logger.error(
                "Failed to save history to file",
                file_path=str(file_path),
                error=str(e)
            )
    
    def _get_file_path(self, user_id: str, session_id: str) -> Path:
        """
        Get file path for a user session.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            Path to the history file
        """
        # Create user directory if needed
        user_dir = self.storage_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        
        return user_dir / f"{session_id}.json"
    
    async def get_all_sessions(self, user_id: str) -> List[str]:
        """
        Get all session IDs for a user.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of session IDs
        """
        user_dir = self.storage_path / user_id
        
        if not user_dir.exists():
            return []
        
        sessions = []
        for file_path in user_dir.glob("*.json"):
            sessions.append(file_path.stem)
        
        return sorted(sessions, reverse=True)
    
    async def update_structured_context(
        self,
        user_id: str,
        session_id: str,
        intent: Optional[IntentType] = None,
        mood: Optional[MoodType] = None,
        activity: Optional[ListeningGoalType] = None,
        genres: Optional[List[str]] = None,
        artists: Optional[List[str]] = None,
        discovery_goal: Optional[DiscoveryPreferenceType] = None,
        confidence: float = 0.5
    ) -> StructuredConversationContext:
        """
        Update structured conversation context with extracted information.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            intent: Detected user intent
            mood: Detected mood
            activity: Detected activity/goal
            genres: Preferred genres
            artists: Preferred artists
            discovery_goal: Discovery preference
            confidence: Confidence score for extraction
            
        Returns:
            Updated StructuredConversationContext
        """
        history = await self._get_or_create_history(user_id, session_id)
        
        # Update structured context
        if intent is not None:
            history.context.structured_context.user_intent = intent
        if mood is not None:
            history.context.structured_context.mood = mood
        if activity is not None:
            history.context.structured_context.activity = activity
        if genres is not None:
            history.context.structured_context.preferred_genres = genres
        if artists is not None:
            history.context.structured_context.preferred_artists = artists
        if discovery_goal is not None:
            history.context.structured_context.discovery_goal = discovery_goal
        
        history.context.structured_context.extracted_at = datetime.utcnow()
        history.context.structured_context.confidence = confidence
        
        history.updated_at = datetime.utcnow()
        
        if self.auto_save:
            await self._save_history(history)
        
        return history.context.structured_context
    
    async def generate_conversation_context_json(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Generate conversation_context.json with structured information.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            Dictionary with structured conversation context
        """
        history = await self._get_or_create_history(user_id, session_id)
        
        context_data = {
            "user_id": user_id,
            "session_id": session_id,
            "user_intent": history.context.structured_context.user_intent.value if history.context.structured_context.user_intent else None,
            "mood": history.context.structured_context.mood.value if history.context.structured_context.mood else None,
            "activity": history.context.structured_context.activity.value if history.context.structured_context.activity else None,
            "preferred_genres": history.context.structured_context.preferred_genres,
            "preferred_artists": history.context.structured_context.preferred_artists,
            "discovery_goal": history.context.structured_context.discovery_goal.value,
            "extracted_at": history.context.structured_context.extracted_at.isoformat(),
            "confidence": history.context.structured_context.confidence,
            "message_count": len(history.messages),
            "session_created_at": history.created_at.isoformat(),
            "session_updated_at": history.updated_at.isoformat()
        }
        
        # Save to file
        context_file_path = self._get_context_file_path(user_id, session_id)
        try:
            with open(context_file_path, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2, default=str)
            logger.info(
                "Generated conversation_context.json",
                user_id=user_id,
                session_id=session_id
            )
        except Exception as e:
            logger.error(
                "Failed to save conversation_context.json",
                file_path=str(context_file_path),
                error=str(e)
            )
        
        return context_data
    
    async def generate_conversation_history_json(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Generate conversation_history.json with full conversation history.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            Dictionary with full conversation history
        """
        history = await self._get_or_create_history(user_id, session_id)
        
        history_data = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": history.created_at.isoformat(),
            "updated_at": history.updated_at.isoformat(),
            "message_count": len(history.messages),
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in history.messages
            ],
            "context": {
                "current_mood": history.context.current_mood.value if history.context.current_mood else None,
                "current_goal": history.context.current_goal.value if history.context.current_goal else None,
                "discovery_preference": history.context.discovery_preference.value,
                "recent_genres": history.context.recent_genres,
                "recent_artists": history.context.recent_artists,
                "structured_context": {
                    "user_intent": history.context.structured_context.user_intent.value if history.context.structured_context.user_intent else None,
                    "mood": history.context.structured_context.mood.value if history.context.structured_context.mood else None,
                    "activity": history.context.structured_context.activity.value if history.context.structured_context.activity else None,
                    "preferred_genres": history.context.structured_context.preferred_genres,
                    "preferred_artists": history.context.structured_context.preferred_artists,
                    "discovery_goal": history.context.structured_context.discovery_goal.value,
                    "extracted_at": history.context.structured_context.extracted_at.isoformat(),
                    "confidence": history.context.structured_context.confidence
                }
            }
        }
        
        # Save to file
        history_file_path = self._get_history_file_path(user_id, session_id)
        try:
            with open(history_file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, default=str)
            logger.info(
                "Generated conversation_history.json",
                user_id=user_id,
                session_id=session_id
            )
        except Exception as e:
            logger.error(
                "Failed to save conversation_history.json",
                file_path=str(history_file_path),
                error=str(e)
            )
        
        return history_data
    
    def _get_context_file_path(self, user_id: str, session_id: str) -> Path:
        """
        Get file path for conversation_context.json.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            Path to the context file
        """
        user_dir = self.storage_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / f"{session_id}_context.json"
    
    def _get_history_file_path(self, user_id: str, session_id: str) -> Path:
        """
        Get file path for conversation_history.json.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            Path to the history file
        """
        user_dir = self.storage_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / f"{session_id}_history.json"
    
    async def get_user_memory(self, user_id: str) -> UserMemory:
        """
        Get or create user memory for tracking recommendations and discovery history.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserMemory with recommendation history
        """
        if user_id in self._memory_cache:
            return self._memory_cache[user_id]
        
        # Try to load from file
        memory_file_path = self._get_memory_file_path(user_id)
        
        if memory_file_path.exists():
            try:
                with open(memory_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                memory = UserMemory(**data)
                self._memory_cache[user_id] = memory
                return memory
            except Exception as e:
                logger.error(
                    "Failed to load user memory from file",
                    file_path=str(memory_file_path),
                    error=str(e)
                )
        
        # Create new memory
        memory = UserMemory(user_id=user_id)
        self._memory_cache[user_id] = memory
        
        if self.auto_save:
            await self._save_user_memory(memory)
        
        return memory
    
    async def add_recommended_song(
        self,
        user_id: str,
        session_id: str,
        song_id: str,
        song_name: str,
        artist: str,
        album: Optional[str] = None,
        feedback: Optional[str] = None
    ) -> RecommendedSong:
        """
        Add a recommended song to user memory.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            song_id: Unique song identifier
            song_name: Name of the song
            artist: Artist name
            album: Optional album name
            feedback: Optional user feedback
            
        Returns:
            The added RecommendedSong
        """
        memory = await self.get_user_memory(user_id)
        
        # Check if song already recommended
        for song in memory.previously_recommended_songs:
            if song.song_id == song_id:
                logger.info(
                    "Song already recommended, skipping",
                    song_id=song_id,
                    song_name=song_name
                )
                return song
        
        recommended_song = RecommendedSong(
            song_id=song_id,
            song_name=song_name,
            artist=artist,
            album=album,
            session_id=session_id,
            feedback=feedback
        )
        
        memory.previously_recommended_songs.append(recommended_song)
        
        # Keep only last 100 recommended songs
        if len(memory.previously_recommended_songs) > 100:
            memory.previously_recommended_songs = memory.previously_recommended_songs[-100:]
        
        memory.updated_at = datetime.utcnow()
        
        if self.auto_save:
            await self._save_user_memory(memory)
        
        return recommended_song
    
    async def add_recommended_artist(
        self,
        user_id: str,
        session_id: str,
        artist_id: str,
        artist_name: str,
        feedback: Optional[str] = None
    ) -> RecommendedArtist:
        """
        Add a recommended artist to user memory.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            artist_id: Unique artist identifier
            artist_name: Artist name
            feedback: Optional user feedback
            
        Returns:
            The added RecommendedArtist
        """
        memory = await self.get_user_memory(user_id)
        
        # Check if artist already recommended
        for artist in memory.previously_recommended_artists:
            if artist.artist_id == artist_id:
                logger.info(
                    "Artist already recommended, skipping",
                    artist_id=artist_id,
                    artist_name=artist_name
                )
                return artist
        
        recommended_artist = RecommendedArtist(
            artist_id=artist_id,
            artist_name=artist_name,
            session_id=session_id,
            feedback=feedback
        )
        
        memory.previously_recommended_artists.append(recommended_artist)
        
        # Keep only last 50 recommended artists
        if len(memory.previously_recommended_artists) > 50:
            memory.previously_recommended_artists = memory.previously_recommended_artists[-50:]
        
        memory.updated_at = datetime.utcnow()
        
        if self.auto_save:
            await self._save_user_memory(memory)
        
        return recommended_artist
    
    async def add_discovery_history(
        self,
        user_id: str,
        session_id: str,
        discovery_type: str,
        discovered_item: str,
        confidence: float = 0.5
    ) -> DiscoveryHistory:
        """
        Add a discovery event to user memory.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            discovery_type: Type of discovery (genre, artist, mood, activity)
            discovered_item: The item discovered
            confidence: Confidence score
            
        Returns:
            The added DiscoveryHistory
        """
        memory = await self.get_user_memory(user_id)
        
        discovery = DiscoveryHistory(
            discovery_type=discovery_type,
            discovered_item=discovered_item,
            session_id=session_id,
            confidence=confidence
        )
        
        memory.discovery_history.append(discovery)
        
        # Keep only last 200 discovery events
        if len(memory.discovery_history) > 200:
            memory.discovery_history = memory.discovery_history[-200:]
        
        memory.updated_at = datetime.utcnow()
        
        if self.auto_save:
            await self._save_user_memory(memory)
        
        return discovery
    
    async def add_discussed_genre(self, user_id: str, genre: str) -> None:
        """
        Add a genre to recently discussed genres.
        
        Args:
            user_id: Unique user identifier
            genre: Genre to add
        """
        memory = await self.get_user_memory(user_id)
        
        if genre not in memory.recently_discussed_genres:
            memory.recently_discussed_genres.append(genre)
        
        # Keep only last 30 genres
        if len(memory.recently_discussed_genres) > 30:
            memory.recently_discussed_genres = memory.recently_discussed_genres[-30:]
        
        memory.updated_at = datetime.utcnow()
        
        if self.auto_save:
            await self._save_user_memory(memory)
    
    async def is_song_recommended(self, user_id: str, song_id: str) -> bool:
        """
        Check if a song has been previously recommended.
        
        Args:
            user_id: Unique user identifier
            song_id: Unique song identifier
            
        Returns:
            True if song was previously recommended
        """
        memory = await self.get_user_memory(user_id)
        return any(song.song_id == song_id for song in memory.previously_recommended_songs)
    
    async def is_artist_recommended(self, user_id: str, artist_id: str) -> bool:
        """
        Check if an artist has been previously recommended.
        
        Args:
            user_id: Unique user identifier
            artist_id: Unique artist identifier
            
        Returns:
            True if artist was previously recommended
        """
        memory = await self.get_user_memory(user_id)
        return any(artist.artist_id == artist_id for artist in memory.previously_recommended_artists)
    
    async def get_recommended_song_ids(self, user_id: str) -> List[str]:
        """
        Get list of all previously recommended song IDs.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of song IDs
        """
        memory = await self.get_user_memory(user_id)
        return [song.song_id for song in memory.previously_recommended_songs]
    
    async def get_recommended_artist_ids(self, user_id: str) -> List[str]:
        """
        Get list of all previously recommended artist IDs.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of artist IDs
        """
        memory = await self.get_user_memory(user_id)
        return [artist.artist_id for artist in memory.previously_recommended_artists]
    
    async def generate_user_memory_json(self, user_id: str) -> Dict[str, Any]:
        """
        Generate user_memory.json with recommendation and discovery history.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Dictionary with user memory data
        """
        memory = await self.get_user_memory(user_id)
        
        memory_data = {
            "user_id": user_id,
            "previously_recommended_songs": [
                {
                    "song_id": song.song_id,
                    "song_name": song.song_name,
                    "artist": song.artist,
                    "album": song.album,
                    "recommended_at": song.recommended_at.isoformat(),
                    "session_id": song.session_id,
                    "feedback": song.feedback
                }
                for song in memory.previously_recommended_songs
            ],
            "previously_recommended_artists": [
                {
                    "artist_id": artist.artist_id,
                    "artist_name": artist.artist_name,
                    "recommended_at": artist.recommended_at.isoformat(),
                    "session_id": artist.session_id,
                    "feedback": artist.feedback
                }
                for artist in memory.previously_recommended_artists
            ],
            "recently_discussed_genres": memory.recently_discussed_genres,
            "discovery_history": [
                {
                    "discovery_type": discovery.discovery_type,
                    "discovered_item": discovery.discovered_item,
                    "discovered_at": discovery.discovered_at.isoformat(),
                    "session_id": discovery.session_id,
                    "confidence": discovery.confidence
                }
                for discovery in memory.discovery_history
            ],
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
            "summary": {
                "total_songs_recommended": len(memory.previously_recommended_songs),
                "total_artists_recommended": len(memory.previously_recommended_artists),
                "total_genres_discussed": len(memory.recently_discussed_genres),
                "total_discoveries": len(memory.discovery_history)
            }
        }
        
        # Save to file
        memory_file_path = self._get_memory_file_path(user_id)
        try:
            with open(memory_file_path, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, default=str)
            logger.info(
                "Generated user_memory.json",
                user_id=user_id
            )
        except Exception as e:
            logger.error(
                "Failed to save user_memory.json",
                file_path=str(memory_file_path),
                error=str(e)
            )
        
        return memory_data
    
    def _get_memory_file_path(self, user_id: str) -> Path:
        """
        Get file path for user_memory.json.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Path to the memory file
        """
        user_dir = self.storage_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / "user_memory.json"
    
    async def _save_user_memory(self, memory: UserMemory) -> None:
        """
        Save user memory to file.
        
        Args:
            memory: UserMemory to save
        """
        file_path = self._get_memory_file_path(memory.user_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    memory.model_dump(mode='json'),
                    f,
                    indent=2,
                    default=str
                )
        except Exception as e:
            logger.error(
                "Failed to save user memory to file",
                file_path=str(file_path),
                error=str(e)
            )


class MockContextManager:
    """Mock implementation for testing without file storage."""
    
    def __init__(self, max_history_length: int = 10):
        self.max_history_length = max_history_length
        self._storage: dict[str, ConversationHistory] = {}
        self._memory_cache: dict[str, UserMemory] = {}
    
    async def get_context(self, user_id: str, session_id: str) -> UserContext:
        history = await self._get_or_create_history(user_id, session_id)
        return history.context
    
    async def get_history(
        self,
        user_id: str,
        session_id: str
    ) -> ConversationHistory:
        return await self._get_or_create_history(user_id, session_id)
    
    async def add_message(
        self,
        user_id: str,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: dict = None
    ) -> ConversationMessage:
        history = await self._get_or_create_history(user_id, session_id)
        
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        history.messages.append(message)
        
        if len(history.messages) > self.max_history_length:
            history.messages = history.messages[-self.max_history_length:]
        
        history.updated_at = datetime.utcnow()
        
        return message
    
    async def update_context(
        self,
        user_id: str,
        session_id: str,
        context_updates: dict
    ) -> UserContext:
        history = await self._get_or_create_history(user_id, session_id)
        
        for key, value in context_updates.items():
            if hasattr(history.context, key):
                setattr(history.context, key, value)
            else:
                history.context.metadata[key] = value
        
        history.updated_at = datetime.utcnow()
        
        return history.context
    
    async def set_mood(
        self,
        user_id: str,
        session_id: str,
        mood: MoodType
    ) -> UserContext:
        return await self.update_context(
            user_id,
            session_id,
            {"current_mood": mood}
        )
    
    async def set_goal(
        self,
        user_id: str,
        session_id: str,
        goal: ListeningGoalType
    ) -> UserContext:
        return await self.update_context(
            user_id,
            session_id,
            {"current_goal": goal}
        )
    
    async def add_genre(
        self,
        user_id: str,
        session_id: str,
        genre: str
    ) -> UserContext:
        history = await self._get_or_create_history(user_id, session_id)
        
        if genre not in history.context.recent_genres:
            history.context.recent_genres.append(genre)
        
        if len(history.context.recent_genres) > 20:
            history.context.recent_genres = history.context.recent_genres[-20:]
        
        return history.context
    
    async def add_artist(
        self,
        user_id: str,
        session_id: str,
        artist: str
    ) -> UserContext:
        history = await self._get_or_create_history(user_id, session_id)
        
        if artist not in history.context.recent_artists:
            history.context.recent_artists.append(artist)
        
        if len(history.context.recent_artists) > 20:
            history.context.recent_artists = history.context.recent_artists[-20:]
        
        return history.context
    
    async def clear_history(
        self,
        user_id: str,
        session_id: str
    ) -> None:
        cache_key = f"{user_id}:{session_id}"
        if cache_key in self._storage:
            del self._storage[cache_key]
    
    async def _get_or_create_history(
        self,
        user_id: str,
        session_id: str
    ) -> ConversationHistory:
        cache_key = f"{user_id}:{session_id}"
        
        if cache_key in self._storage:
            return self._storage[cache_key]
        
        history = ConversationHistory(
            user_id=user_id,
            session_id=session_id,
            context=UserContext(user_id=user_id)
        )
        self._storage[cache_key] = history
        
        return history
    
    async def get_all_sessions(self, user_id: str) -> List[str]:
        sessions = [
            key.split(":")[1] 
            for key in self._storage.keys() 
            if key.startswith(f"{user_id}:")
        ]
        return sorted(sessions, reverse=True)
    
    async def update_structured_context(
        self,
        user_id: str,
        session_id: str,
        intent: Optional[IntentType] = None,
        mood: Optional[MoodType] = None,
        activity: Optional[ListeningGoalType] = None,
        genres: Optional[List[str]] = None,
        artists: Optional[List[str]] = None,
        discovery_goal: Optional[DiscoveryPreferenceType] = None,
        confidence: float = 0.5
    ) -> StructuredConversationContext:
        """Mock implementation of structured context update."""
        history = await self._get_or_create_history(user_id, session_id)
        
        if intent is not None:
            history.context.structured_context.user_intent = intent
        if mood is not None:
            history.context.structured_context.mood = mood
        if activity is not None:
            history.context.structured_context.activity = activity
        if genres is not None:
            history.context.structured_context.preferred_genres = genres
        if artists is not None:
            history.context.structured_context.preferred_artists = artists
        if discovery_goal is not None:
            history.context.structured_context.discovery_goal = discovery_goal
        
        history.context.structured_context.extracted_at = datetime.utcnow()
        history.context.structured_context.confidence = confidence
        
        return history.context.structured_context
    
    async def generate_conversation_context_json(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Mock implementation of conversation context JSON generation."""
        history = await self._get_or_create_history(user_id, session_id)
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "user_intent": history.context.structured_context.user_intent.value if history.context.structured_context.user_intent else None,
            "mood": history.context.structured_context.mood.value if history.context.structured_context.mood else None,
            "activity": history.context.structured_context.activity.value if history.context.structured_context.activity else None,
            "preferred_genres": history.context.structured_context.preferred_genres,
            "preferred_artists": history.context.structured_context.preferred_artists,
            "discovery_goal": history.context.structured_context.discovery_goal.value,
            "extracted_at": history.context.structured_context.extracted_at.isoformat(),
            "confidence": history.context.structured_context.confidence,
            "message_count": len(history.messages)
        }
    
    async def generate_conversation_history_json(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Mock implementation of conversation history JSON generation."""
        history = await self._get_or_create_history(user_id, session_id)
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "message_count": len(history.messages),
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in history.messages
            ],
            "context": {
                "current_mood": history.context.current_mood.value if history.context.current_mood else None,
                "current_goal": history.context.current_goal.value if history.context.current_goal else None,
                "discovery_preference": history.context.discovery_preference.value,
                "recent_genres": history.context.recent_genres,
                "recent_artists": history.context.recent_artists
            }
        }
    
    async def get_user_memory(self, user_id: str) -> UserMemory:
        """Mock implementation of user memory retrieval."""
        if user_id in self._memory_cache:
            return self._memory_cache[user_id]
        
        memory = UserMemory(user_id=user_id)
        self._memory_cache[user_id] = memory
        return memory
    
    async def add_recommended_song(
        self,
        user_id: str,
        session_id: str,
        song_id: str,
        song_name: str,
        artist: str,
        album: Optional[str] = None,
        feedback: Optional[str] = None
    ) -> RecommendedSong:
        """Mock implementation of song recommendation tracking."""
        memory = await self.get_user_memory(user_id)
        
        for song in memory.previously_recommended_songs:
            if song.song_id == song_id:
                return song
        
        recommended_song = RecommendedSong(
            song_id=song_id,
            song_name=song_name,
            artist=artist,
            album=album,
            session_id=session_id,
            feedback=feedback
        )
        
        memory.previously_recommended_songs.append(recommended_song)
        
        if len(memory.previously_recommended_songs) > 100:
            memory.previously_recommended_songs = memory.previously_recommended_songs[-100:]
        
        return recommended_song
    
    async def add_recommended_artist(
        self,
        user_id: str,
        session_id: str,
        artist_id: str,
        artist_name: str,
        feedback: Optional[str] = None
    ) -> RecommendedArtist:
        """Mock implementation of artist recommendation tracking."""
        memory = await self.get_user_memory(user_id)
        
        for artist in memory.previously_recommended_artists:
            if artist.artist_id == artist_id:
                return artist
        
        recommended_artist = RecommendedArtist(
            artist_id=artist_id,
            artist_name=artist_name,
            session_id=session_id,
            feedback=feedback
        )
        
        memory.previously_recommended_artists.append(recommended_artist)
        
        if len(memory.previously_recommended_artists) > 50:
            memory.previously_recommended_artists = memory.previously_recommended_artists[-50:]
        
        return recommended_artist
    
    async def add_discovery_history(
        self,
        user_id: str,
        session_id: str,
        discovery_type: str,
        discovered_item: str,
        confidence: float = 0.5
    ) -> DiscoveryHistory:
        """Mock implementation of discovery history tracking."""
        memory = await self.get_user_memory(user_id)
        
        discovery = DiscoveryHistory(
            discovery_type=discovery_type,
            discovered_item=discovered_item,
            session_id=session_id,
            confidence=confidence
        )
        
        memory.discovery_history.append(discovery)
        
        if len(memory.discovery_history) > 200:
            memory.discovery_history = memory.discovery_history[-200:]
        
        return discovery
    
    async def add_discussed_genre(self, user_id: str, genre: str) -> None:
        """Mock implementation of genre discussion tracking."""
        memory = await self.get_user_memory(user_id)
        
        if genre not in memory.recently_discussed_genres:
            memory.recently_discussed_genres.append(genre)
        
        if len(memory.recently_discussed_genres) > 30:
            memory.recently_discussed_genres = memory.recently_discussed_genres[-30:]
    
    async def is_song_recommended(self, user_id: str, song_id: str) -> bool:
        """Mock implementation of song recommendation check."""
        memory = await self.get_user_memory(user_id)
        return any(song.song_id == song_id for song in memory.previously_recommended_songs)
    
    async def is_artist_recommended(self, user_id: str, artist_id: str) -> bool:
        """Mock implementation of artist recommendation check."""
        memory = await self.get_user_memory(user_id)
        return any(artist.artist_id == artist_id for artist in memory.previously_recommended_artists)
    
    async def get_recommended_song_ids(self, user_id: str) -> List[str]:
        """Mock implementation of recommended song IDs retrieval."""
        memory = await self.get_user_memory(user_id)
        return [song.song_id for song in memory.previously_recommended_songs]
    
    async def get_recommended_artist_ids(self, user_id: str) -> List[str]:
        """Mock implementation of recommended artist IDs retrieval."""
        memory = await self.get_user_memory(user_id)
        return [artist.artist_id for artist in memory.previously_recommended_artists]
    
    async def generate_user_memory_json(self, user_id: str) -> Dict[str, Any]:
        """Mock implementation of user memory JSON generation."""
        memory = await self.get_user_memory(user_id)
        
        return {
            "user_id": user_id,
            "previously_recommended_songs": [
                {
                    "song_id": song.song_id,
                    "song_name": song.song_name,
                    "artist": song.artist,
                    "album": song.album,
                    "recommended_at": song.recommended_at.isoformat(),
                    "session_id": song.session_id,
                    "feedback": song.feedback
                }
                for song in memory.previously_recommended_songs
            ],
            "previously_recommended_artists": [
                {
                    "artist_id": artist.artist_id,
                    "artist_name": artist.artist_name,
                    "recommended_at": artist.recommended_at.isoformat(),
                    "session_id": artist.session_id,
                    "feedback": artist.feedback
                }
                for artist in memory.previously_recommended_artists
            ],
            "recently_discussed_genres": memory.recently_discussed_genres,
            "discovery_history": [
                {
                    "discovery_type": discovery.discovery_type,
                    "discovered_item": discovery.discovered_item,
                    "discovered_at": discovery.discovered_at.isoformat(),
                    "session_id": discovery.session_id,
                    "confidence": discovery.confidence
                }
                for discovery in memory.discovery_history
            ],
            "summary": {
                "total_songs_recommended": len(memory.previously_recommended_songs),
                "total_artists_recommended": len(memory.previously_recommended_artists),
                "total_genres_discussed": len(memory.recently_discussed_genres),
                "total_discoveries": len(memory.discovery_history)
            }
        }
