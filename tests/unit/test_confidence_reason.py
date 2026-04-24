"""Tests for build_confidence_reason helper"""

import pytest
from app.services.intent_service import build_confidence_reason


class TestBuildConfidenceReason:

    def test_zero_matches_returns_low_fallback_message(self):
        reason = build_confidence_reason(0, "low")
        assert "No keyword matches" in reason
        assert "low confidence" in reason
        assert "faq fallback" in reason

    def test_one_match_returns_medium_singular(self):
        reason = build_confidence_reason(1, "medium")
        assert "1 keyword match" in reason
        assert "medium confidence" in reason
        # Must use singular "match", not "matches"
        assert "matches" not in reason

    def test_two_matches_returns_medium_plural(self):
        reason = build_confidence_reason(2, "medium")
        assert "2 keyword matches" in reason
        assert "medium confidence" in reason

    def test_three_matches_returns_high(self):
        reason = build_confidence_reason(3, "high")
        assert "3 keyword matches" in reason
        assert "high confidence" in reason

    def test_five_matches_returns_high(self):
        reason = build_confidence_reason(5, "high")
        assert "5 keyword matches" in reason
        assert "high confidence" in reason

    def test_returns_string(self):
        assert isinstance(build_confidence_reason(2, "medium"), str)

    def test_result_is_non_empty(self):
        assert len(build_confidence_reason(0, "low")) > 0
        assert len(build_confidence_reason(1, "medium")) > 0
        assert len(build_confidence_reason(3, "high")) > 0

    def test_deterministic_same_input_same_output(self):
        assert build_confidence_reason(2, "medium") == build_confidence_reason(2, "medium")
