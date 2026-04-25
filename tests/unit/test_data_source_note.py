"""Tests for _build_data_source_note — all 4 message variants."""

import pytest
from unittest.mock import MagicMock
from app.api.routes import _build_data_source_note


def _settings(sheet_id=None, gcs_url=None):
    from app.core.config import Settings
    return Settings(SHEET_ID=sheet_id, GCS_CONTENT_URL=gcs_url)


class TestBuildDataSourceNote:

    def test_sheets_with_verified_gcs(self):
        s = _settings(sheet_id="abc", gcs_url="https://storage.googleapis.com/b/f.json")
        note = _build_data_source_note("sheets", s, gcs_available=True)
        assert "Google Sheets" in note
        assert "verified Google Cloud Storage backup" in note
        assert "Google Cloud Run" in note

    def test_sheets_with_gcs_configured_but_unavailable(self):
        s = _settings(sheet_id="abc", gcs_url="https://storage.googleapis.com/b/f.json")
        note = _build_data_source_note("sheets", s, gcs_available=False)
        assert "Google Sheets" in note
        assert "configured but unavailable" in note

    def test_sheets_without_gcs(self):
        s = _settings(sheet_id="abc", gcs_url=None)
        note = _build_data_source_note("sheets", s, gcs_available=False)
        assert "Google Sheets" in note
        assert "Google Cloud Run" in note
        assert "unavailable" not in note

    def test_gcs_active(self):
        s = _settings(gcs_url="https://storage.googleapis.com/b/f.json")
        note = _build_data_source_note("gcs", s, gcs_available=True)
        assert "Google Cloud Storage" in note
        assert "Google Cloud Run" in note

    def test_fallback(self):
        s = _settings()
        note = _build_data_source_note("fallback", s, gcs_available=False)
        assert "local fallback" in note
        assert "unavailable" in note

    def test_all_notes_are_non_empty_strings(self):
        s = _settings(sheet_id="abc", gcs_url="https://storage.googleapis.com/b/f.json")
        for mode, gcs_avail in [("sheets", True), ("sheets", False), ("gcs", True), ("fallback", False)]:
            note = _build_data_source_note(mode, s, gcs_available=gcs_avail)
            assert isinstance(note, str) and len(note) > 0
