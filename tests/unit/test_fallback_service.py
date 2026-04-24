"""Unit tests for FallbackService"""

import pytest
from app.services.fallback_service import FallbackService

EXPECTED_CATEGORIES = [
    "first_time_voter", "registration", "documents", "correction",
    "status_check", "polling_day", "timeline", "faq"
]
REQUIRED_FIELDS = ["title", "overview", "steps", "documents", "tips", "next_action"]


@pytest.fixture
def svc():
    return FallbackService()


class TestFallbackServiceCompleteness:

    def test_all_8_categories_present(self, svc):
        data = svc.get_fallback_data()
        for cat in EXPECTED_CATEGORIES:
            assert cat in data, f"Missing category: {cat}"

    def test_each_category_has_required_fields(self, svc):
        data = svc.get_fallback_data()
        for cat, content in data.items():
            for field in REQUIRED_FIELDS:
                assert field in content, f"Category '{cat}' missing field '{field}'"

    def test_steps_are_lists(self, svc):
        data = svc.get_fallback_data()
        for cat, content in data.items():
            assert isinstance(content["steps"], list), f"'{cat}'.steps is not a list"

    def test_documents_are_lists(self, svc):
        data = svc.get_fallback_data()
        for cat, content in data.items():
            assert isinstance(content["documents"], list), f"'{cat}'.documents is not a list"

    def test_tips_are_lists(self, svc):
        data = svc.get_fallback_data()
        for cat, content in data.items():
            assert isinstance(content["tips"], list), f"'{cat}'.tips is not a list"

    def test_title_is_non_empty_string(self, svc):
        data = svc.get_fallback_data()
        for cat, content in data.items():
            assert isinstance(content["title"], str) and content["title"], \
                f"'{cat}'.title is empty or not a string"

    def test_overview_is_non_empty_string(self, svc):
        data = svc.get_fallback_data()
        for cat, content in data.items():
            assert isinstance(content["overview"], str) and content["overview"], \
                f"'{cat}'.overview is empty or not a string"


class TestFallbackServiceGetCategory:

    def test_get_known_category(self, svc):
        data = svc.get_category_data("registration")
        assert data["title"] is not None
        assert len(data["steps"]) > 0

    def test_get_unknown_category_returns_faq(self, svc):
        data = svc.get_category_data("nonexistent_category")
        assert "title" in data  # returns faq fallback

    def test_has_category_true(self, svc):
        assert svc.has_category("registration") is True

    def test_has_category_false(self, svc):
        assert svc.has_category("nonexistent") is False

    def test_get_categories_returns_all_8(self, svc):
        cats = svc.get_categories()
        assert len(cats) == 8
        for cat in EXPECTED_CATEGORIES:
            assert cat in cats

    def test_get_fallback_data_returns_copy(self, svc):
        """Modifying returned data should not affect internal state"""
        data = svc.get_fallback_data()
        data["registration"]["title"] = "MODIFIED"
        original = svc.get_fallback_data()
        assert original["registration"]["title"] != "MODIFIED"
