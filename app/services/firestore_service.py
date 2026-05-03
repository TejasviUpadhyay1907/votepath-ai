"""Google Cloud Firestore integration service

This module integrates Google Cloud Firestore for query analytics and logging.
Stores query history for analysis, debugging, and improvement.

Features:
- Query logging for analytics
- Intent distribution tracking
- User behavior analysis
- Performance monitoring
- Production-ready NoSQL database

Why Firestore?
- Serverless NoSQL database
- Real-time data synchronization
- Automatic scaling
- Strong consistency
- Integration with other Google Cloud services
- Free tier: 50K reads, 20K writes per day
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Firestore is optional - gracefully degrade if not available
try:
    from google.cloud.firestore import Client
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False

logger = logging.getLogger(__name__)


class FirestoreService:
    """Service for integrating with Google Cloud Firestore"""

    def __init__(self):
        """Initialize Firestore client"""
        self.db: Optional[Client] = None
        self.enabled = False

    def initialize(self) -> bool:
        """
        Initialize Firestore integration.

        Returns:
            bool: True if successfully initialized, False otherwise
        """
        # Only enable in production (Cloud Run environment)
        # WHY: Local development doesn't need query logging
        if not os.getenv("K_SERVICE"):
            logger.info("Firestore disabled (not running on Cloud Run)")
            return False

        if not FIRESTORE_AVAILABLE:
            logger.warning("google-cloud-firestore not installed, skipping")
            return False

        try:
            # Initialize Firestore client
            # WHY: Client automatically detects project ID from Cloud Run environment
            self.db = Client()

            self.enabled = True
            logger.info("Firestore initialized successfully")
            return True

        except Exception as exc:
            # Graceful degradation - continue without query logging
            # WHY: Application should never fail due to analytics issues
            logger.warning("Failed to initialize Firestore: %s", exc)
            return False

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
        Log a query to Firestore for analytics.

        Args:
            question: User's question
            intent: Detected intent
            confidence: Confidence level
            matched_keywords: Number of matched keywords
            response_time_ms: Response time in milliseconds
            system_mode: Active data source mode
        """
        if not self.enabled or not self.db:
            return

        try:
            # Create query document
            # WHY: Store query data for analytics and improvement
            query_data = {
                "question": question[:200],  # Truncate for storage efficiency
                "intent": intent,
                "confidence": confidence,
                "matched_keywords": matched_keywords,
                "response_time_ms": response_time_ms,
                "system_mode": system_mode,
                "timestamp": datetime.now(timezone.utc),
            }

            # Add to queries collection
            # WHY: Collection-based organization for easy querying
            self.db.collection("queries").add(query_data)

        except Exception as exc:
            # Don't fail requests due to logging issues
            # WHY: Analytics is nice-to-have, not critical
            logger.debug("Failed to log query to Firestore: %s", exc)

    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an error to Firestore for debugging.

        Args:
            error_type: Type of error
            error_message: Error message
            context: Optional context data
        """
        if not self.enabled or not self.db:
            return

        try:
            error_data = {
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
                "timestamp": datetime.now(timezone.utc),
            }

            self.db.collection("errors").add(error_data)

        except Exception as exc:
            logger.debug("Failed to log error to Firestore: %s", exc)

    def get_intent_stats(self, limit: int = 100) -> Dict[str, int]:
        """
        Get intent distribution statistics.

        Args:
            limit: Maximum number of recent queries to analyze

        Returns:
            Dict mapping intent to count
        """
        if not self.enabled or not self.db:
            return {}

        try:
            # Query recent queries
            # WHY: Analyze recent intent distribution for insights
            queries = (
                self.db.collection("queries")
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            # Count intents
            intent_counts: Dict[str, int] = {}
            for query in queries:
                data = query.to_dict()
                intent = data.get("intent", "unknown")
                intent_counts[intent] = intent_counts.get(intent, 0) + 1

            return intent_counts

        except Exception as exc:
            logger.warning("Failed to get intent stats: %s", exc)
            return {}

    def get_average_response_time(self, limit: int = 100) -> float:
        """
        Get average response time from recent queries.

        Args:
            limit: Maximum number of recent queries to analyze

        Returns:
            float: Average response time in milliseconds
        """
        if not self.enabled or not self.db:
            return 0.0

        try:
            queries = (
                self.db.collection("queries")
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            times = []
            for query in queries:
                data = query.to_dict()
                if "response_time_ms" in data:
                    times.append(data["response_time_ms"])

            return sum(times) / len(times) if times else 0.0

        except Exception as exc:
            logger.warning("Failed to get average response time: %s", exc)
            return 0.0

    def is_enabled(self) -> bool:
        """
        Check if Firestore is enabled.

        Returns:
            bool: True if Firestore is active
        """
        return self.enabled


# Global instance
_firestore_service: Optional[FirestoreService] = None


def get_firestore_service() -> FirestoreService:
    """
    Get global Firestore service instance (singleton pattern).

    Returns:
        FirestoreService: Global Firestore service instance
    """
    global _firestore_service
    if _firestore_service is None:
        _firestore_service = FirestoreService()
    return _firestore_service
