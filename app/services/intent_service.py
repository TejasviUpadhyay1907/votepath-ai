"""Intent detection service using keyword matching"""

import re
from typing import List, Dict, Tuple

# ── Scope guard ───────────────────────────────────────────────
# Keywords that confirm the query is election-domain related
ELECTION_DOMAIN_KEYWORDS: List[str] = [
    "vote", "voter", "voting", "election", "register", "registration",
    "document", "id card", "identification", "correction", "status",
    "polling", "booth", "timeline", "deadline", "application",
    "18", "first vote", "ballot", "candidate", "constituency",
    "electoral", "enroll", "verify", "check my", "polling day",
    "vote online", "online voting", "can i vote online", "remote voting",
]

# Keywords that are clearly non-election topics
OUT_OF_SCOPE_KEYWORDS: List[str] = [
    "ipl", "cricket", "football", "soccer", "basketball", "tennis",
    "movie", "film", "cinema", "netflix", "series", "show",
    "weather", "forecast", "rain", "temperature",
    "pizza", "food", "recipe", "restaurant",
    "stock", "share market", "crypto", "bitcoin", "nifty", "sensex",
    "song", "music", "album", "spotify",
    "game", "gaming", "pubg", "fortnite",
    "news", "politics unrelated", "celebrity",
]

# Bundled out-of-scope response (deterministic, no external call)
OUT_OF_SCOPE_DATA: Dict = {
    "title": "Election Topics Only",
    "overview": (
        "I can help with election-process topics such as voter registration, "
        "required documents, voter ID correction, application status checks, "
        "polling day procedures, election timelines, and FAQs."
    ),
    "steps": [
        "Ask about voter registration",
        "Ask about required documents",
        "Ask about polling day procedures",
        "Ask about your application status",
        "Ask about election timelines and deadlines",
    ],
    "documents": [],
    "tips": [
        'Try asking: "I am 18, what should I do?"',
        'Try asking: "What documents are required to vote?"',
        'Try asking: "How do I check my registration status?"',
    ],
    "next_action": "Please ask an election-related question to get started.",
}


def is_out_of_scope(normalized: str) -> bool:
    """
    Return True if the input is clearly non-election-related.

    Logic:
    - If any OUT_OF_SCOPE_KEYWORDS match AND no ELECTION_DOMAIN_KEYWORDS match → out of scope
    - If election keywords are present, always continue normal detection

    Args:
        normalized: Already-normalized (lowercase, stripped) question

    Returns:
        bool: True if the query should return out_of_scope response
    """
    if not normalized:
        return False

    has_election = any(kw in normalized for kw in ELECTION_DOMAIN_KEYWORDS)
    if has_election:
        return False  # Election context present — proceed normally

    has_unrelated = any(kw in normalized for kw in OUT_OF_SCOPE_KEYWORDS)
    return has_unrelated


# Intent keyword mappings — ordered from most specific to most general
INTENT_KEYWORDS: Dict[str, List[str]] = {
    "first_time_voter": [
        "first time", "new voter", "never voted", "voting for the first time",
        "first voter", "beginner", "new to voting", "haven't voted",
        "first time voter", "my first time", "never voted before",
        "18", "i am 18", "i'm 18", "18 years old", "18 year old",
        "just turned 18", "turned 18", "young voter", "new to elections",
        "eligible to vote", "first election", "first vote"
    ],
    "registration": [
        "register", "registration", "sign up", "enroll",
        "how to register", "register to vote", "voter registration",
        "registering", "want to register", "need to register"
    ],
    "documents": [
        "document", "documents", "what id", "identification", "proof",
        "what do i need", "required documents", "what documents",
        "id card", "what to bring", "documents needed"
    ],
    "correction": [
        "correct", "mistake", "error", "wrong", "fix", "incorrect",
        "update", "change", "modify", "edit", "made a mistake",
        "need to update", "need to change", "need to correct", "correction",
        "correct my", "update my", "change my", "error in my"
    ],
    "status_check": [
        "status", "check", "verify", "confirm", "registered",
        "am i registered", "registration status", "check registration",
        "verify registration", "check if", "check my",
        "track my", "application status", "voter application", "track application"
    ],
    "polling_day": [
        "where to vote", "where do i vote", "polling station",
        "polling place", "voting location", "polling location",
        "where can i vote", "find polling", "vote location",
        "polling day", "election day", "voting day", "where is my polling",
        "find my polling", "where can i cast", "cast my vote",
        "booth", "my booth", "find booth", "polling booth",
        "where is my booth", "booth location", "polling station location"
    ],
    "timeline": [
        "deadline", "when", "important dates", "election dates",
        "registration deadline", "last day", "schedule",
        "timeline", "dates", "when is"
    ],
    "faq": [
        "help", "faq", "general question", "information",
        "tell me about", "can you help", "question",
        "vote online", "online voting", "can i vote online", "remote voting",
    ],
}


def normalize_input(question: str) -> str:
    """
    Normalize input text for consistent processing.

    Converts to lowercase, strips whitespace, collapses multiple spaces,
    and removes punctuation that does not affect meaning.

    Args:
        question: Raw question string

    Returns:
        str: Normalized question
    """
    if not question:
        return ""
    normalized = question.lower()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()
    normalized = re.sub(r'[?!.,;:]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def score_intent(question: str, keywords: List[str]) -> int:
    """
    Count how many keywords from the list appear in the question.

    Args:
        question: Normalized question string
        keywords: List of keywords to match

    Returns:
        int: Number of keyword matches found
    """
    score = 0
    for keyword in keywords:
        if keyword in question:
            score += 1
    return score


def detect_intent_with_metadata(question: str) -> Tuple[str, int, str]:
    """
    Detect user intent and return metadata about the detection.

    Checks scope first — clearly non-election queries return "out_of_scope".
    Unclear/random input defaults to "faq".

    Args:
        question: User's question string

    Returns:
        Tuple of (intent, matched_keywords, confidence)
        - intent: detected category name
        - matched_keywords: number of keywords matched
        - confidence: "high" (>=3), "medium" (1-2), or "low" (0 → faq/out_of_scope)
    """
    normalized = normalize_input(question)

    if not normalized:
        return "faq", 0, "low"

    # Scope guard — check before keyword scoring
    if is_out_of_scope(normalized):
        return "out_of_scope", 0, "low"

    scores: Dict[str, int] = {
        intent: score_intent(normalized, keywords)
        for intent, keywords in INTENT_KEYWORDS.items()
    }

    max_score = max(scores.values())

    if max_score == 0:
        return "faq", 0, "low"

    # Pick the first non-faq intent with the highest score
    best_intent = "faq"
    for intent, score in scores.items():
        if score == max_score and intent != "faq":
            best_intent = intent
            break

    # Assign confidence tier
    if max_score >= 3:
        confidence = "high"
    elif max_score >= 1:
        confidence = "medium"
    else:
        confidence = "low"

    return best_intent, max_score, confidence


def get_matched_keyword_names(question: str, intent: str) -> List[str]:
    """
    Return the list of keywords that actually matched for a given intent.

    Used to build the human-readable intent_reason field.

    Args:
        question: User's question string (will be normalized internally)
        intent: The detected intent category

    Returns:
        List[str]: Keywords that were found in the question
    """
    normalized = normalize_input(question)
    keywords = INTENT_KEYWORDS.get(intent, [])
    return [kw for kw in keywords if kw in normalized]


def build_confidence_reason(matched_keywords: int, confidence: str, intent: str = "") -> str:
    """
    Build a concise explanation of why the confidence level was assigned.

    Args:
        matched_keywords: Number of keywords matched during intent detection
        confidence: Confidence tier ("high", "medium", or "low")
        intent: Optional intent name for special cases

    Returns:
        str: One-sentence human-readable explanation
    """
    if intent == "out_of_scope":
        return "Query is unrelated to election topics → out of scope"
    if matched_keywords == 0:
        return "No keyword matches found → low confidence and faq fallback"
    kw_word = "keyword match" if matched_keywords == 1 else "keyword matches"
    return f"{matched_keywords} {kw_word} → {confidence} confidence"


def build_intent_reason(intent: str, matched: List[str]) -> str:
    """
    Build a concise, human-readable explanation of why an intent was selected.

    Args:
        intent: Detected intent category
        matched: List of matched keyword strings

    Returns:
        str: One-line explanation suitable for the intent_reason response field
    """
    if intent == "out_of_scope":
        return "Detected non-election topic → returned out_of_scope guidance"
    if not matched:
        return f"No strong keyword match found → defaulted to '{intent}'"
    kw_display = ", ".join(f'"{kw}"' for kw in matched[:4])  # cap at 4 for readability
    return f"Detected keywords: {kw_display} → mapped to '{intent}'"


def detect_intent(question: str) -> str:
    """
    Detect user intent from question using keyword matching.

    Args:
        question: User's question string

    Returns:
        str: Detected intent category (defaults to "faq" if no match)
    """
    intent, _, _ = detect_intent_with_metadata(question)
    return intent


def get_supported_intents() -> List[str]:
    """
    Get list of all supported intent categories.

    Returns:
        List[str]: List of intent category names
    """
    return list(INTENT_KEYWORDS.keys())
