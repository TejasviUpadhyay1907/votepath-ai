"""Sample API requests for testing"""

from typing import Dict, List


# Valid questions for each intent category
VALID_QUESTIONS_BY_INTENT: Dict[str, List[str]] = {
    "first_time_voter": [
        "I'm voting for the first time, what do I need to know?",
        "This is my first time voting, can you help?",
        "I've never voted before, where do I start?",
        "First time voter here, what should I do?",
        "New voter guide please"
    ],
    "registration": [
        "How do I register to vote?",
        "Where can I sign up to vote?",
        "I want to register for voting",
        "Voter registration process",
        "How to enroll as a voter?"
    ],
    "documents": [
        "What documents do I need to vote?",
        "What ID should I bring?",
        "Required identification for voting",
        "What proof do I need?",
        "Documents needed at polling station"
    ],
    "correction": [
        "I made a mistake on my registration",
        "How do I correct my voter information?",
        "I need to update my registration",
        "There's an error in my voter details",
        "How to change my registration info?"
    ],
    "status_check": [
        "How can I check if I'm registered?",
        "Am I registered to vote?",
        "Verify my voter registration status",
        "Check my registration",
        "How do I confirm I'm registered?"
    ],
    "polling_day": [
        "Where do I vote on election day?",
        "Find my polling station",
        "Where is my polling place?",
        "Voting location near me",
        "Where can I cast my vote?"
    ],
    "timeline": [
        "When are the registration deadlines?",
        "What are the important dates?",
        "Election timeline",
        "When is the last day to register?",
        "Schedule for upcoming election"
    ],
    "faq": [
        "I have a general question",
        "Can you help me?",
        "Tell me about voting",
        "General information please",
        "I need help with something"
    ]
}


# Invalid request payloads
INVALID_REQUESTS: List[Dict] = [
    {},  # Missing question field
    {"question": ""},  # Empty question
    {"question": " "},  # Whitespace only
    {"question": "a" * 501},  # Too long (>500 chars)
    {"wrong_field": "test"},  # Wrong field name
]


# Valid request payloads
VALID_REQUESTS: List[Dict] = [
    {"question": "How do I register to vote?"},
    {"question": "What documents do I need?"},
    {"question": "Where is my polling station?"},
    {"question": "I'm a first time voter"},
    {"question": "Check my registration status"},
]


# Edge case questions (should default to FAQ)
EDGE_CASE_QUESTIONS: List[str] = [
    "xyz123",  # Random text
    "???",  # Only punctuation
    "hello world",  # Generic greeting
    "test test test",  # Repeated words
    "abcdefghijklmnop",  # No keywords
]


# Questions with multiple intent keywords (should pick highest scoring)
AMBIGUOUS_QUESTIONS: List[str] = [
    "I want to register and check my status",  # registration + status_check
    "What documents do I need to register?",  # documents + registration
    "Where do I vote and what ID do I need?",  # polling_day + documents
]


# Questions with variations in case and punctuation
NORMALIZATION_TEST_QUESTIONS: List[str] = [
    "HOW DO I REGISTER TO VOTE?",  # All caps
    "how do i register to vote?",  # All lowercase
    "How   Do   I   Register   To   Vote?",  # Extra spaces
    "How do I register to vote???",  # Multiple punctuation
    "  How do I register to vote?  ",  # Leading/trailing spaces
]
