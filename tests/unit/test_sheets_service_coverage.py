"""
Coverage tests for app/services/sheets_service.py
Uses mocking — no real Google credentials required.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.services.sheets_service import SheetsService
from app.core.config import Settings


@pytest.fixture
def config_public():
    return Settings(SHEET_ID="fake_sheet_id", ACCESS_MODE="public")


@pytest.fixture
def config_service_account():
    return Settings(
        SHEET_ID="fake_sheet_id",
        ACCESS_MODE="service_account",
        CREDENTIALS_PATH="/fake/creds.json"
    )


@pytest.fixture
def config_no_sheet():
    return Settings(SHEET_ID=None, ACCESS_MODE="auto")


# ── initialize() paths ────────────────────────────────────────

class TestInitializePublicMode:

    def test_public_mode_success_with_mocked_gspread(self, config_public):
        """Public mode initializes successfully when gspread is available and Client works"""
        svc = SheetsService(config_public)
        mock_gspread = MagicMock()
        mock_client = MagicMock()
        mock_gspread.Client.return_value = mock_client
        with patch.dict("sys.modules", {"gspread": mock_gspread,
                                         "google.oauth2.service_account": MagicMock()}):
            result = svc.initialize()
        assert result is True
        assert svc._initialized is True

    def test_public_mode_gspread_client_raises(self, config_public):
        """Public mode returns False if gspread.Client raises"""
        svc = SheetsService(config_public)
        mock_gspread = MagicMock()
        mock_gspread.Client.side_effect = Exception("connection refused")
        with patch.dict("sys.modules", {"gspread": mock_gspread,
                                         "google.oauth2.service_account": MagicMock()}):
            result = svc.initialize()
        assert result is False

    def test_public_mode_gspread_not_installed(self, config_public):
        """Public mode returns False gracefully when gspread is not installed"""
        svc = SheetsService(config_public)
        with patch.dict("sys.modules", {"gspread": None}):
            result = svc.initialize()
        assert result is False


class TestInitializeServiceAccountMode:

    def test_service_account_success(self, config_service_account):
        """Service account mode initializes when credentials file exists"""
        svc = SheetsService(config_service_account)
        mock_creds = MagicMock()
        mock_client = MagicMock()
        mock_sa = MagicMock()
        mock_sa.Credentials.from_service_account_file.return_value = mock_creds
        mock_gspread = MagicMock()
        mock_gspread.authorize.return_value = mock_client
        with patch.dict("sys.modules", {"gspread": mock_gspread,
                                         "google.oauth2.service_account": mock_sa}):
            result = svc.initialize()
        assert result is True
        assert svc._initialized is True

    def test_service_account_missing_credentials_path(self):
        """Service account mode returns False when CREDENTIALS_PATH is missing"""
        config = Settings(SHEET_ID="fake_id", ACCESS_MODE="service_account", CREDENTIALS_PATH=None)
        svc = SheetsService(config)
        result = svc.initialize()
        assert result is False

    def test_service_account_credentials_exception(self, config_service_account):
        """Service account mode returns False when credentials file raises"""
        svc = SheetsService(config_service_account)
        with patch("google.oauth2.service_account.Credentials.from_service_account_file",
                   side_effect=FileNotFoundError("creds not found")):
            result = svc.initialize()
        assert result is False


# ── load_data() success path ──────────────────────────────────

class TestLoadDataSuccess:

    def _make_initialized_svc(self, config):
        svc = SheetsService(config)
        svc._initialized = True
        svc.client = MagicMock()
        return svc

    def test_load_data_full_success_path(self, config_public):
        """load_data parses valid sheet rows and returns category dict"""
        svc = self._make_initialized_svc(config_public)

        worksheet = MagicMock()
        worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["registration", "Reg Title", "Overview text", "S1|S2", "D1|D2", "T1", "Next action"],
            ["faq", "FAQ Title", "FAQ overview", "Q1|Q2", "", "Tip1", "Ask more"],
        ]

        spreadsheet = MagicMock()
        spreadsheet.worksheet.return_value = worksheet
        svc.client.open_by_key.return_value = spreadsheet

        result = svc.load_data()

        assert "registration" in result
        assert "faq" in result
        assert result["registration"]["title"] == "Reg Title"
        assert result["registration"]["steps"] == ["S1", "S2"]
        assert result["registration"]["documents"] == ["D1", "D2"]

    def test_load_data_skips_invalid_rows(self, config_public):
        """load_data skips rows with missing category/title"""
        svc = self._make_initialized_svc(config_public)

        worksheet = MagicMock()
        worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        worksheet.get_all_values.return_value = [
            ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
            ["registration", "Valid Title", "Overview", "S1", "D1", "T1", "Next"],
            ["", "No Category", "Overview", "S1", "D1", "T1", "Next"],  # invalid
            ["faq", "", "Overview", "S1", "D1", "T1", "Next"],           # invalid
        ]

        spreadsheet = MagicMock()
        spreadsheet.worksheet.return_value = worksheet
        svc.client.open_by_key.return_value = spreadsheet

        result = svc.load_data()
        assert len(result) == 1
        assert "registration" in result

    def test_load_data_worksheet_open_fails(self, config_public):
        """load_data returns empty dict when worksheet() raises"""
        svc = self._make_initialized_svc(config_public)

        spreadsheet = MagicMock()
        spreadsheet.worksheet.side_effect = Exception("worksheet not found")
        svc.client.open_by_key.return_value = spreadsheet

        result = svc.load_data()
        assert result == {}

    def test_load_data_get_all_values_fails(self, config_public):
        """load_data returns empty dict when get_all_values() raises"""
        svc = self._make_initialized_svc(config_public)

        worksheet = MagicMock()
        worksheet.row_values.return_value = [
            "category", "title", "overview", "steps", "documents", "tips", "next_action"
        ]
        worksheet.get_all_values.side_effect = Exception("read error")

        spreadsheet = MagicMock()
        spreadsheet.worksheet.return_value = worksheet
        svc.client.open_by_key.return_value = spreadsheet

        result = svc.load_data()
        assert result == {}

    def test_load_data_invalid_sheet_structure(self, config_public):
        """load_data returns empty dict when required columns are missing"""
        svc = self._make_initialized_svc(config_public)

        worksheet = MagicMock()
        worksheet.row_values.return_value = ["category", "title"]  # missing columns

        spreadsheet = MagicMock()
        spreadsheet.worksheet.return_value = worksheet
        svc.client.open_by_key.return_value = spreadsheet

        result = svc.load_data()
        assert result == {}
