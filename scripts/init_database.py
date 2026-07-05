"""
Database Initialization Script
Creates the PostgreSQL database and required tables for the AI-Native Music Discovery Companion.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:secure_password@localhost:5432/music_discovery")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", "5432"))
DATABASE_NAME = os.getenv("DATABASE_NAME", "music_discovery")
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "secure_password")


async def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to PostgreSQL server (no database specified)
        conn = await asyncpg.connect(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database="postgres"  # Connect to default postgres database
        )
        
        # Check if database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            DATABASE_NAME
        )
        
        if not db_exists:
            print(f"Creating database: {DATABASE_NAME}")
            await conn.execute(f'CREATE DATABASE "{DATABASE_NAME}"')
            print(f"Database {DATABASE_NAME} created successfully")
        else:
            print(f"Database {DATABASE_NAME} already exists")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        raise


async def create_tables():
    """Create required tables in the database."""
    try:
        # Connect to the music_discovery database
        conn = await asyncpg.connect(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME
        )
        
        print("Creating tables...")
        
        # Users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User preferences table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) UNIQUE NOT NULL,
                preferred_genres TEXT[],
                preferred_artists TEXT[],
                mood_preferences JSONB,
                activity_preferences JSONB,
                audio_feature_preferences JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Conversation history table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                intent VARCHAR(100),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Recommendations table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                track_id VARCHAR(255),
                track_name VARCHAR(255),
                artist_name VARCHAR(255),
                album_name VARCHAR(255),
                genre VARCHAR(100),
                explanation TEXT,
                confidence FLOAT,
                user_feedback VARCHAR(50),
                was_played BOOLEAN DEFAULT FALSE,
                play_duration_ms INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Review insights cache table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS review_insights_cache (
                id SERIAL PRIMARY KEY,
                insight_type VARCHAR(100),
                insight_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        # Scheduler logs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_logs (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR(255) UNIQUE NOT NULL,
                event_type VARCHAR(100),
                status VARCHAR(50),
                metadata JSONB,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversation_history_user_id ON conversation_history(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversation_history_session_id ON conversation_history(session_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_session_id ON recommendations(session_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_scheduler_logs_job_id ON scheduler_logs(job_id)")
        
        print("Tables created successfully")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise


async def main():
    """Main function to initialize the database."""
    print("Starting database initialization...")
    print(f"Database Host: {DATABASE_HOST}")
    print(f"Database Port: {DATABASE_PORT}")
    print(f"Database Name: {DATABASE_NAME}")
    print(f"Database User: {DATABASE_USER}")
    
    try:
        await create_database()
        await create_tables()
        print("\nDatabase initialization completed successfully!")
        
    except Exception as e:
        print(f"\nDatabase initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
