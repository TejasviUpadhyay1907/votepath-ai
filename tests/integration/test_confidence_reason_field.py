"""Integration tests for the confidence_reason response field"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestConfidenceReasonField:

    def test_confidence_reason_present_in_response(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert "confidence_reason" in data

    def test_confidence_reason_is_string(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert isinstance(data["confidence_reason"], str)
        assert len(data["confidence_reason"]) > 0

    def test_confidence_reason_for_strong_match_says_high(self):
        # "register to vote" + "voter registration" + "registration" → high confidence
        data = client.post(
            "/ask",
            json={"question": "I want to register to vote, voter registration help"}
        ).json()
        if data["confidence"] == "high":
            assert "high confidence" in data["confidence_reason"]

    def test_confidence_reason_for_medium_match(self):
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        if data["confidence"] == "medium":
            assert "medium confidence" in data["confidence_reason"]
            assert "keyword match" in data["confidence_reason"]

    def test_confidence_reason_for_faq_fallback(self):
        data = client.post("/ask", json={"question": "xyz gibberish 12345"}).json()
        assert data["confidence"] == "low"
        assert "No keyword matches" in data["confidence_reason"]
        assert "faq fallback" in data["confidence_reason"]

    def test_confidence_reason_aligns_with_confidence_field(self):
        """confidence_reason must always mention the same tier as confidence"""
        for question in [
            "How do I register to vote?",
            "What documents do I need?",
            "xyz gibberish",
        ]:
            data = client.post("/ask", json={"question": question}).json()
            confidence = data["confidence"]
            reason = data["confidence_reason"]
            if confidence == "low" and data["matched_keywords"] == 0:
                assert "faq fallback" in reason
            else:
                assert f"{confidence} confidence" in reason

    def test_full_response_contract_has_13_fields(self):
        """All 13 response fields must be present"""
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        expected = [
            "category", "title", "overview", "steps", "documents", "tips",
            "next_action", "matched_keywords", "confidence", "confidence_reason",
            "intent_reason", "system_mode", "served_from_cache"
        ]
        for field in expected:
            assert field in data, f"Missing field: {field}"

    def test_existing_fields_unchanged(self):
        """Ensure no existing fields were broken"""
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert data["category"] == "registration"
        assert isinstance(data["matched_keywords"], int)
        assert data["confidence"] in ["high", "medium", "low"]
        assert isinstance(data["served_from_cache"], bool)
        assert data["system_mode"] in ["sheets", "fallback"]
