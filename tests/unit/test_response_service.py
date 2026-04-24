"""Unit tests for ResponseService"""

import pytest
from app.services.response_service import ResponseService
from app.models.schemas import QuestionResponse


@pytest.fixture
def svc():
    return ResponseService()


@pytest.fixture
def full_data():
    return {
        "title": "Voter Registration Guide",
        "overview": "How to register to vote",
        "steps": ["Step 1", "Step 2", "Step 3"],
        "documents": ["ID card", "Proof of address"],
        "tips": ["Register early", "Double-check info"],
        "next_action": "Visit the registration portal",
    }


class TestFormatResponse:

    def test_all_fields_populated(self, svc, full_data):
        resp = svc.format_response("registration", full_data)
        assert resp.category == "registration"
        assert resp.title == "Voter Registration Guide"
        assert resp.overview == "How to register to vote"
        assert resp.steps == ["Step 1", "Step 2", "Step 3"]
        assert resp.documents == ["ID card", "Proof of address"]
        assert resp.tips == ["Register early", "Double-check info"]
        assert resp.next_action == "Visit the registration portal"

    def test_missing_title_gets_default(self, svc):
        resp = svc.format_response("faq", {"overview": "Some overview"})
        assert resp.title == "Election Information"

    def test_missing_overview_gets_default(self, svc):
        resp = svc.format_response("faq", {"title": "FAQ"})
        assert len(resp.overview) > 0

    def test_missing_next_action_gets_default(self, svc):
        resp = svc.format_response("faq", {"title": "FAQ", "overview": "Overview"})
        assert len(resp.next_action) > 0

    def test_empty_dict_returns_safe_defaults(self, svc):
        resp = svc.format_response("faq", {})
        assert isinstance(resp, QuestionResponse)
        assert resp.category == "faq"
        assert isinstance(resp.steps, list)
        assert isinstance(resp.documents, list)
        assert isinstance(resp.tips, list)

    def test_non_list_steps_becomes_empty_list(self, svc):
        resp = svc.format_response("faq", {"title": "T", "steps": "not a list"})
        assert resp.steps == []

    def test_non_list_documents_becomes_empty_list(self, svc):
        resp = svc.format_response("faq", {"title": "T", "documents": 123})
        assert resp.documents == []

    def test_strips_whitespace_from_strings(self, svc):
        resp = svc.format_response("faq", {"title": "  FAQ  ", "overview": "  Overview  "})
        assert resp.title == "FAQ"
        assert resp.overview == "Overview"

    def test_filters_empty_strings_from_lists(self, svc):
        resp = svc.format_response("faq", {"title": "T", "steps": ["Step 1", "", "  ", "Step 2"]})
        assert resp.steps == ["Step 1", "Step 2"]

    def test_returns_question_response_type(self, svc, full_data):
        resp = svc.format_response("registration", full_data)
        assert isinstance(resp, QuestionResponse)


class TestEnsureCompleteResponse:

    def test_fills_empty_category(self, svc):
        resp = QuestionResponse(category="", title="T", overview="O", next_action="N")
        result = svc.ensure_complete_response(resp)
        assert result.category == "faq"

    def test_fills_empty_title(self, svc):
        resp = QuestionResponse(category="faq", title="", overview="O", next_action="N")
        result = svc.ensure_complete_response(resp)
        assert result.title == "Election Information"

    def test_none_steps_becomes_empty_list(self, svc):
        """Pydantic v2 rejects None for list fields — ensure format_response handles it"""
        resp = svc.format_response("faq", {"title": "T", "overview": "O", "steps": None})
        assert resp.steps == []
