"""Input validation utilities

This module provides validation and sanitization functions for user input
and data from external sources (Google Sheets, GCS).

Security principles:
- Defense in depth: Multiple layers of validation
- Fail safely: Invalid input is rejected with clear error messages
- Sanitize early: Clean input before processing or logging
- Prevent injection: Remove SQL, XSS, and control character attacks

Validation functions:
- validate_question(): Ensures user questions are valid and safe to process
- validate_sheet_row(): Checks that sheet rows have required structure
- sanitize_input(): Removes potentially dangerous characters and patterns

Example usage:
    >>> is_valid, error = validate_question("How do I register to vote?")
    >>> if not is_valid:
    ...     return {"error": error}
    >>> clean_text = sanitize_input(user_input)
"""

import re
from typing import Tuple, Optional, List

from app.core.constants import (
    MAX_QUESTION_LENGTH,
    MIN_ROW_COLUMNS,
)


def validate_question(question: str) -> Tuple[bool, Optional[str]]:
    """
    Validate question input

    Args:
        question: User's question string

    Returns:
        Tuple of (is_valid, error_message)
    """
    # CHECK 1: Null/empty check
    # WHY: Prevents processing empty requests that waste resources
    if not question:
        return False, "Question cannot be empty"

    # CHECK 2: Type validation
    # WHY: Ensures we're working with string data, not numbers or objects
    if not isinstance(question, str):
        return False, "Question must be a string"

    # CHECK 3: Whitespace-only check
    # WHY: "   " is technically non-empty but has no content to process
    cleaned = question.strip()
    if not cleaned:
        return False, "Question cannot be empty after removing whitespace"

    # CHECK 4: Length validation
    # WHY: Prevents abuse (very long inputs) and ensures reasonable processing time
    # MAX_QUESTION_LENGTH is set to 500 characters - enough for detailed questions
    if len(cleaned) > MAX_QUESTION_LENGTH:
        return False, f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters"

    return True, None


def validate_sheet_row(row: List[str]) -> bool:
    """
    Validate that a sheet row has required fields

    Args:
        row: List of cell values from a sheet row

    Returns:
        bool: True if row is valid
    """
    # Row must have at least MIN_ROW_COLUMNS columns
    # (category, title, overview, steps, documents, tips, next_action)
    if not row or len(row) < MIN_ROW_COLUMNS:
        return False

    # Category and title are required (first two columns)
    category = row[0].strip() if row[0] else ""
    title = row[1].strip() if row[1] else ""

    if not category or not title:
        return False

    return True


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to remove potentially dangerous characters

    Args:
        text: Input text to sanitize

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # STEP 1: Remove control characters (except newline and tab)
    # WHY: Control characters can cause issues in logs, databases, and output
    # We preserve \n and \t as they're commonly used in legitimate input
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # STEP 2: Remove script tags
    # WHY: Prevents XSS (Cross-Site Scripting) attacks if output is ever rendered as HTML
    # Even though we return JSON, defense-in-depth is important
    sanitized = re.sub(
        r'<script[^>]*>.*?</script>',
        '',
        sanitized,
        flags=re.IGNORECASE | re.DOTALL
    )

    # STEP 3: Remove SQL injection patterns
    # WHY: Although we don't use SQL databases, this prevents injection attempts
    # from being logged or processed. Basic protection against common patterns.
    sql_patterns = [
        r'(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b)\s+',
        r';\s*--',
        r'\/\*.*?\*\/',
    ]
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    # STEP 4: Normalize whitespace
    # WHY: Prevents whitespace-based attacks and ensures consistent formatting
    sanitized = re.sub(r'\s+', ' ', sanitized)

    return sanitized.strip()
