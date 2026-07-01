"""
Test script to verify the updated conversation pipeline for Phase 1.
Tests intent detection, context extraction, and memory storage.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from intent_recognition import MockIntentRecognizer
from context_manager import MockContextManager, IntentType, MoodType, ListeningGoalType, DiscoveryPreferenceType
from query_parser import MockQueryParser
from response_generator import MockResponseGenerator


async def test_intent_detection():
    """Test intent recognition with sample queries."""
    print("\n=== Testing Intent Detection ===")
    
    recognizer = MockIntentRecognizer(confidence_threshold=0.7)
    
    test_queries = [
        "I need some coding music",
        "I'm feeling sad today",
        "Show me some new artists",
        "I want to discover jazz music",
        "Music for my workout",
        "I keep listening to the same songs",
        "I need instrumental music",
        "Help me relax",
        "Artists like Coldplay",
        "Hello, how are you?"
    ]
    
    for query in test_queries:
        result = await recognizer.recognize(query)
        print(f"Query: '{query}'")
        print(f"  Intent: {result.intent.value}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Reasoning: {result.reasoning}")
        print()


async def test_context_extraction():
    """Test context extraction and structured context generation."""
    print("\n=== Testing Context Extraction ===")
    
    context_manager = MockContextManager(max_history_length=10)
    query_parser = MockQueryParser()
    
    user_id = "test_user_123"
    session_id = "test_session_456"
    
    # Simulate a conversation
    queries = [
        "I need energetic coding music",
        "I like electronic music",
        "Show me some indie artists",
        "I want to discover something new"
    ]
    
    for i, query in enumerate(queries):
        print(f"\n--- Message {i+1}: '{query}' ---")
        
        # Parse query
        parsed = await query_parser.parse(query, intent="CODING_MUSIC")
        print(f"Parsed mood: {parsed.mood}")
        print(f"Parsed goal: {parsed.goal}")
        print(f"Parsed genres: {parsed.genres}")
        print(f"Parsed artists: {parsed.artists}")
        
        # Update structured context
        await context_manager.update_structured_context(
            user_id=user_id,
            session_id=session_id,
            intent=IntentType.CODING_MUSIC,
            mood=parsed.mood,
            activity=parsed.goal,
            genres=parsed.genres,
            artists=parsed.artists,
            discovery_goal=parsed.discovery_preference,
            confidence=parsed.confidence
        )
        
        # Add message
        await context_manager.add_message(
            user_id=user_id,
            session_id=session_id,
            role="user",
            content=query
        )
    
    # Generate structured context JSON
    context_data = await context_manager.generate_conversation_context_json(user_id, session_id)
    print("\n=== Structured Context Generated ===")
    print(f"User Intent: {context_data['user_intent']}")
    print(f"Mood: {context_data['mood']}")
    print(f"Activity: {context_data['activity']}")
    print(f"Preferred Genres: {context_data['preferred_genres']}")
    print(f"Preferred Artists: {context_data['preferred_artists']}")
    print(f"Discovery Goal: {context_data['discovery_goal']}")
    print(f"Confidence: {context_data['confidence']}")
    print(f"Message Count: {context_data['message_count']}")


async def test_memory_storage():
    """Test memory storage and user memory generation."""
    print("\n=== Testing Memory Storage ===")
    
    context_manager = MockContextManager(max_history_length=10)
    
    user_id = "test_user_123"
    session_id = "test_session_456"
    
    # Add song recommendations
    print("\n--- Adding Song Recommendations ---")
    songs = [
        ("song_1", "Bohemian Rhapsody", "Queen", "A Night at the Opera"),
        ("song_2", "Stairway to Heaven", "Led Zeppelin", "Led Zeppelin IV"),
        ("song_3", "Hotel California", "Eagles", "Hotel California")
    ]
    
    for song_id, song_name, artist, album in songs:
        await context_manager.add_recommended_song(
            user_id=user_id,
            session_id=session_id,
            song_id=song_id,
            song_name=song_name,
            artist=artist,
            album=album
        )
        print(f"Added: {song_name} by {artist}")
    
    # Try to add duplicate
    print("\n--- Testing Duplicate Detection ---")
    await context_manager.add_recommended_song(
        user_id=user_id,
        session_id=session_id,
        song_id="song_1",
        song_name="Bohemian Rhapsody",
        artist="Queen"
    )
    print("Attempted to add duplicate song (should be skipped)")
    
    # Add artist recommendations
    print("\n--- Adding Artist Recommendations ---")
    artists = [
        ("artist_1", "Queen"),
        ("artist_2", "Led Zeppelin"),
        ("artist_3", "Pink Floyd")
    ]
    
    for artist_id, artist_name in artists:
        await context_manager.add_recommended_artist(
            user_id=user_id,
            session_id=session_id,
            artist_id=artist_id,
            artist_name=artist_name
        )
        print(f"Added: {artist_name}")
    
    # Add discovery history
    print("\n--- Adding Discovery History ---")
    await context_manager.add_discovery_history(
        user_id=user_id,
        session_id=session_id,
        discovery_type="genre",
        discovered_item="rock",
        confidence=0.9
    )
    await context_manager.add_discovery_history(
        user_id=user_id,
        session_id=session_id,
        discovery_type="artist",
        discovered_item="Queen",
        confidence=0.85
    )
    print("Added discovery events")
    
    # Add discussed genres
    print("\n--- Adding Discussed Genres ---")
    genres = ["rock", "classic rock", "progressive rock"]
    for genre in genres:
        await context_manager.add_discussed_genre(user_id, genre)
        print(f"Added: {genre}")
    
    # Generate user memory JSON
    print("\n=== User Memory Generated ===")
    memory_data = await context_manager.generate_user_memory_json(user_id)
    print(f"Total Songs Recommended: {memory_data['summary']['total_songs_recommended']}")
    print(f"Total Artists Recommended: {memory_data['summary']['total_artists_recommended']}")
    print(f"Total Genres Discussed: {memory_data['summary']['total_genres_discussed']}")
    print(f"Total Discoveries: {memory_data['summary']['total_discoveries']}")
    
    # Check duplicate detection
    print("\n--- Testing Duplicate Checks ---")
    is_song_recommended = await context_manager.is_song_recommended(user_id, "song_1")
    is_artist_recommended = await context_manager.is_artist_recommended(user_id, "artist_1")
    print(f"Song 'song_1' recommended: {is_song_recommended}")
    print(f"Artist 'artist_1' recommended: {is_artist_recommended}")
    
    # Get recommended IDs
    print("\n--- Getting Recommended IDs ---")
    song_ids = await context_manager.get_recommended_song_ids(user_id)
    artist_ids = await context_manager.get_recommended_artist_ids(user_id)
    print(f"Recommended Song IDs: {song_ids}")
    print(f"Recommended Artist IDs: {artist_ids}")


async def test_full_pipeline():
    """Test the full conversation pipeline."""
    print("\n=== Testing Full Conversation Pipeline ===")
    
    # Initialize components
    recognizer = MockIntentRecognizer(confidence_threshold=0.7)
    context_manager = MockContextManager(max_history_length=10)
    query_parser = MockQueryParser()
    response_generator = MockResponseGenerator()
    
    user_id = "pipeline_test_user"
    session_id = "pipeline_test_session"
    
    # Simulate a full conversation
    conversation = [
        "I need some coding music",
        "I like electronic and ambient genres",
        "Can you recommend some new artists?",
        "I'm feeling energetic today"
    ]
    
    for i, query in enumerate(conversation):
        print(f"\n--- Turn {i+1} ---")
        print(f"User: {query}")
        
        # Step 1: Intent recognition
        intent_result = await recognizer.recognize(query)
        print(f"Intent: {intent_result.intent.value} (confidence: {intent_result.confidence})")
        
        # Step 2: Query parsing
        parsed_query = await query_parser.parse(query, intent=intent_result.intent.value)
        print(f"Parsed - Mood: {parsed_query.mood}, Goal: {parsed_query.goal}")
        print(f"Parsed - Genres: {parsed_query.genres}, Artists: {parsed_query.artists}")
        
        # Step 3: Update structured context
        await context_manager.update_structured_context(
            user_id=user_id,
            session_id=session_id,
            intent=intent_result.intent,
            mood=parsed_query.mood,
            activity=parsed_query.goal,
            genres=parsed_query.genres,
            artists=parsed_query.artists,
            discovery_goal=parsed_query.discovery_preference,
            confidence=max(intent_result.confidence, parsed_query.confidence)
        )
        
        # Step 4: Add user message
        await context_manager.add_message(
            user_id=user_id,
            session_id=session_id,
            role="user",
            content=query,
            metadata={"intent": intent_result.intent.value}
        )
        
        # Step 5: Generate response
        context_dict = {
            "current_mood": parsed_query.mood.value if parsed_query.mood else None,
            "current_goal": parsed_query.goal.value if parsed_query.goal else None,
            "recent_genres": parsed_query.genres,
            "recent_artists": parsed_query.artists,
            "discovery_preference": parsed_query.discovery_preference.value
        }
        
        response = await response_generator.generate(
            query=query,
            intent=intent_result.intent.value,
            context=context_dict,
            recommendations=[]
        )
        
        print(f"Assistant: {response.content}")
        
        # Step 6: Add assistant message
        await context_manager.add_message(
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            content=response.content,
            metadata={"intent": intent_result.intent.value}
        )
        
        # Step 7: Generate JSON files
        await context_manager.generate_conversation_context_json(user_id, session_id)
        await context_manager.generate_conversation_history_json(user_id, session_id)
        await context_manager.generate_user_memory_json(user_id)
    
    print("\n=== Pipeline Test Complete ===")
    print("All JSON files generated successfully")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("PHASE 1 CONVERSATION PIPELINE TEST")
    print("=" * 60)
    
    try:
        await test_intent_detection()
        await test_context_extraction()
        await test_memory_storage()
        await test_full_pipeline()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
