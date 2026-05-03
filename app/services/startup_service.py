"""Startup orchestration service.

This module manages the application startup sequence, implementing a resilient
data loading strategy with automatic fallback:

Data source priority:
  1. Google Sheets  (primary) - Live, editable content for non-technical users
  2. Google Cloud Storage  (secondary) - Reliable backup when Sheets unavailable
  3. Local fallback dataset  (always available) - Ensures app never fails to start

Key features:
- Automatic fallback chain: Tries each source in order until one succeeds
- Health checking: Verifies GCS availability even when Sheets is active
- Graceful degradation: Always provides basic functionality, even if all external sources fail
- Transparent reporting: Tracks which source is active for debugging and monitoring
- Google Cloud integration: Initializes Cloud Logging, Monitoring, and Firestore

GCS is always health-checked during startup when configured,
even if Sheets is the active source, so /debug/source can
truthfully report gcs_available = true.

Example startup flow:
    1. Load configuration from environment
    2. Initialize logging system
    3. Initialize Google Cloud services (Logging, Monitoring, Firestore)
    4. Try Google Sheets → Success? Use it and health-check GCS
    5. Sheets failed? Try GCS → Success? Use it
    6. GCS failed? Use local fallback (always succeeds)
    7. Populate cache with loaded data
    8. Report startup summary
"""

import logging
from typing import Dict, Optional
from app.core.config import Settings, get_settings
from app.core.logging_config import setup_logging
from app.services.sheets_service import SheetsService
from app.services.gcs_service import GCSService
from app.services.fallback_service import FallbackService
from app.services.cloud_logging_service import get_cloud_logging_service
from app.services.cloud_monitoring_service import get_cloud_monitoring_service
from app.services.firestore_service import get_firestore_service
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
        self.cloud_logging_enabled: bool = False
        self.cloud_monitoring_enabled: bool = False
        self.firestore_enabled: bool = False

    def _load_configuration(self) -> Settings:
        config = get_settings()
        if not config.validate_config():
            logger.warning("Configuration validation failed, using defaults")
        return config

    def _initialize_logging(self, config: Settings) -> None:
        setup_logging(config.LOG_LEVEL)
        logger.info("Logging initialized at %s level", config.LOG_LEVEL)

    def _initialize_google_cloud_services(self) -> None:
        """
        Initialize Google Cloud services (Logging, Monitoring, Firestore).

        WHY: These services enhance production monitoring and analytics.
        They're optional and gracefully degrade if unavailable.
        """
        # Initialize Cloud Logging
        # WHY: Centralized log management for all Cloud Run instances
        try:
            cloud_logging = get_cloud_logging_service()
            self.cloud_logging_enabled = cloud_logging.initialize()
            if self.cloud_logging_enabled:
                logger.info("Google Cloud Logging enabled")
        except Exception as exc:
            logger.warning("Cloud Logging initialization failed: %s", exc)

        # Initialize Cloud Monitoring
        # WHY: Custom metrics for response time, intent distribution, etc.
        try:
            cloud_monitoring = get_cloud_monitoring_service()
            self.cloud_monitoring_enabled = cloud_monitoring.initialize()
            if self.cloud_monitoring_enabled:
                logger.info("Google Cloud Monitoring enabled")
        except Exception as exc:
            logger.warning("Cloud Monitoring initialization failed: %s", exc)

        # Initialize Firestore
        # WHY: Query logging for analytics and improvement
        try:
            firestore = get_firestore_service()
            self.firestore_enabled = firestore.initialize()
            if self.firestore_enabled:
                logger.info("Google Cloud Firestore enabled")
        except Exception as exc:
            logger.warning("Firestore initialization failed: %s", exc)

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
        # TIER 1: Google Sheets (Primary Source)
        # WHY: Sheets allows non-technical users to update content in real-time
        # without code deployments. This is the preferred source for live data.
        sheets_data = self._attempt_sheets_load()
        if sheets_data:
            self.mode = "sheets"
            self.sheets_loaded = True
            logger.info("Operating in SHEETS mode")

            # PARALLEL HEALTH CHECK: Verify GCS availability even when Sheets succeeds
            # WHY: The /debug/source endpoint needs to report accurate GCS status
            # for monitoring and debugging. This doesn't affect the active data source.
            if self.config.GCS_CONTENT_URL:
                self._verify_gcs_availability()

            return sheets_data

        # TIER 2: Google Cloud Storage (Secondary Source)
        # WHY: GCS provides a reliable backup when Sheets is unavailable
        # (e.g., API quota exceeded, network issues, permission problems)
        gcs_data = self._attempt_gcs_load()
        if gcs_data:
            self.mode = "gcs"
            logger.info("Operating in GCS mode")
            return gcs_data

        # TIER 3: Local Fallback (Always Available)
        # WHY: Ensures the application never fails to start, even if all
        # external services are down. Provides basic election information.
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
            "cloud_logging_enabled": self.cloud_logging_enabled,
            "cloud_monitoring_enabled": self.cloud_monitoring_enabled,
            "firestore_enabled": self.firestore_enabled,
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
            # STEP 1: Load and validate configuration from environment
            # WHY: Configuration must be loaded first as all services depend on it
            self.config = self._load_configuration()
            logger.info(
                "Starting %s v%s",
                self.config.APP_NAME,
                self.config.APP_VERSION
            )

            # STEP 2: Initialize logging system
            # WHY: Logging must be ready before data loading so we can track issues
            self._initialize_logging(self.config)

            # STEP 3: Initialize Google Cloud services
            # WHY: Enable Cloud Logging, Monitoring, and Firestore for production
            self._initialize_google_cloud_services()

            # STEP 4: Load data with automatic fallback chain
            # WHY: This implements the resilience strategy - try best source first,
            # fall back to alternatives if needed, never fail to start
            data = self._load_data_with_fallback()

            # STEP 5: Populate in-memory cache for fast response times
            # WHY: Cache eliminates repeated data lookups and ensures consistent
            # sub-500ms response times required by the performance criteria
            self._populate_cache(data)

            # STEP 6: Build and log startup summary
            summary = self._build_summary()
            logger.info("Startup complete: %s", summary)
            return summary

        except Exception as exc:
            # CRITICAL ERROR HANDLING: If startup fails, attempt graceful degradation
            # WHY: Application should never crash on startup - always provide
            # at least basic functionality using fallback data
            logger.error("Critical error during startup: %s", exc)
            try:
                return self._handle_startup_failure()
            except Exception as fatal:
                # FATAL ERROR: Even fallback failed - this should never happen
                # but we log it clearly for debugging
                logger.critical("Fatal startup error: %s", fatal)
                raise


_startup_service: Optional[StartupService] = None


def get_startup_service() -> StartupService:
    """Get global startup service singleton."""
    global _startup_service
    if _startup_service is None:
        _startup_service = StartupService()
    return _startup_service
