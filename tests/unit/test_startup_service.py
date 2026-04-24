"""Unit tests for StartupService"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.startup_service import StartupService
from app.utils.cache import CacheManager


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the global cache before each test"""
    from app.utils.cache import get_cache
    get_cache().clear()
    yield
    get_cache().clear()


class TestStartupServiceInitialize:

    def test_startup_succeeds_with_fallback_when_no_sheets(self):
        svc = StartupService()
        summary = svc.initialize_application()
        assert summary["mode"] == "fallback"
        assert summary["sheets_loaded"] is False
        assert summary["cache_size"] > 0

    def test_startup_populates_cache(self):
        svc = StartupService()
        svc.initialize_application()
        from app.utils.cache import get_cache
        assert get_cache().size() > 0

    def test_startup_mode_is_fallback_without_sheet_id(self):
        svc = StartupService()
        summary = svc.initialize_application()
        assert summary["mode"] == "fallback"

    def test_startup_returns_dict_with_required_keys(self):
        svc = StartupService()
        summary = svc.initialize_application()
        assert "mode" in summary
        assert "sheets_loaded" in summary
        assert "cache_size" in summary

    def test_startup_with_sheets_success(self):
        """When Sheets loads successfully, mode should be 'sheets'"""
        svc = StartupService()
        fake_data = {
            "registration": {"title": "Reg", "overview": "O", "steps": [], "documents": [], "tips": [], "next_action": ""},
            "faq": {"title": "FAQ", "overview": "O", "steps": [], "documents": [], "tips": [], "next_action": ""},
        }
        with patch.object(svc, '_attempt_sheets_load', return_value=fake_data):
            summary = svc.initialize_application()
        assert summary["mode"] == "sheets"
        assert summary["sheets_loaded"] is True
        assert summary["cache_size"] == 2

    def test_startup_with_sheets_failure_falls_back(self):
        """When Sheets fails, system should still start with fallback"""
        svc = StartupService()
        with patch.object(svc, '_attempt_sheets_load', return_value=None):
            summary = svc.initialize_application()
        assert summary["mode"] == "fallback"
        assert summary["sheets_loaded"] is False
        assert summary["cache_size"] > 0

    def test_startup_never_raises_on_sheets_failure(self):
        """Startup must not raise even if Sheets throws an exception"""
        svc = StartupService()
        with patch.object(svc, '_attempt_sheets_load', side_effect=Exception("Network error")):
            try:
                summary = svc.initialize_application()
                assert summary["cache_size"] > 0
            except Exception:
                pytest.fail("startup_service.initialize_application() raised unexpectedly")
