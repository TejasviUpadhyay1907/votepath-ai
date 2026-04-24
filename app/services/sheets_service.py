"""Google Sheets integration service"""

import logging
from typing import Dict, Optional, List
from app.core.config import Settings

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
    
    def parse_row(self, row: List[str]) -> Optional[Dict]:
        """
        Parse a single row into structured data
        
        Args:
            row: List of cell values from sheet row
            
        Returns:
            Optional[Dict]: Parsed data or None if invalid
        """
        try:
            # Validate row has minimum required fields
            if not row or len(row) < 7:
                return None
            
            category = row[0].strip() if row[0] else ""
            title = row[1].strip() if row[1] else ""
            
            # Category and title are required
            if not category or not title:
                return None
            
            # Parse pipe-separated arrays
            def parse_array(value: str) -> List[str]:
                if not value:
                    return []
                return [item.strip() for item in value.split("|") if item.strip()]
            
            overview = row[2].strip() if len(row) > 2 and row[2] else ""
            steps = parse_array(row[3]) if len(row) > 3 else []
            documents = parse_array(row[4]) if len(row) > 4 else []
            tips = parse_array(row[5]) if len(row) > 5 else []
            next_action = row[6].strip() if len(row) > 6 and row[6] else ""
            
            return {
                "category": category,
                "title": title,
                "overview": overview,
                "steps": steps,
                "documents": documents,
                "tips": tips,
                "next_action": next_action
            }
            
        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            return None
    
    def load_data(self) -> Dict[str, Dict]:
        """
        Load and parse data from Google Sheets
        
        Returns:
            Dict[str, Dict]: Dictionary mapping categories to response data
                            Returns empty dict on failure
        """
        if not self._initialized:
            logger.warning("Sheets service not initialized")
            return {}
        
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
            
            # Get worksheet
            try:
                worksheet = spreadsheet.worksheet(self.config.WORKSHEET_NAME)
            except Exception as e:
                logger.warning(f"Failed to open worksheet '{self.config.WORKSHEET_NAME}': {e}")
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
            
            # Parse rows
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
            
            logger.info(f"Loaded {len(data)} categories from Google Sheets")
            return data
            
        except Exception as e:
            logger.error(f"Unexpected error loading sheet data: {e}")
            return {}
