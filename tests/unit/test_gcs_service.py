"""Unit tests for GCSService — no real GCS credentials required."""

import json
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from app.services.gcs_service import GCSService, _validate_row, _parse_row


# ── _validate_row ─────────────────────────────────────────────

class TestValidateRow:

    def test_valid_row_passes(self):
        row = {"category": "registration", "title": "T", "overview": "O",
               "steps": [], "documents": [], "tips": [], "next_action": "N"}
        assert _validate_row(row) is True

    def test_missing_field_fails(self):
        row = {"category": "registration", "title": "T"}
        assert _validate_row(row) is False

    def test_empty_category_fails(self):
        row = {"category": "", "title": "T", "overview": "O",
               "steps": [], "documents": [], "tips": [], "next_action": "N"}
        assert _validate_row(row) is False

    def test_non_dict_fails(self):
        assert _validate_row("not a dict") is False
        assert _validate_row(None) is False


# ── _parse_row ────────────────────────────────────────────────

class TestParseRow:

    def test_valid_row_parsed(self):
        row = {"category": "registration", "title": "  Reg Title  ",
               "overview": "Overview", "steps": ["S1", "S2"],
               "documents": ["D1"], "tips": ["T1"], "next_action": "Next"}
        result = _parse_row(row)
        assert result is not None
        cat, data = result
        assert cat == "registration"
        assert data["title"] == "Reg Title"  # stripped
        assert data["steps"] == ["S1", "S2"]

    def test_invalid_row_returns_none(self):
        assert _parse_row({"category": "", "title": "T"}) is None

    def test_empty_lists_normalised(self):
        row = {"category": "faq", "title": "FAQ", "overview": "O",
               "steps": [], "documents": [], "tips": [], "next_action": ""}
        _, data = _parse_row(row)
        assert data["steps"] == []
        assert data["documents"] == []

    def test_non_string_items_in_list_filtered(self):
        row = {"category": "faq", "title": "FAQ", "overview": "O",
               "steps": ["valid", None, 123, "  ", "also valid"],
               "documents": [], "tips": [], "next_action": ""}
        _, data = _parse_row(row)
        assert data["steps"] == ["valid", "also valid"]


# ── GCSService ────────────────────────────────────────────────

class TestGCSServiceConfiguration:

    def test_not_configured_when_url_is_none(self):
        svc = GCSService(None)
        assert svc.is_configured is False

    def test_configured_when_url_is_set(self):
        svc = GCSService("https://storage.googleapis.com/bucket/file.json")
        assert svc.is_configured is True

    def test_not_loaded_initially(self):
        svc = GCSService("https://storage.googleapis.com/bucket/file.json")
        assert svc.is_loaded is False

    def test_load_data_returns_none_when_not_configured(self):
        svc = GCSService(None)
        assert svc.load_data() is None


class TestGCSServiceLoadSuccess:

    def _mock_urlopen(self, payload):
        """Return a context manager mock that yields a response with payload."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: mock_resp
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_valid_json_loads_successfully(self):
        payload = [
            {"category": "registration", "title": "Reg", "overview": "O",
             "steps": ["S1"], "documents": ["D1"], "tips": ["T1"], "next_action": "N"},
            {"category": "faq", "title": "FAQ", "overview": "O",
             "steps": [], "documents": [], "tips": [], "next_action": ""},
        ]
        svc = GCSService("https://storage.googleapis.com/bucket/file.json")
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(payload)):
            result = svc.load_data()
        assert result is not None
        assert "registration" in result
        assert "faq" in result
        assert svc.is_loaded is True

    def test_invalid_rows_skipped(self):
        payload = [
            {"category": "registration", "title": "Reg", "overview": "O",
             "steps": [], "documents": [], "tips": [], "next_action": ""},
            {"category": "", "title": "Bad"},  # invalid
        ]
        svc = GCSService("https://storage.googleapis.com/bucket/file.json")
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(payload)):
            result = svc.load_data()
        assert result is not None
        assert len(result) == 1
        assert "registration" in result

    def test_all_invalid_rows_returns_none(self):
        payload = [{"category": "", "title": "Bad"}]
        svc = GCSService("https://storage.googleapis.com/bucket/file.json")
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(payload)):
            result = svc.load_data()
        assert result is None
        assert svc.is_loaded is False


class TestGCSServiceLoadFailure:

    def test_network_error_returns_none(self):
        import urllib.error
        svc = GCSService("https://storage.googleapis.com/bucket/file.json")
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            result = svc.load_data()
        assert result is None
        assert svc.is_loaded is False

    def test_invalid_json_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not valid json {{{"
        mock_resp.__enter__ = lambda s: mock_resp
        mock_resp.__exit__ = MagicMock(return_value=False)
        svc = GCSService("https://storage.googleapis.com/bucket/file.json")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = svc.load_data()
        assert result is None

    def test_non_array_json_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"key": "value"}).encode()
        mock_resp.__enter__ = lambda s: mock_resp
        mock_resp.__exit__ = MagicMock(return_value=False)
        svc = GCSService("https://storage.googleapis.com/bucket/file.json")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = svc.load_data()
        assert result is None

    def test_unexpected_exception_returns_none(self):
        svc = GCSService("https://storage.googleapis.com/bucket/file.json")
        with patch("urllib.request.urlopen", side_effect=Exception("unexpected")):
            result = svc.load_data()
        assert result is None
