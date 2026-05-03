"""Google BigQuery integration service

This module integrates Google BigQuery for query analytics and insights.
BigQuery provides powerful data analytics capabilities with a generous free tier.

Features:
- Query analytics storage
- Intent distribution analysis
- Performance metrics tracking
- User behavior insights
- SQL-based analytics

Why BigQuery?
- 1TB free queries per month
- Serverless data warehouse
- Real-time analytics
- Integration with other Google Cloud services
- No infrastructure management

Free Tier:
- 10GB storage free
- 1TB queries free per month
- Perfect for analytics workload
"""

import logging
import os
from typing import Optional, Dict
from datetime import datetime, timezone

# BigQuery is optional - gracefully degrade if not available
try:
    from google.cloud import bigquery
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False

logger = logging.getLogger(__name__)


class BigQueryService:
    """Service for integrating with Google BigQuery"""

    def __init__(self):
        """Initialize BigQuery client"""
        self.client: Optional[bigquery.Client] = None
        self.dataset_id = "votepath_analytics"
        self.table_id = "query_logs"
        self.enabled = False

    def initialize(self) -> bool:
        """
        Initialize BigQuery integration.

        Returns:
            bool: True if successfully initialized, False otherwise
        """
        # Only enable in production (Cloud Run environment)
        if not os.getenv("K_SERVICE"):
            logger.info("BigQuery disabled (not running on Cloud Run)")
            return False

        if not BIGQUERY_AVAILABLE:
            logger.warning("google-cloud-bigquery not installed, skipping")
            return False

        try:
            # Initialize BigQuery client
            self.client = bigquery.Client()

            # Ensure dataset and table exist
            self._ensure_dataset_exists()
            self._ensure_table_exists()

            self.enabled = True
            logger.info("BigQuery initialized successfully")
            return True

        except Exception as exc:
            # Graceful degradation - continue without BigQuery
            logger.warning("Failed to initialize BigQuery: %s", exc)
            return False

    def _ensure_dataset_exists(self) -> None:
        """Create dataset if it doesn't exist"""
        if not self.client:
            return

        try:
            dataset_ref = f"{self.client.project}.{self.dataset_id}"
            self.client.get_dataset(dataset_ref)
        except Exception:
            # Dataset doesn't exist, create it
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            self.client.create_dataset(dataset, exists_ok=True)
            logger.info("Created BigQuery dataset: %s", self.dataset_id)

    def _ensure_table_exists(self) -> None:
        """Create table if it doesn't exist"""
        if not self.client:
            return

        try:
            table_ref = f"{self.client.project}.{self.dataset_id}.{self.table_id}"
            self.client.get_table(table_ref)
        except Exception:
            # Table doesn't exist, create it
            schema = [
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("question", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("intent", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("confidence", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("matched_keywords", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("response_time_ms", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("system_mode", "STRING", mode="REQUIRED"),
            ]

            table = bigquery.Table(table_ref, schema=schema)
            self.client.create_table(table, exists_ok=True)
            logger.info("Created BigQuery table: %s", self.table_id)

    def log_query(
        self,
        question: str,
        intent: str,
        confidence: str,
        matched_keywords: int,
        response_time_ms: float,
        system_mode: str
    ) -> None:
        """
        Log a query to BigQuery for analytics.

        Args:
            question: User's question
            intent: Detected intent
            confidence: Confidence level
            matched_keywords: Number of matched keywords
            response_time_ms: Response time in milliseconds
            system_mode: Active data source mode
        """
        if not self.enabled or not self.client:
            return

        try:
            table_ref = f"{self.client.project}.{self.dataset_id}.{self.table_id}"

            rows_to_insert = [{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "question": question[:500],  # Truncate for storage
                "intent": intent,
                "confidence": confidence,
                "matched_keywords": matched_keywords,
                "response_time_ms": response_time_ms,
                "system_mode": system_mode,
            }]

            errors = self.client.insert_rows_json(table_ref, rows_to_insert)

            if errors:
                logger.warning("BigQuery insert errors: %s", errors)

        except Exception as exc:
            # Don't fail requests due to analytics issues
            logger.debug("Failed to log query to BigQuery: %s", exc)

    def get_intent_distribution(self, limit: int = 1000) -> Dict[str, int]:
        """
        Get intent distribution from recent queries.

        Args:
            limit: Maximum number of recent queries to analyze

        Returns:
            Dict mapping intent to count
        """
        if not self.enabled or not self.client:
            return {}

        try:
            query = f"""
                SELECT intent, COUNT(*) as count
                FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
                WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
                GROUP BY intent
                ORDER BY count DESC
                LIMIT {limit}
            """

            results = self.client.query(query).result()
            return {row.intent: row.count for row in results}

        except Exception as exc:
            logger.warning("Failed to get intent distribution: %s", exc)
            return {}

    def get_average_response_time(self) -> float:
        """
        Get average response time from recent queries.

        Returns:
            float: Average response time in milliseconds
        """
        if not self.enabled or not self.client:
            return 0.0

        try:
            query = f"""
                SELECT AVG(response_time_ms) as avg_time
                FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
                WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
            """

            results = self.client.query(query).result()
            for row in results:
                return float(row.avg_time) if row.avg_time else 0.0

            return 0.0

        except Exception as exc:
            logger.warning("Failed to get average response time: %s", exc)
            return 0.0

    def is_enabled(self) -> bool:
        """
        Check if BigQuery is enabled.

        Returns:
            bool: True if BigQuery is active
        """
        return self.enabled


# Global instance
_bigquery_service: Optional[BigQueryService] = None


def get_bigquery_service() -> BigQueryService:
    """
    Get global BigQuery service instance (singleton pattern).

    Returns:
        BigQueryService: Global BigQuery service instance
    """
    global _bigquery_service
    if _bigquery_service is None:
        _bigquery_service = BigQueryService()
    return _bigquery_service
