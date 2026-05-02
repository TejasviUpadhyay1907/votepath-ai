"""Tests for simplified Sheets service (public CSV access)"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.sheets_service import SheetsService
from app.core.config import Settings


class TestSheetsServiceInitialize:
    """Test Sheets service initialization"""

    def test_initialize_with_sheet_id_returns_true(self):
        """Service initializes when SHEET_ID is provided"""
        config = Settings(SHEET_ID="1Itn_TfzyZ9jArJJzFoTyIRXb8lq0MbDz9EBZTs3ohAM")
        svc = SheetsService(config)
        result = svc.initialize()
        assert result is True
        assert svc._initialized is True

    def test_initialize_without_sheet_id_returns_false(self):
        """Service fails to initialize without SHEET_ID"""
        config = Settings(SHEET_ID=None)
        svc = SheetsService(config)
        result = svc.initialize()
        assert result is False
        assert svc._initialized is False


class TestSheetsServiceLoadData:
    """Test Sheets data loading via CSV export"""

    @patch('app.services.sheets_service.requests.get')
    def test_load_data_success(self, mock_get):
        """Successfully loads data from public sheet CSV"""
        mock_response = MagicMock()
        mock_response.text = """category,title,overview,steps,documents,tips,next_action
first_time_voter,First Time Voter,Guide for first time voters,Step1;Step2,Doc1;Doc2,Tip1,Action1
registration,Voter Registration,How to register,Step1,Doc1,Tip1,Action1"""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc.initialize()
        
        data = svc.load_data()
        
        assert len(data) == 8  # Auto-creates missing categories
        assert "first_time_voter" in data
        assert "registration" in data
        assert data["first_time_voter"]["title"] == "First Time Voter"

    @patch('app.services.sheets_service.requests.get')
    def test_load_data_network_error_returns_empty(self, mock_get):
        """Returns empty dict on network error"""
        mock_get.side_effect = Exception("Network error")

        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc.initialize()
        
        data = svc.load_data()
        
        assert data == {}

    def test_load_data_without_initialize_returns_empty(self):
        """Returns empty dict if not initialized"""
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        # Don't call initialize()
        
        data = svc.load_data()
        
        assert data == {}


class TestSheetsServiceParsing:
    """Test row parsing and normalization"""

    def test_parse_row_valid_data(self):
        """Parses valid row correctly"""
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        
        row = ["first_time_voter", "Title", "Overview", "Step1;Step2", "Doc1;Doc2", "Tip1", "Action"]
        result = svc.parse_row(row)
        
        assert result is not None
        assert result["category"] == "first_time_voter"
        assert result["title"] == "Title"
        assert result["steps"] == ["Step1", "Step2"]
        assert result["documents"] == ["Doc1", "Doc2"]

    def test_parse_row_missing_category_returns_none(self):
        """Returns None if category is missing"""
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        
        row = ["", "Title", "Overview", "Steps", "Docs", "Tips", "Action"]
        result = svc.parse_row(row)
        
        assert result is None

    def test_parse_row_auto_repairs_weak_fields(self):
        """Auto-repairs rows with weak/missing fields"""
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        
        row = ["first_time_voter", "", "", "", "", "", ""]
        result = svc.parse_row(row)
        
        assert result is not None
        assert result["title"] != ""  # Auto-repaired
        assert len(result["steps"]) > 0  # Auto-repaired
        assert svc._repaired_rows == 1

    def test_parse_array_field_semicolon_separator(self):
        """Parses semicolon-separated arrays"""
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        
        result = svc._parse_array_field("Item1;Item2;Item3")
        
        assert result == ["Item1", "Item2", "Item3"]

    def test_parse_array_field_comma_separator(self):
        """Parses comma-separated arrays"""
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        
        result = svc._parse_array_field("Item1,Item2,Item3")
        
        assert result == ["Item1", "Item2", "Item3"]

    def test_normalize_value_handles_none(self):
        """Normalizes None and empty values"""
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        
        assert svc._normalize_value(None) == ""
        assert svc._normalize_value("") == ""
        assert svc._normalize_value("None") == ""
        assert svc._normalize_value("N/A") == ""
        assert svc._normalize_value("Valid") == "Valid"


class TestSheetsServiceCategoryDefaults:
    """Test category auto-creation and defaults"""

    @patch('app.services.sheets_service.requests.get')
    def test_ensures_all_8_required_categories(self, mock_get):
        """Auto-creates missing categories to ensure exactly 8"""
        mock_response = MagicMock()
        mock_response.text = """category,title,overview,steps,documents,tips,next_action
first_time_voter,Title,Overview,Steps,Docs,Tips,Action"""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc.initialize()
        
        data = svc.load_data()
        
        assert len(data) == 8
        assert "first_time_voter" in data
        assert "registration" in data
        assert "documents" in data
        assert "correction" in data
        assert "status_check" in data
        assert "polling_day" in data
        assert "timeline" in data
        assert "faq" in data
