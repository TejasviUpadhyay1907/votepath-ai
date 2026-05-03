"""Additional tests for config.py coverage"""

import pytest
from app.core.config import Settings, get_settings


class TestConfigValidation:
    """Test config validation"""

    def test_validate_config_with_valid_settings(self):
        config = Settings()
        assert config.validate_config() is True

    def test_validate_config_with_invalid_access_mode(self):
        config = Settings(ACCESS_MODE="invalid")
        assert config.validate_config() is False

    def test_validate_config_with_invalid_log_level(self):
        config = Settings(LOG_LEVEL="INVALID")
        assert config.validate_config() is False

    def test_validate_config_with_invalid_port_low(self):
        config = Settings(PORT=0)
        assert config.validate_config() is False

    def test_validate_config_with_invalid_port_high(self):
        config = Settings(PORT=99999)
        assert config.validate_config() is False

    def test_validate_config_with_valid_port(self):
        config = Settings(PORT=8080)
        assert config.validate_config() is True


class TestCorsOrigins:
    """Test CORS origins configuration"""

    def test_get_cors_origins_empty_returns_defaults(self):
        config = Settings(FRONTEND_ORIGINS="")
        origins = config.get_cors_origins()
        assert len(origins) == 4
        assert "http://localhost:8080" in origins

    def test_get_cors_origins_with_single_origin(self):
        config = Settings(FRONTEND_ORIGINS="https://example.com")
        origins = config.get_cors_origins()
        assert len(origins) == 1
        assert "https://example.com" in origins

    def test_get_cors_origins_with_multiple_origins(self):
        config = Settings(FRONTEND_ORIGINS="https://example.com,https://test.com")
        origins = config.get_cors_origins()
        assert len(origins) == 2
        assert "https://example.com" in origins
        assert "https://test.com" in origins

    def test_get_cors_origins_strips_whitespace(self):
        config = Settings(FRONTEND_ORIGINS=" https://example.com , https://test.com ")
        origins = config.get_cors_origins()
        assert "https://example.com" in origins
        assert "https://test.com" in origins


class TestAccessModeDetection:
    """Test access mode determination"""

    def test_determine_access_mode_public_with_sheet_id(self):
        config = Settings(ACCESS_MODE="public", SHEET_ID="test_id")
        assert config.determine_access_mode() == "public"

    def test_determine_access_mode_public_without_sheet_id(self):
        config = Settings(ACCESS_MODE="public", SHEET_ID=None)
        assert config.determine_access_mode() == "fallback"

    def test_determine_access_mode_service_account_with_creds(self):
        config = Settings(ACCESS_MODE="service_account", SHEET_ID="test_id", CREDENTIALS_PATH="/path")
        assert config.determine_access_mode() == "service_account"

    def test_determine_access_mode_service_account_without_creds(self):
        config = Settings(ACCESS_MODE="service_account", SHEET_ID="test_id", CREDENTIALS_PATH=None)
        assert config.determine_access_mode() == "fallback"

    def test_determine_access_mode_auto_with_sheet_id(self):
        config = Settings(ACCESS_MODE="auto", SHEET_ID="test_id")
        assert config.determine_access_mode() == "public"

    def test_determine_access_mode_auto_without_sheet_id(self):
        config = Settings(ACCESS_MODE="auto", SHEET_ID=None)
        assert config.determine_access_mode() == "fallback"


class TestConfigHelpers:
    """Test config helper methods"""

    def test_is_sheets_configured_true(self):
        config = Settings(SHEET_ID="test_id")
        assert config.is_sheets_configured() is True

    def test_is_sheets_configured_false(self):
        config = Settings(SHEET_ID=None)
        assert config.is_sheets_configured() is False

    def test_is_gcs_configured_true(self):
        config = Settings(GCS_CONTENT_URL="https://example.com/data.json")
        assert config.is_gcs_configured() is True

    def test_is_gcs_configured_false(self):
        config = Settings(GCS_CONTENT_URL=None)
        assert config.is_gcs_configured() is False


class TestGetSettings:
    """Test get_settings singleton"""

    def test_get_settings_returns_settings(self):
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self):
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestConfigDefaults:
    """Test default configuration values"""

    def test_default_worksheet_name(self):
        config = Settings()
        assert config.WORKSHEET_NAME == "VotePath_Data"

    def test_default_access_mode(self):
        config = Settings()
        assert config.ACCESS_MODE == "auto"

    def test_default_port(self):
        config = Settings()
        assert config.PORT == 8080

    def test_default_log_level(self):
        config = Settings()
        assert config.LOG_LEVEL == "INFO"

    def test_default_cache_enabled(self):
        config = Settings()
        assert config.CACHE_ENABLED is True

    def test_default_response_timeout(self):
        config = Settings()
        assert config.RESPONSE_TIMEOUT_MS == 500
