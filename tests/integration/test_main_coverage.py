"""
Coverage tests for app/main.py — lifespan, endpoints, frontend serving.
Uses TestClient which triggers the lifespan context manager.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


# TestClient with lifespan=True triggers the full startup/shutdown sequence
@pytest.fixture(scope="module")
def client_with_lifespan():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


class TestLifespanAndStartup:

    def test_app_starts_via_lifespan(self, client_with_lifespan):
        """Lifespan context runs startup without raising"""
        resp = client_with_lifespan.get("/")
        assert resp.status_code == 200

    def test_app_state_set_after_startup(self, client_with_lifespan):
        """startup_mode and sheets_loaded are set on app.state"""
        assert hasattr(app.state, "startup_mode")
        assert hasattr(app.state, "sheets_loaded")
        assert app.state.startup_mode in ("sheets", "fallback")
        assert isinstance(app.state.sheets_loaded, bool)

    def test_health_endpoint_via_lifespan_client(self, client_with_lifespan):
        """GET / returns healthy status after full startup"""
        data = client_with_lifespan.get("/").json()
        assert data["status"] == "healthy"
        assert data["mode"] in ("sheets", "fallback")

    def test_categories_endpoint_via_lifespan_client(self, client_with_lifespan):
        """GET /categories returns all 8 categories after startup"""
        data = client_with_lifespan.get("/categories").json()
        assert len(data["categories"]) == 8

    def test_ask_endpoint_via_lifespan_client(self, client_with_lifespan):
        """POST /ask works after full startup"""
        resp = client_with_lifespan.post("/ask", json={"question": "How do I register?"})
        assert resp.status_code == 200
        assert resp.json()["category"] == "registration"


class TestFrontendEndpoint:

    def test_ui_endpoint_returns_html(self):
        """GET /ui serves the frontend HTML file"""
        client = TestClient(app)
        resp = client.get("/ui")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_ui_contains_votepath_title(self):
        """Frontend HTML contains the app title"""
        client = TestClient(app)
        resp = client.get("/ui")
        assert "VotePath" in resp.text

    def test_static_css_served(self):
        """Static CSS file is accessible"""
        client = TestClient(app)
        resp = client.get("/static/style.css")
        assert resp.status_code == 200
        assert "text/css" in resp.headers["content-type"]

    def test_static_js_served(self):
        """Static JS file is accessible"""
        client = TestClient(app)
        resp = client.get("/static/script.js")
        assert resp.status_code == 200
