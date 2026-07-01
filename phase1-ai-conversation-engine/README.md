# Phase 1: AI Conversation Engine

The AI Conversation Engine is the first phase of the AI-Native Music Discovery Companion. It provides natural language understanding, intent recognition, query parsing, and conversational response generation for music discovery.

## Features

- **Natural Language Understanding**: Understands user queries in natural language
- **Intent Recognition**: Classifies queries into 13 supported intents:
  - Discover new artists
  - Mood-based recommendations
  - Activity-based recommendations
  - Genre exploration
  - Artist exploration
  - Escape repetitive playlists
  - Instrumental music
  - Coding music
  - Workout music
  - Relaxation music
  - Clarification
  - Feedback
  - General chat

- **Mood Detection**: Detects user mood from queries (energetic, calm, melancholic, etc.)
- **Listening Goal Detection**: Detects listening goals (coding, workout, studying, etc.)
- **Discovery Preferences**: Handles novelty levels (familiar, balanced, novel, experimental)
- **Conversation Memory**: Maintains conversation history in `phase1/data/chat_history/`
- **Context Management**: Tracks user context across sessions
- **Query Parsing**: Extracts structured parameters from natural language
- **Response Generation**: Generates natural, conversational responses using Groq LLM

## Architecture

### Components

1. **Intent Recognition Module** (`intent_recognition/`)
   - Uses Groq LLM to classify user queries into intents
   - Supports fallback models for reliability
   - Includes mock implementation for testing

2. **Context Manager** (`context_manager/`)
   - Manages conversation history and user context
   - Stores history in `data/chat_history/`
   - Tracks mood, goals, genres, and artists
   - Includes mock implementation for testing

3. **Query Parser** (`query_parser/`)
   - Extracts structured parameters from queries
   - Detects mood, goals, genres, artists
   - Handles discovery preferences and constraints
   - Includes mock implementation for testing

4. **Response Generator** (`response_generator/`)
   - Generates natural conversational responses
   - Uses Groq LLM for response generation
   - Adapts tone based on context
   - Includes mock implementation for testing

5. **API Server** (`api/`)
   - FastAPI-based REST API
   - Endpoints for chat, intent, parsing, and context
   - Health check endpoint
   - CORS support

## Installation

### Prerequisites

- Python 3.11+
- Groq API key (or use mock mode)

### Setup

1. Navigate to the phase directory:
```bash
cd phase1-ai-conversation-engine
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Ensure the data directory exists:
```bash
mkdir -p data/chat_history
```

## Configuration

Edit `config.yaml` to customize the service:

```yaml
# Server Configuration
server:
  host: "0.0.0.0"
  port: 8001
  workers: 4

# Groq LLM Configuration
groq:
  api_key: "${GROQ_API_KEY}"
  primary_model: "llama-3.1-70b-versatile"
  secondary_model: "mixtral-8x7b"
  fallback_model: "llama-3.1-8b"

# Conversation Memory
memory:
  max_history_length: 10
  storage_path: "./data/chat_history"
```

## Running the Service

### Production Mode (with Groq API)

```bash
# Set environment variables
export GROQ_API_KEY=your_api_key_here

# Run the service
python -m api.main
```

Or using uvicorn directly:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Mock Mode (without Groq API)

```bash
# Set mock mode
export USE_MOCKS=true

# Run the service
python -m api.main
```

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status and dependency status.

### Chat
```
POST /chat
Content-Type: application/json

{
  "query": "I need some coding music",
  "user_id": "user123",
  "session_id": "session456"
}
```

Response:
```json
{
  "response": "Coding music should help you stay in the flow state...",
  "intent": "CODING_MUSIC",
  "confidence": 0.85,
  "parsed_query": {
    "mood": null,
    "goal": "coding",
    "genres": [],
    "artists": [],
    "discovery_preference": "balanced"
  },
  "recommendations": []
}
```

### Intent Recognition
```
POST /intent
Content-Type: application/json

{
  "query": "I need some coding music"
}
```

Response:
```json
{
  "intent": "CODING_MUSIC",
  "confidence": 0.85,
  "reasoning": "Matched keyword: coding"
}
```

### Query Parsing
```
POST /parse
Content-Type: application/json

{
  "query": "I need energetic coding music",
  "intent": "CODING_MUSIC"
}
```

Response:
```json
{
  "parsed_query": {
    "mood": "energetic",
    "goal": "coding",
    "genres": [],
    "artists": [],
    "discovery_preference": "balanced"
  },
  "confidence": 0.75
}
```

### Get Context
```
GET /context?user_id=user123&session_id=session456
```

Response:
```json
{
  "context": {
    "user_id": "user123",
    "current_mood": "energetic",
    "current_goal": "coding",
    "recent_genres": ["electronic", "ambient"],
    "recent_artists": []
  },
  "messages": [
    {
      "role": "user",
      "content": "I need some coding music",
      "timestamp": "2024-01-01T00:00:00"
    }
  ]
}
```

### Clear Context
```
DELETE /context?user_id=user123&session_id=session456
```

### Get Sessions
```
GET /sessions/user123
```

Response:
```json
{
  "user_id": "user123",
  "sessions": ["session456", "session789"]
}
```

## Conversation History Storage

Conversation history is stored in `data/chat_history/` with the following structure:

```
data/chat_history/
├── user123/
│   ├── session456.json
│   └── session789.json
└── user456/
    └── session123.json
```

Each JSON file contains:
- User context (mood, goal, genres, artists)
- Conversation messages
- Timestamps

## Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Using Mock Mode

Set `USE_MOCKS=true` in `.env` to use mock implementations without requiring Groq API keys. This is useful for development and testing.

## Development

### Project Structure

```
phase1-ai-conversation-engine/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   └── schemas.py           # Pydantic models
├── intent_recognition/
│   ├── __init__.py
│   ├── intent_recognizer.py # Intent recognition logic
│   ├── intent_schemas.py    # Intent enums and models
│   └── intent_prompts.py    # LLM prompts
├── context_manager/
│   ├── __init__.py
│   ├── context_manager.py   # Context management logic
│   └── context_schemas.py   # Context models
├── query_parser/
│   ├── __init__.py
│   ├── query_parser.py      # Query parsing logic
│   ├── parser_schemas.py    # Parsed query models
│   └── parser_prompts.py    # LLM prompts
├── response_generator/
│   ├── __init__.py
│   ├── response_generator.py # Response generation logic
│   ├── response_schemas.py   # Response models
│   └── response_prompts.py   # LLM prompts
├── data/
│   └── chat_history/         # Conversation history storage
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Dependencies

- FastAPI - Web framework
- Groq - LLM API client
- SQLAlchemy - Database ORM
- AsyncPG - PostgreSQL async driver
- Redis - Caching
- Pydantic - Data validation
- Structlog - Structured logging
- PyYAML - Configuration parsing

## Phase Independence

This phase operates as a completely independent microservice:

- **Own Repository**: Separate codebase from other phases
- **Own Dependencies**: Independent `requirements.txt`
- **Own Configuration**: Separate `config.yaml`
- **Own Storage**: Conversation history in `data/chat_history/`
- **API Interface**: REST API for communication with other phases
- **Mock Layer**: Includes mock implementations for isolated testing
- **Independent Deployment**: Can be deployed as a standalone Docker container

## Communication with Other Phases

- **Receives from**: Phase 4 (Backend API) via REST API calls
- **Sends to**: Phase 3 (AI Orchestration) via REST API calls
- **External Dependencies**: Groq LLM API (external service)
- **Data Exchange**: JSON payloads via HTTP/REST

## License

Part of the AI-Native Music Discovery Companion project.
