"""Google Sheets integration service - SIMPLIFIED PUBLIC ACCESS"""

import logging
import csv
import io
from typing import Dict, Optional, List
import requests
from app.core.config import Settings

logger = logging.getLogger(__name__)


# Category-specific defaults for auto-repair
CATEGORY_DEFAULTS = {
    "first_time_voter": {
        "title": "First Time Voter Guide",
        "overview": "Complete guide for first-time voters",
        "steps": ["Check eligibility", "Register online", "Verify details"],
        "documents": ["Aadhaar Card", "Address Proof", "Passport Photo"],
        "tips": ["Apply early", "Double-check details"],
        "next_action": "Start your voter registration online"
    },
    "registration": {
        "title": "Voter Registration",
        "overview": "How to register as a voter",
        "steps": ["Visit portal", "Fill form", "Submit application"],
        "documents": ["Aadhaar Card", "Address Proof", "Identity Proof"],
        "tips": ["Use official portal only"],
        "next_action": "Apply for voter registration"
    },
    "documents": {
        "title": "Required Documents",
        "overview": "Documents needed for voter registration",
        "steps": ["Gather documents", "Verify validity"],
        "documents": ["Aadhaar Card", "Passport", "Driving License"],
        "tips": ["Ensure documents are valid"],
        "next_action": "Prepare documents before applying"
    },
    "correction": {
        "title": "Correct Voter Details",
        "overview": "How to correct voter information",
        "steps": ["Login portal", "Edit details", "Submit request"],
        "documents": ["Voter ID", "Address Proof"],
        "tips": ["Check spelling carefully"],
        "next_action": "Submit correction request"
    },
    "status_check": {
        "title": "Check Application Status",
        "overview": "Track your voter registration status",
        "steps": ["Enter application ID", "Check status"],
        "documents": ["Application ID"],
        "tips": ["Save your ID"],
        "next_action": "Track application status"
    },
    "polling_day": {
        "title": "Polling Day Guide",
        "overview": "What to do on election day",
        "steps": ["Find booth", "Carry ID", "Vote"],
        "documents": ["Voter ID", "Any valid ID"],
        "tips": ["Reach early"],
        "next_action": "Visit polling booth"
    },
    "timeline": {
        "title": "Election Timeline",
        "overview": "Important election dates",
        "steps": ["Check election dates"],
        "documents": ["Not applicable"],
        "tips": ["Stay updated"],
        "next_action": "Check schedule regularly"
    },
    "faq": {
        "title": "Frequently Asked Questions",
        "overview": "Common election questions",
        "steps": ["Review FAQs"],
        "documents": ["Not applicable"],
        "tips": ["Use official sources"],
        "next_action": "Explore official info"
    }
}

REQUIRED_CATEGORIES = [
    "first_time_voter", "registration", "documents", "correction",
    "status_check", "polling_day", "timeline", "faq"
]

GENERIC_DEFAULTS = {
    "title": "Election Information",
    "overview": "General election information",
    "steps": ["Visit official election website", "Follow instructions"],
    "documents": ["Valid ID", "Address Proof"],
    "tips": ["Check official sources", "Apply early"],
    "next_action": "Visit your local election office for more information"
}


class SheetsService:
    """Service for interfacing with Google Sheets - PUBLIC ACCESS ONLY"""

    def __init__(self, config: Settings):
        self.config = config
        self._initialized = False
        self._repaired_rows = 0

    def initialize(self) -> bool:
        """Initialize Sheets service"""
        if not self.config.SHEET_ID:
            logger.info("No SHEET_ID configured")
            return False

        self._initialized = True
        logger.info("Sheets service initialized for public access")
        return True

    def _normalize_value(self, value: str) -> str:
        """Normalize a single cell value"""
        if not value:
            return ""
        value = str(value).strip()
        if value.lower() in ("none", "n/a", "-", "null", "na"):
            return ""
        return value

    def _parse_array_field(self, value: str) -> List[str]:
        """Parse array field with multiple separator support"""
        value = self._normalize_value(value)
        if not value:
            return []

        # Try semicolon first, then comma, then pipe
        if ";" in value:
            items = [item.strip() for item in value.split(";") if item.strip()]
        elif "," in value:
            items = [item.strip() for item in value.split(",") if item.strip()]
        elif "|" in value:
            items = [item.strip() for item in value.split("|") if item.strip()]
        else:
            items = [value] if value else []

        items = [item for item in items if item.lower() not in ("none", "n/a", "-", "null", "na")]
        return items

    def _repair_row_with_defaults(self, category: str, parsed: Dict) -> Dict:
        """Repair a row with weak fields using category-specific defaults"""
        repaired = False
        defaults = CATEGORY_DEFAULTS.get(category, GENERIC_DEFAULTS)

        if not parsed.get("title"):
            parsed["title"] = defaults.get("title", GENERIC_DEFAULTS["title"])
            repaired = True

        if not parsed.get("overview"):
            parsed["overview"] = defaults.get("overview", GENERIC_DEFAULTS["overview"])
            repaired = True

        if not parsed.get("steps"):
            parsed["steps"] = defaults.get("steps", GENERIC_DEFAULTS["steps"])
            repaired = True

        if not parsed.get("documents"):
            parsed["documents"] = defaults.get("documents", GENERIC_DEFAULTS["documents"])
            repaired = True

        if not parsed.get("tips"):
            parsed["tips"] = defaults.get("tips", GENERIC_DEFAULTS["tips"])
            repaired = True

        if not parsed.get("next_action"):
            parsed["next_action"] = defaults.get("next_action", GENERIC_DEFAULTS["next_action"])
            repaired = True

        if repaired:
            self._repaired_rows += 1
            logger.debug("Auto-repaired row for category: %s", category)

        return parsed

    def _ensure_required_categories(self, data: Dict[str, Dict]) -> Dict[str, Dict]:
        """Ensure all 8 required categories are present"""
        for category in REQUIRED_CATEGORIES:
            if category not in data:
                defaults = CATEGORY_DEFAULTS.get(category, GENERIC_DEFAULTS)
                data[category] = {
                    "title": defaults["title"],
                    "overview": defaults["overview"],
                    "steps": defaults["steps"].copy(),
                    "documents": defaults["documents"].copy(),
                    "tips": defaults["tips"].copy(),
                    "next_action": defaults["next_action"]
                }
                self._repaired_rows += 1
                logger.info("Auto-created missing category: %s", category)

        return data

    def parse_row(self, row: List[str]) -> Optional[Dict]:
        """Parse a single row into structured data"""
        try:
            if not row or len(row) < 7:
                return None

            category = self._normalize_value(row[0])
            title = self._normalize_value(row[1])

            if not category:
                return None

            overview = self._normalize_value(row[2]) if len(row) > 2 else ""
            steps = self._parse_array_field(row[3]) if len(row) > 3 else []
            documents = self._parse_array_field(row[4]) if len(row) > 4 else []
            tips = self._parse_array_field(row[5]) if len(row) > 5 else []
            next_action = self._normalize_value(row[6]) if len(row) > 6 else ""

            parsed = {
                "category": category,
                "title": title,
                "overview": overview,
                "steps": steps,
                "documents": documents,
                "tips": tips,
                "next_action": next_action
            }

            parsed = self._repair_row_with_defaults(category, parsed)
            return parsed

        except Exception as e:
            logger.warning("Error parsing row: %s", e)
            return None

    def load_data(self) -> Dict[str, Dict]:
        """Load and parse data from Google Sheets using public CSV export"""
        if not self._initialized:
            logger.warning("Sheets service not initialized")
            return {}

        self._repaired_rows = 0

        try:
            # Use Google Sheets CSV export URL (works for public sheets)
            sheet_url = f"https://docs.google.com/spreadsheets/d/{self.config.SHEET_ID}/export?format=csv&gid=0"

            logger.info("Fetching public sheet: %s", self.config.SHEET_ID)

            response = requests.get(sheet_url, timeout=10)
            response.raise_for_status()

            # Parse CSV
            csv_data = list(csv.reader(io.StringIO(response.text)))

            if not csv_data or len(csv_data) < 2:
                logger.warning("Sheet has no data rows")
                return {}

            # Skip header row
            data_rows = csv_data[1:]

            # Parse rows
            data = {}
            skipped = 0

            for row in data_rows:
                parsed = self.parse_row(row)
                if parsed:
                    category = parsed.pop("category")
                    data[category] = parsed
                else:
                    skipped += 1

            if skipped > 0:
                logger.warning("Skipped %d invalid rows", skipped)

            # Ensure all required categories
            data = self._ensure_required_categories(data)

            if self._repaired_rows > 0:
                logger.info("Auto-repaired %d rows/categories", self._repaired_rows)

            logger.info(
                "Successfully loaded %d categories from Google Sheets",
                len(data)
            )
            return data

        except requests.RequestException as e:
            logger.warning("Failed to fetch sheet data: %s", e)
            return {}
        except Exception as e:
            logger.error("Unexpected error loading sheet data: %s", e)
            return {}
