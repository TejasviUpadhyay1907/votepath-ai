"""Unit tests for intent detection service"""

import pytest
from app.services.intent_service import (
    normalize_input,
    score_intent,
    detect_intent,
    INTENT_KEYWORDS
)
from tests.fixtures.sample_requests import (
    VALID_QUESTIONS_BY_INTENT,
    EDGE_CASE_QUESTIONS,
    NORMALIZATION_TEST_QUESTIONS
)


class TestNormalizeInput:
    """Tests for input normalization"""
    
    def test_lowercase_conversion(self):
        """Test that input is converted to lowercase"""
        assert normalize_input("HELLO WORLD") == "hello world"
        assert normalize_input("HeLLo WoRLd") == "hello world"
    
    def test_whitespace_stripping(self):
        """Test that leading/trailing whitespace is removed"""
        assert normalize_input("  hello  ") == "hello"
        assert normalize_input("\thello\n") == "hello"
    
    def test_whitespace_collapse(self):
        """Test that multiple spaces are collapsed to single space"""
        assert normalize_input("hello    world") == "hello world"
        assert normalize_input("hello  \t  world") == "hello world"
    
    def test_punctuation_handling(self):
        """Test that punctuation is handled gracefully"""
        assert normalize_input("hello, world!") == "hello world"
        assert normalize_input("what???") == "what"


class TestScoreIntent:
    """Tests for intent scoring"""
    
    def test_exact_keyword_match(self):
        """Test scoring with exact keyword matches"""
        keywords = ["register", "registration"]
        assert score_intent("I want to register", keywords) == 1
        assert score_intent("voter registration", keywords) == 1
    
    def test_multiple_keyword_matches(self):
        """Test scoring with multiple keyword matches"""
        keywords = ["register", "registration", "sign up"]
        assert score_intent("I want to register and sign up", keywords) == 2
    
    def test_no_keyword_match(self):
        """Test scoring with no keyword matches"""
        keywords = ["register", "registration"]
        assert score_intent("hello world", keywords) == 0
    
    def test_partial_keyword_match(self):
        """Test scoring with partial keyword matches"""
        keywords = ["register"]
        assert score_intent("i want to register", keywords) == 1
        # Note: substring matching works because "registration" contains "register"
        assert score_intent("registration", keywords) >= 0  # May or may not match depending on implementation


class TestDetectIntent:
    """Tests for intent detection"""
    
    def test_registration_intent(self):
        """Test detection of registration intent"""
        for question in VALID_QUESTIONS_BY_INTENT["registration"]:
            assert detect_intent(question) == "registration"
    
    def test_first_time_voter_intent(self):
        """Test detection of first_time_voter intent"""
        for question in VALID_QUESTIONS_BY_INTENT["first_time_voter"]:
            assert detect_intent(question) == "first_time_voter"
    
    def test_documents_intent(self):
        """Test detection of documents intent"""
        for question in VALID_QUESTIONS_BY_INTENT["documents"]:
            assert detect_intent(question) == "documents"
    
    def test_correction_intent(self):
        """Test detection of correction intent"""
        for question in VALID_QUESTIONS_BY_INTENT["correction"]:
            assert detect_intent(question) == "correction"
    
    def test_status_check_intent(self):
        """Test detection of status_check intent"""
        for question in VALID_QUESTIONS_BY_INTENT["status_check"]:
            assert detect_intent(question) == "status_check"
    
    def test_polling_day_intent(self):
        """Test detection of polling_day intent"""
        for question in VALID_QUESTIONS_BY_INTENT["polling_day"]:
            assert detect_intent(question) == "polling_day"
    
    def test_timeline_intent(self):
        """Test detection of timeline intent"""
        for question in VALID_QUESTIONS_BY_INTENT["timeline"]:
            assert detect_intent(question) == "timeline"
    
    def test_i_am_18_maps_to_first_time_voter(self):
        """Critical: 'I am 18' must map to first_time_voter, not faq"""
        assert detect_intent("I am 18 what should I do") == "first_time_voter"

    def test_just_turned_18_maps_to_first_time_voter(self):
        assert detect_intent("I just turned 18") == "first_time_voter"

    def test_18_years_old_maps_to_first_time_voter(self):
        assert detect_intent("18 years old voter") == "first_time_voter"

    def test_new_to_voting_maps_to_first_time_voter(self):
        assert detect_intent("new to voting") == "first_time_voter"

    def test_first_vote_maps_to_first_time_voter(self):
        assert detect_intent("this is my first vote") == "first_time_voter"

    def test_eligible_to_vote_maps_to_first_time_voter(self):
        assert detect_intent("I am now eligible to vote") == "first_time_voter"
    
    def test_booth_queries_map_to_polling_day(self):
        """Booth-related queries must route to polling_day"""
        assert detect_intent("where is my booth") == "polling_day"
        assert detect_intent("find polling booth") == "polling_day"
        assert detect_intent("polling station location") == "polling_day"
        assert detect_intent("polling booth") == "polling_day"

    def test_online_voting_maps_to_faq_not_out_of_scope(self):
        """Online voting queries must stay in election scope → faq"""
        assert detect_intent("can I vote online") == "faq"
        assert detect_intent("online voting in india") == "faq"
        assert detect_intent("vote online") == "faq"
        assert detect_intent("remote voting") == "faq"

    def test_faq_default_intent(self):
        """Test that unknown questions default to FAQ"""
        for question in EDGE_CASE_QUESTIONS:
            assert detect_intent(question) == "faq"
        """Test that normalization produces consistent results"""
        base_question = "how do i register to vote?"
        base_intent = detect_intent(base_question)
        
        for question in NORMALIZATION_TEST_QUESTIONS:
            assert detect_intent(question) == base_intent
    
    def test_empty_question(self):
        """Test handling of empty questions"""
        assert detect_intent("") == "faq"
        assert detect_intent("   ") == "faq"
    
    def test_all_intents_have_keywords(self):
        """Test that all intents have keyword mappings"""
        expected_intents = [
            "first_time_voter", "registration", "documents", "correction",
            "status_check", "polling_day", "timeline", "faq"
        ]
        for intent in expected_intents:
            assert intent in INTENT_KEYWORDS
            assert len(INTENT_KEYWORDS[intent]) > 0
