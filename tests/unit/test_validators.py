"""Unit tests for input validation utilities"""

import pytest
from app.utils.validators import validate_question, validate_sheet_row, sanitize_input


class TestValidateQuestion:

    def test_valid_question(self):
        ok, err = validate_question("How do I register to vote?")
        assert ok is True
        assert err is None

    def test_empty_string(self):
        ok, err = validate_question("")
        assert ok is False
        assert err is not None

    def test_whitespace_only(self):
        ok, err = validate_question("   ")
        assert ok is False
        assert err is not None

    def test_too_long(self):
        ok, err = validate_question("a" * 501)
        assert ok is False
        assert "500" in err

    def test_exactly_500_chars(self):
        ok, err = validate_question("a" * 500)
        assert ok is True

    def test_non_string_input(self):
        ok, err = validate_question(None)  # type: ignore
        assert ok is False


class TestValidateSheetRow:

    def test_valid_row(self):
        row = ["registration", "Title", "Overview", "Step1|Step2", "Doc1", "Tip1", "Next"]
        assert validate_sheet_row(row) is True

    def test_empty_row(self):
        assert validate_sheet_row([]) is False

    def test_too_few_columns(self):
        assert validate_sheet_row(["registration", "Title"]) is False

    def test_missing_category(self):
        row = ["", "Title", "Overview", "Steps", "Docs", "Tips", "Next"]
        assert validate_sheet_row(row) is False

    def test_missing_title(self):
        row = ["registration", "", "Overview", "Steps", "Docs", "Tips", "Next"]
        assert validate_sheet_row(row) is False

    def test_whitespace_category_treated_as_empty(self):
        row = ["   ", "Title", "Overview", "Steps", "Docs", "Tips", "Next"]
        assert validate_sheet_row(row) is False


class TestSanitizeInput:

    def test_normal_text_unchanged(self):
        result = sanitize_input("How do I register?")
        assert "register" in result

    def test_empty_string(self):
        assert sanitize_input("") == ""

    def test_none_returns_empty(self):
        assert sanitize_input(None) == ""  # type: ignore

    def test_strips_control_characters(self):
        result = sanitize_input("hello\x00world")
        assert "\x00" not in result

    def test_collapses_whitespace(self):
        result = sanitize_input("hello    world")
        assert result == "hello world"

    def test_removes_script_tags(self):
        result = sanitize_input("<script>alert('xss')</script>hello")
        assert "<script>" not in result
        assert "hello" in result
