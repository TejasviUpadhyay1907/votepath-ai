"""Google Cloud Logging integration service

This module integrates Google Cloud Logging for structured log management.
Logs are sent to Cloud Logging for centralized monitoring and analysis.

Features:
- Structured logging to Cloud Logging
- Automatic log level mapping
- Request context tracking
- Error tracking and alerting
- Production-ready logging

Why Cloud Logging?
- Centralized log management across all Cloud Run instances
- Advanced filtering and search capabilities
- Integration with Cloud Monitoring for alerts
- Long-term log retention and analysis
- No local disk space usage
"""

import logging
import os
from typing import Optional

# Cloud Logging is optional - gracefully degrade if not available
try:
    from google.cloud import logging as cloud_logging
    CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    CLOUD_LOGGING_AVAILABLE = False

logger = logging.getLogger(__name__)


class CloudLoggingService:
    """Service for integrating with Google Cloud Logging"""

    def __init__(self):
        """Initialize Cloud Logging client"""
        self.client: Optional[cloud_logging.Client] = None
        self.enabled = False

    def initialize(self) -> bool:
        """
        Initialize Cloud Logging integration.

        Returns:
            bool: True if successfully initialized, False otherwise
        """
        # Only enable in production (Cloud Run environment)
        # WHY: Local development should use console logging for easier debugging
        if not os.getenv("K_SERVICE"):  # K_SERVICE is set by Cloud Run
            logger.info("Cloud Logging disabled (not running on Cloud Run)")
            return False

        if not CLOUD_LOGGING_AVAILABLE:
            logger.warning("google-cloud-logging not installed, skipping Cloud Logging")
            return False

        try:
            # Initialize Cloud Logging client
            # WHY: Client automatically detects project ID from Cloud Run environment
            self.client = cloud_logging.Client()

            # Setup logging integration
            # WHY: This redirects Python logging to Cloud Logging automatically
            self.client.setup_logging()

            self.enabled = True
            logger.info("Cloud Logging initialized successfully")
            return True

        except Exception as exc:
            # Graceful degradation - continue with console logging
            # WHY: Application should never fail due to logging issues
            logger.warning("Failed to initialize Cloud Logging: %s", exc)
            return False

    def log_structured(
        self,
        message: str,
        severity: str = "INFO",
        **kwargs
    ) -> None:
        """
        Log a structured message to Cloud Logging.

        Args:
            message: Log message
            severity: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            **kwargs: Additional structured data to include in log
        """
        if not self.enabled or not self.client:
            # Fallback to standard logging
            getattr(logger, severity.lower(), logger.info)(message)
            return

        try:
            # Get the default logger
            # WHY: Uses 'python' logger which is standard for Python apps
            cloud_logger = self.client.logger("python")

            # Log with structured data
            # WHY: Structured logs are easier to query and analyze
            cloud_logger.log_struct(
                {
                    "message": message,
                    "severity": severity,
                    **kwargs
                },
                severity=severity
            )
        except Exception as exc:
            # Fallback to standard logging on error
            logger.warning("Failed to log to Cloud Logging: %s", exc)
            getattr(logger, severity.lower(), logger.info)(message)

    def is_enabled(self) -> bool:
        """
        Check if Cloud Logging is enabled.

        Returns:
            bool: True if Cloud Logging is active
        """
        return self.enabled


# Global instance
_cloud_logging_service: Optional[CloudLoggingService] = None


def get_cloud_logging_service() -> CloudLoggingService:
    """
    Get global Cloud Logging service instance (singleton pattern).

    Returns:
        CloudLoggingService: Global Cloud Logging service instance
    """
    global _cloud_logging_service
    if _cloud_logging_service is None:
        _cloud_logging_service = CloudLoggingService()
    return _cloud_logging_service
