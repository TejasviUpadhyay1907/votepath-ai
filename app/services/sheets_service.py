"""Google Sheets integration service with robust normalization"""

import logging
from typing import Dict, Optional, List
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

# Required categories - must have all 8
REQUIRED_CATEGORIES = [
    "first_time_voter",
    "registration", 
    "documents",
    "correction",
    "status_check",
    "polling_day",
    "timeline",
    "faq"
]

# Generic defaults for unknown categories or as fallback
GENERIC_DEFAULTS = {
    "title": "Election Information",
    "overview": "General election information",
    "steps": ["Visit official election website", "Follow instructions"],
    "documents": ["Valid ID", "Address Proof"],
    "tips": ["Check official sources", "Apply early"],
    "next_action": "Visit your local election office for more information"
}

logger = logging.getLogger(__name__)


class SheetsService:
    """Service for interfacing with Google Sheets API"""
    
    def __init__(self, config: Settings):
        """
        Initialize Sheets service
        
        Args:
            config: Application settings
        """
        self.config = config
        self.client = None
        self._initialized = False
        self._repaired_rows = 0  # Track how many rows were auto-repaired
    
    def initialize(self) -> bool:
        """
        Initialize Google Sheets client based on access mode
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            access_mode = self.config.determine_access_mode()
            
            if access_mode == "fallback":
                logger.info("Sheets service in fallback mode - no credentials configured")
                return False
            
            # Try to import gspread
            try:
                import gspread
                from google.oauth2.service_account import Credentials
            except ImportError:
                logger.warning("gspread or google-auth not installed, using fallback mode")
                return False
            
            if access_mode == "public":
                # Public read-only access
                try:
                    self.client = gspread.Client(auth=None)
                    self._initialized = True
                    logger.info("Sheets service initialized in public mode")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to initialize public Sheets access: {e}")
                    return False
            
            elif access_mode == "service_account":
                # Service account authentication
                try:
                    if not self.config.CREDENTIALS_PATH:
                        logger.warning("Service account mode requires CREDENTIALS_PATH")
                        return False
                    
                    scopes = [
                        'https://www.googleapis.com/auth/spreadsheets.readonly',
                        'https://www.googleapis.com/auth/drive.readonly'
                    ]
                    
                    creds = Credentials.from_service_account_file(
                        self.config.CREDENTIALS_PATH,
                        scopes=scopes
                    )
                    
                    self.client = gspread.authorize(creds)
                    self._initialized = True
                    logger.info("Sheets service initialized with service account")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Failed to initialize service account: {e}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error initializing Sheets service: {e}")
            return False
    
    def validate_sheet_structure(self, worksheet) -> bool:
        """
        Validate that required columns exist in the sheet
        
        Args:
            worksheet: gspread worksheet object
            
        Returns:
            bool: True if structure is valid
        """
        try:
            # Get first row (headers)
            headers = worksheet.row_values(1)
            
            required_columns = [
                "category", "title", "overview", "steps",
                "documents", "tips", "next_action"
            ]
            
            # Check if all required columns are present (case-insensitive)
            headers_lower = [h.lower().strip() for h in headers]
            
            for col in required_columns:
                if col not in headers_lower:
                    logger.warning(f"Missing required column: {col}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating sheet structure: {e}")
            return False
    
    def _normalize_value(self, value: str) -> str:
        """
        Normalize a single cell value.
        Converts None, "None", "N/A", "-", empty to empty string.
        
        Args:
            value: Raw cell value
            
        Returns:
            str: Normalized value
        """
        if not value:
            return ""
        
        value = str(value).strip()
        
        # Treat these as empty
        if value.lower() in ("none", "n/a", "-", "null", "na"):
            return ""
        
        return value
    
    def _parse_array_field(self, value: str) -> List[str]:
        """
        Parse array field with multiple separator support.
        Tries semicolon first, then comma, then pipe.
        
        Args:
            value: Raw cell value
            
        Returns:
            List[str]: Parsed array
        """
        value = self._normalize_value(value)
        
        if not value:
            return []
        
        # Try semicolon first
        if ";" in value:
            items = [item.strip() for item in value.split(";") if item.strip()]
        # Then comma
        elif "," in value:
            items = [item.strip() for item in value.split(",") if item.strip()]
        # Then pipe
        elif "|" in value:
            items = [item.strip() for item in value.split("|") if item.strip()]
        else:
            # Single item
            items = [value] if value else []
        
        # Filter out "None" and similar values from list items
        items = [item for item in items if item.lower() not in ("none", "n/a", "-", "null", "na")]
        
        return items
    
    def _repair_row_with_defaults(self, category: str, parsed: Dict) -> Dict:
        """
        Repair a row with weak fields using category-specific defaults.
        Repairs ALL fields: title, overview, steps, documents, tips, next_action.
        
        Args:
            category: Category name
            parsed: Parsed row data
            
        Returns:
            Dict: Repaired row data
        """
        repaired = False
        defaults = CATEGORY_DEFAULTS.get(category, GENERIC_DEFAULTS)
        
        # Repair title
        if not parsed.get("title"):
            parsed["title"] = defaults.get("title", GENERIC_DEFAULTS["title"])
            repaired = True
        
        # Repair overview
        if not parsed.get("overview"):
            parsed["overview"] = defaults.get("overview", GENERIC_DEFAULTS["overview"])
            repaired = True
        
        # Repair steps
        if not parsed.get("steps"):
            parsed["steps"] = defaults.get("steps", GENERIC_DEFAULTS["steps"])
            repaired = True
        
        # Repair documents
        if not parsed.get("documents"):
            parsed["documents"] = defaults.get("documents", GENERIC_DEFAULTS["documents"])
            repaired = True
        
        # Repair tips
        if not parsed.get("tips"):
            parsed["tips"] = defaults.get("tips", GENERIC_DEFAULTS["tips"])
            repaired = True
        
        # Repair next_action
        if not parsed.get("next_action"):
            parsed["next_action"] = defaults.get("next_action", GENERIC_DEFAULTS["next_action"])
            repaired = True
        
        if repaired:
            self._repaired_rows += 1
            logger.debug(f"Auto-repaired row for category: {category}")
        
        return parsed
    
    def _ensure_required_categories(self, data: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Ensure all 8 required categories are present.
        Auto-creates missing categories using CATEGORY_DEFAULTS.
        
        Args:
            data: Parsed data dictionary
            
        Returns:
            Dict: Data with all required categories present
        """
        for category in REQUIRED_CATEGORIES:
            if category not in data:
                # Auto-create missing category
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
                logger.info(f"Auto-created missing category: {category}")
        
        return data
    
    def parse_row(self, row: List[str]) -> Optional[Dict]:
        """
        Parse a single row into structured data with robust normalization.
        Handles "None", empty values, and multiple separator formats.
        
        Args:
            row: List of cell values from sheet row
            
        Returns:
            Optional[Dict]: Parsed data or None if invalid
        """
        try:
            # Validate row has minimum required fields
            if not row or len(row) < 7:
                return None
            
            # Normalize and validate critical fields
            category = self._normalize_value(row[0])
            title = self._normalize_value(row[1])
            
            # Category is absolutely required (title can be repaired)
            if not category:
                return None
            
            # Parse other fields with normalization
            overview = self._normalize_value(row[2]) if len(row) > 2 else ""
            steps = self._parse_array_field(row[3]) if len(row) > 3 else []
            documents = self._parse_array_field(row[4]) if len(row) > 4 else []
            tips = self._parse_array_field(row[5]) if len(row) > 5 else []
            next_action = self._normalize_value(row[6]) if len(row) > 6 else ""
            
            # Build parsed data
            parsed = {
                "category": category,
                "title": title,
                "overview": overview,
                "steps": steps,
                "documents": documents,
                "tips": tips,
                "next_action": next_action
            }
            
            # Auto-repair weak fields using category defaults
            parsed = self._repair_row_with_defaults(category, parsed)
            
            return parsed
            
        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            return None
    
    def load_data(self) -> Dict[str, Dict]:
        """
        Load and parse data from Google Sheets with robust fallback logic.
        
        Tries worksheets in order:
        1. WORKSHEET_NAME from env (e.g., "Sheet1")
        2. "VotePath_Data" (default expected name)
        3. First worksheet in spreadsheet
        
        Auto-creates missing categories to guarantee exactly 8 categories.
        
        Returns:
            Dict[str, Dict]: Dictionary mapping categories to response data
                            Always returns at least 8 categories (auto-creates missing ones)
        """
        if not self._initialized:
            logger.warning("Sheets service not initialized")
            return {}
        
        # Reset repair counter
        self._repaired_rows = 0
        
        try:
            if not self.config.SHEET_ID:
                logger.warning("No SHEET_ID configured")
                return {}
            
            # Open spreadsheet
            try:
                spreadsheet = self.client.open_by_key(self.config.SHEET_ID)
            except Exception as e:
                logger.warning(f"Failed to open spreadsheet: {e}")
                return {}
            
            # Try to get worksheet with fallback logic
            worksheet = None
            tried_names = []
            
            # Try 1: Configured WORKSHEET_NAME
            if self.config.WORKSHEET_NAME:
                try:
                    worksheet = spreadsheet.worksheet(self.config.WORKSHEET_NAME)
                    logger.info(f"Using worksheet: {self.config.WORKSHEET_NAME}")
                except Exception as e:
                    tried_names.append(self.config.WORKSHEET_NAME)
                    logger.debug(f"Worksheet '{self.config.WORKSHEET_NAME}' not found: {e}")
            
            # Try 2: Default "VotePath_Data"
            if not worksheet and self.config.WORKSHEET_NAME != "VotePath_Data":
                try:
                    worksheet = spreadsheet.worksheet("VotePath_Data")
                    logger.info("Using default worksheet: VotePath_Data")
                except Exception as e:
                    tried_names.append("VotePath_Data")
                    logger.debug(f"Default worksheet 'VotePath_Data' not found: {e}")
            
            # Try 3: First worksheet
            if not worksheet:
                try:
                    worksheet = spreadsheet.get_worksheet(0)
                    logger.info(f"Using first worksheet: {worksheet.title}")
                except Exception as e:
                    logger.error(f"Failed to get any worksheet. Tried: {tried_names}: {e}")
                    return {}
            
            # Validate structure
            if not self.validate_sheet_structure(worksheet):
                logger.error("Sheet structure validation failed")
                return {}
            
            # Get all rows (skip header)
            try:
                all_rows = worksheet.get_all_values()[1:]  # Skip header row
            except Exception as e:
                logger.error(f"Failed to read sheet data: {e}")
                return {}
            
            # Parse rows with normalization
            data = {}
            skipped = 0
            
            for row in all_rows:
                parsed = self.parse_row(row)
                if parsed:
                    category = parsed.pop("category")
                    data[category] = parsed
                else:
                    skipped += 1
            
            if skipped > 0:
                logger.warning(f"Skipped {skipped} invalid rows")
            
            # Auto-create missing required categories
            data = self._ensure_required_categories(data)
            
            if self._repaired_rows > 0:
                logger.info(f"Auto-repaired {self._repaired_rows} rows/categories with weak or missing fields")
            
            logger.info(f"Successfully loaded {len(data)} categories from Google Sheets")
            return data
            
        except Exception as e:
            logger.error(f"Unexpected error loading sheet data: {e}")
            return {}
