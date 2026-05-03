"""Response formatting service

This module handles the transformation of raw data dictionaries into
standardized QuestionResponse objects with proper validation and defaults.

Key responsibilities:
- Type safety: Ensures all fields are correctly typed
- Completeness: Fills missing fields with sensible defaults
- Consistency: Normalizes data from different sources (Sheets, GCS, fallback)
- Robustness: Never returns null/undefined values that could break the frontend

Data cleaning strategy:
- Strings: Strip whitespace, handle None/empty gracefully
- Lists: Filter out empty items, ensure all items are strings
- Defaults: Provide helpful fallback values for missing data

Example:
    >>> service = ResponseService()
    >>> raw_data = {"title": "  Voter Registration  ", "steps": ["Step 1", "", "Step 2"]}
    >>> response = service.format_response("registration", raw_data)
    >>> print(response.title)  # "Voter Registration" (cleaned)
    >>> print(response.steps)  # ["Step 1", "Step 2"] (empty item removed)
"""

import logging
from typing import Dict, List
from app.models.schemas import QuestionResponse

logger = logging.getLogger(__name__)


class ResponseService:
    """Service for formatting raw data into standardized QuestionResponse objects"""

    def format_response(self, category: str, data: Dict) -> QuestionResponse:
        """
        Format a data dictionary into a QuestionResponse model.

        Ensures all fields are present, correctly typed, and non-null.
        Missing fields are filled with safe defaults.

        Args:
            category: Detected intent category
            data: Raw response data dictionary

        Returns:
            QuestionResponse: Fully populated response
        """
        # EXTRACT AND CLEAN DATA FIELDS
        # WHY: Data from external sources (Sheets, GCS) may have inconsistent formatting,
        # extra whitespace, or unexpected types. Cleaning ensures consistent output.
        title = self._clean_str(data.get("title", ""))
        overview = self._clean_str(data.get("overview", ""))
        steps = self._clean_list(data.get("steps", []))
        documents = self._clean_list(data.get("documents", []))
        tips = self._clean_list(data.get("tips", []))
        next_action = self._clean_str(data.get("next_action", ""))

        # BUILD RESPONSE WITH SAFE DEFAULTS
        # WHY: If any field is missing or empty, we provide sensible defaults
        # rather than returning null/empty values that could break the frontend
        response = QuestionResponse(
            category=category or "faq",
            title=title or "Election Information",
            overview=overview or "Here is information about the election process.",
            steps=steps,
            documents=documents,
            tips=tips,
            next_action=next_action or "Visit your local election authority website for more details.",
            matched_keywords=0,
            confidence="low",
        )

        # FINAL VALIDATION PASS
        # WHY: Double-check that all required fields are populated before returning
        # This is defensive programming to catch any edge cases
        return self.ensure_complete_response(response)

    def ensure_complete_response(self, response: QuestionResponse) -> QuestionResponse:
        """
        Validate and fill any remaining empty fields with safe defaults.

        Args:
            response: QuestionResponse to validate

        Returns:
            QuestionResponse: Complete response with all fields populated
        """
        if not response.category:
            response.category = "faq"
        if not response.title:
            response.title = "Election Information"
        if not response.overview:
            response.overview = "Here is information about the election process."
        if response.steps is None:
            response.steps = []
        if response.documents is None:
            response.documents = []
        if response.tips is None:
            response.tips = []
        if not response.next_action:
            response.next_action = "Visit your local election authority website for more details."
        return response

    # ── private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _clean_str(value) -> str:
        """
        Return a stripped string, or empty string for non-string values.

        Args:
            value: Value to clean

        Returns:
            str: Cleaned string or empty string
        """
        if isinstance(value, str):
            return value.strip()
        return ""

    @staticmethod
    def _clean_list(value) -> List[str]:
        """
        Return a list of non-empty stripped strings.

        Args:
            value: Value to clean

        Returns:
            List[str]: List of cleaned strings
        """
        if not isinstance(value, list):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
