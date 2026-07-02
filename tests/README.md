# Integration Tests for AI Music Discovery Companion

Comprehensive integration test suite covering all phases of the AI Music Discovery Companion system.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test configuration and fixtures
├── requirements.txt            # Test dependencies
├── test_phase1_integration.py  # Phase 1: AI Conversation Engine tests
├── test_phase2_integration.py  # Phase 2: Music Recommendation Engine tests
├── test_phase3_integration.py  # Phase 3: AI Orchestration tests
├── test_phase4_integration.py  # Phase 4: Backend API tests
├── test_phase5_integration.py  # Phase 5: Frontend UI tests
├── test_agent_outputs.py       # Agent output validation tests
└── test_pipeline_execution.py # Pipeline execution tests
```

## Installation

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Phase Tests

```bash
# Phase 1: AI Conversation Engine
pytest -m phase1

# Phase 2: Music Recommendation Engine
pytest -m phase2

# Phase 3: AI Orchestration
pytest -m phase3

# Phase 4: Backend API
pytest -m phase4

# Phase 5: Frontend UI
pytest -m phase5
```

### Run Specific Test Categories

```bash
# API endpoint tests
pytest -m api

# Agent output tests
pytest -m agent

# Pipeline execution tests
pytest -m pipeline

# Integration tests only
pytest -m integration
```

### Run Tests with Coverage

```bash
pytest --cov=phase1-ai-conversation-engine \
       --cov=phase2-music-recommendation-engine \
       --cov=phase3-ai-orchestration \
       --cov=phase4-backend-api \
       --cov=phase5-frontend-ui \
       --cov-report=html
```

### Run Tests in Parallel

```bash
pytest -n auto  # Uses pytest-xdist for parallel execution
```

### Skip Slow Tests

```bash
pytest -m "not slow"
```

### Generate HTML Report

```bash
pytest --html=reports/test-report.html --self-contained-html
```

## Test Categories

### Phase 1: AI Conversation Engine Tests

**File:** `test_phase1_integration.py`

Tests for:
- Intent Recognition
  - Music recommendation intent detection
  - Trending query intent detection
  - Explanation intent detection
  - Artist query intent detection
  - Genre query intent detection
  - Low confidence query handling

- Query Parsing
  - Mood extraction
  - Activity extraction
  - Genre extraction
  - Complex query parsing
  - Energy level parsing
  - Popularity filter parsing

- Response Generation
  - Music recommendation responses
  - Trending query responses
  - Explanation responses
  - Context-aware responses

- Context Management
  - Conversation turn management
  - Context retrieval
  - Context clearing
  - Context limit enforcement

- Prompt Building
  - Intent prompt construction
  - Parser prompt construction
  - Response prompt construction
  - Explanation prompt construction

### Phase 2: Music Recommendation Engine Tests

**File:** `test_phase2_integration.py`

Tests for:
- Mood Activity Matching
  - Mood to music characteristics
  - Activity to music characteristics
  - Combined mood and activity matching
  - Invalid mood handling
  - Characteristic range validation

- Genre Exploration
  - Genre characteristic exploration
  - Similar genre discovery
  - Genre trend analysis
  - Subgenre exploration

- Similarity Search
  - Similar track search
  - Similar artist search
  - Similarity score validation

- Review-Based Discovery
  - Sentiment-based discovery
  - Theme-based discovery
  - Review summary generation
  - Unique descriptor extraction

- Habit Breaking
  - Listening history retrieval
  - Habit identification
  - Habit-breaking suggestions
  - Diversity score calculation

- Recommendation Fusion
  - Multi-source fusion
  - Weighted fusion
  - Deduplication

- Explanation Generation
  - Mood-based explanations
  - Similarity-based explanations
  - Review-based explanations
  - Comprehensive explanations

### Phase 3: AI Orchestration Tests

**File:** `test_phase3_integration.py`

Tests for:
- Orchestration Controller
  - Music recommendation request processing
  - Trending query processing
  - Explanation request processing
  - Artist query processing
  - Unknown intent handling

- Fallback Manager
  - LLM failure fallback
  - Spotify API failure fallback
  - Database failure fallback
  - Cascading fallbacks
  - Context-aware fallbacks

- Performance Monitor
  - LLM latency tracking
  - API call tracking
  - Error rate tracking
  - Performance summary generation
  - Threshold alerting

- Prompt Chain Manager
  - Recommendation chain building
  - Explanation chain building
  - Chain execution
  - Chain with dependencies
  - Chain error handling

- Response Validator
  - Chat response validation
  - Recommendation response validation
  - Explanation response validation
  - Malformed response detection
  - Response structure validation

### Phase 4: Backend API Tests

**File:** `test_phase4_integration.py`

Tests for:
- Health Check
  - Health check endpoint
  - Service status
  - Timestamp validation

- Chat API
  - Basic chat endpoint
  - Chat with conversation history
  - Chat without recommendations
  - Invalid payload handling
  - Rate limiting

- Discover API
  - Basic music discovery
  - Mood-only discovery
  - Genre-based discovery
  - Strategy tracking
  - Limit parameter validation

- Explain API
  - Basic explanation request
  - Explanation content validation
  - Score range validation
  - Invalid recommendation ID handling

- Recommendation History API
  - History retrieval
  - Pagination
  - Structure validation

- Similar Artists API
  - Search by artist ID
  - Search by artist name
  - Limit parameter validation

- Discovery Insights API
  - Insights retrieval
  - Structure validation
  - Type-based filtering
  - Executive summary validation

- Conversation History API
  - History retrieval
  - Session-based filtering
  - Structure validation

### Phase 5: Frontend UI Tests

**File:** `test_phase5_integration.py`

Tests for:
- Frontend Components
  - Component file existence
  - Page file existence
  - API client existence
  - Layout file existence

- Frontend API Integration
  - API client endpoint coverage
  - API client type definitions

- Frontend Page Integration
  - Chat page component usage
  - Discover page component usage
  - Explain page component usage
  - Artist page component usage
  - Home page component usage

- Responsive Design
  - Sidebar responsive classes
  - Page responsive grid classes
  - Dark mode implementation

- Error Handling
  - Error boundary component
  - Error alert component
  - Page error handling

- Loading States
  - Loading spinner component
  - Page loading states

### Agent Output Tests

**File:** `test_agent_outputs.py`

Tests for:
- Intent Recognition Outputs
  - Output format validation
  - Output consistency
  - Confidence calibration

- Query Parser Outputs
  - Output structure validation
  - Output accuracy
  - Missing info handling

- Response Generator Outputs
  - Output format validation
  - Output relevance
  - Recommendation integration
  - Explanation integration

- Mood Matcher Outputs
  - Characteristic validation
  - Value range validation

- Genre Explorer Outputs
  - Structure validation
  - Similar genres output
  - Trends output

- Similarity Searcher Outputs
  - Similar tracks output
  - Similarity score validation
  - Similar artists output

- Review Discovery Outputs
  - Sentiment discovery output
  - Theme discovery output
  - Review summary output

- Habit Breaker Outputs
  - History output
  - Habits output
  - Diversity score output

- Recommendation Fuser Outputs
  - Fused output structure
  - Combined scores validation
  - Deduplication validation

- Explanation Generator Outputs
  - Mood explanation output
  - Similarity explanation output
  - Comprehensive explanation output

- Agent Output Consistency
  - Intent to parser consistency
  - Parser to recommendation consistency
  - Recommendation to explanation consistency
  - Multi-agent pipeline consistency

### Pipeline Execution Tests

**File:** `test_pipeline_execution.py`

Tests for:
- Conversation Pipeline
  - Single-turn execution
  - Multi-turn execution
  - Context-aware execution

- Recommendation Pipeline
  - Mood-based pipeline
  - Multi-source pipeline
  - Explanation generation pipeline

- Orchestration Pipeline
  - Successful execution
  - Fallback execution
  - Performance validation

- End-to-End Pipeline
  - Full music discovery pipeline
  - Explanation request pipeline
  - Error recovery pipeline
  - Performance tracking pipeline
  - Multi-user pipeline
  - Concurrent request pipeline

- Pipeline Stress Tests
  - High volume requests
  - Long conversation handling
  - Memory management

## Test Fixtures

Available fixtures in `conftest.py`:

- `api_client`: HTTP client for API testing
- `sample_user_data`: Sample user data
- `sample_query_data`: Sample query data
- `sample_recommendation_data`: Sample recommendation data
- `sample_artist_data`: Sample artist data
- `sample_insight_data`: Sample insight data
- `sample_conversation_history`: Sample conversation history
- `health_check`: API health check
- `mock_llm_response`: Mock LLM response
- `mock_spotify_response`: Mock Spotify API response
- `test_environment`: Test environment configuration
- `performance_thresholds`: Performance thresholds for testing

## Environment Variables

Set these environment variables before running tests:

```bash
# API Configuration
export API_BASE_URL=http://localhost:8005

# Database Configuration
export DATABASE_URL=sqlite:///test.db
export REDIS_URL=redis://localhost:6379/1

# External API Configuration
export SPOTIFY_CLIENT_ID=test_client_id
export SPOTIFY_CLIENT_SECRET=test_client_secret
export GROQ_API_KEY=test_groq_key

# Test Configuration
export TESTING=true
export MOCK_EXTERNAL_APIS=true
```

## Test Markers

Use pytest markers to organize and run specific tests:

- `phase1`: Phase 1 tests
- `phase2`: Phase 2 tests
- `phase3`: Phase 3 tests
- `phase4`: Phase 4 tests
- `phase5`: Phase 5 tests
- `api`: API endpoint tests
- `agent`: Agent output tests
- `pipeline`: Pipeline execution tests
- `integration`: Integration tests
- `slow`: Slow-running tests
- `unit`: Unit tests

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all phase directories are in PYTHONPATH
2. **API Connection Errors**: Verify API_BASE_URL is set correctly
3. **Database Errors**: Ensure test database is configured
4. **Async Test Errors**: Verify pytest-asyncio is properly configured

### Debugging Failed Tests

Run tests with verbose output:

```bash
pytest -v -s
```

Run specific test with detailed output:

```bash
pytest tests/test_phase1_integration.py::TestIntentRecognition::test_recognize_music_recommendation_intent -v -s
```

## Coverage Goals

Target coverage for each phase:
- Phase 1: >80%
- Phase 2: >80%
- Phase 3: >80%
- Phase 4: >90%
- Phase 5: >70%

## Contributing

When adding new tests:
1. Follow existing test structure
2. Use appropriate markers
3. Add fixtures to conftest.py if needed
4. Update this README
5. Ensure all tests pass before committing

## License

Same as the main project.
