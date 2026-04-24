"""Integration tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures.sample_requests import (
    VALID_REQUESTS,
    VALID_QUESTIONS_BY_INTENT,
    EDGE_CASE_QUESTIONS,
)

client = TestClient(app)


class TestHealthEndpoint:

    def test_health_check_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_health_check_response_structure(self):
        data = client.get("/").json()
        assert "status" in data
        assert "mode" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
        assert data["mode"] in ["sheets", "fallback"]

    def test_health_check_timestamp_is_string(self):
        data = client.get("/").json()
        assert isinstance(data["timestamp"], str)
        assert len(data["timestamp"]) > 0


class TestCategoriesEndpoint:

    def test_categories_returns_200(self):
        assert client.get("/categories").status_code == 200

    def test_categories_response_structure(self):
        data = client.get("/categories").json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_categories_contains_all_8_intents(self):
        categories = client.get("/categories").json()["categories"]
        expected = [
            "first_time_voter", "registration", "documents", "correction",
            "status_check", "polling_day", "timeline", "faq"
        ]
        for cat in expected:
            assert cat in categories


class TestAskEndpoint:

    def test_valid_question_returns_200(self):
        for req in VALID_REQUESTS:
            assert client.post("/ask", json=req).status_code == 200

    def test_response_has_all_required_fields(self):
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        for field in ["category", "title", "overview", "steps", "documents", "tips", "next_action"]:
            assert field in data

    def test_response_field_types(self):
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        assert isinstance(data["category"], str)
        assert isinstance(data["title"], str)
        assert isinstance(data["overview"], str)
        assert isinstance(data["steps"], list)
        assert isinstance(data["documents"], list)
        assert isinstance(data["tips"], list)
        assert isinstance(data["next_action"], str)

    def test_response_includes_confidence_metadata(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert "confidence" in data
        assert data["confidence"] in ["high", "medium", "low"]

    def test_response_includes_matched_keywords(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert "matched_keywords" in data
        assert isinstance(data["matched_keywords"], int)

    def test_missing_question_returns_422(self):
        assert client.post("/ask", json={}).status_code == 422

    def test_empty_question_returns_422(self):
        assert client.post("/ask", json={"question": ""}).status_code == 422

    def test_whitespace_only_question_returns_422(self):
        assert client.post("/ask", json={"question": "   "}).status_code == 422

    def test_too_long_question_returns_422(self):
        assert client.post("/ask", json={"question": "a" * 501}).status_code == 422

    def test_invalid_json_returns_422(self):
        response = client.post(
            "/ask",
            content=b"not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_registration_intent_detected(self):
        data = client.post("/ask", json={"question": "How do I register to vote?"}).json()
        assert data["category"] == "registration"

    def test_documents_intent_detected(self):
        data = client.post("/ask", json={"question": "What documents do I need?"}).json()
        assert data["category"] == "documents"

    def test_first_time_voter_intent_detected(self):
        data = client.post("/ask", json={"question": "I am voting for the first time"}).json()
        assert data["category"] == "first_time_voter"

    def test_polling_day_intent_detected(self):
        data = client.post("/ask", json={"question": "Where do I vote on election day?"}).json()
        assert data["category"] == "polling_day"

    def test_unknown_question_returns_faq(self):
        for q in EDGE_CASE_QUESTIONS:
            data = client.post("/ask", json={"question": q}).json()
            assert data["category"] == "faq"

    def test_response_content_is_non_empty(self):
        data = client.post("/ask", json={"question": "How do I register?"}).json()
        assert len(data["title"]) > 0
        assert len(data["overview"]) > 0
        assert len(data["next_action"]) > 0

    def test_response_time_under_one_second(self):
        import time
        start = time.time()
        client.post("/ask", json={"question": "How do I register?"})
        assert time.time() - start < 1.0

    def test_all_intents_return_valid_responses(self):
        for intent, questions in VALID_QUESTIONS_BY_INTENT.items():
            resp = client.post("/ask", json={"question": questions[0]})
            assert resp.status_code == 200
            data = resp.json()
            assert data["category"] == intent


class TestDebugSourceEndpoint:

    def test_debug_source_returns_200(self):
        assert client.get("/debug/source").status_code == 200

    def test_debug_source_response_structure(self):
        data = client.get("/debug/source").json()
        assert "content_source" in data
        assert "cache_loaded" in data
        assert "fallback_active" in data
        assert "cache_size" in data
        assert "app_version" in data
        assert "sheets_configured" in data
        assert "sheet_name" in data
        assert "access_mode" in data

    def test_debug_source_sheets_configured_is_bool(self):
        data = client.get("/debug/source").json()
        assert isinstance(data["sheets_configured"], bool)

    def test_debug_source_sheet_name_is_string(self):
        data = client.get("/debug/source").json()
        assert isinstance(data["sheet_name"], str)

    def test_debug_source_access_mode_is_valid(self):
        data = client.get("/debug/source").json()
        assert data["access_mode"] in ["auto", "public", "service_account"]

    def test_debug_source_content_source_is_valid(self):
        data = client.get("/debug/source").json()
        assert data["content_source"] in ["sheets", "fallback"]

    def test_debug_source_cache_loaded_is_bool(self):
        data = client.get("/debug/source").json()
        assert isinstance(data["cache_loaded"], bool)

    def test_debug_source_does_not_expose_secrets(self):
        """Ensure no credentials, tokens, or sheet IDs are in the response"""
        raw = client.get("/debug/source").text
        sensitive_keywords = ["password", "token", "secret", "credential", "private_key"]
        for keyword in sensitive_keywords:
            assert keyword not in raw.lower()

    def test_debug_source_cache_size_is_non_negative(self):
        data = client.get("/debug/source").json()
        assert data["cache_size"] >= 0


class TestErrorHandling:

    def test_invalid_endpoint_returns_404(self):
        assert client.get("/invalid").status_code == 404

    def test_wrong_method_on_ask_returns_405(self):
        assert client.get("/ask").status_code == 405

