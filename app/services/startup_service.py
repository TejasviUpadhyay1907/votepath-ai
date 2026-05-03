"""Startup orchestration service.

Data source priority:
  1. Google Sheets  (primary)
  2. Google Cloud Storage  (secondary)
  3. Local fallback dataset  (always available)

GCS is always health-checked during startup when configured,
even if Sheets is the active source, so /debug/source can
truthfully report gcs_available = true.
"""

import logging
from typing import Dict, Optional
from app.core.config import Settings, get_settings
from app.core.logging_config import setup_logging
from app.services.sheets_service import SheetsService
from app.services.gcs_service import GCSService
from app.services.fallback_service import FallbackService
from app.utils.cache import get_cache

logger = logging.getLogger(__name__)


class StartupService:
    """Orchestrates the application startup sequence."""

    def __init__(self):
        self.config: Optional[Settings] = None
        self.mode: str = "fallback"
        self.sheets_loaded: bool = False
        self.gcs_loaded: bool = False
        self.gcs_available: bool = False   # True if GCS URL is reachable and valid
        self.sheets_repaired_rows: int = 0  # Track auto-repaired rows

    def _load_configuration(self) -> Settings:
        config = get_settings()
        if not config.validate_config():
            logger.warning("Configuration validation failed, using defaults")
        return config

    def _initialize_logging(self, config: Settings) -> None:
        setup_logging(config.LOG_LEVEL)
        logger.info("Logging initialized at %s level", config.LOG_LEVEL)

    def _attempt_sheets_load(self) -> Optional[Dict]:
        """Best-effort Google Sheets load. Returns data dict or None."""
        try:
            logger.info("Attempting to load data from Google Sheets...")
            sheets_service = SheetsService(self.config)
            if not sheets_service.initialize():
                logger.info("Sheets initialization failed, will try GCS")
                return None
            data = sheets_service.load_data()
            if not data:
                logger.warning("Sheets load returned empty data, will try GCS")
                return None
            # Track repair count
            self.sheets_repaired_rows = sheets_service._repaired_rows
            logger.info("Successfully loaded %d categories from Google Sheets", len(data))
            return data
        except Exception as exc:
            logger.warning("Exception during Sheets load: %s", exc)
            return None

    def _verify_gcs_availability(self) -> Optional[Dict]:
        """
        Fetch and validate GCS content regardless of whether Sheets is active.

        When Sheets is the active source this method is called to health-check
        GCS so /debug/source can report gcs_available = true.

        Returns:
            Parsed data dict if GCS is reachable and valid, else None.
        """
        if not self.config.GCS_CONTENT_URL:
            return None
        try:
            logger.info("Verifying Google Cloud Storage availability...")
            gcs_service = GCSService(self.config.GCS_CONTENT_URL)
            data = gcs_service.load_data()
            if data:
                self.gcs_available = True
                logger.info("GCS health-check passed — %d categories available", len(data))
            else:
                logger.warning("GCS health-check failed — no valid data returned")
            return data
        except Exception as exc:
            logger.warning("GCS health-check exception: %s", exc)
            return None

    def _attempt_gcs_load(self) -> Optional[Dict]:
        """
        Load GCS as the active content source (used when Sheets fails).
        Also sets gcs_available if successful.
        """
        data = self._verify_gcs_availability()
        if data:
            self.gcs_loaded = True
        return data

    def _load_fallback_data(self) -> Dict:
        """Load bundled local fallback data — always succeeds."""
        try:
            logger.info("Loading local fallback data...")
            fallback_service = FallbackService()
            data = fallback_service.get_fallback_data()
            logger.info("Loaded %d categories from local fallback", len(data))
            return data
        except Exception as exc:
            logger.error("Failed to load fallback data: %s", exc)
            return {
                "faq": {
                    "title": "FAQ",
                    "overview": "Frequently asked questions",
                    "steps": [], "documents": [], "tips": [], "next_action": ""
                }
            }

    def _populate_cache(self, data: Dict) -> None:
        try:
            cache = get_cache()
            cache.populate(data)
            logger.info("Cache populated with %d entries", cache.size())
        except Exception as exc:
            logger.error("Failed to populate cache: %s", exc)

    def _load_data_with_fallback(self) -> Dict:
        """
        Load data from available sources with fallback chain.

        Returns:
            Dict: Loaded data from best available source
        """
        # Tier 1: Google Sheets
        sheets_data = self._attempt_sheets_load()
        if sheets_data:
            self.mode = "sheets"
            self.sheets_loaded = True
            logger.info("Operating in SHEETS mode")

            # Health-check GCS in parallel path
            if self.config.GCS_CONTENT_URL:
                self._verify_gcs_availability()

            return sheets_data

        # Tier 2: Google Cloud Storage
        gcs_data = self._attempt_gcs_load()
        if gcs_data:
            self.mode = "gcs"
            logger.info("Operating in GCS mode")
            return gcs_data

        # Tier 3: Local fallback
        self.mode = "fallback"
        logger.info("Operating in FALLBACK mode")
        return self._load_fallback_data()

    def _build_summary(self) -> dict:
        """Build startup summary dictionary."""
        cache = get_cache()
        return {
            "mode": self.mode,
            "sheets_loaded": self.sheets_loaded,
            "gcs_loaded": self.gcs_loaded,
            "gcs_available": self.gcs_available,
            "cache_size": cache.size(),
            "sheets_repaired_rows": self.sheets_repaired_rows,
        }

    def _handle_startup_failure(self) -> dict:
        """Handle critical startup failure with fallback."""
        self.mode = "fallback"
        self.sheets_loaded = False
        self.gcs_loaded = False
        self.gcs_available = False
        data = self._load_fallback_data()
        self._populate_cache(data)
        return self._build_summary()

    def initialize_application(self) -> dict:
        """
        Execute complete startup sequence.

        Flow:
          1. Try Google Sheets → use as active source if successful
          2. If Sheets succeeds AND GCS is configured → health-check GCS
          3. If Sheets fails → try GCS as active source
          4. If GCS also fails → use local fallback

        Returns:
            dict: Startup summary
        """
        try:
            self.config = self._load_configuration()
            logger.info(
                "Starting %s v%s",
                self.config.APP_NAME,
                self.config.APP_VERSION
            )
            self._initialize_logging(self.config)

            data = self._load_data_with_fallback()
            self._populate_cache(data)

            summary = self._build_summary()
            logger.info("Startup complete: %s", summary)
            return summary

        except Exception as exc:
            logger.error("Critical error during startup: %s", exc)
            try:
                return self._handle_startup_failure()
            except Exception as fatal:
                logger.critical("Fatal startup error: %s", fatal)
                raise


_startup_service: Optional[StartupService] = None


def get_startup_service() -> StartupService:
    """Get global startup service singleton."""
    global _startup_service
    if _startup_service is None:
        _startup_service = StartupService()
    return _startup_service
