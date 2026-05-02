"""Unit tests for SheetsService — mocked gspread"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.sheets_service import SheetsService
from app.core.config import Settings


@pytest.fixture
def config_no_creds():
    return Settings(SHEET_ID=None, ACCESS_MODE="auto", CREDENTIALS_PATH=None)


@pytest.fixture
def config_public():
    return Settings(SHEET_ID="fake_sheet_id", ACCESS_MODE="public", CREDENTIALS_PATH=None)


@pytest.fixture
def config_service_account():
    return Settings(
        SHEET_ID="fake_sheet_id",
        ACCESS_MODE="service_account",
        CREDENTIALS_PATH="/fake/creds.json"
    )


class TestSheetsServiceInitialize:

    def test_no_credentials_returns_false(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        result = svc.initialize()
        assert result is False

    def test_public_mode_without_sheet_id_returns_false(self):
        config = Settings(SHEET_ID=None, ACCESS_MODE="public")
        svc = SheetsService(config)
        result = svc.initialize()
        assert result is False

    def test_service_account_without_credentials_path_returns_false(self):
        config = Settings(SHEET_ID="fake_id", ACCESS_MODE="service_account", CREDENTIALS_PATH=None)
        svc = SheetsService(config)
        result = svc.initialize()
        assert result is False

    def test_gspread_import_error_returns_false(self, config_public):
        svc = SheetsService(config_public)
        with patch.dict("sys.modules", {"gspread": None}):
            result = svc.initialize()
        assert result is False


class TestSheetsServiceValidateStructure:

    def test_valid_headers_returns_true(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        worksheet = MagicMock()
        worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        assert svc.validate_sheet_structure(worksheet) is True

    def test_missing_column_returns_false(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        worksheet = MagicMock()
        worksheet.row_values.return_value = ["category", "title", "overview"]
        assert svc.validate_sheet_structure(worksheet) is False

    def test_case_insensitive_headers(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        worksheet = MagicMock()
        worksheet.row_values.return_value = [
            "Category", "Title", "Overview", "Steps", "Documents", "Tips", "Next_Action"
        ]
        assert svc.validate_sheet_structure(worksheet) is True

    def test_exception_returns_false(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        worksheet = MagicMock()
        worksheet.row_values.side_effect = Exception("Network error")
        assert svc.validate_sheet_structure(worksheet) is False


class TestSheetsServiceParseRow:

    def test_valid_row_parsed_correctly(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        row = [
            "registration", "Voter Registration", "How to register",
            "Step 1|Step 2", "ID|Proof", "Tip 1|Tip 2", "Visit portal"
        ]
        result = svc.parse_row(row)
        assert result is not None
        assert result["category"] == "registration"
        assert result["title"] == "Voter Registration"
        assert result["steps"] == ["Step 1", "Step 2"]
        assert result["documents"] == ["ID", "Proof"]
        assert result["tips"] == ["Tip 1", "Tip 2"]
        assert result["next_action"] == "Visit portal"

    def test_empty_row_returns_none(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        assert svc.parse_row([]) is None

    def test_too_few_columns_returns_none(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        assert svc.parse_row(["registration", "Title"]) is None

    def test_missing_category_returns_none(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        row = ["", "Title", "Overview", "Steps", "Docs", "Tips", "Next"]
        assert svc.parse_row(row) is None

    def test_missing_title_auto_repaired(self, config_no_creds):
        """Missing title is now auto-repaired with defaults"""
        svc = SheetsService(config_no_creds)
        row = ["registration", "", "Overview", "Steps", "Docs", "Tips", "Next"]
        result = svc.parse_row(row)
        assert result is not None
        assert result["title"] == "Voter Registration"  # Auto-repaired from defaults

    def test_empty_optional_fields_become_defaults(self, config_no_creds):
        """Empty optional fields are repaired with defaults"""
        svc = SheetsService(config_no_creds)
        # Steps must have at least one value
        row = ["registration", "Title", "", "Step 1", "", "", ""]
        result = svc.parse_row(row)
        assert result is not None
        assert result["overview"] == "How to register as a voter"  # Auto-repaired from defaults
        assert result["steps"] == ["Step 1"]
        # Documents, tips, next_action are repaired by _repair_row_with_defaults
        assert result["documents"] == ["Aadhaar Card", "Address Proof", "Identity Proof"]  # Repaired
        assert "Use official portal only" in result["tips"]  # Repaired
        assert result["next_action"] == "Apply for voter registration"  # Repaired

    def test_pipe_separated_values_split_correctly(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        row = ["faq", "FAQ", "Overview", "A|B|C", "X|Y", "T1|T2|T3", "Next"]
        result = svc.parse_row(row)
        assert result["steps"] == ["A", "B", "C"]
        assert result["documents"] == ["X", "Y"]
        assert result["tips"] == ["T1", "T2", "T3"]


class TestSheetsServiceLoadData:

    def test_load_data_not_initialized_returns_empty(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        result = svc.load_data()
        assert result == {}

    def test_load_data_no_sheet_id_returns_empty(self, config_no_creds):
        svc = SheetsService(config_no_creds)
        svc._initialized = True
        result = svc.load_data()
        assert result == {}

    def test_load_data_spreadsheet_open_fails_returns_empty(self, config_public):
        svc = SheetsService(config_public)
        svc._initialized = True
        svc.client = MagicMock()
        svc.client.open_by_key.side_effect = Exception("Not found")
        result = svc.load_data()
        assert result == {}

    def test_load_data_skips_invalid_rows(self, config_public):
        """Should skip invalid rows and auto-create missing required categories"""
        svc = SheetsService(config_public)
        svc._initialized = True

        worksheet = MagicMock()
        worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["registration", "Reg Title", "Overview", "S1|S2", "D1", "T1", "Next"],
            ["", "No Category", "Overview", "", "", "", ""],  # invalid — no category
            ["documents", "Documents", "Required docs", "S1", "D1", "T1", "Next"],
            ["correction", "Correction", "Fix details", "S1", "D1", "T1", "Next"],
            ["status_check", "Status", "Check status", "S1", "D1", "T1", "Next"],
            ["polling_day", "Polling Day", "Vote day", "S1", "D1", "T1", "Next"],
            ["timeline", "Timeline", "Important dates", "S1", "D1", "T1", "Next"],
            ["faq", "FAQ", "Frequently asked questions", "S1", "D1", "T1", "Next"],
        ]

        spreadsheet = MagicMock()
        spreadsheet.worksheet.return_value = worksheet
        svc.client = MagicMock()
        svc.client.open_by_key.return_value = spreadsheet

        result = svc.load_data()
        assert "registration" in result
        # Should have all 8 required categories (7 from sheet + 1 auto-created first_time_voter)
        assert len(result) == 8
        assert all(cat in result for cat in ["first_time_voter", "registration", "documents", "correction", "status_check", "polling_day", "timeline", "faq"])
