# Design Document: VotePath AI Backend

## Overview

VotePath AI Backend is a FastAPI-based election education assistant designed for hackathon deployment with production-ready quality. The system provides deterministic, rule-based responses to election-related questions through intent detection, Google Sheets integration, and intelligent fallback mechanisms.

### Core Design Principles

1. **Reliability First**: Never fail - graceful degradation at every layer
2. **Best-Effort External Integration**: Google Sheets is optional, not required
3. **Minimal Resource Footprint**: <1MB repository, <256MB memory, sub-second responses
4. **Clean Architecture**: Layered design with clear separation of concerns
5. **Production Quality**: Comprehensive error handling, logging, and testing

### Key Features

- RESTful API with FastAPI
- Flexible Google Sheets integration (public-read OR service account)
- Bundled local fallback data for all 8 intent categories
- In-memory caching for performance
- Comprehensive input normalization and validation
- Structured 7-field response format
- Health check and category listing endpoints

## Architecture

### System Layers

The system follows a layered architecture pattern:

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │
│  - Route handlers                       │
│  - Request validation                   │
│  - Response serialization               │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Service Layer                   │
│  - Intent detection                     │
│  - Response formatting                  │
│  - Startup orchestration                │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Data Access Layer                  │
│  - Google Sheets service                │
│  - Fallback data service                │
│  - Cache manager                        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Models & Utils                  │
│  - Pydantic schemas                     │
│  - Validators                           │
│  - Configuration                        │
└─────────────────────────────────────────┘
```

### Data Flow

**Request Processing Flow:**

```
HTTP Request → Route Handler → Intent Detection → Cache Lookup → Response Formatting → JSON Response
                                                         ↓
                                                   Cache Miss
                                                         ↓
                                                  Fallback Data → Response
```

**Startup Flow:**

```
Application Start → Load Config → Initialize Logging → Attempt Sheets Preload
                                                              ↓
                                                         Success/Failure
                                                              ↓
                                                    Populate Cache (Sheets or Fallback)
                                                              ↓
                                                      Start FastAPI Server
```

### Dependency Flow

```
main.py
  ├── api/routes.py
  │     ├── services/intent_service.py
  │     ├── services/response_service.py
  │     └── utils/cache.py
  ├── services/startup_service.py
  │     ├── services/sheets_service.py
  │     ├── services/fallback_service.py
  │     ├── utils/cache.py
  │     └── core/config.py
  └── core/logging_config.py
```

## Components and Interfaces

### 1. API Layer

#### `api/routes.py`

**Purpose**: Define HTTP endpoints and handle request/response lifecycle

**Endpoints:**

```python
@router.get("/")
async def health_check() -> dict
    """
    Returns system health status
    Response: {"status": "healthy", "mode": "sheets|fallback"}
    """

@router.post("/ask")
async def ask_question(request: QuestionRequest) -> QuestionResponse
    """
    Process user question and return structured response
    Request: {"question": str}
    Response: QuestionResponse (7-field structure)
    """

@router.get("/categories")
async def get_categories() -> dict
    """
    Returns list of supported intent categories
    Response: {"categories": List[str]}
    """
```

**Dependencies:**
- `services/intent_service.py`: Intent detection
- `services/response_service.py`: Response formatting
- `utils/cache.py`: Cache access
- `models/schemas.py`: Request/response models

### 2. Core Configuration

#### `core/config.py`

**Purpose**: Centralized configuration management

**Configuration Class:**

```python
class Settings(BaseSettings):
    # Google Sheets Configuration
    SHEET_ID: Optional[str] = None
    WORKSHEET_NAME: str = "VotePath_Data"
    ACCESS_MODE: str = "auto"  # "auto", "public", "service_account"
    CREDENTIALS_PATH: Optional[str] = None
    
    # Application Configuration
    APP_NAME: str = "VotePath AI Backend"
    APP_VERSION: str = "1.0.0"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"
    
    # Performance Configuration
    CACHE_ENABLED: bool = True
    RESPONSE_TIMEOUT_MS: int = 500
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

**Key Methods:**
- `get_settings() -> Settings`: Singleton pattern for config access
- `validate_config() -> bool`: Validate configuration at startup
- `determine_access_mode() -> str`: Auto-detect best Sheets access mode

#### `core/logging_config.py`

**Purpose**: Configure structured logging

**Configuration:**
- JSON-formatted logs for production
- Console output for development
- Log levels: DEBUG, INFO, WARNING, ERROR
- Automatic credential redaction in logs

### 3. Models

#### `models/schemas.py`

**Purpose**: Pydantic models for request/response validation

**Models:**

```python
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    
    @validator('question')
    def validate_question(cls, v):
        # Strip whitespace, validate non-empty
        return v.strip()

class QuestionResponse(BaseModel):
    category: str
    title: str
    overview: str
    steps: List[str] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)
    tips: List[str] = Field(default_factory=list)
    next_action: str = ""
    
class HealthResponse(BaseModel):
    status: str
    mode: str  # "sheets" or "fallback"
    timestamp: str

class CategoriesResponse(BaseModel):
    categories: List[str]
```

### 4. Services

#### `services/intent_service.py`

**Purpose**: Detect user intent from question text

**Key Components:**

```python
INTENT_KEYWORDS = {
    "first_time_voter": ["first time", "new voter", "never voted", "voting for the first time"],
    "registration": ["register", "registration", "sign up", "enroll"],
    "documents": ["document", "id", "identification", "proof", "what do i need"],
    "correction": ["correct", "mistake", "error", "wrong", "change", "update"],
    "status_check": ["status", "check", "verify", "confirm", "registered"],
    "polling_day": ["polling day", "election day", "voting day", "where to vote", "polling station"],
    "timeline": ["timeline", "deadline", "when", "dates", "schedule"],
    "faq": ["help", "faq", "question", "info", "information"]
}

def normalize_input(question: str) -> str:
    """
    Normalize input: lowercase, strip whitespace, handle punctuation
    """
    
def detect_intent(question: str) -> str:
    """
    Detect intent using keyword matching with scoring
    Returns: intent category (str)
    Default: "faq" if no match
    """
    
def score_intent(question: str, keywords: List[str]) -> int:
    """
    Count keyword matches in question
    Returns: match count (int)
    """
```

**Algorithm:**
1. Normalize input (lowercase, strip, remove extra punctuation)
2. For each intent, count keyword matches
3. Return intent with highest score
4. Default to "faq" if no matches or tie

**Performance Target**: <100ms for typical queries

#### `services/sheets_service.py`

**Purpose**: Interface with Google Sheets API

**Key Methods:**

```python
class SheetsService:
    def __init__(self, config: Settings):
        self.config = config
        self.client = None
        
    def initialize(self) -> bool:
        """
        Initialize Google Sheets client based on access mode
        Returns: True if successful, False otherwise
        """
        
    def load_data(self) -> Dict[str, Dict]:
        """
        Load and parse data from Google Sheets
        Returns: Dict mapping intent -> response data
        Raises: Exception on failure (caught by caller)
        """
        
    def validate_sheet_structure(self, worksheet) -> bool:
        """
        Validate required columns exist
        Required: category, title, overview, steps, documents, tips, next_action
        """
        
    def parse_row(self, row: List[str]) -> Optional[Dict]:
        """
        Parse single row into structured data
        Returns: None if row is invalid
        """
```

**Access Modes:**

1. **Public Read Mode**: Use gspread with public sheet URL
2. **Service Account Mode**: Use google-auth with credentials file
3. **Auto Mode**: Try public first, fall back to service account

**Error Handling:**
- All exceptions caught and logged
- Never crash on Sheets failure
- Return empty dict on failure (triggers fallback)

#### `services/fallback_service.py`

**Purpose**: Provide bundled local fallback data

**Structure:**

```python
class FallbackService:
    def get_fallback_data(self) -> Dict[str, Dict]:
        """
        Returns complete fallback dataset for all 8 categories
        """
        
    def get_category_data(self, category: str) -> Dict:
        """
        Returns fallback data for specific category
        """
```

**Fallback Data Storage**: Embedded in `data/fallback_content.py` as Python dict

**Data Structure:**
```python
FALLBACK_DATA = {
    "first_time_voter": {
        "title": "First Time Voter Guide",
        "overview": "...",
        "steps": ["...", "..."],
        "documents": ["...", "..."],
        "tips": ["...", "..."],
        "next_action": "..."
    },
    # ... all 8 categories
}
```

#### `services/response_service.py`

**Purpose**: Format responses into standardized structure

**Key Methods:**

```python
class ResponseService:
    def format_response(self, category: str, data: Dict) -> QuestionResponse:
        """
        Format data into QuestionResponse model
        Ensures all fields present, handles missing data
        """
        
    def ensure_complete_response(self, response: QuestionResponse) -> QuestionResponse:
        """
        Validate response completeness
        Fill empty fields with defaults
        """
```

**Formatting Rules:**
- All 7 fields must be present
- Empty arrays for missing list fields
- Empty strings for missing text fields
- Beginner-friendly language
- Actionable next steps

#### `services/startup_service.py`

**Purpose**: Orchestrate application startup sequence

**Startup Sequence:**

```python
class StartupService:
    def initialize_application(self) -> dict:
        """
        Execute startup sequence
        Returns: {"mode": str, "sheets_loaded": bool, "cache_size": int}
        """
        
    def _load_configuration(self) -> Settings:
        """Load and validate configuration"""
        
    def _initialize_logging(self, config: Settings):
        """Configure logging system"""
        
    def _attempt_sheets_load(self) -> Optional[Dict]:
        """Best-effort Google Sheets preload"""
        
    def _load_fallback_data(self) -> Dict:
        """Load bundled fallback data"""
        
    def _populate_cache(self, data: Dict):
        """Populate cache with loaded data"""
```

**Startup Logic:**
1. Load configuration from environment
2. Initialize logging with config
3. Attempt Google Sheets preload (best-effort)
4. If Sheets fails, load fallback data
5. Populate cache with data
6. Log startup mode and status
7. Return startup summary

**Failure Handling**: Never fail startup - always proceed with fallback

### 5. Utilities

#### `utils/cache.py`

**Purpose**: In-memory cache for response data

**Implementation:**

```python
class CacheManager:
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        
    def set(self, category: str, data: Dict):
        """Thread-safe cache write"""
        
    def get(self, category: str) -> Optional[Dict]:
        """Thread-safe cache read"""
        
    def populate(self, data: Dict[str, Dict]):
        """Bulk populate cache"""
        
    def clear(self):
        """Clear cache (for testing)"""
        
    def size(self) -> int:
        """Return number of cached entries"""
```

**Cache Strategy:**
- In-memory dictionary
- Thread-safe with locks
- No expiration (static content)
- Preloaded at startup
- Keyed by intent category

#### `utils/validators.py`

**Purpose**: Input validation utilities

**Functions:**

```python
def validate_question(question: str) -> Tuple[bool, Optional[str]]:
    """
    Validate question input
    Returns: (is_valid, error_message)
    """
    
def validate_sheet_row(row: List[str]) -> bool:
    """
    Validate sheet row has required fields
    """
    
def sanitize_input(text: str) -> str:
    """
    Sanitize user input for safety
    """
```

### 6. Data

#### `data/fallback_content.py`

**Purpose**: Bundled fallback content for all categories

**Structure**: Python dictionary with complete response data for all 8 intents

**Content Requirements:**
- Comprehensive coverage of all categories
- Production-quality content
- Follows same structure as Sheets data
- Sufficient for full demonstration

## Data Models

### Intent Categories

The system supports 8 predefined intent categories:

1. **first_time_voter**: Guidance for new voters
2. **registration**: Voter registration process
3. **documents**: Required identification documents
4. **correction**: Correcting registration errors
5. **status_check**: Checking registration status
6. **polling_day**: Polling day procedures and locations
7. **timeline**: Election timeline and deadlines
8. **faq**: General frequently asked questions

### Response Structure

All responses follow this 7-field structure:

```json
{
  "category": "string (intent category)",
  "title": "string (response title)",
  "overview": "string (brief overview)",
  "steps": ["string", "string", ...],
  "documents": ["string", "string", ...],
  "tips": ["string", "string", ...],
  "next_action": "string (actionable next step)"
}
```

### Google Sheets Schema

Expected sheet structure:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| category | string | Yes | Intent category |
| title | string | Yes | Response title |
| overview | string | Yes | Brief overview |
| steps | string | No | Pipe-separated steps |
| documents | string | No | Pipe-separated documents |
| tips | string | No | Pipe-separated tips |
| next_action | string | No | Next action text |

**Parsing Rules:**
- Pipe character (`|`) separates array elements
- Empty cells become empty arrays/strings
- Invalid rows are skipped with warning log

## Error Handling

### Error Handling Strategy

The system implements defense-in-depth error handling:

**Layer 1: Input Validation**
- Pydantic models validate all inputs
- Custom validators for business rules
- Return HTTP 422 for invalid requests

**Layer 2: Service Boundaries**
- Try-except blocks around all external calls
- Graceful degradation on service failures
- Never propagate exceptions to API layer

**Layer 3: Fallback Chain**
- Google Sheets → Cache → Fallback Data
- Each failure triggers next fallback
- Always return valid response

**Layer 4: Global Exception Handler**
- FastAPI exception handlers for uncaught errors
- Return generic error response
- Log full stack trace

### Error Scenarios and Handling

| Scenario | Handling | User Impact |
|----------|----------|-------------|
| Invalid JSON | HTTP 422 with details | Clear error message |
| Empty question | HTTP 422 with details | Validation error |
| Sheets API failure | Use cached/fallback data | Transparent |
| Cache miss | Use fallback data | Transparent |
| Invalid credentials | Start in fallback mode | Transparent |
| Network timeout | Use cached/fallback data | Transparent |
| Malformed sheet data | Skip row, log warning | Transparent |
| Unknown intent | Return FAQ response | Helpful default |

### Logging Strategy

**Log Levels:**
- **DEBUG**: Detailed flow information (development only)
- **INFO**: Startup mode, cache hits, normal operations
- **WARNING**: Fallback usage, skipped rows, degraded mode
- **ERROR**: Exceptions, failures, unexpected conditions

**Log Content:**
- Timestamp (ISO 8601)
- Log level
- Component name
- Message
- Context (request ID, intent, etc.)
- Stack trace (errors only)

**Security:**
- Never log credentials or API keys
- Redact sensitive data automatically
- Sanitize user input in logs

## Testing Strategy

### Testing Approach

The system requires comprehensive testing across multiple dimensions:

**1. Unit Tests**
- Test individual functions and methods
- Mock external dependencies
- Focus on business logic correctness
- Target: 80%+ code coverage

**2. Integration Tests**
- Test API endpoints end-to-end
- Test service interactions
- Test database/cache operations
- Use test fixtures for data

**3. Error Scenario Tests**
- Test all failure modes
- Test fallback behavior
- Test graceful degradation
- Verify error messages

**4. Performance Tests**
- Verify response time targets
- Test under load
- Memory usage profiling
- Startup time verification

### Test Organization

```
tests/
├── unit/
│   ├── test_intent_service.py
│   ├── test_response_service.py
│   ├── test_sheets_service.py
│   ├── test_fallback_service.py
│   ├── test_cache.py
│   └── test_validators.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_startup_flow.py
│   └── test_end_to_end.py
├── fixtures/
│   ├── sample_sheets_data.py
│   └── sample_requests.py
└── conftest.py
```

### Key Test Cases

**Intent Detection Tests:**
- Test each intent with typical questions
- Test synonym matching
- Test ambiguous inputs
- Test empty/invalid inputs
- Test normalization (case, whitespace, punctuation)
- Test scoring algorithm
- Test default fallback to FAQ

**Sheets Service Tests:**
- Test public access mode
- Test service account mode
- Test auto mode selection
- Test connection failures
- Test malformed data handling
- Test row validation
- Mock gspread library

**Cache Tests:**
- Test cache population
- Test cache retrieval
- Test cache miss handling
- Test thread safety
- Test cache clearing

**Response Formatting Tests:**
- Test complete response structure
- Test missing field handling
- Test empty array/string defaults
- Test data type validation

**API Endpoint Tests:**
- Test /ask with valid questions
- Test /ask with invalid inputs
- Test /categories endpoint
- Test / health check
- Test error responses
- Test response times

**Fallback Behavior Tests:**
- Test startup with Sheets unavailable
- Test runtime Sheets failure
- Test fallback data completeness
- Test transparent fallback switching

### Testing Tools

- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **httpx**: API testing client
- **unittest.mock**: Mocking framework

### Coverage Goals

- Overall: 80%+ code coverage
- Critical paths: 95%+ coverage
- Intent detection: 100% coverage
- Error handlers: 100% coverage


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Input Normalization Consistency

*For any* input string, the normalization function SHALL produce output that is lowercase with leading/trailing whitespace removed and extra internal whitespace collapsed to single spaces.

**Validates: Requirements 2.2**

### Property 2: Intent Detection Robustness

*For any* valid question string, intent detection SHALL produce the same result regardless of case variations, punctuation placement, or keyword position within the text.

**Validates: Requirements 2.3, 2.4, 2.5**

### Property 3: Intent Scoring Correctness

*For any* question containing keywords from multiple intents, the intent detection SHALL return the intent category with the highest keyword match count.

**Validates: Requirements 2.7**

### Property 4: Default Intent Fallback

*For any* question containing no matching keywords from any intent category, the intent detection SHALL return "faq" as the default intent.

**Validates: Requirements 2.8**

### Property 5: Sheet Data Parsing Structure

*For any* valid sheet data with required columns, the parsing function SHALL produce a dictionary mapping intent categories to response dictionaries with all 7 required fields.

**Validates: Requirements 3.5**

### Property 6: Column Validation Correctness

*For any* sheet structure (list of column names), the column validation function SHALL return true if and only if all required columns (category, title, overview, steps, documents, tips, next_action) are present.

**Validates: Requirements 3.6**

### Property 7: Row Validation Correctness

*For any* sheet row data, the row validation function SHALL correctly classify the row as valid (has non-empty category and title) or invalid (missing required fields), and invalid rows SHALL be skipped without causing errors.

**Validates: Requirements 3.7**

### Property 8: Log Credential Sanitization

*For any* log message or error message, if the message contains credential-like patterns (API keys, tokens, passwords), the logging system SHALL redact or remove those patterns before writing to logs.

**Validates: Requirements 3.9, 7.2, 15.5**

### Property 9: Response Structure Completeness

*For any* input data passed to the response formatter, the resulting response SHALL contain exactly 7 fields: category, title, overview, steps, documents, tips, and next_action.

**Validates: Requirements 5.1, 5.2**

### Property 10: Response Default Handling

*For any* input data with missing or null fields, the response formatter SHALL populate missing text fields with empty strings and missing array fields with empty arrays.

**Validates: Requirements 5.3**

### Property 11: Response Array Type Correctness

*For any* formatted response, the fields steps, documents, and tips SHALL always be arrays of strings (List[str]), never null or other types.

**Validates: Requirements 5.4, 5.5, 5.6**

### Property 12: System Response Validity

*For any* request to the /ask endpoint, even in the presence of component failures (Sheets unavailable, cache miss, etc.), the system SHALL return a valid QuestionResponse object with all required fields populated.

**Validates: Requirements 6.3**

### Property 13: Error Message Descriptiveness

*For any* invalid input that triggers validation errors, the error response SHALL contain a non-empty, descriptive error message that explains what was invalid.

**Validates: Requirements 6.9**

### Property 14: Input Sanitization Safety

*For any* user input string, the sanitization function SHALL remove or escape potentially dangerous characters (e.g., SQL injection patterns, script tags) before processing.

**Validates: Requirements 7.3**

### Property 15: Fallback Data Completeness

*For any* request for fallback data, the fallback service SHALL provide data for all 8 supported intent categories: first_time_voter, registration, documents, correction, status_check, polling_day, timeline, faq.

**Validates: Requirements 13.1**

### Property 16: Fallback Data Structure Consistency

*For any* category in the fallback data, the data structure SHALL match the expected schema with all 7 required fields (category, title, overview, steps, documents, tips, next_action) present and correctly typed.

**Validates: Requirements 13.3**

### Property 17: Configuration Default Application

*For any* configuration parameter that is missing or not provided, the configuration system SHALL apply a sensible default value and the system SHALL start successfully.

**Validates: Requirements 14.3**

### Property 18: Log Message Format Completeness

*For any* log message generated by the system, the log entry SHALL include both a timestamp (ISO 8601 format) and contextual information (component name, log level, message).

**Validates: Requirements 15.7**


## Deployment Architecture

### Container Strategy

The application uses Docker for containerization with a multi-stage build approach:

**Dockerfile Structure:**

```dockerfile
# Stage 1: Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
ENV PATH=/root/.local/bin:$PATH
ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Build Optimizations:**
- Multi-stage build reduces final image size
- Slim Python base image (<100MB)
- No cache for pip to minimize size
- Only copy necessary application files

### Google Cloud Run Configuration

**Deployment Settings:**
- **Port**: 8080 (Cloud Run standard)
- **Memory**: 256MB (sufficient for in-memory cache)
- **CPU**: 1 vCPU
- **Concurrency**: 80 requests per instance
- **Timeout**: 60 seconds
- **Min Instances**: 0 (scale to zero)
- **Max Instances**: 10 (hackathon scale)

**Environment Variables:**
```bash
SHEET_ID=<google-sheet-id>
WORKSHEET_NAME=VotePath_Data
ACCESS_MODE=auto
CREDENTIALS_PATH=/secrets/credentials.json  # If using service account
LOG_LEVEL=INFO
```

**Secrets Management:**
- Service account credentials stored in Google Secret Manager
- Mounted as volume at `/secrets/credentials.json`
- Never included in container image
- Automatic rotation support

### CI/CD Pipeline

**Build Pipeline:**
1. Run linters (flake8, black)
2. Run type checker (mypy)
3. Run unit tests with coverage
4. Build Docker image
5. Push to Google Container Registry
6. Deploy to Cloud Run

**Quality Gates:**
- Test coverage > 80%
- No type errors
- No linting errors
- All tests passing

## Configuration Reference

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| SHEET_ID | string | None | Google Sheet ID (optional) |
| WORKSHEET_NAME | string | "VotePath_Data" | Worksheet name to read |
| ACCESS_MODE | string | "auto" | Access mode: auto, public, service_account |
| CREDENTIALS_PATH | string | None | Path to service account JSON |
| APP_NAME | string | "VotePath AI Backend" | Application name |
| APP_VERSION | string | "1.0.0" | Application version |
| PORT | int | 8080 | Server port |
| LOG_LEVEL | string | "INFO" | Logging level |
| CACHE_ENABLED | bool | true | Enable in-memory caching |
| RESPONSE_TIMEOUT_MS | int | 500 | Target response time |

### Access Mode Behavior

**auto (default):**
- Try public access first (if SHEET_ID provided)
- Fall back to service account (if CREDENTIALS_PATH provided)
- Fall back to local data (if both fail)

**public:**
- Use public read-only access
- Requires SHEET_ID
- No authentication needed
- Falls back to local data on failure

**service_account:**
- Use service account authentication
- Requires SHEET_ID and CREDENTIALS_PATH
- Full API access
- Falls back to local data on failure

### Startup Modes

**Sheets Mode:**
- Google Sheets successfully loaded
- Cache populated from Sheets
- Health endpoint returns: `{"status": "healthy", "mode": "sheets"}`

**Fallback Mode:**
- Google Sheets unavailable or failed
- Cache populated from local fallback data
- Health endpoint returns: `{"status": "healthy", "mode": "fallback"}`
- System fully functional

## Performance Characteristics

### Response Time Targets

| Endpoint | Target | Typical | Max Acceptable |
|----------|--------|---------|----------------|
| GET / | <50ms | 20ms | 100ms |
| GET /categories | <50ms | 20ms | 100ms |
| POST /ask (cached) | <100ms | 50ms | 500ms |
| POST /ask (uncached) | <500ms | 200ms | 1000ms |

### Resource Usage

**Memory:**
- Base application: ~50MB
- Cached data (8 categories): ~10MB
- Request handling: ~5MB per concurrent request
- Total typical: ~100MB
- Peak (80 concurrent): ~250MB

**CPU:**
- Intent detection: <10ms CPU time
- Response formatting: <5ms CPU time
- Cache lookup: <1ms CPU time
- Total per request: <20ms CPU time

**Startup:**
- Container start: ~2 seconds
- Application initialization: ~3 seconds
- Sheets preload (success): ~2 seconds
- Sheets preload (failure): ~1 second (timeout)
- Total startup: 5-8 seconds

### Scalability

**Vertical Scaling:**
- Single instance handles 80 concurrent requests
- Memory scales linearly with concurrency
- CPU usage minimal (I/O bound)

**Horizontal Scaling:**
- Stateless design enables unlimited horizontal scaling
- Each instance has independent cache
- No shared state between instances
- Cloud Run auto-scaling handles load

**Load Capacity:**
- Single instance: ~800 requests/second (cached)
- 10 instances: ~8,000 requests/second
- Sufficient for hackathon demo and evaluation

## Security Considerations

### Input Validation

**Request Validation:**
- Pydantic models validate all inputs
- Question length: 1-500 characters
- JSON structure validation
- Type checking on all fields

**Input Sanitization:**
- Strip leading/trailing whitespace
- Remove control characters
- Escape special characters
- Prevent injection attacks

### Credential Management

**Best Practices:**
- Never commit credentials to repository
- Use environment variables for secrets
- Mount secrets from Secret Manager
- Rotate credentials regularly
- Audit credential access

**Credential Redaction:**
- Automatic redaction in logs
- Pattern matching for API keys
- Mask sensitive data in errors
- No credentials in responses

### API Security

**Rate Limiting:**
- Cloud Run provides DDoS protection
- Consider adding rate limiting for production
- Monitor for abuse patterns

**CORS Configuration:**
- Configure allowed origins
- Restrict methods to GET, POST
- Set appropriate headers

**HTTPS:**
- Cloud Run enforces HTTPS
- No HTTP traffic allowed
- TLS 1.2+ required

## Monitoring and Observability

### Logging Strategy

**Log Levels:**
- **DEBUG**: Detailed flow (development only)
- **INFO**: Normal operations, startup, cache hits
- **WARNING**: Fallback usage, degraded mode, retries
- **ERROR**: Exceptions, failures, unexpected conditions

**Structured Logging:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "component": "intent_service",
  "message": "Intent detected",
  "context": {
    "intent": "registration",
    "confidence": 0.95,
    "request_id": "abc123"
  }
}
```

### Metrics

**Application Metrics:**
- Request count by endpoint
- Response time percentiles (p50, p95, p99)
- Error rate by type
- Cache hit rate
- Intent distribution

**System Metrics:**
- Memory usage
- CPU utilization
- Container restarts
- Startup time

**Business Metrics:**
- Questions per intent category
- Fallback mode usage
- Sheets load success rate

### Health Checks

**Liveness Probe:**
- Endpoint: GET /
- Expected: HTTP 200
- Frequency: Every 10 seconds
- Failure threshold: 3 consecutive failures

**Readiness Probe:**
- Endpoint: GET /
- Expected: HTTP 200 with valid JSON
- Frequency: Every 5 seconds
- Success threshold: 1 success

### Alerting

**Critical Alerts:**
- Error rate > 5%
- Response time p95 > 1 second
- Memory usage > 90%
- Container crash loop

**Warning Alerts:**
- Fallback mode active > 1 hour
- Sheets load failures > 3 consecutive
- Cache miss rate > 10%

## Development Workflow

### Local Development Setup

**Prerequisites:**
- Python 3.11+
- pip
- Docker (optional)

**Setup Steps:**
```bash
# Clone repository
git clone <repository-url>
cd votepath-ai-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Testing dependencies

# Set environment variables
export SHEET_ID=<your-sheet-id>  # Optional
export LOG_LEVEL=DEBUG

# Run application
uvicorn app.main:app --reload --port 8080

# Run tests
pytest tests/ --cov=app --cov-report=html

# Run linters
black app/ tests/
flake8 app/ tests/
mypy app/
```

### Testing Workflow

**Unit Tests:**
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_intent_service.py -v

# Run with coverage
pytest tests/unit/ --cov=app.services --cov-report=term
```

**Integration Tests:**
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with real Sheets (requires credentials)
SHEET_ID=<id> pytest tests/integration/test_sheets_service.py
```

**Property-Based Tests:**
```bash
# Run property tests with verbose output
pytest tests/unit/test_properties.py -v --hypothesis-show-statistics
```

### Code Quality Tools

**Formatting:**
- **black**: Code formatter (line length 100)
- **isort**: Import sorting

**Linting:**
- **flake8**: Style guide enforcement
- **pylint**: Code analysis

**Type Checking:**
- **mypy**: Static type checking
- Strict mode enabled

**Testing:**
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **hypothesis**: Property-based testing
- **pytest-asyncio**: Async test support

## Implementation Roadmap

### Phase 1: Core Infrastructure (Day 1)

1. Project structure setup
2. Configuration management (core/config.py)
3. Logging configuration (core/logging_config.py)
4. Pydantic models (models/schemas.py)
5. Basic FastAPI app (main.py)
6. Health check endpoint

**Deliverable**: Application starts and responds to health checks

### Phase 2: Data Layer (Day 1-2)

1. Cache manager (utils/cache.py)
2. Fallback data service (services/fallback_service.py)
3. Fallback content (data/fallback_content.py)
4. Input validators (utils/validators.py)
5. Unit tests for data layer

**Deliverable**: Fallback mode fully functional

### Phase 3: Intent Detection (Day 2)

1. Intent service (services/intent_service.py)
2. Keyword mapping configuration
3. Normalization logic
4. Scoring algorithm
5. Unit tests with property-based tests

**Deliverable**: Intent detection working with all 8 categories

### Phase 4: Response Formatting (Day 2)

1. Response service (services/response_service.py)
2. Response formatting logic
3. Default value handling
4. Unit tests with property-based tests

**Deliverable**: Structured responses generated correctly

### Phase 5: Google Sheets Integration (Day 3)

1. Sheets service (services/sheets_service.py)
2. Authentication handling (public + service account)
3. Data parsing and validation
4. Error handling and fallback
5. Integration tests with mocked Sheets

**Deliverable**: Sheets integration working with graceful fallback

### Phase 6: API Layer (Day 3)

1. API routes (api/routes.py)
2. /ask endpoint implementation
3. /categories endpoint
4. Request/response handling
5. Integration tests for all endpoints

**Deliverable**: Full API functional

### Phase 7: Startup Orchestration (Day 3-4)

1. Startup service (services/startup_service.py)
2. Initialization sequence
3. Mode detection and logging
4. Cache population
5. Integration tests for startup

**Deliverable**: Application starts correctly in all modes

### Phase 8: Testing & Quality (Day 4)

1. Complete unit test coverage
2. Property-based tests for all properties
3. Integration tests for all scenarios
4. Error scenario tests
5. Performance tests
6. Coverage reporting

**Deliverable**: 80%+ test coverage, all tests passing

### Phase 9: Deployment (Day 4-5)

1. Dockerfile creation
2. Docker build and test
3. Cloud Run configuration
4. Environment variable setup
5. Deployment scripts
6. Documentation (README)

**Deliverable**: Application deployed to Cloud Run

### Phase 10: Validation & Polish (Day 5)

1. End-to-end testing in Cloud Run
2. Performance validation
3. Security review
4. Documentation review
5. Demo preparation

**Deliverable**: Production-ready application

## Success Criteria

### Functional Requirements

- ✅ All 3 API endpoints functional
- ✅ All 8 intent categories supported
- ✅ Google Sheets integration working (both modes)
- ✅ Fallback mode fully functional
- ✅ Structured responses with all 7 fields
- ✅ Graceful error handling (no crashes)

### Quality Requirements

- ✅ Test coverage > 80%
- ✅ All property-based tests passing (100 iterations each)
- ✅ No type errors (mypy strict mode)
- ✅ No linting errors (flake8, pylint)
- ✅ Code formatted (black)

### Performance Requirements

- ✅ Response time < 500ms (cached)
- ✅ Startup time < 10 seconds
- ✅ Memory usage < 256MB
- ✅ Repository size < 1MB

### Deployment Requirements

- ✅ Deployed to Google Cloud Run
- ✅ Health checks passing
- ✅ Secrets properly managed
- ✅ Logging configured
- ✅ Documentation complete

### Evaluation Targets

- ✅ Correctness: 98-99%
- ✅ Reliability: 98-99%
- ✅ Performance: 98-99%
- ✅ Code Quality: 98-99%
- ✅ Documentation: 98-99%

## Appendix

### Technology Stack Summary

**Core Framework:**
- Python 3.11+
- FastAPI 0.104+
- Pydantic 2.5+
- Uvicorn 0.24+

**Google Sheets Integration:**
- google-auth 2.23+
- gspread 5.12+

**Testing:**
- pytest 7.4+
- pytest-asyncio 0.21+
- pytest-cov 4.1+
- hypothesis 6.92+ (property-based testing)
- httpx 0.25+ (API testing)

**Development Tools:**
- black (formatting)
- flake8 (linting)
- mypy (type checking)
- isort (import sorting)

**Deployment:**
- Docker
- Google Cloud Run
- Google Secret Manager

### File Structure Reference

```
votepath-ai-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                # API endpoint definitions
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration management
│   │   └── logging_config.py        # Logging setup
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py               # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── intent_service.py        # Intent detection
│   │   ├── sheets_service.py        # Google Sheets integration
│   │   ├── fallback_service.py      # Fallback data provider
│   │   ├── response_service.py      # Response formatting
│   │   └── startup_service.py       # Startup orchestration
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── cache.py                 # Cache manager
│   │   └── validators.py            # Input validation
│   └── data/
│       ├── __init__.py
│       └── fallback_content.py      # Bundled fallback data
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest configuration
│   ├── unit/
│   │   ├── test_intent_service.py
│   │   ├── test_response_service.py
│   │   ├── test_sheets_service.py
│   │   ├── test_fallback_service.py
│   │   ├── test_cache.py
│   │   ├── test_validators.py
│   │   └── test_properties.py       # Property-based tests
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_startup_flow.py
│   │   └── test_end_to_end.py
│   └── fixtures/
│       ├── sample_sheets_data.py
│       └── sample_requests.py
├── .github/
│   └── workflows/
│       └── ci.yml                   # CI/CD pipeline
├── Dockerfile                       # Container definition
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore rules
├── .dockerignore                    # Docker ignore rules
├── README.md                        # Project documentation
├── pytest.ini                       # Pytest configuration
├── mypy.ini                         # Mypy configuration
└── .flake8                          # Flake8 configuration
```

### Glossary of Terms

- **Intent**: A predefined category representing the user's query purpose
- **Intent Detection**: The process of mapping a user question to an intent category
- **Keyword Matching**: Algorithm that counts keyword occurrences to determine intent
- **Normalization**: Process of standardizing input (lowercase, trim, etc.)
- **Fallback Mode**: Operating mode using bundled local data instead of Google Sheets
- **Sheets Mode**: Operating mode using data loaded from Google Sheets
- **Cache**: In-memory storage of response data for fast retrieval
- **Property-Based Testing**: Testing approach that verifies universal properties across many generated inputs
- **Graceful Degradation**: System behavior that maintains functionality despite component failures
- **Best-Effort**: Attempt operation but don't fail if unsuccessful

### References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [gspread Documentation](https://docs.gspread.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)

