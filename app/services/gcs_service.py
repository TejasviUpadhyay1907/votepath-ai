"""Google Cloud Storage content service.

Fetches election guidance content from a public-read GCS JSON file.
No credentials required — uses a public object URL.
Falls back gracefully if unavailable.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Required fields every GCS content row must have
_REQUIRED_FIELDS = {"category", "title", "overview", "steps", "documents", "tips", "next_action"}

# Valid election categories
_VALID_CATEGORIES = {
    "first_time_voter", "registration", "documents", "correction",
    "status_check", "polling_day", "timeline", "faq",
}


def _clean_str(value) -> str:
    """Return stripped string or empty string."""
    return value.strip() if isinstance(value, str) else ""


def _clean_list(value) -> List[str]:
    """Return list of non-empty stripped strings."""
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _validate_row(row: dict) -> bool:
    """
    Validate a single GCS content row.

    Returns True only if all required fields are present and
    the category is a recognised election category.
    """
    if not isinstance(row, dict):
        return False
    if not _REQUIRED_FIELDS.issubset(row.keys()):
        return False
    if not _clean_str(row.get("category")):
        return False
    if not _clean_str(row.get("title")):
        return False
    return True


def _parse_row(row: dict) -> Optional[tuple]:
    """
    Parse and normalise a validated GCS content row.

    Returns:
        (category, data_dict) or None if invalid
    """
    if not _validate_row(row):
        return None

    category = _clean_str(row["category"])
    return category, {
        "title":       _clean_str(row["title"]),
        "overview":    _clean_str(row.get("overview", "")),
        "steps":       _clean_list(row.get("steps", [])),
        "documents":   _clean_list(row.get("documents", [])),
        "tips":        _clean_list(row.get("tips", [])),
        "next_action": _clean_str(row.get("next_action", "")),
    }


class GCSService:
    """
    Fetches election content from a public-read Google Cloud Storage JSON file.

    The GCS object must be a JSON array of category objects.
    No authentication is required — the object must be publicly readable.
    """

    def __init__(self, content_url: Optional[str]):
        """
        Args:
            content_url: Full public URL to the GCS JSON file.
                         e.g. https://storage.googleapis.com/bucket/votepath-content.json
        """
        self._url = content_url
        self._loaded = False

    @property
    def is_configured(self) -> bool:
        """True if a GCS_CONTENT_URL is set."""
        return bool(self._url)

    @property
    def is_loaded(self) -> bool:
        """True if content was successfully fetched and parsed."""
        return self._loaded

    def load_data(self) -> Optional[Dict[str, Dict]]:
        """
        Fetch and parse content from GCS.

        Returns:
            Dict mapping category → response data, or None on any failure.
        """
        if not self._url:
            logger.info("GCS_CONTENT_URL not configured — skipping GCS load")
            return None

        try:
            logger.info("Fetching content from Google Cloud Storage...")
            req = urllib.request.Request(
                self._url,
                headers={"User-Agent": "VotePath-AI/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = resp.read().decode("utf-8")

        except urllib.error.URLError as exc:
            logger.warning("GCS fetch failed (network): %s", exc)
            return None
        except Exception as exc:
            logger.warning("GCS fetch failed (unexpected): %s", exc)
            return None

        # Parse JSON
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("GCS content is not valid JSON: %s", exc)
            return None

        if not isinstance(payload, list):
            logger.warning("GCS content must be a JSON array, got %s", type(payload).__name__)
            return None

        # Parse rows
        data: Dict[str, Dict] = {}
        skipped = 0
        for row in payload:
            result = _parse_row(row)
            if result:
                category, content = result
                data[category] = content
            else:
                skipped += 1

        if skipped:
            logger.warning("GCS: skipped %d invalid rows", skipped)

        if not data:
            logger.warning("GCS: no valid rows found in content file")
            return None

        self._loaded = True
        logger.info("GCS: loaded %d categories successfully", len(data))
        return data
