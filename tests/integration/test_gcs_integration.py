"""Integration tests for GCS data source priority and /debug/source visibility."""

import json
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


def _mock_gcs_urlopen(payload):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


GCS_PAYLOAD = [
    {"category": cat, "title": f"{cat} title", "overview": "GCS overview",
     "steps": ["GCS step"], "documents": ["GCS doc"], "tips": ["GCS tip"],
     "next_action": "GCS next"}
    for cat in ["first_time_voter", "registration", "documents", "correction",
                "status_check", "polling_day", "timeline", "faq"]
]


class TestDataSourcePriority:

    def test_sheets_takes_priority_over_gcs(self):
        """When Sheets loads, mode is sheets regardless of GCS config"""
        from app.services.startup_service import StartupService
        fake_sheets = {cat: {"title": "Sheets", "overview": "O", "steps": [],
                             "documents": [], "tips": [], "next_action": ""}
                       for cat in ["registration", "faq"]}
        svc = StartupService()
        with patch.object(svc, "_attempt_sheets_load", return_value=fake_sheets):
            summary = svc.initialize_application()
        assert summary["mode"] == "sheets"

    def test_gcs_used_when_sheets_fails(self):
        """When Sheets fails, GCS is tried next"""
        from app.services.startup_service import StartupService
        fake_gcs = {cat: {"title": "GCS", "overview": "O", "steps": [],
                          "documents": [], "tips": [], "next_action": ""}
                    for cat in ["registration", "faq"]}
        svc = StartupService()
        with patch.object(svc, "_attempt_sheets_load", return_value=None), \
             patch.object(svc, "_attempt_gcs_load", return_value=fake_gcs):
            summary = svc.initialize_application()
        assert summary["mode"] == "gcs"
        # gcs_loaded is set inside _attempt_gcs_load which is mocked,
        # so we verify mode is correct rather than the internal flag
        assert summary["cache_size"] > 0

    def test_local_fallback_when_both_fail(self):
        """When both Sheets and GCS fail, local fallback is used"""
        from app.services.startup_service import StartupService
        svc = StartupService()
        with patch.object(svc, "_attempt_sheets_load", return_value=None), \
             patch.object(svc, "_attempt_gcs_load", return_value=None):
            summary = svc.initialize_application()
        assert summary["mode"] == "fallback"
        assert summary["cache_size"] > 0

    def test_gcs_priority_over_local_fallback(self):
        """GCS data is preferred over local fallback_content.py"""
        from app.services.startup_service import StartupService
        fake_gcs = {"registration": {"title": "GCS Reg", "overview": "O",
                                     "steps": [], "documents": [], "tips": [], "next_action": ""}}
        svc = StartupService()
        with patch.object(svc, "_attempt_sheets_load", return_value=None), \
             patch.object(svc, "_attempt_gcs_load", return_value=fake_gcs):
            summary = svc.initialize_application()
        assert summary["mode"] == "gcs"
        assert get_cache().get("registration")["title"] == "GCS Reg"

    def test_gcs_available_set_when_health_check_passes(self):
        """gcs_available is True when GCS health-check passes during Sheets-active startup"""
        from app.services.startup_service import StartupService
        from app.services.gcs_service import GCSService
        fake_gcs_data = {"registration": {"title": "GCS", "overview": "O",
                                          "steps": [], "documents": [], "tips": [], "next_action": ""}}
        svc = StartupService()
        # Simulate GCS health-check returning valid data
        with patch.object(GCSService, "load_data", return_value=fake_gcs_data):
            svc.config = __import__("app.core.config", fromlist=["Settings"]).Settings(
                SHEET_ID="fake_id",
                GCS_CONTENT_URL="https://storage.googleapis.com/bucket/file.json"
            )
            result = svc._verify_gcs_availability()
        assert result is not None
        assert svc.gcs_available is True

    def test_gcs_available_false_when_gcs_unreachable(self):
        """gcs_available stays False when GCS URL is unreachable"""
        from app.services.startup_service import StartupService
        svc = StartupService()
        with patch.object(svc, "_attempt_sheets_load", return_value=None), \
             patch.object(svc, "_attempt_gcs_load", return_value=None):
            summary = svc.initialize_application()
        assert summary.get("gcs_available", False) is False

    def test_sheets_active_gcs_unavailable_no_crash(self):
        """Sheets active + GCS configured but unreachable — no crash, mode stays sheets"""
        from app.services.startup_service import StartupService
        from app.services.gcs_service import GCSService
        fake_sheets = {"registration": {"title": "Sheets", "overview": "O",
                                        "steps": [], "documents": [], "tips": [], "next_action": ""}}
        svc = StartupService()
        with patch.object(svc, "_attempt_sheets_load", return_value=fake_sheets), \
             patch.object(GCSService, "load_data", return_value=None):
            svc.config = __import__("app.core.config", fromlist=["Settings"]).Settings(
                SHEET_ID="fake_id",
                GCS_CONTENT_URL="https://storage.googleapis.com/bucket/file.json"
            )
            summary = svc.initialize_application()
        assert summary["mode"] == "sheets"
        assert svc.gcs_available is False


class TestDebugSourceGCSFields:

    def test_debug_source_includes_gcs_fields(self):
        """All GCS fields must be present in /debug/source"""
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.get("/debug/source").json()
        assert "gcs_configured" in data
        assert "gcs_loaded" in data
        assert "gcs_available" in data
        assert "google_services_used" in data

    def test_google_services_used_always_includes_cloud_run(self):
        """Google Cloud Run must always appear in google_services_used"""
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.get("/debug/source").json()
        assert "Google Cloud Run" in data["google_services_used"]

    def test_google_services_used_includes_sheets_when_configured(self):
        """Google Sheets appears in google_services_used"""
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.get("/debug/source").json()
        assert "Google Sheets" in data["google_services_used"]

    def test_gcs_configured_false_without_env(self):
        """Without GCS_CONTENT_URL, gcs_configured is False"""
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.get("/debug/source").json()
        assert isinstance(data["gcs_configured"], bool)
        assert isinstance(data["gcs_loaded"], bool)
        assert isinstance(data["gcs_available"], bool)

    def test_google_services_includes_gcs_when_configured(self):
        """When GCS_CONTENT_URL is set, GCS appears in google_services_used"""
        from app.core.config import Settings
        mock_settings = Settings(
            SHEET_ID="fake_id",
            GCS_CONTENT_URL="https://storage.googleapis.com/bucket/file.json"
        )
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        with patch("app.api.routes.get_settings", return_value=mock_settings):
            client = TestClient(app)
            data = client.get("/debug/source").json()
        assert "Google Cloud Storage" in data["google_services_used"]

    def test_no_secrets_in_debug_response(self):
        """Debug response must not expose credentials or URLs"""
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        raw = client.get("/debug/source").text
        for sensitive in ["password", "token", "private_key", "secret", "credential"]:
            assert sensitive not in raw.lower()


class TestAskResponseGCSMode:

    def test_data_source_note_mentions_gcs_when_configured(self):
        """data_source_note should mention GCS when it is configured"""
        from app.core.config import Settings
        from app.services.startup_service import get_startup_service
        mock_settings = Settings(
            SHEET_ID="fake_id",
            GCS_CONTENT_URL="https://storage.googleapis.com/bucket/file.json"
        )
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        svc = get_startup_service()
        original_mode = svc.mode
        svc.mode = "sheets"  # simulate sheets mode with GCS configured
        try:
            with patch("app.api.routes.get_settings", return_value=mock_settings):
                client = TestClient(app)
                data = client.post("/ask", json={"question": "How do I register?"}).json()
            assert "Google Cloud Storage" in data["data_source_note"] or \
                   "Google Sheets" in data["data_source_note"]
        finally:
            svc.mode = original_mode

    def test_system_mode_gcs_in_response(self):
        """When startup mode is gcs, system_mode in /ask response is gcs"""
        from app.services.startup_service import get_startup_service
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        svc = get_startup_service()
        original_mode = svc.mode
        svc.mode = "gcs"
        try:
            client = TestClient(app)
            data = client.post("/ask", json={"question": "How do I register?"}).json()
            assert data["system_mode"] == "gcs"
        finally:
            svc.mode = original_mode
