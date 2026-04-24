"""Unit tests for scope detection (out_of_scope vs election domain)"""

import pytest
from app.services.intent_service import detect_intent, detect_intent_with_metadata, is_out_of_scope, normalize_input


class TestIsOutOfScope:

    def test_ipl_is_out_of_scope(self):
        assert is_out_of_scope(normalize_input("ipl")) is True

    def test_cricket_is_out_of_scope(self):
        assert is_out_of_scope(normalize_input("cricket score")) is True

    def test_weather_is_out_of_scope(self):
        assert is_out_of_scope(normalize_input("weather today")) is True

    def test_movie_is_out_of_scope(self):
        assert is_out_of_scope(normalize_input("movie recommendation")) is True

    def test_pizza_is_out_of_scope(self):
        assert is_out_of_scope(normalize_input("pizza near me")) is True

    def test_stock_market_is_out_of_scope(self):
        assert is_out_of_scope(normalize_input("stock market")) is True

    def test_election_keyword_overrides_unrelated(self):
        """If election keyword present, never out_of_scope even with unrelated words"""
        assert is_out_of_scope(normalize_input("cricket and voter registration")) is False

    def test_random_text_is_not_out_of_scope(self):
        """Random gibberish should fall through to faq, not out_of_scope"""
        assert is_out_of_scope(normalize_input("asdfgh")) is False

    def test_empty_string_is_not_out_of_scope(self):
        assert is_out_of_scope("") is False

    def test_online_voting_is_not_out_of_scope(self):
        """Online voting must stay in election scope"""
        assert is_out_of_scope(normalize_input("can I vote online")) is False
        assert is_out_of_scope(normalize_input("online voting")) is False
        assert is_out_of_scope(normalize_input("vote online")) is False


class TestDetectIntentOutOfScope:

    def test_ipl_returns_out_of_scope(self):
        assert detect_intent("ipl") == "out_of_scope"

    def test_cricket_returns_out_of_scope(self):
        assert detect_intent("cricket") == "out_of_scope"

    def test_weather_returns_out_of_scope(self):
        assert detect_intent("weather today") == "out_of_scope"

    def test_movie_returns_out_of_scope(self):
        assert detect_intent("movie recommendation") == "out_of_scope"

    def test_football_returns_out_of_scope(self):
        assert detect_intent("football match") == "out_of_scope"

    def test_song_returns_out_of_scope(self):
        assert detect_intent("song lyrics") == "out_of_scope"

    def test_election_queries_not_affected(self):
        assert detect_intent("I am 18 what should I do") == "first_time_voter"
        assert detect_intent("How do I register to vote") == "registration"
        assert detect_intent("What documents are required") == "documents"

    def test_faq_fallback_still_works(self):
        assert detect_intent("asdfgh") == "faq"
        assert detect_intent("vote") == "faq"
        assert detect_intent("election help") == "faq"

    def test_out_of_scope_metadata(self):
        intent, kw, conf = detect_intent_with_metadata("ipl")
        assert intent == "out_of_scope"
        assert kw == 0
        assert conf == "low"


class TestOutOfScopeApiResponse:
    """Integration-style tests for out_of_scope response via TestClient"""

    def test_out_of_scope_response_has_all_fields(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.utils.cache import get_cache
        from app.services.fallback_service import FallbackService
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.post("/ask", json={"question": "ipl"}).json()
        assert data["category"] == "out_of_scope"
        for field in ["title", "overview", "steps", "documents", "tips", "next_action",
                      "matched_keywords", "confidence", "confidence_reason",
                      "intent_reason", "system_mode", "served_from_cache", "data_source_note"]:
            assert field in data, f"Missing field: {field}"

    def test_out_of_scope_title_is_election_topics_only(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.utils.cache import get_cache
        from app.services.fallback_service import FallbackService
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.post("/ask", json={"question": "cricket"}).json()
        assert data["category"] == "out_of_scope"
        assert "Election" in data["title"]

    def test_out_of_scope_intent_reason_is_descriptive(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.utils.cache import get_cache
        from app.services.fallback_service import FallbackService
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.post("/ask", json={"question": "weather"}).json()
        assert "out_of_scope" in data["intent_reason"]
        assert "non-election" in data["intent_reason"]

    def test_out_of_scope_steps_are_election_suggestions(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.utils.cache import get_cache
        from app.services.fallback_service import FallbackService
        cache = get_cache()
        if cache.size() == 0:
            cache.populate(FallbackService().get_fallback_data())
        client = TestClient(app)
        data = client.post("/ask", json={"question": "movie"}).json()
        assert len(data["steps"]) > 0
        assert len(data["tips"]) > 0
