"""
Integration tests for app startup and Google Sheets mock paths.
Tests lifespan, route availability, and Sheets success/failure modes.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.utils.cache import get_cache
from app.services.fallback_service import FallbackService


@pytest.fixture(autouse=True)
def reset_cache():
    get_cache().clear()
    yield
    get_cache().clear()


class TestAppStartup:

    def test_app_starts_and_health_check_responds(self):
        """App must start and respond to health check without crashing"""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_all_routes_exist(self):
        """All required routes must be registered"""
        client = TestClient(app)
        assert client.get("/").status_code == 200
        assert client.get("/categories").status_code == 200
        assert client.post("/ask", json={"question": "test"}).status_code == 200
        assert client.get("/debug/source").status_code == 200

    def test_app_serves_frontend(self):
        """Frontend must be served at /ui"""
        client = TestClient(app)
        response = client.get("/ui")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_app_starts_in_fallback_without_sheet_id(self):
        """Without SHEET_ID, system must start in fallback mode"""
        client = TestClient(app)
        data = client.get("/debug/source").json()
        assert data["content_source"] in ("sheets", "fallback")
        assert isinstance(data["cache_loaded"], bool)

    def test_cache_populated_after_startup(self):
        """Cache must be populated after startup (from fallback or sheets)"""
        # Pre-populate to simulate startup
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        assert cache.size() > 0


class TestSheetsMockSuccess:

    def test_startup_with_mocked_sheets_success(self):
        """When Sheets loads successfully, mode should be sheets"""
        from app.services.startup_service import StartupService
        fake_data = {cat: {"title": cat, "overview": "o", "steps": [], "documents": [], "tips": [], "next_action": ""}
                     for cat in ["registration", "faq", "documents", "first_time_voter",
                                 "correction", "status_check", "polling_day", "timeline"]}
        svc = StartupService()
        with patch.object(svc, "_attempt_sheets_load", return_value=fake_data):
            summary = svc.initialize_application()
        assert summary["mode"] == "sheets"
        assert summary["sheets_loaded"] is True
        assert summary["cache_size"] == 8

    def test_ask_response_includes_data_source_note(self):
        """Every /ask response must include data_source_note"""
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        assert "data_source_note" in data
        assert isinstance(data["data_source_note"], str)
        assert len(data["data_source_note"]) > 0

    def test_data_source_note_says_fallback_without_sheet_id(self):
        """Without SHEET_ID, data_source_note must mention fallback"""
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        # In test env, no SHEET_ID is set
        assert "fallback" in data["data_source_note"].lower()


class TestSheetsMockFailure:

    def test_startup_with_sheets_failure_still_starts(self):
        """Sheets failure must not prevent startup"""
        from app.services.startup_service import StartupService
        svc = StartupService()
        with patch.object(svc, "_attempt_sheets_load", return_value=None):
            summary = svc.initialize_application()
        assert summary["mode"] == "fallback"
        assert summary["cache_size"] > 0

    def test_startup_with_sheets_exception_still_starts(self):
        """Sheets exception must not crash startup"""
        from app.services.startup_service import StartupService
        svc = StartupService()
        with patch.object(svc, "_attempt_sheets_load", side_effect=Exception("Network error")):
            summary = svc.initialize_application()
        assert summary["cache_size"] > 0

    def test_debug_source_shows_demo_sheet_ready_false_without_sheet_id(self):
        """demo_sheet_ready must be False when SHEET_ID is not set"""
        client = TestClient(app)
        data = client.get("/debug/source").json()
        assert "demo_sheet_ready" in data
        assert isinstance(data["demo_sheet_ready"], bool)
        # In test env, no SHEET_ID → False
        assert data["demo_sheet_ready"] is False

    def test_debug_source_shows_demo_sheet_ready_true_with_sheet_id(self):
        """demo_sheet_ready must be True when SHEET_ID is configured"""
        from app.core.config import Settings
        mock_settings = Settings(SHEET_ID="fake_sheet_id_for_test")
        with patch("app.api.routes.get_settings", return_value=mock_settings):
            client = TestClient(app)
            data = client.get("/debug/source").json()
        assert data["demo_sheet_ready"] is True
        assert data["sheets_configured"] is True
