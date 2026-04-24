"""Unit tests for Settings configuration"""

import pytest
from app.core.config import Settings


class TestCorsOrigins:

    def test_default_origins_are_localhost(self):
        s = Settings()
        origins = s.get_cors_origins()
        assert "http://localhost:8080" in origins
        assert "http://127.0.0.1:8080" in origins

    def test_custom_origins_parsed_from_env(self):
        s = Settings(FRONTEND_ORIGINS="https://myapp.run.app,https://staging.run.app")
        origins = s.get_cors_origins()
        assert "https://myapp.run.app" in origins
        assert "https://staging.run.app" in origins
        assert len(origins) == 2

    def test_empty_frontend_origins_returns_defaults(self):
        s = Settings(FRONTEND_ORIGINS="")
        origins = s.get_cors_origins()
        assert len(origins) >= 2

    def test_whitespace_in_origins_stripped(self):
        s = Settings(FRONTEND_ORIGINS=" https://a.run.app , https://b.run.app ")
        origins = s.get_cors_origins()
        assert "https://a.run.app" in origins
        assert "https://b.run.app" in origins


class TestSheetsConfigured:

    def test_sheets_not_configured_without_sheet_id(self):
        s = Settings(SHEET_ID=None)
        assert s.is_sheets_configured() is False

    def test_sheets_configured_with_sheet_id(self):
        s = Settings(SHEET_ID="abc123")
        assert s.is_sheets_configured() is True


class TestValidateConfig:

    def test_valid_config_returns_true(self):
        s = Settings()
        assert s.validate_config() is True

    def test_invalid_access_mode_returns_false(self):
        s = Settings(ACCESS_MODE="invalid_mode")
        assert s.validate_config() is False

    def test_invalid_log_level_returns_false(self):
        s = Settings(LOG_LEVEL="VERBOSE")
        assert s.validate_config() is False
