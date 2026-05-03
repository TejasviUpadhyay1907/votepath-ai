"""Google Cloud Monitoring integration service

This module integrates Google Cloud Monitoring for custom metrics tracking.
Metrics are sent to Cloud Monitoring for dashboards and alerting.

Features:
- Custom metric recording (response time, intent distribution, cache hits)
- Automatic metric aggregation
- Integration with Cloud Monitoring dashboards
- Alert configuration support
- Production-ready monitoring

Why Cloud Monitoring?
- Real-time performance tracking
- Custom dashboards for business metrics
- Alerting on anomalies
- Historical trend analysis
- Integration with Cloud Logging
"""

import logging
import os
import time
from typing import Optional, Dict

# Cloud Monitoring is optional - gracefully degrade if not available
try:
    from google.cloud import monitoring_v3
    CLOUD_MONITORING_AVAILABLE = True
except ImportError:
    CLOUD_MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)


class CloudMonitoringService:
    """Service for integrating with Google Cloud Monitoring"""

    def __init__(self):
        """Initialize Cloud Monitoring client"""
        self.client: Optional[monitoring_v3.MetricServiceClient] = None
        self.project_id: Optional[str] = None
        self.enabled = False

    def initialize(self) -> bool:
        """
        Initialize Cloud Monitoring integration.

        Returns:
            bool: True if successfully initialized, False otherwise
        """
        # Only enable in production (Cloud Run environment)
        # WHY: Local development doesn't need metric tracking
        if not os.getenv("K_SERVICE"):
            logger.info("Cloud Monitoring disabled (not running on Cloud Run)")
            return False

        if not CLOUD_MONITORING_AVAILABLE:
            logger.warning("google-cloud-monitoring not installed, skipping")
            return False

        try:
            # Get project ID from environment
            # WHY: Cloud Run sets GOOGLE_CLOUD_PROJECT automatically
            self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")

            if not self.project_id:
                logger.warning("No project ID found, Cloud Monitoring disabled")
                return False

            # Initialize Monitoring client
            self.client = monitoring_v3.MetricServiceClient()

            self.enabled = True
            logger.info("Cloud Monitoring initialized for project: %s", self.project_id)
            return True

        except Exception as exc:
            # Graceful degradation - continue without monitoring
            logger.warning("Failed to initialize Cloud Monitoring: %s", exc)
            return False

    def record_response_time(self, duration_ms: float, intent: str) -> None:
        """
        Record API response time metric.

        Args:
            duration_ms: Response time in milliseconds
            intent: Detected intent category
        """
        if not self.enabled:
            return

        try:
            self._write_metric(
                "votepath/response_time",
                duration_ms,
                {"intent": intent}
            )
        except Exception as exc:
            # Don't fail requests due to monitoring issues
            logger.debug("Failed to record response time: %s", exc)

    def record_intent_detection(self, intent: str, confidence: str) -> None:
        """
        Record intent detection metric.

        Args:
            intent: Detected intent category
            confidence: Confidence level (high/medium/low)
        """
        if not self.enabled:
            return

        try:
            self._write_metric(
                "votepath/intent_detection",
                1,  # Counter metric
                {"intent": intent, "confidence": confidence}
            )
        except Exception as exc:
            logger.debug("Failed to record intent detection: %s", exc)

    def record_cache_hit(self, hit: bool) -> None:
        """
        Record cache hit/miss metric.

        Args:
            hit: True if cache hit, False if cache miss
        """
        if not self.enabled:
            return

        try:
            self._write_metric(
                "votepath/cache_hits",
                1,
                {"hit": "true" if hit else "false"}
            )
        except Exception as exc:
            logger.debug("Failed to record cache hit: %s", exc)

    def record_data_source(self, source: str) -> None:
        """
        Record active data source metric.

        Args:
            source: Data source (sheets/gcs/fallback)
        """
        if not self.enabled:
            return

        try:
            self._write_metric(
                "votepath/data_source",
                1,
                {"source": source}
            )
        except Exception as exc:
            logger.debug("Failed to record data source: %s", exc)

    def _write_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Write a custom metric to Cloud Monitoring.

        Args:
            metric_type: Metric type identifier
            value: Metric value
            labels: Optional metric labels
        """
        if not self.enabled or not self.client or not self.project_id:
            return

        # Build metric descriptor path
        # WHY: Custom metrics use custom.googleapis.com domain
        project_name = f"projects/{self.project_id}"
        metric_type_full = f"custom.googleapis.com/{metric_type}"

        # Create time series data
        # WHY: Time series format required by Cloud Monitoring API
        series = monitoring_v3.TimeSeries()
        series.metric.type = metric_type_full

        # Add labels if provided
        if labels:
            for key, val in labels.items():
                series.metric.labels[key] = str(val)

        # Set resource type to Cloud Run service
        # WHY: Associates metrics with the Cloud Run service
        series.resource.type = "cloud_run_revision"
        series.resource.labels["project_id"] = self.project_id
        series.resource.labels["service_name"] = os.getenv("K_SERVICE", "votepath-ai-backend")
        series.resource.labels["revision_name"] = os.getenv("K_REVISION", "unknown")
        series.resource.labels["location"] = os.getenv("CLOUD_RUN_REGION", "asia-south1")

        # Create data point
        # WHY: Each metric needs a timestamp and value
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)

        interval = monitoring_v3.TimeInterval(
            {"end_time": {"seconds": seconds, "nanos": nanos}}
        )

        point = monitoring_v3.Point(
            {
                "interval": interval,
                "value": {"double_value": value},
            }
        )

        series.points = [point]

        # Write to Cloud Monitoring
        self.client.create_time_series(
            name=project_name,
            time_series=[series]
        )

    def is_enabled(self) -> bool:
        """
        Check if Cloud Monitoring is enabled.

        Returns:
            bool: True if Cloud Monitoring is active
        """
        return self.enabled


# Global instance
_cloud_monitoring_service: Optional[CloudMonitoringService] = None


def get_cloud_monitoring_service() -> CloudMonitoringService:
    """
    Get global Cloud Monitoring service instance (singleton pattern).

    Returns:
        CloudMonitoringService: Global Cloud Monitoring service instance
    """
    global _cloud_monitoring_service
    if _cloud_monitoring_service is None:
        _cloud_monitoring_service = CloudMonitoringService()
    return _cloud_monitoring_service
