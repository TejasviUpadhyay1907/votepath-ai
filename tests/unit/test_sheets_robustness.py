"""Tests for Google Sheets robustness features"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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


class TestWorksheetFallback:
    """Test worksheet name fallback logic"""

    def test_uses_configured_worksheet_name(self, sheets_service, mock_config):
        """Should use WORKSHEET_NAME from config if it exists"""
        # Setup
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["registration", "Registration", "How to register", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["documents", "Documents", "Required docs", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["correction", "Correction", "Fix details", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["status_check", "Status", "Check status", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["polling_day", "Polling Day", "Vote day", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["timeline", "Timeline", "Important dates", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["faq", "FAQ", "Questions", "Step 1", "Doc 1", "Tip 1", "Next"],
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        # Execute
        result = sheets_service.load_data()
        
        # Verify
        assert len(result) == 8
        assert all(cat in result for cat in ["first_time_voter", "registration", "documents", "correction", "status_check", "polling_day", "timeline", "faq"])
        mock_spreadsheet.worksheet.assert_called_once_with("Sheet1")

    def test_falls_back_to_votepath_data(self, sheets_service, mock_config):
        """Should try VotePath_Data if configured name fails"""
        # Setup
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        # First call (Sheet1) fails, second call (VotePath_Data) succeeds
        mock_spreadsheet.worksheet.side_effect = [
            Exception("Sheet1 not found"),
            mock_worksheet
        ]
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["registration", "Registration", "How to register", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["documents", "Documents", "Required docs", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["correction", "Correction", "Fix details", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["status_check", "Status", "Check status", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["polling_day", "Polling Day", "Vote day", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["timeline", "Timeline", "Important dates", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["faq", "FAQ", "Questions", "Step 1", "Doc 1", "Tip 1", "Next"],
        ]
        
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        # Execute
        result = sheets_service.load_data()
        
        # Verify
        assert len(result) == 8
        assert all(cat in result for cat in ["first_time_voter", "registration", "documents", "correction", "status_check", "polling_day", "timeline", "faq"])
        assert mock_spreadsheet.worksheet.call_count == 2

    def test_falls_back_to_first_worksheet(self, sheets_service, mock_config):
        """Should use first worksheet if named sheets fail"""
        # Setup
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        # Both named worksheets fail
        mock_spreadsheet.worksheet.side_effect = Exception("Not found")
        mock_spreadsheet.get_worksheet.return_value = mock_worksheet
        mock_worksheet.title = "ActualSheetName"
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["registration", "Registration", "How to register", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["documents", "Documents", "Required docs", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["correction", "Correction", "Fix details", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["status_check", "Status", "Check status", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["polling_day", "Polling Day", "Vote day", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["timeline", "Timeline", "Important dates", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["faq", "FAQ", "Questions", "Step 1", "Doc 1", "Tip 1", "Next"],
        ]
        
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        # Execute
        result = sheets_service.load_data()
        
        # Verify
        assert len(result) == 8
        assert all(cat in result for cat in ["first_time_voter", "registration", "documents", "correction", "status_check", "polling_day", "timeline", "faq"])
        mock_spreadsheet.get_worksheet.assert_called_once_with(0)


class TestMinimumCategoryValidation:
    """Test minimum category count validation and auto-creation"""

    def test_auto_creates_missing_categories(self, sheets_service, mock_config):
        """Should auto-create missing categories to reach 8 required"""
        # Setup
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        # Only 3 categories provided - system will auto-create the other 5
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["registration", "Registration", "How to register", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["documents", "Documents", "Required docs", "Step 1", "Doc 1", "Tip 1", "Next"],
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        # Execute
        result = sheets_service.load_data()
        
        # Verify - should have all 8 required categories
        assert len(result) == 8
        assert all(cat in result for cat in ["first_time_voter", "registration", "documents", "correction", "status_check", "polling_day", "timeline", "faq"])

    def test_accepts_exactly_8_categories(self, sheets_service, mock_config):
        """Should accept exactly 8 required categories"""
        # Setup
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        mock_worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["first_time_voter", "First Time Voter", "Guide", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["registration", "Registration", "How to register", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["documents", "Documents", "Required docs", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["correction", "Correction", "Fix details", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["status_check", "Status", "Check status", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["polling_day", "Polling Day", "Vote day", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["timeline", "Timeline", "Important dates", "Step 1", "Doc 1", "Tip 1", "Next"],
            ["faq", "FAQ", "Questions", "Step 1", "Doc 1", "Tip 1", "Next"],
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        # Execute
        result = sheets_service.load_data()
        
        # Verify
        assert len(result) == 8
        assert all(cat in result for cat in ["first_time_voter", "registration", "documents", "correction", "status_check", "polling_day", "timeline", "faq"])


class TestSemicolonSeparatedValues:
    """Test semicolon-separated array parsing"""

    def test_parses_semicolon_separated_steps(self, sheets_service):
        """Should parse semicolon-separated steps"""
        row = [
            "voter_registration",
            "Register to Vote",
            "How to register",
            "Step 1; Step 2; Step 3",
            "Doc 1",
            "Tip 1",
            "Next"
        ]
        
        result = sheets_service.parse_row(row)
        
        assert result is not None
        assert result["steps"] == ["Step 1", "Step 2", "Step 3"]

    def test_parses_pipe_separated_steps(self, sheets_service):
        """Should still parse pipe-separated steps"""
        row = [
            "voter_registration",
            "Register to Vote",
            "How to register",
            "Step 1 | Step 2 | Step 3",
            "Doc 1",
            "Tip 1",
            "Next"
        ]
        
        result = sheets_service.parse_row(row)
        
        assert result is not None
        assert result["steps"] == ["Step 1", "Step 2", "Step 3"]

    def test_prefers_semicolon_over_pipe(self, sheets_service):
        """Should prefer semicolon separator when both present"""
        row = [
            "voter_registration",
            "Register to Vote",
            "How to register",
            "Step 1; Step 2 | with pipe",
            "Doc 1",
            "Tip 1",
            "Next"
        ]
        
        result = sheets_service.parse_row(row)
        
        assert result is not None
        assert len(result["steps"]) == 2
        assert "Step 1" in result["steps"]
        assert "Step 2 | with pipe" in result["steps"]

    def test_handles_single_value_without_separator(self, sheets_service):
        """Should handle single value without separator"""
        row = [
            "voter_registration",
            "Register to Vote",
            "How to register",
            "Single step",
            "Single doc",
            "Single tip",
            "Next"
        ]
        
        result = sheets_service.parse_row(row)
        
        assert result is not None
        assert result["steps"] == ["Single step"]
        assert result["documents"] == ["Single doc"]
        assert result["tips"] == ["Single tip"]


class TestMissingColumns:
    """Test handling of missing required columns"""

    def test_fails_on_missing_category_column(self, sheets_service, mock_config):
        """Should fail validation if category column missing"""
        # Setup
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        # Missing 'category' column
        mock_worksheet.row_values.return_value = [
            "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        # Execute
        result = sheets_service.load_data()
        
        # Verify
        assert result == {}

    def test_fails_on_missing_steps_column(self, sheets_service, mock_config):
        """Should fail validation if steps column missing"""
        # Setup
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        # Missing 'steps' column
        mock_worksheet.row_values.return_value = [
            "category", "title", "overview", "documents", "tips", "next_action"
        ]
        
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        sheets_service.client = mock_client
        sheets_service._initialized = True
        
        # Execute
        result = sheets_service.load_data()
        
        # Verify
        assert result == {}


class TestGCSAvailabilityWithSheets:
    """Test that GCS availability is checked when Sheets is active"""

    @patch('app.services.startup_service.SheetsService')
    @patch('app.services.startup_service.GCSService')
    def test_gcs_health_check_when_sheets_active(self, mock_gcs_class, mock_sheets_class):
        """Should health-check GCS even when Sheets is active source"""
        from app.services.startup_service import StartupService
        
        # Setup
        startup = StartupService()
        
        # Mock Sheets success
        mock_sheets = Mock()
        mock_sheets.initialize.return_value = True
        mock_sheets.load_data.return_value = {
            f"category_{i}": {"title": f"Title {i}", "overview": "", "steps": [], "documents": [], "tips": [], "next_action": ""}
            for i in range(8)
        }
        mock_sheets_class.return_value = mock_sheets
        
        # Mock GCS health check
        mock_gcs = Mock()
        mock_gcs.load_data.return_value = {
            f"category_{i}": {"title": f"Title {i}", "overview": "", "steps": [], "documents": [], "tips": [], "next_action": ""}
            for i in range(8)
        }
        mock_gcs_class.return_value = mock_gcs
        
        # Execute
        with patch('app.services.startup_service.get_settings') as mock_settings:
            mock_config = Mock()
            mock_config.APP_NAME = "Test"
            mock_config.APP_VERSION = "1.0"
            mock_config.LOG_LEVEL = "INFO"
            mock_config.GCS_CONTENT_URL = "https://storage.googleapis.com/test/content.json"
            mock_config.validate_config.return_value = True
            mock_settings.return_value = mock_config
            
            result = startup.initialize_application()
        
        # Verify
        assert result["mode"] == "sheets"
        assert result["sheets_loaded"] is True
        assert result["gcs_available"] is True
        assert result["gcs_loaded"] is False  # Not loaded as active source
