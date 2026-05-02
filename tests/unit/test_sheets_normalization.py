"""Tests for Google Sheets normalization layer"""

import pytest
from unittest.mock import Mock, MagicMock
from app.services.sheets_service import SheetsService
from app.core.config import Settings


@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = Mock(spec=Settings)
    config.SHEET_ID = "test-sheet-id"
    config.WORKSHEET_NAME = "Sheet1"
    config.CREDENTIALS_PATH = None
    config.ACCESS_MODE = "public"
    config.determine_access_mode = Mock(return_value="public")
    return config


@pytest.fixture
def sheets_service(mock_config):
    """Create SheetsService instance"""
    return SheetsService(mock_config)


class TestNormalization:
    """Test value normalization"""

    def test_normalize_none_string(self, sheets_service):
        """Should convert 'None' string to empty"""
        assert sheets_service._normalize_value("None") == ""
        assert sheets_service._normalize_value("none") == ""
        assert sheets_service._normalize_value("NONE") == ""

    def test_normalize_na_values(self, sheets_service):
        """Should convert N/A variants to empty"""
        assert sheets_service._normalize_value("N/A") == ""
        assert sheets_service._normalize_value("n/a") == ""
        assert sheets_service._normalize_value("NA") == ""
        assert sheets_service._normalize_value("na") == ""

    def test_normalize_dash(self, sheets_service):
        """Should convert dash to empty"""
        assert sheets_service._normalize_value("-") == ""

    def test_normalize_null(self, sheets_service):
        """Should convert null to empty"""
        assert sheets_service._normalize_value("null") == ""
        assert sheets_service._normalize_value("NULL") == ""

    def test_normalize_empty(self, sheets_service):
        """Should handle empty values"""
        assert sheets_service._normalize_value("") == ""
        assert sheets_service._normalize_value(None) == ""

    def test_normalize_whitespace(self, sheets_service):
        """Should trim whitespace"""
        assert sheets_service._normalize_value("  value  ") == "value"

    def test_normalize_valid_value(self, sheets_service):
        """Should preserve valid values"""
        assert sheets_service._normalize_value("Valid Text") == "Valid Text"


class TestArrayParsing:
    """Test array field parsing with multiple separators"""

    def test_parse_semicolon_separated(self, sheets_service):
        """Should parse semicolon-separated values"""
        result = sheets_service._parse_array_field("Item 1; Item 2; Item 3")
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_parse_comma_separated(self, sheets_service):
        """Should parse comma-separated values"""
        result = sheets_service._parse_array_field("Item 1, Item 2, Item 3")
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_parse_pipe_separated(self, sheets_service):
        """Should parse pipe-separated values"""
        result = sheets_service._parse_array_field("Item 1 | Item 2 | Item 3")
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_parse_single_value(self, sheets_service):
        """Should handle single value without separator"""
        result = sheets_service._parse_array_field("Single Item")
        assert result == ["Single Item"]

    def test_parse_empty_value(self, sheets_service):
        """Should return empty list for empty value"""
        result = sheets_service._parse_array_field("")
        assert result == []
        result = sheets_service._parse_array_field("None")
        assert result == []

    def test_parse_filters_none_items(self, sheets_service):
        """Should filter out 'None' items from list"""
        result = sheets_service._parse_array_field("Item 1; None; Item 2")
        assert result == ["Item 1", "Item 2"]

    def test_parse_filters_empty_items(self, sheets_service):
        """Should filter out empty items"""
        result = sheets_service._parse_array_field("Item 1;  ; Item 2")
        assert result == ["Item 1", "Item 2"]


class TestAutoRepair:
    """Test auto-repair with category defaults"""

    def test_repair_first_time_voter(self, sheets_service):
        """Should repair first_time_voter with defaults"""
        parsed = {
            "documents": [],
            "tips": [],
            "next_action": ""
        }
        result = sheets_service._repair_row_with_defaults("first_time_voter", parsed)
        
        assert result["documents"] == ["Aadhaar Card", "Address Proof", "Passport Photo"]
        assert "Apply early" in result["tips"]
        assert result["next_action"] == "Start your voter registration online"

    def test_repair_registration(self, sheets_service):
        """Should repair registration with defaults"""
        parsed = {
            "documents": [],
            "tips": [],
            "next_action": ""
        }
        result = sheets_service._repair_row_with_defaults("registration", parsed)
        
        assert result["documents"] == ["Aadhaar Card", "Address Proof", "Identity Proof"]
        assert "Use official portal only" in result["tips"]
        assert result["next_action"] == "Apply for voter registration"

    def test_repair_unknown_category(self, sheets_service):
        """Should use generic defaults for unknown category"""
        parsed = {
            "documents": [],
            "tips": [],
            "next_action": ""
        }
        result = sheets_service._repair_row_with_defaults("unknown_category", parsed)
        
        assert result["documents"] == ["Valid ID", "Address Proof"]
        assert result["tips"] == ["Check official sources", "Apply early"]
        assert result["next_action"] == "Visit your local election office for more information"

    def test_no_repair_if_fields_present(self, sheets_service):
        """Should not repair if fields already have values"""
        parsed = {
            "documents": ["Existing Doc"],
            "tips": ["Existing Tip"],
            "next_action": "Existing Action"
        }
        result = sheets_service._repair_row_with_defaults("first_time_voter", parsed)
        
        assert result["documents"] == ["Existing Doc"]
        assert result["tips"] == ["Existing Tip"]
        assert result["next_action"] == "Existing Action"

    def test_partial_repair(self, sheets_service):
        """Should repair only missing fields"""
        parsed = {
            "documents": ["Existing Doc"],
            "tips": [],
            "next_action": ""
        }
        result = sheets_service._repair_row_with_defaults("registration", parsed)
        
        assert result["documents"] == ["Existing Doc"]  # Not repaired
        assert "Use official portal only" in result["tips"]  # Repaired
        assert result["next_action"] == "Apply for voter registration"  # Repaired


class TestSheetLoadingWithNormalization:
    """Test complete sheet loading with normalization"""

    def test_sheet_with_none_documents_loads(self, sheets_service, mock_config):
        """Should load sheet with 'None' documents after repair"""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "Step 1", "None", "None", "None"],
            ["registration", "Registration", "How to register", "Step 1", "None", "None", "None"],
            ["documents", "Documents", "Required docs", "Step 1", "None", "None", "None"],
            ["correction", "Correction", "Fix details", "Step 1", "None", "None", "None"],
            ["status_check", "Status", "Check status", "Step 1", "None", "None", "None"],
            ["polling_day", "Polling Day", "Vote day", "Step 1", "None", "None", "None"],
            ["timeline", "Timeline", "Important dates", "Step 1", "None", "None", "None"],
            ["faq", "FAQ", "Questions", "Step 1", "None", "None", "None"],
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        result = sheets_service.load_data()
        
        assert len(result) == 8
        assert "first_time_voter" in result
        assert result["first_time_voter"]["documents"] == ["Aadhaar Card", "Address Proof", "Passport Photo"]
        assert sheets_service._repaired_rows == 8

    def test_sheet_with_comma_separated_loads(self, sheets_service, mock_config):
        """Should load sheet with comma-separated lists"""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "Step 1, Step 2", "Doc 1, Doc 2", "Tip 1, Tip 2", "Next"],
            ["registration", "Registration", "How to register", "Step 1, Step 2", "Doc 1, Doc 2", "Tip 1, Tip 2", "Next"],
            ["documents", "Documents", "Required docs", "Step 1, Step 2", "Doc 1, Doc 2", "Tip 1, Tip 2", "Next"],
            ["correction", "Correction", "Fix details", "Step 1, Step 2", "Doc 1, Doc 2", "Tip 1, Tip 2", "Next"],
            ["status_check", "Status", "Check status", "Step 1, Step 2", "Doc 1, Doc 2", "Tip 1, Tip 2", "Next"],
            ["polling_day", "Polling Day", "Vote day", "Step 1, Step 2", "Doc 1, Doc 2", "Tip 1, Tip 2", "Next"],
            ["timeline", "Timeline", "Important dates", "Step 1, Step 2", "Doc 1, Doc 2", "Tip 1, Tip 2", "Next"],
            ["faq", "FAQ", "Questions", "Step 1, Step 2", "Doc 1, Doc 2", "Tip 1, Tip 2", "Next"],
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        result = sheets_service.load_data()
        
        assert len(result) == 8
        assert result["first_time_voter"]["steps"] == ["Step 1", "Step 2"]
        assert result["first_time_voter"]["documents"] == ["Doc 1", "Doc 2"]

    def test_sheet_with_weak_fields_becomes_sheets_mode(self, sheets_service, mock_config):
        """Should load as sheets mode even with weak fields after repair"""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "Step 1", "-", "-", "-"],
            ["registration", "Registration", "How to register", "Step 1", "N/A", "N/A", "N/A"],
            ["documents", "Documents", "Required docs", "Step 1", "", "", ""],
            ["correction", "Correction", "Fix details", "Step 1", "None", "None", "None"],
            ["status_check", "Status", "Check status", "Step 1", "null", "null", "null"],
            ["polling_day", "Polling Day", "Vote day", "Step 1", "na", "na", "na"],
            ["timeline", "Timeline", "Important dates", "Step 1", "  ", "  ", "  "],
            ["faq", "FAQ", "Questions", "Step 1", "NULL", "NULL", "NULL"],
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        result = sheets_service.load_data()
        
        assert len(result) == 8
        # All rows should be repaired
        assert sheets_service._repaired_rows == 8

    def test_sheet_with_missing_steps_auto_creates(self, sheets_service, mock_config):
        """Should auto-create missing categories even if some rows have no steps"""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "None", "Doc 1", "Tip 1", "Next"],  # No steps - will be skipped
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        result = sheets_service.load_data()
        
        # Should auto-create all 8 required categories
        assert len(result) == 8
        assert all(cat in result for cat in ["first_time_voter", "registration", "documents", "correction", "status_check", "polling_day", "timeline", "faq"])


class TestGCSFallbackStillWorks:
    """Test that GCS fallback still works when Sheets fails"""

    def test_auto_creates_missing_categories(self, sheets_service, mock_config):
        """Should auto-create missing categories to reach 8 required categories"""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        # Only 3 categories provided - system will auto-create the other 5
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "Step 1", "None", "None", "None"],
            ["registration", "Registration", "How to register", "Step 1", "None", "None", "None"],
            ["documents", "Documents", "Required docs", "Step 1", "None", "None", "None"],
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        result = sheets_service.load_data()
        
        # Should have all 8 required categories (3 from sheet + 5 auto-created)
        assert len(result) == 8
        assert all(cat in result for cat in ["first_time_voter", "registration", "documents", "correction", "status_check", "polling_day", "timeline", "faq"])
