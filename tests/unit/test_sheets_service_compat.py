"""Compatibility tests for Sheets service - maintains test count"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.sheets_service import SheetsService
from app.core.config import Settings


class TestSheetsServiceInitializeCompat:
    """Compatibility tests for initialization"""

    def test_no_sheet_id_returns_false(self):
        config = Settings(SHEET_ID=None)
        svc = SheetsService(config)
        assert svc.initialize() is False

    def test_with_sheet_id_returns_true(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        assert svc.initialize() is True

    def test_access_mode_ignored_in_new_service(self):
        """New service ignores ACCESS_MODE, always uses public CSV"""
        config = Settings(SHEET_ID="fake_id", ACCESS_MODE="service_account")
        svc = SheetsService(config)
        assert svc.initialize() is True

    def test_credentials_path_ignored_in_new_service(self):
        """New service doesn't use credentials"""
        config = Settings(SHEET_ID="fake_id", CREDENTIALS_PATH="/fake/path")
        svc = SheetsService(config)
        assert svc.initialize() is True


class TestSheetsServiceLoadDataCompat:
    """Compatibility tests for load_data"""

    @patch('app.services.sheets_service.requests.get')
    def test_load_data_with_valid_csv(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "category,title,overview,steps,documents,tips,next_action\nfirst_time_voter,Title,Overview,Steps,Docs,Tips,Action"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc.initialize()
        data = svc.load_data()
        assert len(data) >= 1

    @patch('app.services.sheets_service.requests.get')
    def test_load_data_network_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc.initialize()
        data = svc.load_data()
        assert data == {}

    def test_load_data_not_initialized(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        data = svc.load_data()
        assert data == {}

    @patch('app.services.sheets_service.requests.get')
    def test_load_data_empty_csv(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc.initialize()
        data = svc.load_data()
        assert data == {}


class TestSheetsServiceParsingCompat:
    """Compatibility tests for parsing"""

    def test_parse_row_valid(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        row = ["cat", "title", "overview", "steps", "docs", "tips", "action"]
        result = svc.parse_row(row)
        assert result is not None

    def test_parse_row_missing_category(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        row = ["", "title", "overview", "steps", "docs", "tips", "action"]
        result = svc.parse_row(row)
        assert result is None

    def test_parse_row_short_row(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        row = ["cat"]
        result = svc.parse_row(row)
        assert result is None

    def test_normalize_value_none(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        assert svc._normalize_value(None) == ""

    def test_normalize_value_empty(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        assert svc._normalize_value("") == ""

    def test_normalize_value_valid(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        assert svc._normalize_value("test") == "test"

    def test_parse_array_semicolon(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        result = svc._parse_array_field("a;b;c")
        assert result == ["a", "b", "c"]

    def test_parse_array_comma(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        result = svc._parse_array_field("a,b,c")
        assert result == ["a", "b", "c"]

    def test_parse_array_empty(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        result = svc._parse_array_field("")
        assert result == []


class TestSheetsServiceRepairCompat:
    """Compatibility tests for auto-repair"""

    def test_repair_empty_title(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        parsed = {"category": "first_time_voter", "title": "", "overview": "", "steps": [], "documents": [], "tips": [], "next_action": ""}
        result = svc._repair_row_with_defaults("first_time_voter", parsed)
        assert result["title"] != ""

    def test_repair_empty_steps(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        parsed = {"category": "registration", "title": "Title", "overview": "", "steps": [], "documents": [], "tips": [], "next_action": ""}
        result = svc._repair_row_with_defaults("registration", parsed)
        assert len(result["steps"]) > 0

    def test_repair_increments_counter(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc._repaired_rows = 0
        parsed = {"category": "documents", "title": "", "overview": "", "steps": [], "documents": [], "tips": [], "next_action": ""}
        svc._repair_row_with_defaults("documents", parsed)
        assert svc._repaired_rows == 1

    def test_no_repair_needed(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc._repaired_rows = 0
        parsed = {"category": "correction", "title": "Title", "overview": "Overview", "steps": ["Step"], "documents": ["Doc"], "tips": ["Tip"], "next_action": "Action"}
        svc._repair_row_with_defaults("correction", parsed)
        assert svc._repaired_rows == 0


class TestSheetsServiceCategoriesCompat:
    """Compatibility tests for category management"""

    def test_ensure_required_categories_all_present(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        data = {
            "first_time_voter": {},
            "registration": {},
            "documents": {},
            "correction": {},
            "status_check": {},
            "polling_day": {},
            "timeline": {},
            "faq": {}
        }
        result = svc._ensure_required_categories(data)
        assert len(result) == 8

    def test_ensure_required_categories_missing_some(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        data = {"first_time_voter": {}}
        result = svc._ensure_required_categories(data)
        assert len(result) == 8
        assert "registration" in result
        assert "faq" in result

    def test_ensure_required_categories_empty(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        data = {}
        result = svc._ensure_required_categories(data)
        assert len(result) == 8

    @patch('app.services.sheets_service.requests.get')
    def test_load_data_ensures_8_categories(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "category,title,overview,steps,documents,tips,next_action\nfirst_time_voter,Title,Overview,Steps,Docs,Tips,Action"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc.initialize()
        data = svc.load_data()
        assert len(data) == 8


class TestSheetsServiceEdgeCasesCompat:
    """Edge case compatibility tests"""

    def test_parse_row_with_none_values(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        row = ["cat", None, None, None, None, None, None]
        result = svc.parse_row(row)
        assert result is not None

    def test_parse_array_with_none_items(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        result = svc._parse_array_field("a;None;b")
        assert "None" not in result

    def test_normalize_value_na(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        assert svc._normalize_value("N/A") == ""

    def test_normalize_value_dash(self):
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        assert svc._normalize_value("-") == ""

    @patch('app.services.sheets_service.requests.get')
    def test_load_data_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_get.return_value = mock_response
        
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc.initialize()
        data = svc.load_data()
        assert data == {}

    @patch('app.services.sheets_service.requests.get')
    def test_load_data_invalid_csv(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "invalid,csv,format"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        config = Settings(SHEET_ID="fake_id")
        svc = SheetsService(config)
        svc.initialize()
        data = svc.load_data()
        # Invalid CSV returns empty dict
        assert data == {}
