"""Input validation utilities"""

import re
from typing import Tuple, Optional, List

from app.core.constants import (
    MAX_QUESTION_LENGTH,
    MIN_QUESTION_LENGTH,
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
    if not question:
        return False, "Question cannot be empty"

    if not isinstance(question, str):
        return False, "Question must be a string"

    cleaned = question.strip()
    if not cleaned:
        return False, "Question cannot be empty after removing whitespace"

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

    # Remove control characters except newline and tab
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # Remove potential script tags
    sanitized = re.sub(
        r'<script[^>]*>.*?</script>',
        '',
        sanitized,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove potential SQL injection patterns (basic)
    sql_patterns = [
        r'(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b)\s+',
        r';\s*--',
        r'\/\*.*?\*\/',
    ]
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    # Limit consecutive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized)

    return sanitized.strip()
