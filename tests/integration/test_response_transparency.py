"""Integration tests for the 3 transparency fields: intent_reason, system_mode, served_from_cache"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestIntentReason:

    def test_intent_reason_present_in_response(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert "intent_reason" in data

    def test_intent_reason_is_string(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert isinstance(data["intent_reason"], str)
        assert len(data["intent_reason"]) > 0

    def test_intent_reason_contains_matched_keywords_for_strong_match(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        # Should mention detected keywords
        assert "Detected keywords" in data["intent_reason"] or "register" in data["intent_reason"]

    def test_intent_reason_shows_mapped_category(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert data["category"] in data["intent_reason"]

    def test_intent_reason_fallback_message_for_unknown_question(self):
        data = client.post("/ask", json={"question": "xyz123 gibberish"}).json()
        assert "No strong keyword match" in data["intent_reason"] or "defaulted" in data["intent_reason"]

    def test_intent_reason_for_documents_intent(self):
        data = client.post("/ask", json={"question": "What documents do I need to vote?"}).json()
        assert "intent_reason" in data
        assert "documents" in data["intent_reason"]

    def test_intent_reason_for_polling_day_intent(self):
        data = client.post("/ask", json={"question": "Where do I vote on election day?"}).json()
        assert "intent_reason" in data
        assert "polling_day" in data["intent_reason"]


class TestSystemMode:

    def test_system_mode_present_in_response(self):
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        assert "system_mode" in data

    def test_system_mode_is_valid_value(self):
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        assert data["system_mode"] in ["sheets", "fallback"]

    def test_system_mode_is_string(self):
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        assert isinstance(data["system_mode"], str)

    def test_system_mode_consistent_across_requests(self):
        """Same deployment state should return same mode"""
        r1 = client.post("/ask", json={"question": "How do I register?"}).json()
        r2 = client.post("/ask", json={"question": "What documents do I need?"}).json()
        assert r1["system_mode"] == r2["system_mode"]

    def test_system_mode_without_sheet_id_is_fallback(self):
        """In test environment (no SHEET_ID), mode should be fallback"""
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        # Test environment has no SHEET_ID configured
        assert data["system_mode"] == "fallback"


class TestServedFromCache:

    def test_served_from_cache_present_in_response(self):
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        assert "served_from_cache" in data

    def test_served_from_cache_is_boolean(self):
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        assert isinstance(data["served_from_cache"], bool)

    def test_served_from_cache_true_when_cache_populated(self):
        """served_from_cache reflects actual cache state at request time"""
        # Pre-populate cache to simulate post-startup state
        from app.utils.cache import get_cache
        from app.services.fallback_service import FallbackService
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())

        data = client.post("/ask", json={"question": "How do I register?"}).json()
        assert data["served_from_cache"] is True

    def test_served_from_cache_consistent_for_same_intent(self):
        r1 = client.post("/ask", json={"question": "How do I register?"}).json()
        r2 = client.post("/ask", json={"question": "voter registration process"}).json()
        # Both map to registration — both should have same cache state
        assert r1["served_from_cache"] == r2["served_from_cache"]


class TestAllThreeFieldsTogether:

    def test_all_three_fields_present_simultaneously(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert "intent_reason" in data
        assert "system_mode" in data
        assert "served_from_cache" in data

    def test_all_existing_fields_still_present(self):
        """Ensure backward compatibility — no existing fields removed"""
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        for field in ["category", "title", "overview", "steps", "documents",
                      "tips", "next_action", "matched_keywords", "confidence"]:
            assert field in data, f"Missing field: {field}"

    def test_full_response_contract(self):
        """Verify the complete response contract with all 14 fields"""
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        expected_fields = [
            "category", "title", "overview", "steps", "documents", "tips",
            "next_action", "matched_keywords", "confidence", "confidence_reason",
            "intent_reason", "system_mode", "served_from_cache", "data_source_note"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
