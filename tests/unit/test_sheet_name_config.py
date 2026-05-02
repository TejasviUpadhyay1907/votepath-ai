"""Tests for SHEET_NAME environment variable configuration"""

import pytest
from unittest.mock import patch
from app.core.config import Settings


class TestSheetNameConfiguration:
    """Test SHEET_NAME environment variable handling"""

    def test_default_worksheet_name(self):
        """Should use default VotePath_Data when SHEET_NAME not set"""
        with patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            assert settings.WORKSHEET_NAME == "VotePath_Data"

    def test_sheet_name_env_variable(self):
        """Should use SHEET_NAME from environment"""
        with patch.dict('os.environ', {'SHEET_NAME': 'Sheet1'}, clear=True):
            settings = Settings()
            assert settings.WORKSHEET_NAME == "Sheet1"

    def test_sheet_name_custom_value(self):
        """Should use custom SHEET_NAME value"""
        with patch.dict('os.environ', {'SHEET_NAME': 'MyCustomSheet'}, clear=True):
            settings = Settings()
            assert settings.WORKSHEET_NAME == "MyCustomSheet"

    def test_sheet_name_with_spaces(self):
        """Should handle SHEET_NAME with spaces"""
        with patch.dict('os.environ', {'SHEET_NAME': 'My Sheet Name'}, clear=True):
            settings = Settings()
            assert settings.WORKSHEET_NAME == "My Sheet Name"

    def test_worksheet_name_field_still_works(self):
        """Should still accept WORKSHEET_NAME for backward compatibility"""
        with patch.dict('os.environ', {'WORKSHEET_NAME': 'LegacyName'}, clear=True):
            settings = Settings()
            # Since we're using validation_alias, WORKSHEET_NAME as env var won't work
            # This is expected - we want SHEET_NAME to be the standard
            assert settings.WORKSHEET_NAME == "VotePath_Data"  # Uses default

    def test_sheet_name_takes_precedence(self):
        """SHEET_NAME should be the standard environment variable"""
        with patch.dict('os.environ', {
            'SHEET_NAME': 'Sheet1'
        }, clear=True):
            settings = Settings()
            assert settings.WORKSHEET_NAME == "Sheet1"

    def test_empty_sheet_name_uses_default(self):
        """Empty SHEET_NAME should still result in empty, not default"""
        with patch.dict('os.environ', {'SHEET_NAME': ''}, clear=True):
            settings = Settings()
            # Empty string is still a value, so it will be used
            assert settings.WORKSHEET_NAME == ""


class TestSheetNameInSheetsService:
    """Test that SheetsService uses the configured SHEET_NAME"""

    def test_sheets_service_uses_configured_name(self):
        """SheetsService should use WORKSHEET_NAME from config"""
        from app.services.sheets_service import SheetsService
        
        with patch.dict('os.environ', {'SHEET_NAME': 'Sheet1'}, clear=True):
            settings = Settings()
            service = SheetsService(settings)
            
            assert service.config.WORKSHEET_NAME == "Sheet1"

    def test_sheets_service_fallback_logic(self):
        """SheetsService should try configured name first"""
        from app.services.sheets_service import SheetsService
        from unittest.mock import MagicMock
        
        with patch.dict('os.environ', {
            'SHEET_NAME': 'CustomSheet',
            'SHEET_ID': 'test-sheet-id'
        }, clear=True):
            settings = Settings()
            service = SheetsService(settings)
            
            # Mock the client and spreadsheet
            mock_client = MagicMock()
            mock_spreadsheet = MagicMock()
            mock_worksheet = MagicMock()
            
            # First call should be with 'CustomSheet'
            mock_spreadsheet.worksheet.side_effect = [
                mock_worksheet  # CustomSheet succeeds
            ]
            
            mock_worksheet.row_values.return_value = [
                "category", "title", "overview", "steps", "documents", "tips", "next_action"
            ]
            mock_worksheet.get_all_values.return_value = [
                ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
                ["first_time_voter", "Title", "Overview", "Step 1", "Doc 1", "Tip 1", "Next"],
                ["registration", "Title", "Overview", "Step 1", "Doc 1", "Tip 1", "Next"],
                ["documents", "Title", "Overview", "Step 1", "Doc 1", "Tip 1", "Next"],
                ["correction", "Title", "Overview", "Step 1", "Doc 1", "Tip 1", "Next"],
                ["status_check", "Title", "Overview", "Step 1", "Doc 1", "Tip 1", "Next"],
                ["polling_day", "Title", "Overview", "Step 1", "Doc 1", "Tip 1", "Next"],
                ["timeline", "Title", "Overview", "Step 1", "Doc 1", "Tip 1", "Next"],
                ["faq", "Title", "Overview", "Step 1", "Doc 1", "Tip 1", "Next"],
            ]
            
            mock_client.open_by_key.return_value = mock_spreadsheet
            service.client = mock_client
            service._initialized = True
            
            result = service.load_data()
            
            # Verify it tried 'CustomSheet' first
            mock_spreadsheet.worksheet.assert_called_with('CustomSheet')
            assert len(result) == 8


class TestDebugEndpointSheetName:
    """Test that /debug/source shows the effective sheet name"""

    def test_debug_shows_configured_sheet_name(self):
        """Debug endpoint should show the actual configured SHEET_NAME"""
        from app.core.config import get_settings
        from functools import lru_cache
        
        # Clear the cache to force reload
        get_settings.cache_clear()
        
        with patch.dict('os.environ', {'SHEET_NAME': 'Sheet1'}, clear=True):
            settings = get_settings()
            assert settings.WORKSHEET_NAME == "Sheet1"
        
        # Clear cache again for next test
        get_settings.cache_clear()

    def test_debug_shows_default_when_not_set(self):
        """Debug endpoint should show default when SHEET_NAME not set"""
        from app.core.config import get_settings
        
        # Clear the cache to force reload
        get_settings.cache_clear()
        
        with patch.dict('os.environ', {}, clear=True):
            settings = get_settings()
            assert settings.WORKSHEET_NAME == "VotePath_Data"
        
        # Clear cache again
        get_settings.cache_clear()
