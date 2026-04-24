"""Tests for intent explainability helpers: get_matched_keyword_names and build_intent_reason"""

import pytest
from app.services.intent_service import (
    get_matched_keyword_names,
    build_intent_reason,
)


class TestGetMatchedKeywordNames:

    def test_returns_matched_keywords_for_registration(self):
        matched = get_matched_keyword_names("How do I register to vote?", "registration")
        assert len(matched) > 0
        assert any("register" in kw for kw in matched)

    def test_returns_empty_list_for_no_match(self):
        matched = get_matched_keyword_names("xyz abc 123", "registration")
        assert matched == []

    def test_returns_empty_list_for_unknown_intent(self):
        matched = get_matched_keyword_names("How do I register?", "nonexistent_intent")
        assert matched == []

    def test_returns_multiple_matches_when_present(self):
        matched = get_matched_keyword_names(
            "I want to register and complete voter registration", "registration"
        )
        assert len(matched) >= 2

    def test_case_insensitive_matching(self):
        matched = get_matched_keyword_names("HOW DO I REGISTER TO VOTE", "registration")
        # normalize_input lowercases, so keywords should still match
        assert len(matched) > 0

    def test_faq_intent_matched_keywords(self):
        matched = get_matched_keyword_names("I need help with a question", "faq")
        assert len(matched) > 0


class TestBuildIntentReason:

    def test_matched_keywords_produces_descriptive_reason(self):
        reason = build_intent_reason("registration", ["register", "voter registration"])
        assert "register" in reason
        assert "registration" in reason
        assert "→" in reason

    def test_no_match_produces_fallback_reason(self):
        reason = build_intent_reason("faq", [])
        assert "No strong keyword match" in reason
        assert "faq" in reason
        assert "defaulted" in reason

    def test_reason_caps_at_4_keywords(self):
        many_keywords = ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6"]
        reason = build_intent_reason("registration", many_keywords)
        # Should not list all 6 — capped at 4
        assert "kw5" not in reason
        assert "kw6" not in reason

    def test_reason_is_a_string(self):
        reason = build_intent_reason("documents", ["document", "id card"])
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_reason_includes_intent_name(self):
        reason = build_intent_reason("polling_day", ["polling station"])
        assert "polling_day" in reason
