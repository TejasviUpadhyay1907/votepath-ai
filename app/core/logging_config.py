"""Logging configuration for VotePath AI Backend"""

import logging
import re
import sys
from datetime import datetime, timezone


class CredentialRedactionFilter(logging.Filter):
    """Filter to redact sensitive credentials from log messages"""
    
    # Patterns for sensitive data
    PATTERNS = [
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]+)', r'api_key=***REDACTED***'),
        (r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]+)', r'token=***REDACTED***'),
        (r'password["\']?\s*[:=]\s*["\']?([^\s"\']+)', r'password=***REDACTED***'),
        (r'secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]+)', r'secret=***REDACTED***'),
        (r'credentials["\']?\s*[:=]\s*["\']?([^\s"\']+)', r'credentials=***REDACTED***'),
        (r'Bearer\s+([a-zA-Z0-9_\-\.]+)', r'Bearer ***REDACTED***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Redact sensitive information from log record
        
        Args:
            record: Log record to filter
            
        Returns:
            bool: Always True (don't filter out the record)
        """
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg, flags=re.IGNORECASE)
        
        # Also redact in args if present
        if record.args:
            redacted_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in self.PATTERNS:
                        arg = re.sub(pattern, replacement, arg, flags=re.IGNORECASE)
                redacted_args.append(arg)
            record.args = tuple(redacted_args)
        
        return True


class StructuredFormatter(logging.Formatter):
    """Structured log formatter with timestamp and context"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with structured information
        
        Args:
            record: Log record to format
            
        Returns:
            str: Formatted log message
        """
        # Add timestamp in ISO 8601 format
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Build structured log message
        log_data = {
            'timestamp': timestamp,
            'level': record.levelname,
            'component': record.name,
            'message': record.getMessage(),
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        # Format as readable string (not JSON for simplicity)
        parts = [f"{k}={v}" for k, v in log_data.items()]
        return " | ".join(parts)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Convert log level string to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Add credential redaction filter
    console_handler.addFilter(CredentialRedactionFilter())
    
    # Set formatter
    formatter = StructuredFormatter()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a component
    
    Args:
        name: Component name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
