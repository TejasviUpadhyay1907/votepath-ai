"""Pytest configuration and fixtures for VotePath AI Backend tests"""

import pytest
from typing import Dict
from app.core.config import Settings
from app.utils.cache import CacheManager


@pytest.fixture
def test_config():
    """Fixture providing test configuration"""
    return Settings(
        SHEET_ID=None,
        WORKSHEET_NAME="Test_Sheet",
        ACCESS_MODE="fallback",
        CREDENTIALS_PATH=None,
        APP_NAME="VotePath AI Test",
        APP_VERSION="1.0.0-test",
        PORT=8080,
        LOG_LEVEL="DEBUG",
        CACHE_ENABLED=True,
        RESPONSE_TIMEOUT_MS=500
    )


@pytest.fixture
def test_cache():
    """Fixture providing a fresh cache instance"""
    cache = CacheManager()
    yield cache
    cache.clear()


@pytest.fixture
def sample_response_data():
    """Fixture providing sample response data"""
    return {
        "category": "registration",
        "title": "Voter Registration Guide",
        "overview": "Learn how to register to vote",
        "steps": [
            "Visit the registration website",
            "Fill out the form",
            "Submit your application"
        ],
        "documents": [
            "Valid ID",
            "Proof of address"
        ],
        "tips": [
            "Register early",
            "Double-check your information"
        ],
        "next_action": "Wait for confirmation email"
    }


@pytest.fixture
def sample_questions():
    """Fixture providing sample questions for each intent"""
    return {
        "first_time_voter": "I'm voting for the first time, what do I need to know?",
        "registration": "How do I register to vote?",
        "documents": "What documents do I need to vote?",
        "correction": "I made a mistake on my registration, how do I fix it?",
        "status_check": "How can I check if I'm registered?",
        "polling_day": "Where do I vote on election day?",
        "timeline": "When are the registration deadlines?",
        "faq": "I have a general question about voting"
    }


@pytest.fixture
def invalid_questions():
    """Fixture providing invalid question inputs"""
    return [
        "",  # Empty string
        " ",  # Whitespace only
        "a" * 501,  # Too long (>500 chars)
    ]
