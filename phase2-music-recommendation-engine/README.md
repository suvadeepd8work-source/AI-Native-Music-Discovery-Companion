# Phase 2: Music Recommendation Engine

## Overview

Phase 2 is a completely independent microservice that generates music recommendations using multiple strategies. It receives conversation context, user intent, and conversation memory from Phase 1, and returns ranked recommendations with explanations.

## Features

- **Multi-Strategy Recommendation System**:
  - Review-Based Artist Discovery
  - Mood-Activity Matching
  - Similarity Search
  - Habit Breaking
  - Genre Exploration

- **Integration with External Services**:
  - Last.fm API for track/artist data (Free API)
  - Review Discovery Engine API for review insights

- **Smart Recommendation Fusion**:
  - Combines results from multiple strategies
  - Applies strategy weights for ranking
  - Removes duplicates and filters previously recommended items
  - Generates human-readable explanations

- **Duplicate Avoidance**:
  - Receives previously recommended songs and artists from Phase 1
  - Filters out already-recommended items
  - Ensures variety in recommendations

## Architecture

### Phase Independence

Phase 2 operates as a completely independent microservice:

- **Own Repository**: `phase2-music-recommendation-engine/`
- **Own Dependencies**: `requirements.txt`
- **Own Configuration**: `config.yaml`
- **Own API**: Exposes REST API at port 8002
- **Mock Layer**: Includes mock implementations for testing

### Communication with Phase 1

- **Receives from**: Phase 1 via POST `/recommendations`
- **Sends to**: Phase 1 via RecommendationResponse
- **Data Exchange**: JSON payloads via HTTP/REST

### Recommendation Strategies

#### 1. Review-Based Discovery
- Queries Review Discovery Engine for highly-rated but less-known artists
- Filters by genre alignment with user preferences
- Ranks by review sentiment and discovery score
- Cross-references with Last.fm popularity metrics

#### 2. Mood-Activity Matching
- Maps user mood/activity to audio feature ranges
- Queries Last.fm API with genre-based search
- Applies diversity sampling to prevent repetition
- Uses genre tags and popularity for matching

#### 3. Similarity Search
- Finds artists similar to user's preferred artists
- Uses Last.fm's similar artists API
- Applies user constraints for filtering
- Ranks by similarity + constraint satisfaction

#### 4. Habit Breaking
- Analyzes listening patterns from conversation memory
- Calculates novelty scores for recommendations
- Prioritizes less popular artists for novelty-seeking users
- Selects diverse recommendations to break patterns

#### 5. Genre Exploration
- Finds unexplored related genres
- Gets representative artists for each genre
- Generates educational content about genres
- Expands user's musical horizons

## Installation

### Prerequisites

- Python 3.8+
- Last.fm API Key (Free - obtain from https://www.last.fm/api/account/create)
- Review Discovery Engine (optional, for production use)

### Setup

1. Clone the repository:
```bash
cd phase2-music-recommendation-engine
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. For production use, obtain Last.fm API credentials:
   - Go to https://www.last.fm/api/account/create
   - Create an application (free)
   - Copy API Key to `.env`

## Configuration

Edit `config.yaml` to customize:

- **Server settings**: host, port, workers
- **Last.fm API**: timeout, retries
- **Review Engine**: base URL, timeout
- **Strategy weights**: Adjust importance of each strategy
- **Fusion settings**: diversity thresholds, recommendation limits

## Running the Service

### Production Mode

```bash
python api.py
```

The service will start on `http://localhost:8002`

### Mock Mode (for testing)

Set `USE_MOCKS=true` in `.env` or environment:

```bash
USE_MOCKS=true python api.py
```

Mock mode uses mock data instead of real API calls.

## API Endpoints

### POST /recommendations

Generate music recommendations based on conversation context.

**Request Body**:
```json
{
  "user_id": "user_123",
  "session_id": "session_456",
  "user_intent": "MOOD_BASED",
  "mood": "energetic",
  "activity": "workout",
  "preferred_genres ["electronic", "synthwave"],
  "preferred_artists": ["The Midnight", "Carpenter Brut"],
  "discovery_goal": "novel",
  "previously_recommended_songs": ["track_1", "track_2"],
  "previously_recommended_artists": ["artist_1", "artist_2"],
  "recently_discussed_genres": ["rock", "electronic"],
  "limit": 10,
  "include_explanations": true
}
```

**Response**:
```json
{
  "user_id": "user_123",
  "session_id": "session_456",
  "recommendations": [
    {
      "track": {
        "track_id": "track_3",
        "track_name": "Los Angeles",
        "artist_id": "artist_3",
        "artist_name": "The Midnight",
        "album_name": "Endless Summer",
        "duration_ms": 240000,
        "popularity": 70,
        "audio_features": { ... }
      },
      "confidence": 0.85,
      "explanation": "Based on your energetic workout context...",
      "strategies_used": ["mood_activity", "review_based"],
      "metadata": { ... }
    }
  ],
  "total_count": 10,
  "strategies_executed": ["review_based", "mood_activity", "similarity_search"],
  "execution_time_ms": 1250.5,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "mode": "production",
  "dependencies": {
    "lastfm_api": "configured",
    "review_engine": "http://localhost:8003"
  }
}
```

## Integration with Phase 1

Phase 1 calls Phase 2's `/recommendations` endpoint with:

- **Conversation Context**: mood, activity, preferred genres/artists
- **User Intent**: detected intent from user query
- **Conversation Memory**: previously recommended songs/artists

Phase 2 returns:

- **Ranked Recommendations**: list of tracks with confidence scores
- **Explanations**: human-readable reasoning for each recommendation
- **Strategy Metadata**: which strategies contributed to each recommendation

## Testing

### Unit Tests

```bash
pytest tests/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Using Mock Mode

For testing without real APIs:

```bash
USE_MOCKS=true python api.py
```

Then send requests to the running service.

## Development

### Project Structure

```
phase2-music-recommendation-engine/
├── api.py                      # FastAPI server
├── schemas.py                  # Pydantic models
├── lastfm_client.py            # Last.fm API client
├── review_client.py            # Review Engine API client
├── recommendation_engine.py    # Core recommendation engine
├── config.yaml                 # Configuration
├── requirements.txt            # Dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

### Adding New Strategies

1. Create a new method in `RecommendationEngine` class
2. Implement the strategy logic
3. Return a `StrategyResult` with candidates
4. Add strategy configuration to `config.yaml`
5. Update strategy execution in `generate_recommendations`

## Performance

- **Target Latency**: < 3 seconds for full recommendation
- **Strategy Parallelization**: All strategies execute in parallel
- **Caching**: Last.fm data cached for 24 hours, review insights for 6 hours
- **Rate Limiting**: Configurable rate limits for Last.fm API

## Error Handling

- **Last.fm API Errors**: Automatic retry with exponential backoff
- **Review Engine Errors**: Fallback to other strategies
- **Strategy Failures**: Individual strategy failures don't break the system
- **Empty Results**: Returns error if no recommendations can be generated

## Logging

Logs include:

- Strategy execution times
- Cache hit rates
- API call counts
- Recommendation acceptance rates
- Error details

Logs are written to `./logs/recommendation_engine.log` in JSON format.

## Phase Independence Principles

This phase can:

- Run independently without Phase 1, 3, 4, or 5
- Be deployed as a standalone Docker container
- Use mock data when external services are unavailable
- Be tested in isolation

## License

This is part of the AI-Native Music Discovery Companion project.
