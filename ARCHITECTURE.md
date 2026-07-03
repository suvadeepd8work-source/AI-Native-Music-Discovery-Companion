# AI-Native Music Discovery Companion - Architecture Document

## Overview

The AI-Native Music Discovery Companion is a sophisticated music recommendation system that leverages Groq LLM to provide intelligent, context-aware music suggestions. The system consumes insights from the AI-Powered Review Discovery Engine to deliver personalized recommendations based on natural language queries, user mood, listening patterns, and review-based artist discovery.

### Core Objectives

- **Natural Language Understanding**: Interpret user intent from conversational queries
- **Explainable Recommendations**: Provide clear reasoning for every suggestion
- **Habit Breaking**: Identify and disrupt repetitive listening patterns
- **Review-Based Discovery**: Leverage review insights to introduce underrated artists
- **Context-Aware Suggestions**: Adapt to mood, activity, time, and preferences

### Phase Independence Principle

**Each phase is completely independent and can be developed, tested, and deployed separately.**

**Independence Requirements**:
- **Separate Codebases**: Each phase has its own repository/folder structure
- **Independent Deployment**: Each phase can be deployed without other phases
- **Own Configuration**: Each phase has its own configuration files
- **Own Dependencies**: Each phase manages its own dependencies
- **Clear Interfaces**: Well-defined APIs/contracts between phases
- **Mock Implementations**: Each phase includes mocks for dependencies
- **Isolated Testing**: Each phase can be tested in isolation
- **Version Compatibility**: Each phase specifies compatible versions of dependencies

**Phase Communication**:
- Phases communicate via well-defined REST APIs or message queues
- No direct code dependencies between phases
- Each phase implements its own data layer
- Shared data is exchanged through APIs, not direct database access
- Each phase can be replaced with an alternative implementation

**Development Workflow**:
- Teams can work on different phases independently
- Phase-specific CI/CD pipelines
- Independent versioning and release cycles
- Phase-specific monitoring and logging

---

## Review Discovery Engine Integration

The AI Music Discovery Companion communicates with the AI-Powered Review Discovery Engine through multiple integration points:

### Communication Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│         AI Music Discovery Companion (This System)              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ 1. Direct Database Access
                            │    - PostgreSQL connection to review_insights table
                            │    - Real-time queries for artist data
                            │
                            │ 2. REST API Integration
                            │    - GET /api/v1/review-insights/artists/{genre}
                            │    - GET /api/v1/review-insights/artist/{artist_id}
                            │    - POST /api/v1/review-insights/sync
                            │
                            │ 3. Event-Driven Sync
                            │    - Webhook notifications for new reviews
                            │    - Message queue for async updates
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│         AI-Powered Review Discovery Engine                      │
│  (Phase 1-3 Completed - Generates review insights)              │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Details

#### 1. Database Integration

**Connection**: Direct PostgreSQL connection to Review Discovery Engine database

**Schema Access**:
```sql
-- Access to review_insights table
CREATE TABLE review_insights (
    id SERIAL PRIMARY KEY,
    artist_id VARCHAR(50) UNIQUE,
    artist_name VARCHAR(255),
    spotify_popularity INT,
    review_sentiment FLOAT,
    review_count INT,
    genre_tags TEXT[],
    unique_descriptors TEXT[],
    common_themes TEXT[],
    discovery_score FLOAT,
    last_updated TIMESTAMP
);

-- Access to review_sources table
CREATE TABLE review_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100),
    source_url VARCHAR(500),
    credibility_score FLOAT
);

-- Access to individual reviews (for detailed context)
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    artist_id VARCHAR(50),
    source_id INT,
    review_text TEXT,
    sentiment_score FLOAT,
    extracted_keywords TEXT[],
    published_date DATE
);
```

**Service Implementation**:
```python
class ReviewInsightsService:
    def __init__(self, db_connection: AsyncSession):
        self.db = db_connection
        self.cache = RedisCache()
    
    async def get_highly_rated_artists(
        self, 
        genre: str, 
        limit: int = 10,
        min_discovery_score: float = 0.5
    ) -> List[ReviewArtist]:
        # Check cache first
        cache_key = f"review_artists:{genre}:{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Query database
        query = """
        SELECT artist_id, artist_name, review_sentiment, 
               review_count, genre_tags, unique_descriptors, 
               discovery_score, spotify_popularity
        FROM review_insights
        WHERE discovery_score >= %s
        AND genre_tags @> %s
        ORDER BY discovery_score DESC, review_sentiment DESC
        LIMIT %s
        """
        
        result = await self.db.execute(
            query, 
            [min_discovery_score, [genre], limit]
        )
        artists = [ReviewArtist.from_row(row) for row in result]
        
        # Cache for 6 hours
        await self.cache.set(cache_key, artists, ttl=21600)
        return artists
    
    async def get_artist_review_summary(
        self, 
        artist_id: str
    ) -> ArtistReviewSummary:
        query = """
        SELECT artist_name, review_sentiment, review_count,
               unique_descriptors, common_themes, discovery_score
        FROM review_insights
        WHERE artist_id = %s
        """
        result = await self.db.execute(query, [artist_id])
        return ArtistReviewSummary.from_row(result.fetchone())
    
    async def sync_review_data(self, since: datetime = None):
        """Sync new review data from Review Discovery Engine"""
        # This would be called periodically or via webhook
        sync_query = """
        SELECT * FROM review_insights
        WHERE last_updated >= %s
        ORDER BY last_updated DESC
        """
        results = await self.db.execute(sync_query, [since])
        return [ReviewArtist.from_row(row) for row in results]
```

#### 2. REST API Integration

**Endpoints Called**:
```python
class ReviewAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient()
    
    async def get_artists_by_genre(
        self, 
        genre: str, 
        limit: int = 20
    ) -> List[ReviewArtist]:
        response = await self.client.get(
            f"{self.base_url}/api/v1/review-insights/artists/{genre}",
            params={"limit": limit},
            headers={"X-API-Key": self.api_key}
        )
        response.raise_for_status()
        return [ReviewArtist(**item) for item in response.json()]
    
    async def get_artist_details(
        self, 
        artist_id: str
    ) -> ArtistReviewSummary:
        response = await self.client.get(
            f"{self.base_url}/api/v1/review-insights/artist/{artist_id}",
            headers={"X-API-Key": self.api_key}
        )
        response.raise_for_status()
        return ArtistReviewSummary(**response.json())
    
    async def trigger_sync(self) -> SyncStatus:
        response = await self.client.post(
            f"{self.base_url}/api/v1/review-insights/sync",
            headers={"X-API-Key": self.api_key}
        )
        response.raise_for_status()
        return SyncStatus(**response.json())
```

#### 3. Event-Driven Integration

**Webhook Handler**:
```python
@app.post("/webhooks/review-updates")
async def handle_review_update(payload: ReviewUpdatePayload):
    """Handle webhook notifications from Review Discovery Engine"""
    try:
        # Process new review data
        if payload.event_type == "new_reviews":
            await process_new_reviews(payload.data)
        elif payload.event_type == "artist_updated":
            await update_artist_insights(payload.data)
        
        return {"status": "processed"}
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Processing failed")
```

**Message Queue Integration**:
```python
class ReviewUpdateConsumer:
    async def consume_updates(self):
        """Consume review updates from message queue"""
        async for message in queue.subscribe("review.updates"):
            try:
                update = ReviewUpdate.parse_raw(message.body)
                await process_review_update(update)
                await message.ack()
            except Exception as e:
                logger.error(f"Failed to process update: {e}")
                await message.nack()
```

### Data Flow Between Systems

```
Review Discovery Engine                    Music Discovery Companion
-----------------------                    -------------------------
1. Analyzes music reviews  ──────────────►  Queries review_insights
2. Extracts artist insights              │
3. Calculates discovery scores           │
4. Stores in PostgreSQL   ◄──────────────┘
5. Sends webhook notification ───────────►  Receives webhook
                                         │
                                         ▼
                                  Updates local cache
                                         │
                                         ▼
                                  Uses insights for
                                  recommendation strategies
```

### Synchronization Strategy

**Sync Modes**:
1. **Real-time**: Webhook notifications for critical updates
2. **Scheduled**: Hourly batch sync for new reviews
3. **On-demand**: Manual sync trigger via API
4. **Cache-first**: Local Redis cache with 6-hour TTL

**Conflict Resolution**:
- Last-write-wins for artist data
- Merge for genre tags (union)
- Average for sentiment scores
- Max for discovery scores

---

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend UI                             │
│                    (Phase 5 - React + Tailwind)                 │
│                                                                 │
│  ⚠️  SECURITY BOUNDARY: Frontend NEVER accesses external APIs  │
│  ⚠️  All communication via Backend API only                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API (ONLY)
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API                                 │
│              (Phase 4 - FastAPI + Python)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Auth Module │  │ Rate Limit  │  │ API Routes  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  🔒 GATEWAY: All external API access happens here              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI Orchestration Layer                       │
│                   (Phase 3 - Python)                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Orchestration Controller                       │   │
│  │  - Coordinates all AI components                        │   │
│  │  - Manages prompt chains                                │   │
│  │  - Handles fallback strategies                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────┬───────────────────────┬────────────────────────┘
                │                       │
                ▼                       ▼
┌──────────────────────────┐ ┌──────────────────────────────────┐
│  AI Conversation Engine   │ │  Music Recommendation Engine      │
│    (Phase 1)              │ │       (Phase 2)                   │
│  ┌─────────────────────┐  │ │  ┌─────────────────────────────┐  │
│  │ Intent Recognition  │  │ │  │ Review-Based Discovery     │  │
│  │ Context Manager     │  │ │  │ Mood-Activity Matching     │  │
│  │ Query Parser        │  │ │  │ Similarity Search          │  │
│  │ Response Generator  │  │ │  │ Habit Breaking Engine      │  │
│  └─────────────────────┘  │ │  │ Genre Exploration          │  │
└───────────────────────────┘ │  └─────────────────────────────┘  │
                              └───────────────────────────────────┘
                                        │
                ┌───────────────────────┼───────────────────────┐
                │                       │                       │
                ▼                       ▼                       ▼
┌───────────────────────────┐ ┌───────────────────┐ ┌─────────────────────┐
│   Groq LLM Service       │ │  Spotify API      │ │  Review Discovery   │
│   (Llama 3.1 / Mixtral)  │ │  (Web API)        │ │  Engine API/DB     │
│                           │ │                   │ │  (External System)  │
│  🔒 Backend-only access   │ │  🔒 Backend-only  │ │  🔒 Backend-only    │
└───────────────────────────┘ └───────────────────┘ └─────────────────────┘
```

### Communication Architecture & Security Boundaries

**Critical Security Principle**: The Frontend UI (Phase 5) MUST NEVER directly access:
- Music APIs (Spotify, Deezer, Last.fm, Jamendo)
- Review Discovery Engine outputs or database
- Groq LLM API
- Any external third-party APIs

**All Frontend Communication**:
- Frontend → Backend API (Phase 4) via HTTP/REST only
- Backend API acts as the sole gateway to all external services
- Frontend receives only processed, sanitized responses
- No API keys or credentials exposed to frontend

**Backend API Responsibilities**:
1. **API Gateway**: All external API calls originate from Backend API
2. **Credential Management**: Stores and manages all API keys securely
3. **Request Validation**: Validates and sanitizes all requests before forwarding
4. **Response Processing**: Processes external API responses before sending to frontend
5. **Rate Limiting**: Enforces rate limits on external API calls
6. **Caching**: Caches external API responses to reduce calls
7. **Error Handling**: Handles external API failures gracefully

**External API Access Pattern**:
```
Frontend → Backend API → Phase 3 (Orchestrator) → Phase 2 (Recommendation Engine) → External APIs
```

**Data Flow Security**:
- Frontend sends user query → Backend API
- Backend API validates request → Orchestrator
- Orchestrator coordinates phases → Recommendation Engine
- Recommendation Engine calls external APIs (Spotify, Review Engine)
- External APIs return data → Recommendation Engine processes
- Processed data → Backend API → Frontend (sanitized response)

**Why This Architecture?**
1. **Security**: API keys never exposed to client-side code
2. **Control**: Backend can validate, rate-limit, and cache requests
3. **Flexibility**: Can swap external APIs without frontend changes
4. **Monitoring**: Centralized logging of all external API calls
5. **Cost Control**: Backend can enforce usage limits and quotas

---

## Phase 1: AI Conversation Engine

### Phase Independence
**Phase 1 operates as a completely independent microservice.**

**Independence Characteristics**:
- **Own Repository**: `phase1-ai-conversation-engine/` with its own codebase
- **Own Dependencies**: `requirements.txt` or `pyproject.toml` specific to this phase
- **Own Configuration**: `config.yaml` for phase-specific settings
- **Own Database Schema**: Manages its own PostgreSQL tables for context storage
- **Own Cache**: Dedicated Redis instance or namespace for context caching
- **API Interface**: Exposes REST API for other phases to consume
- **Mock Layer**: Includes mock implementations for Groq LLM, Redis, and PostgreSQL for isolated testing
- **Independent Deployment**: Can be deployed as a standalone Docker container

**Communication with Other Phases**:
- **Receives from**: Phase 4 (Backend API) via REST API calls
- **Sends to**: Phase 3 (AI Orchestration) via REST API or message queue
- **External Dependencies**: Groq LLM API (external service)
- **Data Exchange**: JSON payloads via HTTP/REST

**Deployment Independence**:
- Can run without Phase 2, 3, 4, or 5
- Uses environment variables for configuration
- Health check endpoint: `GET /health`
- Metrics endpoint: `GET /metrics`
- Graceful shutdown handling

### Objectives
- Classify user queries into intent categories with high accuracy
- Extract structured parameters from natural language
- Maintain conversational context across sessions
- Generate natural, conversational responses with explanations
- Handle clarification requests and feedback

### Inputs
- **User Query**: Natural language text from user
- **User Context**: Previous conversation history, user preferences
- **User ID**: Unique identifier for context retrieval
- **Session ID**: Current session identifier for short-term context

### Outputs
- **Intent Classification**: Intent category with confidence score
- **Parsed Query**: Structured parameters (mood, genre, artists, etc.)
- **Generated Response**: Natural language response with recommendations
- **Context Updates**: Updated user context based on interaction

### Folder Structure
```
phase1-ai-conversation-engine/
├── intent_recognition/
│   ├── __init__.py
│   ├── intent_recognizer.py
│   ├── intent_prompts.py
│   └── intent_schemas.py
├── context_manager/
│   ├── __init__.py
│   ├── context_manager.py
│   ├── context_schemas.py
│   └── context_strategies.py
├── query_parser/
│   ├── __init__.py
│   ├── query_parser.py
│   ├── parser_prompts.py
│   └── enrichment_mappings.py
└── response_generator/
    ├── __init__.py
    ├── response_generator.py
    ├── response_prompts.py
    └── explanation_templates.py
```

### API Flow
```
User Query → Backend API → Orchestration Controller
    ↓
Intent Recognition (Groq LLM)
    ↓
Query Parser (Groq LLM)
    ↓
Context Manager (Redis + PostgreSQL)
    ↓
Response Generator (Groq LLM)
    ↓
Backend API → Frontend UI
```

### Storage
**Short-term (Redis, 30 min TTL)**:
- Current conversation history (last 10 exchanges)
- Current mood/activity context
- Active recommendation session
- Pending clarification requests

**Medium-term (PostgreSQL, 7 days)**:
- Recent interaction history
- Last 50 recommendations and user feedback
- Temporary preference adjustments
- Recent listening pattern analysis

**Long-term (PostgreSQL, persistent)**:
- User preference profile
- Genre affinity scores
- Artist affinity scores
- Audio feature preferences
- Habit breaking history
- Discovered artists and their ratings

### Execution Flow
```
1. Receive user query from orchestration controller
2. Retrieve user context from Redis/PostgreSQL
3. Call Intent Recognition with query
   - If confidence < 0.7, fallback to GENERAL_CHAT
   - If multi-intent detected, process both
4. Call Query Parser with query and intent
   - Extract structured parameters
   - Apply enrichment mappings
   - Validate extracted parameters
5. Update context with parsed query
6. Generate response using recommendations and context
7. Validate response quality
8. Return response to orchestration controller
9. Update context with interaction result
```

### Error Handling
**Intent Recognition Errors**:
- LLM timeout → Retry with secondary model
- Invalid response format → Fallback to rule-based classification
- Low confidence → Log warning, use GENERAL_CHAT intent

**Query Parser Errors**:
- Invalid JSON response → Retry with stricter prompt
- Missing required fields → Use default values, log warning
- LLM timeout → Use cached similar queries

**Context Manager Errors**:
- Redis connection failure → Fallback to PostgreSQL only
- PostgreSQL connection failure → Use in-memory context
- Context corruption → Rebuild from conversation history

**Response Generator Errors**:
- LLM timeout → Use cached response or template
- Response too long → Truncate and add ellipsis
- Inappropriate content detected → Regenerate with safety filters

### Retry Mechanism
**Exponential Backoff Strategy**:
```python
class RetryStrategy:
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        self.max_delay = 10.0
    
    async def execute_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except (TimeoutError, ConnectionError) as e:
                if attempt == self.max_retries - 1:
                    raise
                delay = min(
                    self.base_delay * (2 ** attempt),
                    self.max_delay
                )
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
                await asyncio.sleep(delay)
```

**Fallback Chain**:
1. Primary LLM (Llama 3.1 70B)
2. Secondary LLM (Mixtral 8x7B)
3. Cached responses
4. Rule-based responses
5. Generic error message

### Logging
**Log Levels**:
- **DEBUG**: Detailed execution flow, parameter values
- **INFO**: Normal operations, user interactions
- **WARNING**: Low confidence, fallbacks, retries
- **ERROR**: Failures, exceptions, API errors

**Structured Logging Format**:
```python
logger.info(
    "intent_recognition",
    extra={
        "user_id": user_id,
        "query": query,
        "intent": intent,
        "confidence": confidence,
        "latency_ms": latency,
        "model": model_used
    }
)
```

**Correlation IDs**:
- Generate unique ID per request
- Propagate through all components
- Include in all log entries
- Use for tracing and debugging

### Testing Strategy
**Unit Tests**:
- Intent recognition with sample queries
- Query parsing with various formats
- Context CRUD operations
- Response generation with mock LLM

**Integration Tests**:
- End-to-end conversation flow
- Context persistence across sessions
- LLM integration with actual Groq API
- Error handling and fallback mechanisms

**Performance Tests**:
- Intent recognition latency (< 500ms)
- Query parsing latency (< 500ms)
- Response generation latency (< 2s)
- Context retrieval latency (< 100ms)

**Test Coverage Target**: 90%

**Mock Strategy**:
- Mock Groq LLM responses for deterministic tests
- Mock Redis/PostgreSQL for isolated tests
- Use test fixtures for common scenarios
- Parameterized tests for edge cases

---

### Components

#### 1.1 Intent Recognition Module

**Function**: Classify user queries into intent categories using Groq LLM

**Supported Intents**:
- `MOOD_BASED`: "I want music for late-night coding"
- `SIMILARITY_SEARCH`: "Recommend artists similar to Coldplay but less mainstream"
- `HABIT_BREAKING`: "I keep listening to the same songs"
- `GENRE_EXPLORATION`: "I want something energetic but not EDM"
- `UNDISCOVERED_ARTISTS`: "Introduce me to underrated indie artists"
- `MOOD_DETECTION`: "Recommend music based on my current mood"
- `GENRE_DISCOVERY`: "Help me discover genres I've never explored"
- `CLARIFICATION`: User asks for explanation or details
- `FEEDBACK`: User provides feedback on recommendations
- `GENERAL_CHAT`: Conversational interactions

**Implementation**:
```python
class IntentRecognizer:
    def __init__(self, groq_client):
        self.client = groq_client
        self.intent_prompt = """
        Classify the following user query into one of these intents:
        - MOOD_BASED: User wants music based on mood or activity
        - SIMILARITY_SEARCH: User wants artists similar to a reference
        - HABIT_BREAKING: User wants to break repetitive patterns
        - GENRE_EXPLORATION: User wants to explore or avoid genres
        - UNDISCOVERED_ARTISTS: User wants underrated/hidden gems
        - MOOD_DETECTION: User wants mood-based recommendations
        - GENRE_DISCOVERY: User wants to discover new genres
        - CLARIFICATION: User asks for explanation
        - FEEDBACK: User provides feedback
        - GENERAL_CHAT: General conversation
        
        Query: {query}
        
        Return only the intent name and confidence score (0-1).
        Format: INTENT|CONFIDENCE
        """
    
    def recognize(self, query: str) -> tuple[str, float]:
        response = self.client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": self.intent_prompt.format(query=query)}],
            temperature=0.1
        )
        intent, confidence = response.choices[0].message.content.split("|")
        return intent.strip(), float(confidence)
```

**Features**:
- Confidence scoring for intent certainty
- Fallback to general chat for low-confidence queries
- Multi-intent detection for complex queries
- Intent hierarchy for nested requests

#### 1.2 Context Manager

**Function**: Maintain conversation state and user preferences across sessions

**State Storage Layers**:
- **Short-term Context** (Redis, 30 min TTL):
  - Current conversation history (last 10 exchanges)
  - Current mood/activity context
  - Active recommendation session
  - Pending clarification requests

- **Medium-term Context** (PostgreSQL, 7 days):
  - Recent interaction history
  - Last 50 recommendations and user feedback
  - Temporary preference adjustments
  - Recent listening pattern analysis

- **Long-term Context** (PostgreSQL, persistent):
  - User preference profile
  - Genre affinity scores
  - Artist affinity scores
  - Audio feature preferences
  - Habit breaking history
  - Discovered artists and their ratings

**Context Schema**:
```python
class UserContext:
    user_id: str
    session_id: str
    conversation_history: List[ConversationTurn]
    current_mood: Optional[MoodState]
    current_activity: Optional[ActivityState]
    preference_profile: PreferenceProfile
    listening_patterns: ListeningPatternAnalysis
    discovered_artists: List[DiscoveredArtist]
    feedback_history: List[RecommendationFeedback]
```

**Context Update Strategies**:
- Explicit: User directly states preferences
- Implicit: Derived from feedback and listening behavior
- Temporal: Context decay for outdated information
- Session-based: Reset between distinct sessions

#### 1.3 Query Parser & Enricher

**Function**: Extract structured parameters from natural language using Groq LLM

**Extracted Parameters**:
```python
class ParsedQuery:
    intent: str
    mood_descriptors: List[str]  # energetic, calm, melancholic
    activity_context: Optional[str]  # coding, workout, studying
    time_preference: Optional[TimeContext]  # late-night, morning
    genre_inclusions: List[str]
    genre_exclusions: List[str]
    artist_references: List[str]
    energy_level: Optional[float]  # 0.0-1.0
    popularity_filter: Optional[PopularityLevel]  # mainstream, indie, underground
    tempo_range: Optional[Tuple[int, int]]
    instrumental_preference: Optional[bool]
    novelty_preference: Optional[float]  # 0.0-1.0 (familiar to novel)
    explanation_depth: ExplanationLevel
```

**Enrichment Mappings**:
```python
MOOD_MAPPINGS = {
    "chill": {"valence": 0.3-0.6, "energy": 0.2-0.5},
    "energetic": {"valence": 0.6-0.9, "energy": 0.7-1.0},
    "melancholic": {"valence": 0.1-0.4, "energy": 0.2-0.5},
    "upbeat": {"valence": 0.7-1.0, "energy": 0.6-0.9},
    "focus": {"valence": 0.4-0.7, "energy": 0.3-0.6, "instrumental": 0.7}
}

GENRE_HIERARCHIES = {
    "EDM": ["house", "techno", "dubstep", "trance", "drum and bass"],
    "rock": ["alternative rock", "indie rock", "classic rock", "punk"],
    "pop": ["synth-pop", "indie pop", "art pop"]
}

ACTIVITY_FEATURES = {
    "coding": {"energy": 0.4-0.7, "instrumental": 0.6, "tempo": 80-120},
    "workout": {"energy": 0.8-1.0, "tempo": 120-160},
    "studying": {"energy": 0.3-0.6, "instrumental": 0.8},
    "late-night": {"energy": 0.2-0.5, "valence": 0.3-0.6}
}
```

**Implementation**:
```python
class QueryParser:
    def __init__(self, groq_client):
        self.client = groq_client
        self.parser_prompt = """
        Extract structured parameters from this music discovery query.
        
        Query: {query}
        
        Return a JSON object with these fields:
        - mood_descriptors: list of mood terms
        - activity_context: activity if mentioned
        - genre_inclusions: genres to include
        - genre_exclusions: genres to exclude
        - artist_references: artists mentioned
        - energy_level: 0.0-1.0 if specified
        - popularity_filter: "mainstream", "indie", or "underground"
        - novelty_preference: 0.0-1.0 (familiar to novel)
        
        Use null for unspecified fields.
        """
    
    def parse(self, query: str) -> ParsedQuery:
        response = self.client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": self.parser_prompt.format(query=query)}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return ParsedQuery.parse_raw(response.choices[0].message.content)
```

#### 1.4 Response Generator

**Function**: Craft natural, conversational responses with explanations using Groq LLM

**Response Types**:
1. **Direct Recommendation**: Single or small set of recommendations with detailed explanations
2. **Multi-Option Presentation**: Several options with trade-offs explained
3. **Educational Content**: Information about new genres/artists before recommendations
4. **Habit-Breaking Suggestion**: Explanation of pattern and novel suggestions
5. **Clarification Request**: Ask for missing information naturally
6. **Feedback Acknowledgment**: Confirm and incorporate user feedback

**Response Structure**:
```python
class GeneratedResponse:
    greeting: Optional[str]
    main_content: str
    recommendations: List[RecommendationPresentation]
    explanations: List[str]
    follow_up_suggestions: List[str]
    confidence_score: float
```

**Explanation Templates**:
```python
EXPLANATION_PATTERNS = {
    "review_based": """
    {artist} is highly rated in reviews for {reason}. 
    Reviewers describe their music as {description}, 
    which aligns with your interest in {user_preference}.
    """,
    
    "mood_match": """
    Based on your {mood} mood, I selected tracks with 
    {feature} characteristics. {artist}'s {song} has 
    {specific_features} that create this atmosphere.
    """,
    
    "similarity": """
    {artist} shares stylistic elements with {reference_artist}, 
    particularly in {shared_features}. However, they bring 
    unique elements like {unique_features}, making them {comparison}.
    """,
    
    "habit_break": """
    I noticed you've been listening to {pattern} frequently. 
    To break this pattern while maintaining appeal, I suggest 
    {artist}. They offer {novel_elements} while keeping 
    {familiar_elements} that you enjoy.
    """
}
```

**Implementation**:
```python
class ResponseGenerator:
    def __init__(self, groq_client):
        self.client = groq_client
        self.response_prompt = """
        Generate a natural, conversational response for music recommendations.
        
        User Query: {query}
        Parsed Intent: {intent}
        Recommendations: {recommendations}
        Explanations: {explanations}
        Conversation Context: {context}
        
        Guidelines:
        - Be conversational and friendly
        - Explain WHY each recommendation was made
        - Connect recommendations to user's stated preferences
        - Offer 2-3 follow-up questions
        - Keep response under 200 words
        - Use markdown for formatting artist/song names
        """
    
    def generate(self, query: str, intent: str, recommendations: List, 
                 explanations: List, context: dict) -> str:
        response = self.client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": self.response_prompt.format(
                query=query, intent=intent, 
                recommendations=recommendations,
                explanations=explanations, context=context
            )}],
            temperature=0.7
       )
        return response.choices[0].message.content
```

### Technology Stack
- **LLM**: Groq (Llama 3.1 70B or Mixtral 8x7B)
- **Vector Store**: ChromaDB for conversation embeddings
- **Cache**: Redis for session state (30 min TTL)
- **Database**: PostgreSQL for persistent context
- **Framework**: LangChain for LLM orchestration

### Data Flow
```
User Query → Intent Recognition → Query Parsing → Context Enrichment → 
Response Generation → Natural Language Output
```

---

## Phase 2: Music Recommendation Engine

### Phase Independence
**Phase 2 operates as a completely independent microservice.**

**Independence Characteristics**:
- **Own Repository**: `phase2-music-recommendation-engine/` with its own codebase
- **Own Dependencies**: `requirements.txt` or `pyproject.toml` specific to this phase
- **Own Configuration**: `config.yaml` for phase-specific settings
- **Own Database Schema**: Manages its own PostgreSQL tables for recommendations and patterns
- **Own Cache**: Dedicated Redis instance or namespace for Spotify/review data caching
- **Own Vector Store**: Dedicated ChromaDB instance for audio feature embeddings
- **API Interface**: Exposes REST API for other phases to consume
- **Mock Layer**: Includes mock implementations for Spotify API, Review Engine API, ChromaDB, and PostgreSQL for isolated testing
- **Independent Deployment**: Can be deployed as a standalone Docker container

**Communication with Other Phases**:
- **Receives from**: Phase 3 (AI Orchestration) via REST API calls
- **Sends to**: Phase 3 (AI Orchestration) via REST API responses
- **External Dependencies**: 
  - Spotify Web API (external service)
  - Review Discovery Engine API (external service, separate system)
- **Data Exchange**: JSON payloads via HTTP/REST

**Deployment Independence**:
- Can run without Phase 1, 3, 4, or 5
- Uses environment variables for configuration
- Health check endpoint: `GET /health`
- Metrics endpoint: `GET /metrics`
- Graceful shutdown handling
- Can use mock data for Spotify and Review Engine when unavailable

### Objectives
- Generate music recommendations using multiple strategies
- Integrate review insights from Review Discovery Engine
- Match music to user mood and activity context
- Break repetitive listening habits with novel suggestions
- Explain every recommendation with clear reasoning

### Inputs
- **Parsed Query**: Structured parameters from Conversation Engine
- **User Context**: User preferences, listening patterns, history
- **Review Insights**: Artist data from Review Discovery Engine
- **Spotify Data**: Artist/track features from Spotify API

### Outputs
- **Recommendations**: Ranked list of artist/track recommendations
- **Explanations**: Human-readable reasoning for each recommendation
- **Confidence Scores**: Relevance scores for each recommendation
- **Strategy Metadata**: Which strategies contributed to each recommendation

### Folder Structure
```
phase2-music-recommendation-engine/
├── review_based_discovery/
│   ├── __init__.py
│   ├── review_discovery.py
│   ├── scoring_algorithms.py
│   └── review_client.py
├── mood_activity_matching/
│   ├── __init__.py
│   ├── mood_matcher.py
│   ├── feature_mappings.py
│   └── spotify_search.py
├── similarity_search/
│   ├── __init__.py
│   ├── similarity_search.py
│   ├── constraint_filter.py
│   └── feature_calculator.py
├── habit_breaking/
│   ├── __init__.py
│   ├── habit_analyzer.py
│   ├── novelty_calculator.py
│   └── pattern_detector.py
├── genre_exploration/
│   ├── __init__.py
│   ├── genre_explorer.py
│   ├── genre_graph.py
│   └── education_generator.py
├── recommendation_fusion/
│   ├── __init__.py
│   ├── fusion_engine.py
│   ├── ranking_strategies.py
│   └── diversity_sampler.py
└── explanation_generator/
    ├── __init__.py
    ├── explanation_generator.py
    ├── evidence_gatherer.py
    └── template_manager.py
```

### API Flow
```
Orchestration Controller → Recommendation Engine
    ↓
Strategy Selection (based on intent)
    ↓
Parallel Strategy Execution:
    - Review-Based Discovery
    - Mood-Activity Matching
    - Similarity Search
    - Habit Breaking
    - Genre Exploration
    ↓
Recommendation Fusion
    ↓
Explanation Generation
    ↓
Ranked Recommendations with Explanations
    ↓
Orchestration Controller
```

### Storage
**PostgreSQL**:
- User listening patterns
- Recommendation history
- Feedback data
- Cached Spotify data

**Redis**:
- Spotify artist/track cache (24h TTL)
- Review insights cache (6h TTL)
- Feature vectors cache (12h TTL)

**ChromaDB**:
- Audio feature embeddings
- Artist similarity vectors
- Genre cluster embeddings

### Execution Flow
```
1. Receive parsed query and user context
2. Select active strategies based on intent
3. Execute strategies in parallel:
   a. Review-Based Discovery:
      - Query review_insights table
      - Filter by genre and discovery score
      - Cross-reference with Spotify data
      - Rank by combined score
   b. Mood-Activity Matching:
      - Map mood/activity to feature ranges
      - Query Spotify API with constraints
      - Filter and rank by alignment
      - Apply diversity sampling
   c. Similarity Search:
      - Get reference artist features
      - Find similar artists
      - Apply user constraints
      - Rank by similarity + constraint satisfaction
   d. Habit Breaking:
      - Analyze listening patterns
      - Calculate novelty scores
      - Select diverse recommendations
   e. Genre Exploration:
      - Find unexplored related genres
      - Get representative artists
      - Generate educational content
4. Fuse recommendations from all strategies
5. Remove duplicates and re-rank
6. Generate explanations for each recommendation
7. Return ranked list with explanations
```

### Error Handling
**Review Discovery Errors**:
- Database connection failure → Use cached data
- No results found → Fallback to other strategies
- Invalid artist IDs → Log and skip

**Mood Matching Errors**:
- Spotify API timeout → Retry with exponential backoff
- Invalid feature ranges → Use default ranges
- No results → Fallback to genre-based search

**Similarity Search Errors**:
- Artist not found → Suggest similar artists
- Feature extraction failure → Use genre similarity
- API rate limit → Use cached similar artists

**Habit Breaking Errors**:
- Insufficient listening history → Skip habit analysis
- Pattern detection failure → Use standard recommendations
- Novelty calculation error → Use random novelty scores

**Fusion Errors**:
- Empty recommendation list → Return error to user
- Scoring algorithm failure → Use simple ranking
- Diversity sampling error → Return top N without diversity

### Retry Mechanism
**Spotify API Retry**:
```python
class SpotifyRetryHandler:
    def __init__(self):
        self.max_retries = 5
        self.rate_limit_delay = 60  # seconds for 429
    
    async def execute_with_retry(self, func):
        for attempt in range(self.max_retries):
            try:
                return await func()
            except SpotifyRateLimitError:
                logger.warning("Rate limited, waiting 60s")
                await asyncio.sleep(self.rate_limit_delay)
            except SpotifyServerError as e:
                if attempt == self.max_retries - 1:
                    raise
                delay = 2 ** attempt
                logger.warning(f"Server error, retrying in {delay}s")
                await asyncio.sleep(delay)
```

**Database Retry**:
- Connection errors: 3 retries with 1s delay
- Query timeouts: 2 retries with 2s delay
- Deadlocks: Automatic retry with backoff

**Strategy Fallback**:
- If strategy fails completely, exclude from fusion
- If partial strategy success, use available results
- Log all failures for monitoring

### Logging
**Strategy Execution Logs**:
```python
logger.info(
    "strategy_execution",
    extra={
        "strategy": strategy_name,
        "user_id": user_id,
        "query_params": parsed_query.dict(),
        "results_count": len(results),
        "execution_time_ms": execution_time,
        "cache_hit": cache_hit
    }
)
```

**Recommendation Logs**:
- Track which strategies contributed
- Log ranking scores
- Record user feedback
- Monitor recommendation acceptance rate

**Performance Logs**:
- Strategy execution times
- Cache hit rates
- API call counts
- Token usage for explanations

### Testing Strategy
**Unit Tests**:
- Each strategy in isolation
- Scoring algorithms
- Feature calculations
- Explanation generation

**Integration Tests**:
- Strategy fusion
- End-to-end recommendation flow
- Spotify API integration
- Review database integration

**Performance Tests**:
- Recommendation latency (< 3s total)
- Strategy parallelization efficiency
- Cache effectiveness
- Database query performance

**Quality Tests**:
- Recommendation diversity
- Explanation quality (manual review)
- User satisfaction (A/B testing)
- Habit breaking effectiveness

**Test Coverage Target**: 85%

---

### Components

#### 2.1 Multi-Strategy Recommendation System

##### Strategy A: Review-Based Artist Discovery

**Source**: AI-Powered Review Discovery Engine insights (PostgreSQL)

**Process**:
1. Query review database for highly-rated but less-known artists
2. Filter by genre alignment with user preferences
3. Rank by review sentiment strength and uniqueness
4. Cross-reference with Spotify popularity metrics
5. Apply user's novelty preference

**Database Schema**:
```sql
CREATE TABLE review_insights (
    id SERIAL PRIMARY KEY,
    artist_id VARCHAR(50),
    artist_name VARCHAR(255),
    spotify_popularity INT,
    review_sentiment FLOAT,
    review_count INT,
    genre_tags TEXT[],
    unique_descriptors TEXT[],
    discovery_score FLOAT,
    last_updated TIMESTAMP
);

CREATE INDEX idx_review_insights_genre ON review_insights USING GIN(genre_tags);
CREATE INDEX idx_review_insights_discovery ON review_insights(discovery_score DESC);
```

**Algorithm**:
```python
class ReviewBasedDiscovery:
    def __init__(self, db_connection, spotify_client):
        self.db = db_connection
        self.spotify = spotify_client
    
    def discover(self, user_preferences: ParsedQuery, limit: int = 10) -> List[Artist]:
        # Query review insights
        query = """
        SELECT artist_id, artist_name, review_sentiment, 
               review_count, genre_tags, unique_descriptors, discovery_score
        FROM review_insights
        WHERE discovery_score > %s
        AND genre_tags && %s
        ORDER BY discovery_score DESC
        LIMIT %s
        """
        
        results = self.db.execute(query, [
            user_preferences.novelty_preference,
            user_preferences.genre_inclusions,
            limit * 3  # Get more to filter
        ])
        
        # Filter and rank
        candidates = []
        for row in results:
            artist_data = self.spotify.get_artist(row['artist_id'])
            score = self._calculate_score(row, artist_data, user_preferences)
            candidates.append((score, row, artist_data))
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c[2] for c in candidates[:limit]]
    
    def _calculate_score(self, review_row, spotify_data, preferences) -> float:
        score = review_row['discovery_score'] * 0.4
        score += review_row['review_sentiment'] * 0.3
        score += (1 - spotify_data['popularity'] / 100) * 0.2
        score += self._genre_alignment(review_row['genre_tags'], preferences) * 0.1
        return score
```

**Output**: Underrated artists with review-backed rationale

##### Strategy B: Mood-Activity Matching

**Process**:
1. Map user mood/activity to audio feature ranges
2. Query Spotify API with feature constraints
3. Apply user preference weighting
4. Diversity sampling to prevent repetition

**Audio Feature Mappings**:
```python
MOOD_FEATURE_RANGES = {
    "energetic": {
        "energy": (0.7, 1.0),
        "valence": (0.6, 1.0),
        "tempo": (120, 160)
    },
    "calm": {
        "energy": (0.2, 0.5),
        "valence": (0.4, 0.7),
        "tempo": (60, 100)
    },
    "melancholic": {
        "energy": (0.2, 0.5),
        "valence": (0.1, 0.4),
        "acousticness": (0.5, 1.0)
    },
    "focus": {
        "energy": (0.3, 0.6),
        "instrumentalness": (0.6, 1.0),
        "speechiness": (0.0, 0.3)
    }
}

ACTIVITY_FEATURE_RANGES = {
    "coding": {
        "energy": (0.4, 0.7),
        "instrumentalness": (0.5, 0.9),
        "tempo": (80, 120)
    },
    "workout": {
        "energy": (0.8, 1.0),
        "tempo": (120, 160),
        "danceability": (0.7, 1.0)
    },
    "studying": {
        "energy": (0.2, 0.5),
        "instrumentalness": (0.7, 1.0),
        "speechiness": (0.0, 0.2)
    }
}
```

**Implementation**:
```python
class MoodActivityMatcher:
    def __init__(self, spotify_client):
        self.spotify = spotify_client
    
    def match(self, mood: str, activity: Optional[str], 
              preferences: ParsedQuery, limit: int = 10) -> List[Track]:
        # Combine mood and activity features
        feature_ranges = self._combine_features(mood, activity)
        
        # Build Spotify search query
        search_params = self._build_search_params(feature_ranges, preferences)
        
        # Search with seed genres/artists from preferences
        results = self.spotify.search_tracks(
            seed_genres=preferences.genre_inclusions[:2],
            seed_artists=preferences.artist_references[:1],
            limit=limit * 2,
            **search_params
        )
        
        # Filter and rank
        filtered = self._filter_by_features(results, feature_ranges)
        ranked = self._rank_by_alignment(filtered, feature_ranges, preferences)
        
        # Apply diversity sampling
        diverse = self._diversity_sample(ranked, limit)
        
        return diverse
    
    def _combine_features(self, mood: str, activity: Optional[str]) -> dict:
        features = MOOD_FEATURE_RANGES.get(mood, {}).copy()
        if activity and activity in ACTIVITY_FEATURE_RANGES:
            activity_features = ACTIVITY_FEATURE_RANGES[activity]
            for key, value in activity_features.items():
                if key in features:
                    # Intersect ranges
                    features[key] = (
                        max(features[key][0], value[0]),
                        min(features[key][1], value[1])
                    )
                else:
                    features[key] = value
        return features
```

##### Strategy C: Similarity Search with Constraints

**Process**:
1. Identify seed artist from user query
2. Fetch artist audio features and genres
3. Apply user constraints (e.g., "less mainstream")
4. Find similar artists within feature space
5. Filter by constraint parameters
6. Rank by similarity score and constraint satisfaction

**Implementation**:
```python
class SimilaritySearch:
    def __init__(self, spotify_client, groq_client):
        self.spotify = spotify_client
        self.groq = groq_client
    
    def search(self, reference_artist: str, constraints: ParsedQuery, 
               limit: int = 10) -> List[Artist]:
        # Get reference artist data
        ref_artist = self.spotify.get_artist_by_name(reference_artist)
        ref_features = self.spotify.get_artist_audio_features(ref_artist['id'])
        
        # Get similar artists from Spotify
        similar = self.spotify.get_related_artists(ref_artist['id'])
        
        # Apply constraints
        filtered = []
        for artist in similar:
            artist_data = self.spotify.get_artist(artist['id'])
            features = self.spotify.get_artist_audio_features(artist['id'])
            
            if self._meets_constraints(artist_data, features, constraints):
                similarity = self._calculate_similarity(ref_features, features)
                constraint_score = self._calculate_constraint_score(
                    artist_data, constraints
                )
                filtered.append({
                    'artist': artist_data,
                    'similarity': similarity,
                    'constraint_score': constraint_score
                })
        
        # Rank and return
        filtered.sort(key=lambda x: x['similarity'] * 0.6 + x['constraint_score'] * 0.4, 
                     reverse=True)
        return [f['artist'] for f in filtered[:limit]]
    
    def _meets_constraints(self, artist_data, features, constraints) -> bool:
        # Check popularity constraint
        if constraints.popularity_filter == "indie":
            if artist_data['popularity'] > 50:
                return False
        elif constraints.popularity_filter == "underground":
            if artist_data['popularity'] > 20:
                return False
        
        # Check genre exclusions
        artist_genres = set(artist_data['genres'])
        if any(g in artist_genres for g in constraints.genre_exclusions):
            return False
        
        # Check energy level
        if constraints.energy_level:
            if not (constraints.energy_level - 0.2 <= features['energy'] <= 
                   constraints.energy_level + 0.2):
                return False
        
        return True
```

##### Strategy D: Habit Breaking Engine

**Process**:
1. Analyze user's recent listening history (Spotify API)
2. Identify repetitive patterns (same artists, genres, features)
3. Calculate "novelty score" for potential recommendations
4. Prioritize recommendations that break patterns while maintaining alignment
5. Gradual exploration strategy (small steps outside comfort zone)

**Pattern Detection**:
```python
class HabitAnalyzer:
    def __init__(self, spotify_client):
        self.spotify = spotify_client
    
    def analyze_patterns(self, user_id: str, days: int = 30) -> ListeningPatternAnalysis:
        # Get recent listening history
        history = self.spotify.get_recently_played(user_id, limit=50)
        
        # Analyze patterns
        artist_counts = Counter()
        genre_counts = Counter()
        feature_averages = defaultdict(list)
        
        for item in history:
            track = item['track']
            artist_counts[track['artists'][0]['id']] += 1
            
            artist = self.spotify.get_artist(track['artists'][0]['id'])
            for genre in artist['genres']:
                genre_counts[genre] += 1
            
            features = self.spotify.get_track_audio_features(track['id'])
            for key, value in features.items():
                feature_averages[key].append(value)
        
        # Calculate statistics
        total_tracks = len(history)
        top_artist_pct = artist_counts.most_common(1)[0][1] / total_tracks
        top_genre_pct = genre_counts.most_common(1)[0][1] / total_tracks
        
        avg_features = {k: sum(v)/len(v) for k, v in feature_averages.items()}
        
        return ListeningPatternAnalysis(
            repetition_score=top_artist_pct * 0.5 + top_genre_pct * 0.5,
            dominant_artists=[a for a, _ in artist_counts.most_common(5)],
            dominant_genres=[g for g, _ in genre_counts.most_common(5)],
            average_features=avg_features,
            needs_intervention=top_artist_pct > 0.3 or top_genre_pct > 0.4
        )
```

**Novelty Calculation**:
```python
class HabitBreaker:
    def __init__(self, pattern_analyzer, recommendation_engine):
        self.analyzer = pattern_analyzer
        self.engine = recommendation_engine
    
    def break_habit(self, user_id: str, preferences: ParsedQuery, 
                   limit: int = 10) -> List[Recommendation]:
        patterns = self.analyzer.analyze_patterns(user_id)
        
        if not patterns.needs_intervention:
            return self.engine.recommend(preferences, limit)
        
        # Generate candidates
        candidates = self.engine.recommend(preferences, limit * 5)
        
        # Calculate novelty scores
        scored = []
        for candidate in candidates:
            novelty = self._calculate_novelty(candidate, patterns)
            alignment = self._calculate_alignment(candidate, preferences)
            scored.append({
                'candidate': candidate,
                'novelty': novelty,
                'alignment': alignment,
                'combined': novelty * 0.6 + alignment * 0.4
            })
        
        # Select diverse set with high novelty
        scored.sort(key=lambda x: x['combined'], reverse=True)
        selected = self._select_diverse(scored, limit)
        
        return selected
    
    def _calculate_novelty(self, candidate, patterns) -> float:
        novelty = 1.0
        
        # Penalize if artist is in dominant artists
        if candidate.artist_id in patterns.dominant_artists:
            novelty -= 0.5
        
        # Penalize if genres overlap heavily
        candidate_genres = set(candidate.genres)
        dominant_genres = set(patterns.dominant_genres)
        overlap = len(candidate_genres & dominant_genres) / len(candidate_genres)
        novelty -= overlap * 0.3
        
        # Reward feature distance from average
        feature_distance = self._feature_distance(
            candidate.features, patterns.average_features
        )
        novelty += feature_distance * 0.2
        
        return max(0.0, min(1.0, novelty))
```

##### Strategy E: Genre Exploration

**Process**:
1. Identify user's current genre preferences
2. Find related but unexplored genres using genre graph
3. Select representative artists from new genres
4. Provide educational context about the genre
5. Offer gradual entry points (familiar elements first)

**Genre Graph**:
```python
GENRE_RELATIONSHIPS = {
    "rock": {
        "related": ["alternative", "indie rock", "punk", "metal"],
        "entry_point": "alternative rock"
    },
    "pop": {
        "related": ["synth-pop", "indie pop", "art pop", "dream pop"],
        "entry_point": "indie pop"
    },
    "electronic": {
        "related": ["ambient", "downtempo", "IDM", "glitch"],
        "entry_point": "downtempo"
    },
    "hip-hop": {
        "related": ["lo-fi hip-hop", "jazz rap", "conscious hip-hop"],
        "entry_point": "lo-fi hip-hop"
    }
}

class GenreExplorer:
    def __init__(self, spotify_client, groq_client):
        self.spotify = spotify_client
        self.groq = groq_client
    
    def explore(self, user_genres: List[str], preferences: ParsedQuery, 
               limit: int = 10) -> GenreExplorationResult:
        # Find unexplored related genres
        unexplored = self._find_unexplored_genres(user_genres)
        
        # Select best entry point
        entry_genre = self._select_entry_point(unexplored, preferences)
        
        # Get representative artists
        artists = self.spotify.get_genre_artists(entry_genre, limit)
        
        # Generate genre explanation
        explanation = self._generate_genre_explanation(
            entry_genre, user_genres, preferences
        )
        
        return GenreExplorationResult(
            genre=entry_genre,
            artists=artists,
            explanation=explanation,
            similarity_to_known=self._calculate_genre_similarity(
                entry_genre, user_genres
            )
        )
    
    def _generate_genre_explanation(self, new_genre, known_genres, preferences) -> str:
        prompt = f"""
        Explain the music genre "{new_genre}" to someone who enjoys {known_genres}.
        
        Focus on:
        - What makes this genre unique
        - How it relates to genres they already know
        - Key artists to start with
        - What to listen for in the music
        
        Keep it conversational and under 150 words.
        """
        
        response = self.groq.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
```

#### 2.2 Recommendation Fusion Engine

**Purpose**: Combine results from multiple strategies into a coherent set of recommendations

**Fusion Strategies**:
1. **Weighted Fusion**: Combine scores from multiple strategies
2. **Cascade**: Try strategies in order, use next if previous fails
3. **Ensemble**: Run all strategies, select best from each
4. **Hybrid**: Use different strategies for different query types

**Implementation**:
```python
class RecommendationFusion:
    def __init__(self, strategies: dict):
        self.strategies = strategies
    
    def fuse(self, query: ParsedQuery, context: UserContext, 
             limit: int = 10) -> List[Recommendation]:
        # Select strategies based on intent
        active_strategies = self._select_strategies(query.intent)
        
        # Get recommendations from each strategy
        all_recommendations = []
        for strategy_name in active_strategies:
            strategy = self.strategies[strategy_name]
            recommendations = strategy.recommend(query, context, limit)
            all_recommendations.extend(recommendations)
        
        # Remove duplicates
        unique = self._deduplicate(all_recommendations)
        
        # Re-rank based on user context
        ranked = self._rerank_by_context(unique, context)
        
        # Apply diversity
        diverse = self._diversify(ranked, limit)
        
        return diverse
    
    def _select_strategies(self, intent: str) -> List[str]:
        strategy_map = {
            "UNDISCOVERED_ARTISTS": ["review_based", "genre_exploration"],
            "MOOD_BASED": ["mood_activity", "review_based"],
            "SIMILARITY_SEARCH": ["similarity", "review_based"],
            "HABIT_BREAKING": ["habit_breaking", "genre_exploration"],
            "GENRE_DISCOVERY": ["genre_exploration", "review_based"],
            "GENRE_EXPLORATION": ["mood_activity", "similarity"],
            "MOOD_DETECTION": ["mood_activity", "review_based"]
        }
        return strategy_map.get(intent, ["review_based", "mood_activity"])
```

#### 2.3 Explanation Generator

**Purpose**: Generate human-readable explanations for each recommendation

**Explanation Types**:
1. **Review-Based**: Cite specific review insights
2. **Feature-Based**: Explain audio feature alignment
3. **Pattern-Based**: Explain how it breaks habits
4. **Similarity-Based**: Compare to known artists
5. **Genre-Based**: Explain genre characteristics

**Implementation**:
```python
class ExplanationGenerator:
    def __init__(self, groq_client, review_db):
        self.groq = groq_client
        self.review_db = review_db
    
    def generate(self, recommendation: Recommendation, 
                query: ParsedQuery, context: UserContext) -> str:
        # Gather evidence
        evidence = self._gather_evidence(recommendation, query, context)
        
        # Select explanation type
        explanation_type = self._select_explanation_type(evidence)
        
        # Generate explanation
        if explanation_type == "review_based":
            return self._review_explanation(recommendation, evidence)
        elif explanation_type == "feature_based":
            return self._feature_explanation(recommendation, evidence, query)
        elif explanation_type == "pattern_based":
            return self._pattern_explanation(recommendation, evidence, context)
        else:
            return self._similarity_explanation(recommendation, evidence, query)
    
    def _review_explanation(self, recommendation, evidence) -> str:
        review = evidence['review_insight']
        return f"""
        {recommendation.artist_name} is highly rated in reviews for their 
        {review['unique_descriptors'][0]}. Reviewers particularly praise 
        their ability to create {review['unique_descriptors'][1] if len(review['unique_descriptors']) > 1 else 'unique soundscapes'}, 
        which aligns with your interest in discovering quality music.
        """
```

### Technology Stack
- **Spotify API**: Web API for music data and recommendations
- **Database**: PostgreSQL for review insights and user data
- **Vector Search**: ChromaDB for audio feature similarity
- **LLM**: Groq for explanation generation
- **Cache**: Redis for frequent queries

### Data Flow
```
User Query + Context → Strategy Selection → Parallel Strategy Execution → 
Recommendation Fusion → Explanation Generation → Ranked Recommendations
```

---

## Phase 3: AI Orchestration

### Phase Independence
**Phase 3 operates as a completely independent microservice.**

**Independence Characteristics**:
- **Own Repository**: `phase3-ai-orchestration/` with its own codebase
- **Own Dependencies**: `requirements.txt` or `pyproject.toml` specific to this phase
- **Own Configuration**: `config.yaml` for phase-specific settings
- **Own Database Schema**: Manages its own PostgreSQL tables for request history and metrics
- **Own Cache**: Dedicated Redis instance or namespace for response caching
- **Own Metrics**: Dedicated Prometheus instance or namespace for performance tracking
- **API Interface**: Exposes REST API for other phases to consume
- **Mock Layer**: Includes mock implementations for Phase 1, Phase 2, Groq LLM, Redis, and PostgreSQL for isolated testing
- **Independent Deployment**: Can be deployed as a standalone Docker container

**Communication with Other Phases**:
- **Receives from**: Phase 4 (Backend API) via REST API calls
- **Sends to**: 
  - Phase 1 (AI Conversation Engine) via REST API calls
  - Phase 2 (Music Recommendation Engine) via REST API calls
- **External Dependencies**: Groq LLM API (external service)
- **Data Exchange**: JSON payloads via HTTP/REST

**Deployment Independence**:
- Can run without Phase 1, 2, 4, or 5 (uses mocks for dependent phases)
- Uses environment variables for configuration
- Health check endpoint: `GET /health`
- Metrics endpoint: `GET /metrics`
- Graceful shutdown handling
- Can operate in "mock mode" for testing without dependent phases

### Objectives
- Coordinate all AI components seamlessly
- Manage prompt chains and dependencies
- Handle errors with robust fallback strategies
- Cache AI responses for performance
- Monitor AI performance and costs
- Ensure coherent AI behavior across the system

### Inputs
- **User Query**: Natural language query from user
- **User ID**: Unique identifier for context retrieval
- **Request Metadata**: Session info, timestamps, correlation IDs

### Outputs
- **Orchestrated Response**: Final response after all processing
- **Performance Metrics**: Latency, token usage, cost tracking
- **Cache Status**: Whether response was cached
- **Fallback Status**: Whether fallbacks were used

### Folder Structure
```
phase3-ai-orchestration/
├── orchestration_controller/
│   ├── __init__.py
│   ├── controller.py
│   ├── request_router.py
│   └── cache_manager.py
├── prompt_chain_manager/
│   ├── __init__.py
│   ├── chain_manager.py
│   ├── chain_definitions.py
│   └── chain_executors.py
├── fallback_manager/
│   ├── __init__.py
│   ├── fallback_manager.py
│   ├── fallback_strategies.py
│   └── rule_engine.py
├── response_validator/
│   ├── __init__.py
│   ├── validator.py
│   ├── quality_checks.py
│   └── safety_filters.py
└── performance_monitor/
    ├── __init__.py
    ├── monitor.py
    ├── metrics_collector.py
    └── cost_tracker.py
```

### API Flow
```
Backend API → Orchestration Controller
    ↓
Cache Check (Redis)
    ↓
Context Retrieval (Redis + PostgreSQL)
    ↓
Prompt Chain Execution:
    - Intent Recognition
    - Query Parsing
    - Recommendation Generation
    - Response Generation
    ↓
Response Validation
    ↓
Fallback (if validation fails)
    ↓
Cache Update
    ↓
Performance Tracking
    ↓
Backend API
```

### Storage
**Redis**:
- Response cache (1h TTL)
- Session context (30 min TTL)
- Prompt chain cache (15 min TTL)
- Rate limiting counters

**PostgreSQL**:
- Request history for analytics
- Performance metrics long-term storage
- Fallback event logs

**Prometheus**:
- Real-time metrics
- Performance data
- Cost tracking

### Execution Flow
```
1. Receive request from Backend API
2. Generate correlation ID for tracing
3. Check cache for identical recent requests
4. If cache hit, return cached response
5. Retrieve user context from Redis/PostgreSQL
6. Select appropriate prompt chain based on intent
7. Execute prompt chain:
   a. Intent Recognition
   b. Query Parsing
   c. Context Enrichment
   d. Recommendation Generation
   e. Response Generation
8. Validate response quality
9. If validation fails, trigger fallback chain
10. Cache successful response
11. Track performance metrics
12. Return response to Backend API
```

### Error Handling
**Controller Errors**:
- Cache connection failure → Continue without cache
- Context retrieval failure → Use empty context
- Chain selection failure → Use default chain

**Prompt Chain Errors**:
- LLM timeout → Retry with fallback model
- Invalid chain output → Restart chain with error context
- Chain execution failure → Use fallback chain

**Validation Errors**:
- Response too short → Regenerate with length constraint
- Missing recommendations → Add error message
- Inappropriate content → Regenerate with safety filters

**Fallback Errors**:
- All fallbacks exhausted → Return generic error
- Rule engine failure → Return static message
- Cache fallback failure → Return error directly

### Retry Mechanism
**LLM Retry Strategy**:
```python
class LLMRetryStrategy:
    def __init__(self):
        self.max_retries = 3
        self.models = [
            "llama-3.1-70b-versatile",  # Primary
            "mixtral-8x7b",            # Secondary
            "llama-3.1-8b"              # Tertiary
        ]
    
    async def execute_with_fallback(self, prompt, context):
        for model in self.models:
            try:
                return await self._call_llm(model, prompt, context)
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue
        raise AllModelsFailedError()
```

**Chain Retry**:
- If chain fails at step N, retry from step N
- Max 2 retries per chain
- If chain fails completely, use fallback chain

**Cache Retry**:
- Redis connection failure: Log and continue
- Cache write failure: Log and continue (non-critical)
- Cache read failure: Log and continue

### Logging
**Request Logging**:
```python
logger.info(
    "orchestration_request",
    extra={
        "correlation_id": correlation_id,
        "user_id": user_id,
        "query": query,
        "cache_hit": cache_hit,
        "chain_used": chain_name,
        "total_latency_ms": total_latency
    }
)
```

**Component Logging**:
- Log each component execution time
- Track LLM calls with model and token usage
- Record fallback activations
- Monitor cache hit rates

**Error Logging**:
- Log all errors with stack traces
- Record retry attempts
- Track fallback usage
- Alert on repeated failures

### Testing Strategy
**Unit Tests**:
- Controller logic
- Chain selection
- Cache operations
- Validation rules

**Integration Tests**:
- End-to-end chain execution
- Fallback chain activation
- Cache integration
- Performance tracking

**Load Tests**:
- Concurrent request handling
- Cache performance under load
- LLM rate limit handling
- Memory usage monitoring

**Chaos Tests**:
- LLM failures
- Cache failures
- Database failures
- Network failures

**Test Coverage Target**: 85%

---

### Components

#### 3.1 Orchestration Controller

**Function**: Central coordinator for all AI operations

**Responsibilities**:
- Route requests to appropriate AI components
- Manage prompt chains and dependencies
- Handle errors and fallback strategies
- Cache AI responses for performance
- Monitor AI performance and costs

**Implementation**:
```python
class OrchestrationController:
    def __init__(self, groq_client, conversation_engine, 
                 recommendation_engine, context_manager):
        self.groq = groq_client
        self.conversation = conversation_engine
        self.recommendation = recommendation_engine
        self.context = context_manager
        self.cache = RedisCache()
    
    async def process_request(self, user_id: str, query: str) -> Response:
        # Get user context
        context = await self.context.get_context(user_id)
        
        # Check cache for similar queries
        cached = await self.cache.get(f"{user_id}:{query}")
        if cached and self._is_cache_valid(cached, context):
            return cached['response']
        
        # Process through conversation engine
        intent = await self.conversation.recognize_intent(query)
        parsed_query = await self.conversation.parse_query(query, intent)
        
        # Update context
        await self.context.update_context(user_id, parsed_query)
        
        # Get recommendations
        recommendations = await self.recommendation.recommend(
            parsed_query, context
        )
        
        # Generate explanations
        explanations = await self.recommendation.generate_explanations(
            recommendations, parsed_query, context
        )
        
        # Generate response
        response = await self.conversation.generate_response(
            query, intent, recommendations, explanations, context
        )
        
        # Cache result
        await self.cache.set(f"{user_id}:{query}", {
            'response': response,
            'timestamp': datetime.now()
        }, ttl=3600)
        
        return response
```

#### 3.2 Prompt Chain Manager

**Function**: Manage complex multi-step AI operations using prompt chains

**Chain Types**:

##### Chain 1: Intent → Parse → Recommend
```python
class IntentToRecommendChain:
    def __init__(self, groq_client):
        self.groq = groq_client
        self.chain = (
            {"intent": intent_recognition} |
            {"parsed": query_parser} |
            {"recommendations": recommendation_generator}
        )
    
    async def execute(self, query: str) -> dict:
        return await self.chain.ainvoke({"query": query})
```

##### Chain 2: Habit Analysis → Pattern Detection → Novel Recommendations
```python
class HabitBreakingChain:
    def __init__(self, groq_client, spotify_client):
        self.groq = groq_client
        self.spotify = spotify_client
    
    async def execute(self, user_id: str) -> dict:
        # Step 1: Analyze listening patterns
        patterns = await self.analyze_patterns(user_id)
        
        # Step 2: Detect repetitive behaviors
        habits = await self.detect_habits(patterns)
        
        # Step 3: Generate novelty strategy
        strategy = await self.generate_novelty_strategy(habits)
        
        # Step 4: Get recommendations
        recommendations = await self.get_recommendations(strategy)
        
        return {
            "patterns": patterns,
            "habits": habits,
            "recommendations": recommendations
        }
```

##### Chain 3: Genre Exploration → Education → Recommendations
```python
class GenreExplorationChain:
    def __init__(self, groq_client, spotify_client):
        self.groq = groq_client
        self.spotify = spotify_client
    
    async def execute(self, user_genres: List[str]) -> dict:
        # Step 1: Find related unexplored genres
        new_genres = await self.find_related_genres(user_genres)
        
        # Step 2: Select entry point
        entry_genre = await self.select_entry_point(new_genres, user_genres)
        
        # Step 3: Generate educational content
        education = await self.generate_genre_education(entry_genre, user_genres)
        
        # Step 4: Get representative artists
        artists = await self.get_genre_artists(entry_genre)
        
        return {
            "genre": entry_genre,
            "education": education,
            "artists": artists
        }
```

#### 3.3 Fallback Strategy Manager

**Function**: Handle AI failures gracefully with fallback mechanisms

**Fallback Hierarchy**:
1. **Primary**: Groq LLM (Llama 3.1 70B)
2. **Secondary**: Groq LLM (Mixtral 8x7B)
3. **Tertiary**: Cached responses
4. **Quaternary**: Rule-based responses
5. **Last Resort**: Generic error message

**Implementation**:
```python
class FallbackManager:
    def __init__(self, primary_llm, secondary_llm, cache):
        self.primary = primary_llm
        self.secondary = secondary_llm
        self.cache = cache
        self.rule_engine = RuleEngine()
    
    async def execute_with_fallback(self, prompt: str, context: dict) -> str:
        # Try primary
        try:
            response = await self.primary.generate(prompt, context)
            if self._validate_response(response):
                return response
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}")
        
        # Try secondary
        try:
            response = await self.secondary.generate(prompt, context)
            if self._validate_response(response):
                return response
        except Exception as e:
            logger.warning(f"Secondary LLM failed: {e}")
        
        # Try cache
        cached = await self.cache.get_similar(prompt)
        if cached:
            logger.info("Using cached response")
            return cached
        
        # Try rule-based
        try:
            response = self.rule_engine.generate(prompt, context)
            if response:
                return response
        except Exception as e:
            logger.warning(f"Rule engine failed: {e}")
        
        # Last resort
        return "I'm having trouble processing your request right now. Please try again later."
```

#### 3.4 Response Validator

**Function**: Ensure AI responses meet quality standards

**Validation Criteria**:
- Response length (50-500 words)
- Contains recommendations when expected
- Explanations are present and coherent
- No harmful or inappropriate content
- Follows conversation guidelines
- Markdown formatting correct

**Implementation**:
```python
class ResponseValidator:
    def __init__(self, groq_client):
        self.groq = groq_client
    
    def validate(self, response: str, expected_type: str) -> ValidationResult:
        issues = []
        
        # Check length
        word_count = len(response.split())
        if word_count < 20:
            issues.append("Response too short")
        elif word_count > 500:
            issues.append("Response too long")
        
        # Check for recommendations if expected
        if expected_type in ["recommendation", "discovery"]:
            if not self._contains_recommendations(response):
                issues.append("Missing recommendations")
        
        # Check for explanations
        if not self._contains_explanations(response):
            issues.append("Missing explanations")
        
        # Check for inappropriate content
        if self._contains_inappropriate_content(response):
            issues.append("Inappropriate content detected")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            confidence=self._calculate_confidence(response, issues)
        )
    
    def _contains_inappropriate_content(self, response: str) -> bool:
        # Use Groq to check for inappropriate content
        prompt = f"""
        Check if this response contains any inappropriate, harmful, or offensive content:
        
        {response}
        
        Return "SAFE" or "UNSAFE" with a brief explanation.
        """
        
        result = self.groq.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        return "UNSAFE" in result.choices[0].message.content
```

#### 3.5 Performance Monitor

**Function**: Track AI performance, costs, and latency

**Metrics Tracked**:
- LLM request latency
- Token usage per request
- Cost per request
- Cache hit rate
- Error rates by component
- User satisfaction scores

**Implementation**:
```python
class PerformanceMonitor:
    def __init__(self, metrics_store):
        self.metrics = metrics_store
    
    def track_request(self, request_id: str, component: str, 
                     latency: float, tokens: int, cost: float):
        self.metrics.record({
            "request_id": request_id,
            "component": component,
            "timestamp": datetime.now(),
            "latency_ms": latency,
            "tokens_used": tokens,
            "cost_usd": cost
        })
    
    def get_metrics(self, component: str, time_range: timedelta) -> dict:
        return self.metrics.query({
            "component": component,
            "timestamp": {
                "$gte": datetime.now() - time_range
            }
        })
```

### Technology Stack
- **Orchestration**: LangChain for prompt chains
- **LLM**: Groq (Llama 3.1 70B primary, Mixtral 8x7B fallback)
- **Cache**: Redis for response caching
- **Metrics**: Prometheus + Grafana for monitoring
- **Queue**: Celery for async task processing

### Data Flow
```
User Request → Orchestration Controller → Prompt Chain → 
LLM Execution → Response Validation → Fallback (if needed) → 
Response → Performance Tracking
```

---

## Phase 4: Backend API

### Phase Independence
**Phase 4 operates as a completely independent microservice.**

**Independence Characteristics**:
- **Own Repository**: `phase4-backend-api/` with its own codebase
- **Own Dependencies**: `requirements.txt` or `pyproject.toml` specific to this phase
- **Own Configuration**: `config.yaml` for phase-specific settings
- **Own Database Schema**: Manages its own PostgreSQL tables for users, conversations, feedback
- **Own Cache**: Dedicated Redis instance or namespace for rate limiting and session data
- **API Interface**: Exposes REST API for Phase 5 (Frontend UI) to consume
- **Mock Layer**: Includes mock implementations for Phase 3 (AI Orchestration), Spotify OAuth, Redis, and PostgreSQL for isolated testing
- **Independent Deployment**: Can be deployed as a standalone Docker container

**Communication with Other Phases**:
- **Receives from**: Phase 5 (Frontend UI) via HTTP/REST API calls
- **Sends to**: Phase 3 (AI Orchestration) via REST API calls
- **External Dependencies**: 
  - Spotify OAuth API (external service)
  - Spotify Web API (external service, for user data)
- **Data Exchange**: JSON payloads via HTTP/REST

**Deployment Independence**:
- Can run without Phase 1, 2, 3, or 5 (uses mocks for Phase 3)
- Uses environment variables for configuration
- Health check endpoint: `GET /health`
- Metrics endpoint: `GET /metrics`
- Graceful shutdown handling
- Can operate in "mock mode" for testing without Phase 3

### Objectives
- Provide RESTful API endpoints for frontend communication
- Handle authentication and authorization
- Implement rate limiting and request throttling
- Coordinate backend services (orchestration, recommendations, etc.)
- Validate and sanitize all inputs
- Provide comprehensive error handling

### Inputs
- **HTTP Requests**: REST API calls from frontend
- **JWT Tokens**: Authentication tokens from clients
- **Request Bodies**: JSON payloads for POST/PUT requests
- **Query Parameters**: URL parameters for GET requests

### Outputs
- **HTTP Responses**: JSON responses with appropriate status codes
- **Error Messages**: Structured error responses
- **Rate Limit Headers**: X-RateLimit-* headers
- **CORS Headers**: Cross-origin resource sharing headers

### Folder Structure
```
phase4-backend-api/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py         # Chat/recommendation endpoints
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── user.py         # User profile endpoints
│   │   │   ├── spotify.py      # Spotify integration endpoints
│   │   │   └── feedback.py     # Feedback endpoints
│   │   ├── dependencies.py     # Dependency injection
│   │   └── middleware.py       # Custom middleware
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── security.py         # Security utilities
│   │   └── logging.py          # Logging configuration
│   ├── services/
│   │   ├── orchestration.py   # AI orchestration service
│   │   ├── recommendation.py   # Recommendation service
│   │   ├── conversation.py     # Conversation service
│   │   ├── spotify.py          # Spotify API service
│   │   └── review_insights.py # Review insights service
│   ├── models/
│   │   ├── user.py             # User models
│   │   ├── conversation.py     # Conversation models
│   │   ├── recommendation.py   # Recommendation models
│   │   └── feedback.py         # Feedback models
│   └── database/
│       ├── connection.py       # Database connection
│       ├── repositories.py     # Repository pattern
│       └── migrations/         # Database migrations
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── requirements.txt
├── Dockerfile
└── .env.example
```

### API Flow
```
Frontend UI → HTTP Request
    ↓
CORS Middleware
    ↓
Rate Limiting Middleware
    ↓
Authentication Middleware (JWT)
    ↓
Request Validation (Pydantic)
    ↓
Route Handler
    ↓
Service Layer
    ↓
Orchestration Layer
    ↓
Response Serialization
    ↓
HTTP Response
```

### Storage
**PostgreSQL**:
- User accounts and profiles
- Conversation history
- Recommendation feedback
- Spotify tokens (encrypted)

**Redis**:
- Rate limiting counters
- Session data
- Blacklisted tokens

**File System**:
- Log files (rotated daily)
- Temporary file uploads

### Execution Flow
```
1. Receive HTTP request from frontend
2. Apply CORS middleware
3. Check rate limits (per user/IP)
4. Validate JWT token (if required)
5. Validate request body with Pydantic
6. Route to appropriate handler
7. Handler calls service layer
8. Service layer calls orchestration
9. Process response from orchestration
10. Serialize response with Pydantic
11. Add rate limit headers
12. Return HTTP response
```

### Error Handling
**Authentication Errors**:
- Invalid token → 401 Unauthorized
- Expired token → 401 Unauthorized with refresh prompt
- Missing token → 401 Unauthorized

**Rate Limiting Errors**:
- Rate limit exceeded → 429 Too Many Requests
- Include Retry-After header

**Validation Errors**:
- Invalid input → 422 Unprocessable Entity
- Missing required fields → 400 Bad Request
- Invalid format → 400 Bad Request

**Service Errors**:
- Orchestration failure → 500 Internal Server Error
- Database error → 500 Internal Server Error
- External API error → 502 Bad Gateway

**Global Exception Handler**:
- Catch all unhandled exceptions
- Log error details
- Return 500 with generic message
- Include correlation ID for debugging

### Retry Mechanism
**Service Layer Retry**:
```python
class ServiceRetry:
    def __init__(self):
        self.max_retries = 2
        self.retryable_exceptions = [
            ConnectionError,
            TimeoutError,
            ServiceUnavailableError
        ]
    
    async def execute_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except tuple(self.retryable_exceptions) as e:
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
```

**Database Retry**:
- Connection pool handles retries automatically
- Configure max retry attempts in SQLAlchemy
- Implement circuit breaker for persistent failures

**External API Retry**:
- Spotify API: Exponential backoff, max 5 retries
- Groq API: Exponential backoff, max 3 retries
- Review API: Exponential backoff, max 3 retries

### Logging
**Request Logging**:
```python
logger.info(
    "api_request",
    extra={
        "method": request.method,
        "path": request.url.path,
        "user_id": user_id if authenticated else None,
        "status_code": response.status_code,
        "latency_ms": latency,
        "correlation_id": correlation_id
    }
)
```

**Error Logging**:
- Log all errors with stack traces
- Include request context (headers, body)
- Log rate limit violations
- Track authentication failures

**Security Logging**:
- Log authentication attempts
- Track failed logins
- Monitor suspicious activity
- Log token refresh events

### Testing Strategy
**Unit Tests**:
- Route handlers with mock services
- Pydantic model validation
- Middleware functionality
- Utility functions

**Integration Tests**:
- API endpoints with real services
- Database operations
- Authentication flow
- Rate limiting

**End-to-End Tests**:
- Complete user flows
- Error scenarios
- Performance under load
- Security testing

**Test Coverage Target**: 90%

**API Contract Testing**:
- OpenAPI schema validation
- Response schema validation
- Error response consistency
- Header validation

---

### Components

#### 4.1 API Framework

**Framework**: FastAPI with Python 3.11+

**Structure**:
```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py         # Chat/recommendation endpoints
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── user.py         # User profile endpoints
│   │   │   ├── spotify.py      # Spotify integration endpoints
│   │   │   └── feedback.py     # Feedback endpoints
│   │   ├── dependencies.py     # Dependency injection
│   │   └── middleware.py       # Custom middleware
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── security.py         # Security utilities
│   │   └── logging.py          # Logging configuration
│   ├── services/
│   │   ├── orchestration.py   # AI orchestration service
│   │   ├── recommendation.py   # Recommendation service
│   │   ├── conversation.py     # Conversation service
│   │   ├── spotify.py          # Spotify API service
│   │   └── review_insights.py # Review insights service
│   ├── models/
│   │   ├── user.py             # User models
│   │   ├── conversation.py     # Conversation models
│   │   ├── recommendation.py   # Recommendation models
│   │   └── feedback.py         # Feedback models
│   └── database/
│       ├── connection.py       # Database connection
│       ├── repositories.py     # Repository pattern
│       └── migrations/         # Database migrations
├── tests/
├── requirements.txt
└── Dockerfile
```

#### 4.2 API Endpoints

##### Authentication Endpoints

```python
# POST /api/v1/auth/spotify/login
# Initiate Spotify OAuth login
@router.post("/auth/spotify/login")
async def spotify_login():
    spotify_auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={settings.SPOTIFY_CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={settings.SPOTIFY_REDIRECT_URI}&"
        f"scope=user-read-recently-played user-top-read user-library-read"
    )
    return {"auth_url": spotify_auth_url}

# POST /api/v1/auth/spotify/callback
# Handle Spotify OAuth callback
@router.post("/auth/spotify/callback")
async def spotify_callback(code: str, db: Session = Depends(get_db)):
    # Exchange code for access token
    token_response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET
        }
    )
    
    token_data = token_response.json()
    
    # Get user profile from Spotify
    profile_response = requests.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"}
    )
    profile = profile_response.json()
    
    # Create or update user
    user = await get_or_create_user(db, profile, token_data)
    
    # Generate JWT
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
```

##### Chat/Recommendation Endpoints

```python
# POST /api/v1/chat/message
# Send a message and get recommendations
@router.post("/chat/message")
async def chat_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service)
):
    try:
        response = await orchestration_service.process_request(
            user_id=current_user.id,
            query=message.content
        )
        
        return ChatResponse(
            message=response.content,
            recommendations=response.recommendations,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

# GET /api/v1/chat/history
# Get conversation history
@router.get("/chat/history")
async def get_chat_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history = await get_conversation_history(db, current_user.id, limit)
    return {"history": history}

# POST /api/v1/chat/feedback
# Provide feedback on recommendations
@router.post("/chat/feedback")
async def submit_feedback(
    feedback: RecommendationFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    await save_feedback(db, current_user.id, feedback)
    return {"status": "success"}
```

##### User Profile Endpoints

```python
# GET /api/v1/user/profile
# Get user profile
@router.get("/user/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "spotify_id": current_user.spotify_id,
        "display_name": current_user.display_name,
        "preferences": current_user.preferences,
        "created_at": current_user.created_at
    }

# PUT /api/v1/user/preferences
# Update user preferences
@router.put("/user/preferences")
async def update_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    await update_user_preferences(db, current_user.id, preferences)
    return {"status": "success"}

# GET /api/v1/user/listening-patterns
# Get listening pattern analysis
@router.get("/user/listening-patterns")
async def get_listening_patterns(
    current_user: User = Depends(get_current_user),
    spotify_service: SpotifyService = Depends(get_spotify_service)
):
    patterns = await spotify_service.analyze_patterns(current_user.id)
    return patterns
```

##### Spotify Integration Endpoints

```python
# GET /api/v1/spotify/recently-played
# Get recently played tracks
@router.get("/spotify/recently-played")
async def get_recently_played(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    spotify_service: SpotifyService = Depends(get_spotify_service)
):
    tracks = await spotify_service.get_recently_played(
        current_user.spotify_id, 
        limit
    )
    return {"tracks": tracks}

# GET /api/v1/spotify/top-artists
# Get user's top artists
@router.get("/spotify/top-artists")
async def get_top_artists(
    time_range: str = "medium_term",
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    spotify_service: SpotifyService = Depends(get_spotify_service)
):
    artists = await spotify_service.get_top_artists(
        current_user.spotify_id,
        time_range,
        limit
    )
    return {"artists": artists}
```

#### 4.3 Authentication & Authorization

**JWT-based Authentication**:
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = verify_token(token)
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

#### 4.4 Rate Limiting

**Implementation using slowapi**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/chat/message")
@limiter.limit("10/minute")
async def chat_message(
    request: Request,
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    # ... endpoint logic
```

#### 4.5 Error Handling

**Global exception handler**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

#### 4.6 Database Models

**SQLAlchemy models**:
```python
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    spotify_id = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    email = Column(String)
    preferences = Column(JSON)
    spotify_access_token = Column(String)
    spotify_refresh_token = Column(String)
    token_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="user")
    feedback = relationship("RecommendationFeedback", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    session_id = Column(String)
    message = Column(String, nullable=False)
    intent = Column(String)
    response = Column(String)
    recommendations = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="conversations")

class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    recommendation_id = Column(String)
    artist_id = Column(String)
    track_id = Column(String)
    rating = Column(Integer)  # 1-5
    liked = Column(Boolean)
    feedback_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="feedback")
```

#### 4.7 Service Layer

**Orchestration Service**:
```python
class OrchestrationService:
    def __init__(
        self,
        conversation_engine: ConversationEngine,
        recommendation_engine: RecommendationEngine,
        context_manager: ContextManager
    ):
        self.conversation = conversation_engine
        self.recommendation = recommendation_engine
        self.context = context_manager
    
    async def process_request(self, user_id: str, query: str) -> ChatResponse:
        # Get context
        context = await self.context.get_context(user_id)
        
        # Recognize intent
        intent = await self.conversation.recognize_intent(query)
        
        # Parse query
        parsed_query = await self.conversation.parse_query(query, intent)
        
        # Get recommendations
        recommendations = await self.recommendation.recommend(
            parsed_query, context
        )
        
        # Generate response
        response = await self.conversation.generate_response(
            query, intent, recommendations, context
        )
        
        # Update context
        await self.context.update_context(user_id, {
            "last_query": query,
            "last_intent": intent,
            "last_recommendations": recommendations
        })
        
        return ChatResponse(
            content=response,
            recommendations=recommendations,
            intent=intent
        )
```

### Technology Stack
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy
- **Cache**: Redis
- **Authentication**: JWT + OAuth 2.0 (Spotify)
- **Rate Limiting**: slowapi
- **Validation**: Pydantic
- **Async**: asyncio + httpx
- **Testing**: pytest + pytest-asyncio

### API Security
- HTTPS only
- JWT authentication
- Rate limiting per user
- Input validation with Pydantic
- SQL injection prevention (ORM)
- XSS protection
- CORS configuration
- API key for Groq (environment variable)

---

## Phase 5: Frontend UI

### Phase Independence
**Phase 5 operates as a completely independent web application.**

**Independence Characteristics**:
- **Own Repository**: `phase5-frontend-ui/` with its own codebase
- **Own Dependencies**: `package.json` with its own npm dependencies
- **Own Configuration**: `.env` and `vite.config.ts` for phase-specific settings
- **Own State Management**: Zustand stores for local state (no shared state with other phases)
- **Own Storage**: LocalStorage and SessionStorage for client-side data
- **API Client**: Axios with interceptors for communicating with Phase 4
- **Mock Layer**: Includes mock API responses for isolated testing without Phase 4
- **Independent Deployment**: Can be deployed as a standalone static site or SPA

**Communication with Other Phases**:
- **Receives from**: Phase 4 (Backend API) via HTTP/REST API calls
- **Sends to**: Phase 4 (Backend API) via HTTP/REST API calls
- **External Dependencies**: 
  - Spotify OAuth (redirects to Spotify, then back to Phase 4)
- **Data Exchange**: JSON payloads via HTTP/REST

**Deployment Independence**:
- Can run without Phase 1, 2, 3, or 4 (uses mock API responses)
- Uses environment variables for API endpoint configuration
- Can be deployed to any static hosting (Vercel, Netlify, S3, etc.)
- Can be served as a Docker container with nginx
- Can operate in "mock mode" for testing without backend

**Development Independence**:
- Can be developed completely independently of backend phases
- Uses TypeScript for type safety
- Hot module replacement for rapid development
- Independent build process with Vite

### Objectives
- Provide intuitive, modern web interface for music discovery
- **Replicate Spotify's exact design language and UI patterns**
- Enable real-time chat interactions with AI
- Display recommendations with rich media and explanations
- Handle Spotify authentication seamlessly
- Support responsive design for all devices
- Provide smooth user experience with loading states

### Design Philosophy
**Spotify Clone Design**:
- **Exact visual replication** of Spotify's web player interface
- Use Spotify's color palette: Black (#191414), Dark Gray (#121212), Green (#1DB954), White (#FFFFFF)
- Match Spotify's typography, spacing, and component styling
- Replicate Spotify's layout structure (sidebar, main content, player bar)
- Use Spotify's icon style and animations
- Match Spotify's hover states and transitions
- Implement Spotify's dark mode as the default (and only) theme
- Use Spotify's card designs for artists, albums, and recommendations
- Replicate Spotify's chat/conversation interface patterns

### Inputs
- **User Interactions**: Clicks, form submissions, keyboard input
- **API Responses**: JSON data from backend API
- **User Events**: Scroll, resize, focus events
- **Browser Events**: Online/offline status, visibility changes

### Outputs
- **HTTP Requests**: API calls to backend
- **User Actions**: Feedback submissions, preference updates
- **Analytics Events**: User behavior tracking
- **Error Reports**: Frontend error logging

### Folder Structure
```
phase5-frontend-ui/
├── src/
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── TypingIndicator.tsx
│   │   ├── recommendations/
│   │   │   ├── RecommendationCard.tsx
│   │   │   ├── RecommendationList.tsx
│   │   │   ├── ArtistCard.tsx
│   │   │   └── SpotifyPlayer.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── SpotifyLoginButton.tsx
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── MainLayout.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── ProfilePage.tsx
│   │   └── HistoryPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useChat.ts
│   │   ├── useRecommendations.ts
│   │   └── useSpotify.ts
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── chatStore.ts
│   │   └── uiStore.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── authService.ts
│   │   └── chatService.ts
│   ├── types/
│   │   ├── chat.ts
│   │   ├── recommendation.ts
│   │   └── user.ts
│   ├── utils/
│   │   ├── formatting.ts
│   │   └── validation.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── .env.example
```

### API Flow
```
User Interaction → Component Event Handler
    ↓
State Update (Zustand)
    ↓
Service Layer (if API call needed)
    ↓
HTTP Request (Axios)
    ↓
Backend API
    ↓
Response Processing
    ↓
State Update
    ↓
Component Re-render
```

### Storage
**LocalStorage**:
- Auth token (persisted)
- User preferences
- Theme preference (dark/light)
- Sidebar state

**SessionStorage**:
- Temporary chat state
- Form data
- Navigation history

**Memory (Zustand)**:
- Current chat messages
- Loading states
- Error states
- UI state

### Execution Flow
```
1. User interacts with component (click, type, etc.)
2. Component event handler captures interaction
3. Handler updates local state or calls service
4. If service call:
   a. Service makes HTTP request via Axios
   b. Axios interceptors add auth token
   c. Request sent to backend API
   d. Response received and processed
   e. Error handling (401 redirect, etc.)
5. Service updates Zustand store
6. Components subscribed to store re-render
7. UI updates with new data
8. Loading states shown during async operations
9. Error states shown on failures
```

### Error Handling
**API Errors**:
- 401 Unauthorized → Redirect to login, clear token
- 403 Forbidden → Show permission error
- 404 Not Found → Show resource not found
- 429 Rate Limited → Show rate limit message
- 500 Server Error → Show generic error, offer retry
- Network Error → Show offline message

**Component Errors**:
- Error boundaries catch component errors
- Show fallback UI on component failure
- Log errors to error tracking service
- Attempt recovery where possible

**State Errors**:
- Invalid state → Reset to default
- Missing data → Show loading state
- Corrupted data → Clear and refetch

### Retry Mechanism
**API Retry**:
```typescript
const retryRequest = async (
  fn: () => Promise<any>,
  maxRetries = 3
) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => 
        setTimeout(resolve, 1000 * (i + 1))
      );
    }
  }
};
```

**Component Retry**:
- Failed data fetch → Show retry button
- Failed image load → Show placeholder
- Failed WebSocket → Attempt reconnection

**Optimistic UI**:
- Update UI immediately on user action
- Revert on failure
- Show error message if revert needed

### Logging
**Error Logging**:
```typescript
const logError = (error: Error, context: any) => {
  console.error('[Frontend Error]', {
    message: error.message,
    stack: error.stack,
    context,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent
  });
  
  // Send to error tracking service
  errorTrackingService.capture(error, context);
};
```

**User Analytics**:
- Track page views
- Track feature usage
- Track recommendation interactions
- Track session duration

**Performance Logging**:
- Track page load times
- Track API response times
- Track render times
- Track memory usage

### Testing Strategy
**Unit Tests**:
- Component rendering
- Hook behavior
- Utility functions
- Service layer

**Integration Tests**:
- Component interactions
- State management
- API integration
- Routing

**E2E Tests**:
- Complete user flows
- Authentication flow
- Chat interaction
- Recommendation feedback

**Visual Regression Tests**:
- Screenshot comparisons
- Responsive design testing
- Theme testing

**Test Coverage Target**: 80%

**Testing Tools**:
- Vitest for unit tests
- React Testing Library for component tests
- Playwright for E2E tests
- Percy for visual regression

---

### Components

#### 5.1 Technology Stack

**Framework**: React 18 with TypeScript
**Styling**: TailwindCSS with custom Spotify theme
**UI Components**: Custom components matching Spotify's design system
**Icons**: Lucide React (styled to match Spotify icons)
**State Management**: Zustand
**HTTP Client**: Axios
**Routing**: React Router v6

**Spotify Design System Implementation**:
- Custom Tailwind config with Spotify color palette
- CSS variables for Spotify design tokens
- Custom component library replicating Spotify's UI components
- Spotify-style animations and transitions
- Spotify typography (Circular font family)

#### 5.2 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── TypingIndicator.tsx
│   │   ├── recommendations/
│   │   │   ├── RecommendationCard.tsx
│   │   │   ├── RecommendationList.tsx
│   │   │   ├── ArtistCard.tsx
│   │   │   └── SpotifyPlayer.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── SpotifyLoginButton.tsx
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── MainLayout.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── ProfilePage.tsx
│   │   └── HistoryPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useChat.ts
│   │   ├── useRecommendations.ts
│   │   └── useSpotify.ts
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── chatStore.ts
│   │   └── uiStore.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── authService.ts
│   │   └── chatService.ts
│   ├── types/
│   │   ├── chat.ts
│   │   ├── recommendation.ts
│   │   └── user.ts
│   ├── utils/
│   │   ├── formatting.ts
│   │   └── validation.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
├── tailwind.config.js
├── vite.config.ts
└── tsconfig.json
```

#### 5.3 Core Components

##### Chat Interface

```typescript
// src/components/chat/ChatInterface.tsx
import { useState } from 'react';
import { useChatStore } from '@/store/chatStore';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';

export function ChatInterface() {
  const [isTyping, setIsTyping] = useState(false);
  const { messages, sendMessage } = useChatStore();

  const handleSendMessage = async (content: string) => {
    setIsTyping(true);
    await sendMessage(content);
    setIsTyping(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList messages={messages} />
      </div>
      {isTyping && <TypingIndicator />}
      <div className="p-4 border-t">
        <MessageInput onSend={handleSendMessage} disabled={isTyping} />
      </div>
    </div>
  );
}
```

##### Message Component

```typescript
// src/components/chat/MessageList.tsx
import { Message } from '@/types/chat';
import { RecommendationCard } from '../recommendations/RecommendationCard';

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          <div
            className={`max-w-2xl rounded-lg p-4 ${
              message.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}
          >
            <p className="whitespace-pre-wrap">{message.content}</p>
            {message.recommendations && (
              <div className="mt-4 space-y-2">
                {message.recommendations.map((rec) => (
                  <RecommendationCard key={rec.id} recommendation={rec} />
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
```

##### Recommendation Card

```typescript
// src/components/recommendations/RecommendationCard.tsx
import { Recommendation } from '@/types/recommendation';
import { Play, Heart, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const { artist, track, explanation, spotifyUrl } = recommendation;

  return (
    <div className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <img
          src={artist.imageUrl}
          alt={artist.name}
          className="w-16 h-16 rounded object-cover"
        />
        <div className="flex-1">
          <h4 className="font-semibold text-lg">{track.name}</h4>
          <p className="text-gray-600">{artist.name}</p>
          <p className="text-sm text-gray-500 mt-2">{explanation}</p>
        </div>
        <div className="flex gap-2">
          <Button
            size="icon"
            variant="ghost"
            onClick={() => window.open(spotifyUrl, '_blank')}
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost">
            <Heart className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
```

##### Spotify Login Button

```typescript
// src/components/auth/SpotifyLoginButton.tsx
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/store/authStore';

export function SpotifyLoginButton() {
  const { loginWithSpotify } = useAuthStore();

  return (
    <Button
      onClick={loginWithSpotify}
      className="bg-green-500 hover:bg-green-600"
    >
      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
      </svg>
      Continue with Spotify
    </Button>
  );
}
```

#### 5.4 State Management (Zustand)

```typescript
// src/store/chatStore.ts
import { create } from 'zustand';
import { Message } from '@/types/chat';
import { chatService } from '@/services/chatService';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  error: null,

  sendMessage: async (content: string) => {
    set({ isLoading: true, error: null });
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    set((state) => ({ messages: [...state.messages, userMessage] }));

    try {
      const response = await chatService.sendMessage(content);
      
      // Add AI response
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        recommendations: response.recommendations,
        timestamp: new Date(),
      };
      set((state) => ({ messages: [...state.messages, aiMessage] }));
    } catch (error) {
      set({ error: 'Failed to send message' });
    } finally {
      set({ isLoading: false });
    }
  },

  clearMessages: () => set({ messages: [] }),
}));
```

```typescript
// src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authService } from '@/services/authService';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loginWithSpotify: () => void;
  logout: () => void;
  setUser: (user: User, token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      loginWithSpotify: () => {
        window.location.href = authService.getSpotifyAuthUrl();
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
        authService.logout();
      },

      setUser: (user, token) => {
        set({ user, token, isAuthenticated: true });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

#### 5.5 API Service

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

```typescript
// src/services/chatService.ts
import api from './api';
import { ChatMessage, ChatResponse } from '@/types/chat';

export const chatService = {
  sendMessage: async (content: string): Promise<ChatResponse> => {
    const response = await api.post('/chat/message', { content });
    return response.data;
  },

  getHistory: async (limit: number = 20) => {
    const response = await api.get(`/chat/history?limit=${limit}`);
    return response.data;
  },

  submitFeedback: async (feedback: RecommendationFeedback) => {
    const response = await api.post('/chat/feedback', feedback);
    return response.data;
  },
};
```

#### 5.6 Pages

##### Chat Page

```typescript
// src/pages/ChatPage.tsx
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';

export function ChatPage() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <ChatInterface />
      </div>
    </div>
  );
}
```

##### Home Page

```typescript
// src/pages/HomePage.tsx
import { SpotifyLoginButton } from '@/components/auth/SpotifyLoginButton';
import { useAuthStore } from '@/store/authStore';

export function HomePage() {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-blue-600">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-center mb-2">
          AI Music Discovery
        </h1>
        <p className="text-gray-600 text-center mb-8">
          Discover your next favorite artist with AI-powered recommendations
        </p>
        <SpotifyLoginButton />
      </div>
    </div>
  );
}
```

#### 5.7 Styling (TailwindCSS - Spotify Theme)

**Spotify Theme Configuration**:
```javascript
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        spotify: {
          green: '#1DB954',
          black: '#191414',
          dark: '#121212',
          light: '#FFFFFF',
          gray: {
            100: '#FFFFFF',
            200: '#E9E9E9',
            300: '#D3D3D3',
            400: '#B3B3B3',
            500: '#727272',
            600: '#535353',
            700: '#404040',
            800: '#282828',
            900: '#181818',
            950: '#000000',
          }
        },
      },
      fontFamily: {
        circular: ['Circular', 'Helvetica', 'Arial', 'sans-serif'],
      },
      borderRadius: {
        'spotify': '8px',
        'spotify-lg': '12px',
        'spotify-xl': '16px',
      },
      boxShadow: {
        'spotify': '0 4px 12px rgba(0, 0, 0, 0.3)',
        'spotify-lg': '0 8px 24px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

**Spotify Design Tokens (CSS Variables)**:
```css
:root {
  --spotify-green: #1DB954;
  --spotify-black: #191414;
  --spotify-dark: #121212;
  --spotify-light: #FFFFFF;
  --spotify-gray-100: #FFFFFF;
  --spotify-gray-200: #E9E9E9;
  --spotify-gray-300: #D3D3D3;
  --spotify-gray-400: #B3B3B3;
  --spotify-gray-500: #727272;
  --spotify-gray-600: #535353;
  --spotify-gray-700: #404040;
  --spotify-gray-800: #282828;
  --spotify-gray-900: #181818;
  --spotify-gray-950: #000000;
  
  --spotify-radius: 8px;
  --spotify-radius-lg: 12px;
  --spotify-radius-xl: 16px;
  
  --spotify-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  --spotify-shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.4);
  
  --spotify-transition: all 0.2s ease;
  --spotify-transition-fast: all 0.1s ease;
}
```

**Layout Structure (Spotify Clone)**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Sidebar (240px) │    Main Content (flex-1)                   │
│  ┌───────────────┐ │  ┌─────────────────────────────────────┐ │
│  │ Logo          │ │  │ Header (64px)                        │ │
│  │ Navigation    │ │  │ - Search bar                         │ │
│  │ - Home        │ │  │ - User profile                       │ │
│  │ - Search      │ │  └─────────────────────────────────────┘ │
│  │ - Library     │ │                                           │
│  │               │ │  ┌─────────────────────────────────────┐ │
│  │ Playlist      │ │  │ Chat Interface                      │ │
│  │ - Liked Songs │ │  │ - Message list (scrollable)         │ │
│  │ - Create      │ │  │ - Recommendation cards              │ │
│  │               │ │  │ - Typing indicator                 │ │
│  │               │ │  └─────────────────────────────────────┘ │
│  │               │ │                                           │
│  │               │ │  ┌─────────────────────────────────────┐ │
│  │               │ │  │ Message Input (fixed bottom)         │ │
│  │               │ │  └─────────────────────────────────────┘ │
│  └───────────────┘ │                                           │
└───────────────────┴───────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  Player Bar (90px) - Fixed at bottom                            │
│  ┌──────────────┬──────────────────────────────────────────────┐│
│  │ Now Playing │ Playback Controls (center)                   ││
│  │ - Artist     │ - Play/Pause, Next, Previous               ││
│  │ - Track      │ - Progress bar                             ││
│  │ - Album Art  │ - Volume control                           ││
│  └──────────────┴──────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### 5.8 Features

**Key UI Features (Spotify Clone)**:
1. **Real-time Chat**: Streaming responses with typing indicators (Spotify-style chat interface)
2. **Rich Recommendations**: Cards with album art, artist info, and explanations (Spotify card design)
3. **Spotify Integration**: Direct links to open in Spotify
4. **Feedback System**: Like/dislike recommendations (Spotify heart icon style)
5. **Conversation History**: View past conversations (Spotify library style)
6. **User Profile**: Manage preferences and view listening patterns (Spotify profile page)
7. **Responsive Design**: Mobile-friendly interface (Spotify mobile app patterns)
8. **Dark Mode Only**: Spotify's signature dark theme (no light mode toggle)

**Spotify-Specific UI Elements**:
- **Sidebar**: Navigation with Home, Search, Library (exact Spotify layout)
- **Player Bar**: Fixed bottom player with playback controls (Spotify player design)
- **Card Hover Effects**: Green play button overlay on hover (Spotify card behavior)
- **Typography**: Circular font family matching Spotify
- **Icons**: Custom-styled icons matching Spotify's icon set
- **Animations**: Smooth transitions matching Spotify's animation timing
- **Scrollbars**: Custom dark scrollbars matching Spotify
- **Hover States**: Green accent on hover (Spotify's signature green)
- **Gradient Overlays**: Subtle gradients on cards (Spotify visual style)
- **Responsive Grid**: Adaptive grid layouts for recommendations (Spotify grid system)

**User Experience (Spotify-Native)**:
- Exact Spotify visual language and interaction patterns
- Smooth animations matching Spotify's timing (0.2s transitions)
- Quick suggestions for common queries (Spotify search style)
- Progressive disclosure of information (Spotify expand/collapse patterns)
- Keyboard shortcuts matching Spotify's shortcuts
- Drag-and-drop functionality (Spotify playlist management style)
- Context menus on right-click (Spotify context menu design)

### Technology Stack Summary
- **Framework**: React 18 + TypeScript
- **Styling**: TailwindCSS
- **Components**: shadcn/ui
- **Icons**: Lucide React
- **State**: Zustand
- **HTTP**: Axios
- **Routing**: React Router v6
- **Build**: Vite

---

## Integration Points

### Review Discovery Engine Integration

The system consumes insights from the AI-Powered Review Discovery Engine through:

1. **Database Access**: Direct PostgreSQL connection to review_insights table
2. **API Integration**: REST endpoint for real-time review queries
3. **Data Synchronization**: Periodic sync of review data

**Integration Schema**:
```python
class ReviewInsightsService:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_highly_rated_artists(self, genre: str, limit: int = 10):
        query = """
        SELECT artist_id, artist_name, review_sentiment, 
               unique_descriptors, discovery_score
        FROM review_insights
        WHERE genre_tags @> %s
        ORDER BY discovery_score DESC, review_sentiment DESC
        LIMIT %s
        """
        return self.db.execute(query, [genre, limit])
    
    def get_artist_review_summary(self, artist_id: str):
        query = """
        SELECT artist_name, review_sentiment, review_count,
               unique_descriptors, common_themes
        FROM review_insights
        WHERE artist_id = %s
        """
        return self.db.execute(query, [artist_id]).fetchone()
```

### Spotify API Integration

**Scopes Required**:
- `user-read-recently-played`: Analyze listening patterns
- `user-top-read`: Get user's top artists/tracks
- `user-library-read`: Access saved tracks
- `user-modify-playback-state`: Play recommendations (optional)

**Rate Limiting**:
- Implement exponential backoff
- Cache responses where possible
- Respect Spotify's rate limits

### Groq LLM Integration

**API Usage**:
```python
from groq import Groq

client = Groq(api_key=settings.GROQ_API_KEY)

response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[
        {"role": "system", "content": "You are a music discovery assistant."},
        {"role": "user", "content": user_query}
    ],
    temperature=0.7,
    max_tokens=500
)
```

**Models Used**:
- **Primary**: Llama 3.1 70B Versatile (for complex reasoning)
- **Secondary**: Mixtral 8x7B (for faster, simpler tasks)
- **Fallback**: Llama 3.1 8B (for cost optimization)

---

## Data Flow Summary

### End-to-End Request Flow

```
1. User sends message via Frontend UI
   ↓
2. Frontend sends POST /api/v1/chat/message with JWT auth
   ↓
3. Backend API validates token and rate limits
   ↓
4. Orchestration Controller receives request
   ↓
5. Context Manager retrieves user context
   ↓
6. Conversation Engine:
   - Recognizes intent (Groq LLM)
   - Parses query parameters (Groq LLM)
   ↓
7. Recommendation Engine:
   - Selects strategies based on intent
   - Executes parallel recommendation strategies
   - Fuses results from multiple strategies
   - Generates explanations (Groq LLM)
   ↓
8. Response Generator crafts natural response (Groq LLM)
   ↓
9. Response Validator checks quality
   ↓
10. Response returned to Frontend
    ↓
11. Frontend displays message with recommendations
```

### Data Storage Flow

```
User Interaction → Conversation History (PostgreSQL)
                → User Context (Redis + PostgreSQL)
                → Feedback (PostgreSQL)
                → Performance Metrics (Prometheus)

Spotify Data → Listening Patterns (PostgreSQL)
             → User Profile (PostgreSQL)

Review Insights → Review Database (PostgreSQL)
                → Cached in Redis
```

---

## Security Considerations

### API Security
- HTTPS only for all endpoints
- JWT authentication with short expiry
- Rate limiting per user and per IP
- Input validation on all endpoints
- SQL injection prevention via ORM
- XSS protection in frontend

### Data Privacy
- Encrypt Spotify tokens at rest
- Minimal data collection
- User data deletion on request
- GDPR compliance
- No sharing of user data with third parties

### Groq API Security
- API key stored in environment variables
- Never expose API key in frontend
- Monitor API usage for anomalies
- Implement cost limits

---

## Performance Optimization

### Caching Strategy
1. **Response Cache**: Cache AI responses for identical queries (TTL: 1 hour)
2. **Context Cache**: Redis for session context (TTL: 30 minutes)
3. **Spotify Cache**: Cache artist/track data (TTL: 24 hours)
4. **Review Cache**: Cache review insights (TTL: 6 hours)

### Database Optimization
- Index on user_id, artist_id, genre_tags
- Connection pooling
- Query optimization
- Read replicas for scaling

### AI Optimization
- Batch processing for recommendations
- Smaller models for simple tasks
- Prompt caching for repeated patterns
- Async processing for non-critical operations

---

## Monitoring & Observability

### Metrics to Track
- API response times
- LLM latency and token usage
- Cache hit rates
- User engagement (messages per session)
- Recommendation acceptance rate
- Error rates by component
- Spotify API quota usage

### Logging Strategy
- Structured logging with JSON
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracing
- Sensitive data redaction

### Alerts
- High error rate (>5%)
- Slow response times (>2s p95)
- LLM API failures
- Spotify API rate limits
- Database connection issues

---

## Deployment Considerations

### Infrastructure Requirements
- **Backend**: 2-4 CPU, 8-16 GB RAM per instance
- **Database**: PostgreSQL with sufficient storage
- **Cache**: Redis with persistence
- **Frontend**: Static hosting (CDN)

### Scalability
- Horizontal scaling for API servers
- Database read replicas
- Redis clustering
- CDN for frontend assets

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379

# Spotify
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:3000/callback

# Groq
GROQ_API_KEY=your_groq_api_key

# Security
SECRET_KEY=your_jwt_secret
ALLOWED_ORIGINS=http://localhost:3000

# Production
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## Phase 6: Automated Scheduler

### Overview

Phase 6 is an automated scheduler that executes the complete music discovery workflow on a weekly basis. It runs every Monday at 10:00 AM IST to ensure the system stays up-to-date with the latest reviews, insights, and recommendations.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 6: Scheduler                           │
│                   (APScheduler + AsyncIO)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Weekly Schedule (Monday 10:00 AM IST)
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Review        │   │ Insight      │   │ Frontend      │
│ Downloader    │   │ Generator    │   │ Updater       │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Workflow     │
                    │ Executor    │
                    └───────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Phase 1      │   │ Phase 2      │   │ Phase 3      │
│ Sync          │   │ Sync          │   │ Sync          │
└───────────────┘   └───────────────┘   └───────────────┘
```

### Components

#### 1. Scheduler (`scheduler.py`)
- **Technology**: APScheduler with AsyncIO
- **Schedule**: Every Monday at 10:00 AM IST
- **Timezone**: Asia/Kolkata
- **Job Store**: Memory (configurable to SQLAlchemy)
- **Executor**: AsyncIO with max 4 workers

**Features**:
- Automatic weekly execution
- Manual workflow trigger for testing
- Graceful shutdown
- Misfire handling (1 hour grace time)
- Job coalescing to prevent duplicate runs

#### 2. Workflow Executor (`workflow_executor.py`)
- Coordinates all phases of the music discovery system
- Executes phase sync operations in parallel
- Aggregates results from all phases
- Handles individual phase failures gracefully

**Workflow Steps**:
1. Sync Phase 1: AI Conversation Engine
2. Sync Phase 2: Music Recommendation Engine
3. Sync Phase 3: AI Orchestration
4. Sync Phase 4: Backend API

#### 3. Review Downloader (`review_downloader.py`)
- Downloads latest reviews from multiple music review sources
- Supports parallel downloads from multiple sources
- Configurable review limits per source

**Review Sources**:
- Pitchfork
- Rolling Stone
- NME
- AllMusic

**Features**:
- Async HTTP requests
- Timeout handling
- Error recovery
- Statistics tracking

#### 4. Insight Generator (`insight_generator.py`)
- Generates AI-powered insights from downloaded reviews
- Uses Groq API for natural language analysis
- Supports multiple insight types

**Insight Types**:
- Pain Points
- Theme Clusters
- User Segments
- Product Insights
- Executive Summary

**Features**:
- Parallel insight generation
- Configurable insight types
- Error handling per type
- Statistics tracking

#### 5. Frontend Updater (`frontend_updater.py`)
- Updates frontend with latest data
- Clears frontend cache
- Updates multiple frontend components

**Update Targets**:
- Insights Page
- Recommendations Page
- History Page
- Frontend Cache

**Features**:
- Async API calls
- Timeout handling
- Component-level updates
- Cache invalidation

#### 6. Scheduler Logger (`scheduler_logger.py`)
- Logs all scheduler executions
- Stores detailed execution history
- JSON-formatted logs for easy parsing

**Log Events**:
- Workflow Start
- Workflow Completion
- Workflow Failure
- Step Completion

**Features**:
- File-based logging
- JSON format
- Queryable history
- Error tracking

### Weekly Workflow Execution

```
┌─────────────────────────────────────────────────────────────────┐
│                    Weekly Workflow Start                         │
│                    (Monday 10:00 AM IST)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Log Workflow  │
                    │ Start         │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Download      │   │ Generate     │   │ Update        │
│ Latest        │   │ Insights     │   │ Frontend      │
│ Reviews       │   │              │   │               │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Execute       │
                    │ Complete     │
                    │ Workflow     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Log Workflow  │
                    │ Completion    │
                    └───────────────┘
```

### Configuration

**Scheduler Settings** (`config.yaml`):
```yaml
scheduler:
  enabled: true
  timezone: "Asia/Kolkata"
  day_of_week: "mon"
  hour: 10
  minute: 0

review_sources:
  - pitchfork
  - rolling_stone
  - nme
  - allmusic

insight_generation:
  insight_types:
    - pain_points
    - theme_clusters
    - user_segments
    - product_insights
    - executive_summary
```

### Execution Modes

#### Production Mode
```bash
python main.py
```
- Runs continuously
- Executes on schedule
- Logs to file
- Uses real APIs

#### Manual Execution
```bash
python main.py manual
```
- Executes workflow once
- For testing or on-demand runs
- Same logic as scheduled execution

#### Mock Mode
```bash
USE_MOCKS=true python main.py
```
- Uses mock implementations
- No external API calls
- For development and testing

### Logging

**Log Location**: `./logs/scheduler/scheduler.log`

**Log Format**: JSON

**Log Entry Structure**:
```json
{
  "event": "workflow_start",
  "job_id": "workflow_20240115_100000",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

**Query History**:
```python
from scheduler_logger import SchedulerLogger

logger = SchedulerLogger(config)
history = await logger.get_workflow_history(limit=10)
```

### Error Handling

**Individual Step Failures**:
- Logged but don't stop workflow
- Other steps continue execution
- Final status includes all step results

**Workflow Failures**:
- Logged with error details
- Can be retried manually
- Graceful degradation

**Misfire Handling**:
- 1 hour grace time for delayed executions
- Coalescing prevents duplicate runs
- Automatic recovery

### Performance

**Execution Time**:
- Mock Mode: ~5-10 seconds
- Production Mode: ~2-5 minutes (depends on API calls)

**Parallel Execution**:
- Review downloads: Parallel across sources
- Insight generation: Parallel across types
- Frontend updates: Parallel across components
- Phase syncs: Parallel across phases

**Resource Usage**:
- Minimal CPU during idle time
- Burst usage during execution
- Memory: ~100-200 MB

### Monitoring

**Status Check**:
```python
scheduler.get_job_status()
```

**Next Run Time**:
```python
scheduler.get_next_run_time()
```

**Log Monitoring**:
- Console output for real-time status
- File logs for detailed history
- JSON format for easy parsing

### Phase Independence

Phase 6 is completely independent:
- **Separate Codebase**: Own directory structure
- **Independent Deployment**: Can run as standalone service
- **Own Configuration**: Separate config.yaml
- **Own Dependencies**: Separate requirements.txt
- **Mock Implementations**: All components have mocks
- **Isolated Testing**: Can test without other phases
- **Clear Interfaces**: Well-defined component APIs

**Dependencies on Other Phases**:
- Optional: Can run without other phases
- Graceful degradation: Works if phases are unavailable
- No direct code dependencies: Uses HTTP APIs
- Can be deployed independently

---

## Future Enhancements

### Phase 7: Deployment
- Docker containerization
- Kubernetes orchestration
- CI/CD pipeline
- Multi-region deployment
- Load balancing

### Phase 8: Advanced Features
- Voice input/output
- Collaborative playlists
- Social features
- Mobile apps (iOS/Android)
- Offline mode
- Advanced analytics dashboard

### Phase 9: AI Improvements
- Fine-tuned models for music domain
- Multi-modal AI (album art analysis)
- Personalized model per user
- Real-time mood detection from music
- Predictive recommendations

---

## Conclusion

This architecture provides a comprehensive foundation for an AI-Native Music Discovery Companion that:

1. **Understands natural language** through Groq LLM-powered conversation engine
2. **Generates intelligent recommendations** using multiple strategies including review-based discovery
3. **Explains every recommendation** with clear, contextual reasoning
4. **Breaks listening habits** through pattern analysis and novelty scoring
5. **Integrates seamlessly** with Spotify and the Review Discovery Engine
6. **Scales efficiently** through caching, async processing, and modern infrastructure

The modular design allows for independent development and testing of each phase, with clear interfaces between components. The use of Groq LLM throughout ensures consistent AI behavior while leveraging state-of-the-art language models for natural language understanding and generation.
