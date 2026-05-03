"""Configuration management for VotePath AI Backend"""

from functools import lru_cache
from typing import Optional, List

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


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
    APP_NAME: str = "VotePath AI Backend"
    APP_VERSION: str = "1.0.0"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"  # "production", "development", "test"

    # CORS — comma-separated allowed origins (empty = safe local defaults)
    FRONTEND_ORIGINS: str = ""

    # Google Cloud Storage — public-read content URL (optional)
    GCS_CONTENT_URL: Optional[str] = None

    # Performance Configuration
    CACHE_ENABLED: bool = True
    RESPONSE_TIMEOUT_MS: int = 500

    # ── helpers ──────────────────────────────────────────────────

    def get_cors_origins(self) -> List[str]:
        """
        Return the list of allowed CORS origins.

        If FRONTEND_ORIGINS is set, parse it as comma-separated values.
        Otherwise return safe local development defaults.
        """
        if self.FRONTEND_ORIGINS.strip():
            return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]
        return [
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

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
        if self.ACCESS_MODE not in ("auto", "public", "service_account"):
            return False
        if self.LOG_LEVEL.upper() not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            return False
        if not 1 <= self.PORT <= 65535:
            return False
        return True

    def determine_access_mode(self) -> str:
        """
        Determine the best Google Sheets access mode based on configuration.

        Returns:
            str: "public", "service_account", or "fallback"
        """
        if self.ACCESS_MODE == "public":
            return "public" if self.SHEET_ID else "fallback"

        if self.ACCESS_MODE == "service_account":
            return "service_account" if (self.SHEET_ID and self.CREDENTIALS_PATH) else "fallback"

        # auto — prefer public (simpler), then service account, then fallback
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
