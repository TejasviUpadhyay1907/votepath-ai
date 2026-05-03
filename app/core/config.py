"""Configuration management for VotePath AI Backend

This module handles all application configuration using Pydantic Settings.
Configuration is loaded from environment variables with sensible defaults.

Configuration sources (in order of precedence):
1. Environment variables (highest priority)
2. .env file (if present)
3. Default values defined in this module

Key configuration areas:
- Google Sheets: SHEET_ID, WORKSHEET_NAME, ACCESS_MODE, CREDENTIALS_PATH
- Google Cloud Storage: GCS_CONTENT_URL (optional backup)
- Application: PORT, LOG_LEVEL, ENVIRONMENT
- CORS: FRONTEND_ORIGINS (comma-separated list)
- Performance: CACHE_ENABLED, RESPONSE_TIMEOUT_MS

Access modes:
- "auto": Automatically choose best available method (public > service_account > fallback)
- "public": Use public sheet access (requires publicly readable sheet)
- "service_account": Use service account credentials (requires CREDENTIALS_PATH)

Example .env file:
    SHEET_ID=1abc123...
    WORKSHEET_NAME=VotePath_Data
    ACCESS_MODE=auto
    LOG_LEVEL=INFO
    PORT=8080
"""

from functools import lru_cache
from typing import Optional, List

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from app.core.constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_PORT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_ENVIRONMENT,
    DEFAULT_CACHE_ENABLED,
    DEFAULT_RESPONSE_TIMEOUT_MS,
    DEFAULT_CORS_ORIGINS,
    VALID_ACCESS_MODES,
    VALID_LOG_LEVELS,
    MIN_PORT,
    MAX_PORT,
)


class Settings(BaseSettings):
    """Application configuration settings"""

    # Pydantic v2 style — eliminates deprecation warning
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Google Sheets Configuration
    SHEET_ID: Optional[str] = None
    WORKSHEET_NAME: str = Field(default="VotePath_Data", validation_alias="SHEET_NAME")
    ACCESS_MODE: str = "auto"          # "auto", "public", "service_account"
    CREDENTIALS_PATH: Optional[str] = None

    # Application Configuration
    APP_NAME: str = APP_NAME
    APP_VERSION: str = APP_VERSION
    PORT: int = DEFAULT_PORT
    LOG_LEVEL: str = DEFAULT_LOG_LEVEL
    ENVIRONMENT: str = DEFAULT_ENVIRONMENT

    # CORS — comma-separated allowed origins (empty = safe local defaults)
    FRONTEND_ORIGINS: str = ""

    # Google Cloud Storage — public-read content URL (optional)
    GCS_CONTENT_URL: Optional[str] = None

    # Performance Configuration
    CACHE_ENABLED: bool = DEFAULT_CACHE_ENABLED
    RESPONSE_TIMEOUT_MS: int = DEFAULT_RESPONSE_TIMEOUT_MS

    # ── helpers ──────────────────────────────────────────────────

    def get_cors_origins(self) -> List[str]:
        """
        Return the list of allowed CORS origins.

        If FRONTEND_ORIGINS is set, parse it as comma-separated values.
        Otherwise return safe local development defaults.
        """
        # WHY: CORS configuration must be explicit for security. If FRONTEND_ORIGINS
        # is set in environment, use those values. Otherwise, default to safe local
        # development origins (localhost:8080, localhost:3000) for testing.
        if self.FRONTEND_ORIGINS.strip():
            return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]
        return DEFAULT_CORS_ORIGINS

    def is_sheets_configured(self) -> bool:
        """
        Check if Google Sheets is configured.

        Returns:
            bool: True if SHEET_ID is set
        """
        return bool(self.SHEET_ID)

    def is_gcs_configured(self) -> bool:
        """
        Check if Google Cloud Storage is configured.

        Returns:
            bool: True if GCS_CONTENT_URL is set
        """
        return bool(self.GCS_CONTENT_URL)

    def validate_config(self) -> bool:
        """
        Validate configuration settings.

        Returns:
            bool: True if all settings are valid
        """
        if self.ACCESS_MODE not in VALID_ACCESS_MODES:
            return False
        if self.LOG_LEVEL.upper() not in VALID_LOG_LEVELS:
            return False
        if not MIN_PORT <= self.PORT <= MAX_PORT:
            return False
        return True

    def determine_access_mode(self) -> str:
        """
        Determine the best Google Sheets access mode based on configuration.

        Returns:
            str: "public", "service_account", or "fallback"
        """
        # EXPLICIT PUBLIC MODE
        # WHY: User explicitly wants public access (no authentication required)
        # This is simpler but requires the sheet to be publicly readable
        if self.ACCESS_MODE == "public":
            return "public" if self.SHEET_ID else "fallback"

        # EXPLICIT SERVICE ACCOUNT MODE
        # WHY: User explicitly wants service account authentication
        # This is more secure and allows private sheets, but requires credentials
        if self.ACCESS_MODE == "service_account":
            return "service_account" if (self.SHEET_ID and self.CREDENTIALS_PATH) else "fallback"

        # AUTO MODE: Intelligent selection based on available configuration
        # WHY: Prefer public (simpler, no credentials needed) if SHEET_ID is set.
        # Fall back to service account if credentials are also available.
        # This makes deployment easier - just set SHEET_ID for public sheets.
        if self.SHEET_ID:
            return "public"
        if self.SHEET_ID and self.CREDENTIALS_PATH:
            return "service_account"
        return "fallback"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings: Cached settings instance
    """
    return Settings()
