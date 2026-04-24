# Implementation Plan: VotePath AI Backend

## Overview

This implementation plan follows a layered architecture approach, building from core infrastructure through data access, business logic, API layer, and comprehensive testing. The system will be implemented in Python using FastAPI, with flexible Google Sheets integration, in-memory caching, and graceful fallback mechanisms. The plan includes 18 property-based tests to validate correctness properties and comprehensive unit/integration testing targeting 80%+ code coverage.

## Tasks

- [x] 1. Set up project structure and core infrastructure
  - Create directory structure: app/, tests/, with subdirectories for api/, core/, models/, services/, utils/, data/
  - Create __init__.py files for all Python packages
  - Create requirements.txt with pinned versions: fastapi==0.104.1, uvicorn==0.24.0, pydantic==2.5.0, google-auth==2.23.0, gspread==5.12.0
  - Create requirements-dev.txt with testing dependencies: pytest==7.4.3, pytest-asyncio==0.21.1, pytest-cov==4.1.0, hypothesis==6.92.0, httpx==0.25.2
  - Create .gitignore to exclude venv/, __pycache__/, .env, *.pyc, .coverage, htmlcov/
  - Create .env.example with template environment variables
  - _Requirements: 11.1, 11.2, 11.5_

- [x] 2. Implement configuration management and logging
  - [x] 2.1 Create core/config.py with Settings class using Pydantic BaseSettings
    - Define configuration fields: SHEET_ID, WORKSHEET_NAME, ACCESS_MODE, CREDENTIALS_PATH, APP_NAME, APP_VERSION, PORT, LOG_LEVEL, CACHE_ENABLED, RESPONSE_TIMEOUT_MS
    - Implement get_settings() singleton function
    - Implement validate_config() method
    - Implement determine_access_mode() method for auto-detection
    - _Requirements: 14.1, 14.2, 14.3, 14.6_
  
  - [ ]* 2.2 Write property test for configuration defaults
    - **Property 17: Configuration Default Application**
    - **Validates: Requirements 14.3**
  
  - [x] 2.3 Create core/logging_config.py with structured logging configuration
    - Configure JSON-formatted logs for production
    - Configure console output for development
    - Implement credential redaction patterns for API keys, tokens, passwords
    - Set up log levels: DEBUG, INFO, WARNING, ERROR
    - _Requirements: 15.1, 15.2, 15.5, 15.6, 15.7_
  
  - [ ]* 2.4 Write property test for log credential sanitization
    - **Property 8: Log Credential Sanitization**
    - **Validates: Requirements 3.9, 7.2, 15.5**
  
  - [ ]* 2.5 Write property test for log message format completeness
    - **Property 18: Log Message Format Completeness**
    - **Validates: Requirements 15.7**

- [x] 3. Create data models and validation utilities
  - [x] 3.1 Create models/schemas.py with Pydantic models
    - Define QuestionRequest model with question field (1-500 chars) and validator
    - Define QuestionResponse model with 7 fields: category, title, overview, steps, documents, tips, next_action
    - Define HealthResponse model with status, mode, timestamp fields
    - Define CategoriesResponse model with categories list
    - _Requirements: 1.2, 5.1, 5.2, 12.1_
  
  - [ ]* 3.2 Write property test for response structure completeness
    - **Property 9: Response Structure Completeness**
    - **Validates: Requirements 5.1, 5.2**
  
  - [ ]* 3.3 Write property test for response default handling
    - **Property 10: Response Default Handling**
    - **Validates: Requirements 5.3**
  
  - [ ]* 3.4 Write property test for response array type correctness
    - **Property 11: Response Array Type Correctness**
    - **Validates: Requirements 5.4, 5.5, 5.6**
  
  - [x] 3.5 Create utils/validators.py with validation functions
    - Implement validate_question(question: str) -> Tuple[bool, Optional[str]]
    - Implement validate_sheet_row(row: List[str]) -> bool
    - Implement sanitize_input(text: str) -> str to remove dangerous characters
    - _Requirements: 6.10, 7.3_
  
  - [ ]* 3.6 Write property test for input sanitization safety
    - **Property 14: Input Sanitization Safety**
    - **Validates: Requirements 7.3**

- [x] 4. Implement cache manager and fallback data
  - [x] 4.1 Create utils/cache.py with CacheManager class
    - Implement __init__ with _cache dict and threading.Lock
    - Implement set(category: str, data: Dict) with thread-safe write
    - Implement get(category: str) -> Optional[Dict] with thread-safe read
    - Implement populate(data: Dict[str, Dict]) for bulk loading
    - Implement clear() and size() methods
    - _Requirements: 4.1, 4.2, 4.4, 4.5_
  
  - [ ]* 4.2 Write unit tests for cache operations
    - Test cache population, retrieval, miss handling, thread safety, clearing
    - _Requirements: 10.3_
  
  - [x] 4.3 Create data/fallback_content.py with FALLBACK_DATA dictionary
    - Define complete fallback data for all 8 intent categories: first_time_voter, registration, documents, correction, status_check, polling_day, timeline, faq
    - Each category must have all 7 fields: title, overview, steps (list), documents (list), tips (list), next_action
    - Use production-quality, beginner-friendly content
    - _Requirements: 13.1, 13.3, 13.5_
  
  - [ ]* 4.4 Write property test for fallback data completeness
    - **Property 15: Fallback Data Completeness**
    - **Validates: Requirements 13.1**
  
  - [ ]* 4.5 Write property test for fallback data structure consistency
    - **Property 16: Fallback Data Structure Consistency**
    - **Validates: Requirements 13.3**
  
  - [x] 4.6 Create services/fallback_service.py with FallbackService class
    - Implement get_fallback_data() -> Dict[str, Dict] returning complete dataset
    - Implement get_category_data(category: str) -> Dict for specific category
    - _Requirements: 13.2, 13.4_
  
  - [ ]* 4.7 Write unit tests for fallback service
    - Test data retrieval for all categories, test data structure validity
    - _Requirements: 10.4_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement intent detection service
  - [x] 6.1 Create services/intent_service.py with intent detection logic
    - Define INTENT_KEYWORDS dictionary mapping 8 intents to keyword lists
    - Implement normalize_input(question: str) -> str for lowercase, strip, whitespace collapse
    - Implement score_intent(question: str, keywords: List[str]) -> int for keyword counting
    - Implement detect_intent(question: str) -> str with scoring algorithm, default to "faq"
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_
  
  - [ ]* 6.2 Write property test for input normalization consistency
    - **Property 1: Input Normalization Consistency**
    - **Validates: Requirements 2.2**
  
  - [ ]* 6.3 Write property test for intent detection robustness
    - **Property 2: Intent Detection Robustness**
    - **Validates: Requirements 2.3, 2.4, 2.5**
  
  - [ ]* 6.4 Write property test for intent scoring correctness
    - **Property 3: Intent Scoring Correctness**
    - **Validates: Requirements 2.7**
  
  - [ ]* 6.5 Write property test for default intent fallback
    - **Property 4: Default Intent Fallback**
    - **Validates: Requirements 2.8**
  
  - [ ]* 6.6 Write unit tests for intent detection
    - Test each intent with typical questions, test synonym matching, test ambiguous inputs, test empty/invalid inputs, test normalization edge cases
    - _Requirements: 10.1_

- [x] 7. Implement response formatting service
  - [x] 7.1 Create services/response_service.py with ResponseService class
    - Implement format_response(category: str, data: Dict) -> QuestionResponse
    - Implement ensure_complete_response(response: QuestionResponse) -> QuestionResponse
    - Handle missing fields with defaults: empty strings for text, empty arrays for lists
    - Ensure beginner-friendly language and actionable next steps
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 12.1, 12.2, 12.3, 12.4_
  
  - [ ]* 7.2 Write unit tests for response formatting
    - Test complete response structure, test missing field handling, test data type validation
    - _Requirements: 10.2_

- [x] 8. Implement Google Sheets integration service
  - [x] 8.1 Create services/sheets_service.py with SheetsService class
    - Implement __init__(config: Settings) to store configuration
    - Implement initialize() -> bool for client initialization based on access mode (public, service_account, auto)
    - Implement validate_sheet_structure(worksheet) -> bool to check required columns
    - Implement parse_row(row: List[str]) -> Optional[Dict] to parse single row with pipe-separated arrays
    - Implement load_data() -> Dict[str, Dict] to load and parse all sheet data
    - Handle all exceptions gracefully, log errors without exposing credentials, return empty dict on failure
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_
  
  - [ ]* 8.2 Write property test for sheet data parsing structure
    - **Property 5: Sheet Data Parsing Structure**
    - **Validates: Requirements 3.5**
  
  - [ ]* 8.3 Write property test for column validation correctness
    - **Property 6: Column Validation Correctness**
    - **Validates: Requirements 3.6**
  
  - [ ]* 8.4 Write property test for row validation correctness
    - **Property 7: Row Validation Correctness**
    - **Validates: Requirements 3.7**
  
  - [ ]* 8.5 Write unit tests for sheets service with mocked gspread
    - Test public access mode, test service account mode, test auto mode selection, test connection failures, test malformed data handling, test row validation
    - _Requirements: 10.5_

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement startup orchestration service
  - [x] 10.1 Create services/startup_service.py with StartupService class
    - Implement _load_configuration() -> Settings
    - Implement _initialize_logging(config: Settings)
    - Implement _attempt_sheets_load() -> Optional[Dict] with best-effort Sheets preload
    - Implement _load_fallback_data() -> Dict
    - Implement _populate_cache(data: Dict)
    - Implement initialize_application() -> dict returning startup summary with mode, sheets_loaded, cache_size
    - Log startup mode (sheets/fallback), log Sheets success/failure, never fail startup
    - _Requirements: 3.3, 3.4, 6.1, 6.6, 14.4, 14.5, 14.6, 14.7, 15.1, 15.2_
  
  - [ ]* 10.2 Write integration tests for startup flow
    - Test startup with Sheets available, test startup with Sheets unavailable, test startup with invalid credentials, test cache population, test mode detection
    - _Requirements: 10.7_

- [x] 11. Implement API layer and endpoints
  - [x] 11.1 Create main.py with FastAPI application
    - Initialize FastAPI app with title, version, description
    - Call startup_service.initialize_application() on startup event
    - Include API router from api/routes.py
    - Configure CORS if needed
    - _Requirements: 1.1, 11.6_
  
  - [x] 11.2 Create api/routes.py with API endpoints
    - Implement GET / health check endpoint returning HealthResponse with status and mode
    - Implement POST /ask endpoint accepting QuestionRequest, calling intent detection, cache lookup, response formatting, returning QuestionResponse
    - Implement GET /categories endpoint returning CategoriesResponse with all 8 intent categories
    - Add error handling for invalid JSON (HTTP 422), add global exception handler for uncaught errors
    - Target <500ms response time for cached requests
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_
  
  - [ ]* 11.3 Write property test for system response validity
    - **Property 12: System Response Validity**
    - **Validates: Requirements 6.3**
  
  - [ ]* 11.4 Write property test for error message descriptiveness
    - **Property 13: Error Message Descriptiveness**
    - **Validates: Requirements 6.9**
  
  - [ ]* 11.5 Write integration tests for API endpoints
    - Test /ask with valid questions for all intents, test /ask with invalid inputs, test /categories endpoint, test / health check, test error responses, test response times
    - _Requirements: 10.7_

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Create comprehensive test suite
  - [x] 13.1 Create tests/conftest.py with pytest fixtures
    - Create fixtures for test cache, test config, sample sheets data, sample requests
    - Configure pytest-asyncio for async tests
    - _Requirements: 10.8_
  
  - [x] 13.2 Create tests/fixtures/sample_sheets_data.py with test data
    - Define sample valid sheet data for testing
    - Define sample invalid sheet data for error testing
    - _Requirements: 10.8_
  
  - [x] 13.3 Create tests/fixtures/sample_requests.py with test requests
    - Define sample valid questions for each intent
    - Define sample invalid requests for error testing
    - _Requirements: 10.8_
  
  - [ ]* 13.4 Create tests/unit/test_properties.py with all property-based tests
    - Consolidate all 18 property-based tests using Hypothesis
    - Configure 100 iterations per property test
    - Test Properties 1-18 as defined in design document
    - _Requirements: 10.8_
  
  - [ ]* 13.5 Write integration test for end-to-end flow
    - Test complete request flow from API to response with Sheets mode
    - Test complete request flow with fallback mode
    - Test graceful degradation scenarios
    - _Requirements: 10.4, 10.9_
  
  - [ ]* 13.6 Write error scenario tests
    - Test all failure modes: Sheets API failure, cache miss, network timeout, malformed data, invalid credentials
    - Test fallback behavior for each failure mode
    - Test error logging without credential exposure
    - _Requirements: 10.5_
  
  - [x] 13.7 Run full test suite with coverage reporting
    - Execute pytest with coverage: pytest tests/ --cov=app --cov-report=html --cov-report=term
    - Verify 80%+ code coverage target achieved
    - Verify all tests passing
    - _Requirements: 10.8_

- [x] 14. Create deployment configuration
  - [x] 14.1 Create Dockerfile with multi-stage build
    - Stage 1: Build stage with python:3.11-slim, install dependencies from requirements.txt
    - Stage 2: Runtime stage copying dependencies and app code, expose port 8080
    - Set CMD to run uvicorn app.main:app --host 0.0.0.0 --port 8080
    - Optimize for minimal image size (<100MB)
    - _Requirements: 11.1_
  
  - [x] 14.2 Create .dockerignore file
    - Exclude venv/, __pycache__/, .env, *.pyc, .git/, tests/, .coverage, htmlcov/, .pytest_cache/
    - _Requirements: 11.1_
  
  - [x] 14.3 Create README.md with comprehensive documentation
    - Add project overview and features
    - Add local development setup instructions
    - Add environment variable configuration reference
    - Add deployment instructions for Google Cloud Run
    - Add API endpoint documentation with examples
    - Add testing instructions
    - Add troubleshooting section
    - _Requirements: 11.3_
  
  - [x] 14.4 Test Docker build and run locally
    - Build Docker image: docker build -t votepath-ai-backend .
    - Run container locally: docker run -p 8080:8080 votepath-ai-backend
    - Test health check endpoint: curl http://localhost:8080/
    - Test /ask endpoint with sample question
    - Verify fallback mode works without credentials
    - _Requirements: 11.1_

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Final integration and validation
  - [x] 16.1 Verify all 15 requirements are satisfied
    - Review requirements document and confirm each acceptance criterion is met
    - Document any deviations or limitations
    - _Requirements: All_
  
  - [x] 16.2 Verify all 18 correctness properties are tested
    - Confirm all property-based tests are implemented and passing
    - Review property test statistics from Hypothesis
    - _Requirements: 10.8_
  
  - [x] 16.3 Run performance validation
    - Test response times for all endpoints
    - Verify <500ms target for cached requests
    - Verify <10 second startup time
    - Test memory usage under load (<256MB target)
    - _Requirements: 8.3, 8.4, 8.5_
  
  - [x] 16.4 Run security review
    - Verify no credentials in repository
    - Verify credential redaction in logs
    - Verify input sanitization working
    - Verify HTTPS enforcement (Cloud Run default)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 16.5 Prepare deployment documentation
    - Document environment variables for Cloud Run
    - Document secrets management with Google Secret Manager
    - Document deployment steps
    - Document monitoring and logging setup
    - _Requirements: 11.3, 11.4_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and allow for user feedback
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows and component interactions
- Target 80%+ code coverage across all critical paths
- All code will be implemented in Python 3.11+ using FastAPI framework
- The system prioritizes reliability and graceful degradation over feature completeness
