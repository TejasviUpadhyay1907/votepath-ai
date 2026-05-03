"""Application-wide constants and configuration values

This module centralizes all magic numbers and strings used throughout the application.
Extracting constants improves:
- Maintainability: Change values in one place
- Readability: Named constants are self-documenting
- Consistency: Same values used everywhere
- Testability: Easy to override for testing

Constant categories:
- Rate Limiting: Request limits and time windows
- Validation: Input length limits and requirements
- Timeouts: External service timeout values
- Defaults: Fallback values for configuration
- Categories: Required election information categories

Usage:
    from app.core.constants import MAX_QUESTION_LENGTH, RATE_LIMIT_REQUESTS

    if len(question) > MAX_QUESTION_LENGTH:
        raise ValueError(f"Question too long (max {MAX_QUESTION_LENGTH})")
"""

# Rate Limiting
RATE_LIMIT_REQUESTS = 100  # Maximum requests per window
RATE_LIMIT_WINDOW = 60  # Time window in seconds

# Validation
MAX_QUESTION_LENGTH = 500  # Maximum characters in a question
MIN_QUESTION_LENGTH = 1  # Minimum characters in a question
MIN_ROW_COLUMNS = 7  # Minimum columns required in a sheet row

# Required Categories
REQUIRED_CATEGORIES_COUNT = 8  # Number of required election categories
REQUIRED_CATEGORIES = [
    "first_time_voter",
    "registration",
    "documents",
    "correction",
    "status_check",
    "polling_day",
    "timeline",
    "faq",
]

# Timeouts
GCS_TIMEOUT_SECONDS = 8  # Timeout for GCS requests
SHEETS_TIMEOUT_SECONDS = 10  # Timeout for Sheets requests

# Cache
DEFAULT_CACHE_ENABLED = True
DEFAULT_RESPONSE_TIMEOUT_MS = 500

# Logging
LOG_TRUNCATE_LENGTH = 60  # Characters to show in log messages

# HTTP
DEFAULT_USER_AGENT = "VotePath-AI/1.0"

# Application
APP_NAME = "VotePath AI Backend"
APP_VERSION = "1.0.0"
DEFAULT_PORT = 8080
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENVIRONMENT = "production"

# CORS
DEFAULT_CORS_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Access Modes
VALID_ACCESS_MODES = ("auto", "public", "service_account")
VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

# Port Range
MIN_PORT = 1
MAX_PORT = 65535
