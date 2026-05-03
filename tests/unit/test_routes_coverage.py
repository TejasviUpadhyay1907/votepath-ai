"""Additional tests for routes.py coverage"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRoutesErrorHandling:
    """Test error handling in routes"""

    def test_ask_with_missing_question_field(self):
        """Test /ask with missing question field"""
        response = client.post("/ask", json={})
        assert response.status_code == 422

    def test_ask_with_null_question(self):
        """Test /ask with null question"""
        response = client.post("/ask", json={"question": None})
        assert response.status_code == 422

    def test_ask_with_empty_string(self):
        """Test /ask with empty string"""
        response = client.post("/ask", json={"question": ""})
        assert response.status_code == 422

    def test_ask_with_whitespace_only(self):
        """Test /ask with whitespace only"""
        response = client.post("/ask", json={"question": "   "})
        assert response.status_code == 422

    def test_ask_with_very_long_question(self):
        """Test /ask with question exceeding max length"""
        long_question = "a" * 1001
        response = client.post("/ask", json={"question": long_question})
        assert response.status_code == 422

    def test_ask_with_invalid_json(self):
        """Test /ask with invalid JSON"""
        response = client.post("/ask", data="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    def test_ask_with_wrong_content_type(self):
        """Test /ask with wrong content type"""
        response = client.post("/ask", data="question=test")
        assert response.status_code == 422

    def test_health_check_includes_timestamp(self):
        """Test health check includes timestamp"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_health_check_includes_mode(self):
        """Test health check includes mode"""
        response = client.get("/")
        data = response.json()
        assert "mode" in data
        assert data["mode"] in ["sheets", "gcs", "fallback"]

    def test_categories_returns_list(self):
        """Test categories returns list"""
        response = client.get("/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) == 8

    def test_debug_source_has_all_fields(self):
        """Test debug source has all required fields"""
        response = client.get("/debug/source")
        assert response.status_code == 200
        data = response.json()
        required_fields = [
            "content_source", "cache_loaded", "fallback_active",
            "cache_size", "app_version"
        ]
        for field in required_fields:
            assert field in data

    def test_ui_endpoint_returns_html(self):
        """Test /ui returns HTML"""
        response = client.get("/ui")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_static_files_accessible(self):
        """Test static files are accessible"""
        response = client.get("/static/style.css")
        assert response.status_code == 200

    def test_ask_with_special_characters(self):
        """Test /ask with special characters"""
        response = client.post("/ask", json={"question": "How do I register? @#$%"})
        assert response.status_code == 200
        data = response.json()
        assert "category" in data

    def test_ask_with_unicode(self):
        """Test /ask with unicode characters"""
        response = client.post("/ask", json={"question": "मतदान कैसे करें"})
        assert response.status_code == 200
        data = response.json()
        assert "category" in data

    def test_ask_response_has_all_13_fields(self):
        """Test /ask response has all 13 required fields"""
        response = client.post("/ask", json={"question": "register"})
        data = response.json()
        required_fields = [
            "category", "title", "overview", "steps", "documents",
            "tips", "next_action", "matched_keywords", "confidence",
            "confidence_reason", "intent_reason", "system_mode",
            "served_from_cache", "data_source_note"
        ]
        for field in required_fields:
            assert field in data

    def test_categories_includes_all_8(self):
        """Test categories includes all 8 required categories"""
        response = client.get("/categories")
        data = response.json()
        required = [
            "first_time_voter", "registration", "documents", "correction",
            "status_check", "polling_day", "timeline", "faq"
        ]
        for cat in required:
            assert cat in data["categories"]

    def test_debug_source_no_secrets(self):
        """Test debug source doesn't expose secrets"""
        response = client.get("/debug/source")
        data = response.json()
        content = str(data).lower()
        assert "password" not in content
        assert "secret" not in content
        assert "key" not in content
        assert "token" not in content
