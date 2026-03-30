"""Configuration settings for the GitHub issue analyzer.

This module centralizes all configuration parameters for the application,
loading sensitive values from environment variables and providing sensible
defaults for optional settings.

Environment Variables:
    GITHUB_TOKEN: GitHub personal access token for API authentication
    MIN_CONFIDENCE_THRESHOLD: Minimum confidence score (default: 30)
    SMTP_SERVER: SMTP server hostname (default: smtp.gmail.com)
    SMTP_PORT: SMTP server port (default: 587)
    SMTP_USERNAME: Email username for sending reports
    SMTP_PASSWORD: Email password or app password
    EMAIL_FROM: Sender email address (defaults to SMTP_USERNAME)
    TEAM_EMAILS: Comma-separated list of recipient emails

Example:
    >>> from config import GITHUB_TOKEN, validate_config
    >>> result = validate_config()
    >>> if not result['valid']:
    ...     print("Missing config:", result['errors'])
"""

import os
from pathlib import Path
from typing import List, Dict, Any

from .secrets_provider import get_secret


def _get_bool_env(var_name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable with a safe default."""
    value = os.getenv(var_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_float_env(var_name: str, default: float) -> float:
    """Parse a float environment variable with fallback to default."""
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# =============================================================================
# API Configuration
# =============================================================================

#: GitHub personal access token for API authentication.
#: Without a token, API requests are limited to 60/hour.
#: With a token, the limit increases to 5000/hour.
GITHUB_TOKEN: str | None = get_secret("GITHUB_TOKEN")

#: Target repository in "owner/repo" format
TARGET_REPO: str = os.getenv("TARGET_REPO", "hashicorp/terraform-provider-google")


# =============================================================================
# Analysis Thresholds
# =============================================================================

#: Minimum confidence score (0-100) for an issue to be considered relevant.
MIN_CONFIDENCE_THRESHOLD: int = int(os.getenv("MIN_CONFIDENCE_THRESHOLD", "75"))

#: High confidence threshold for priority sorting
HIGH_CONFIDENCE_THRESHOLD: int = 85

#: Medium confidence threshold for categorization
MEDIUM_CONFIDENCE_THRESHOLD: int = 75

#: Weight factor for TF-IDF similarity scores (0.0-1.0)
TFIDF_WEIGHT: float = _get_float_env("TFIDF_WEIGHT", 0.7)

#: Weight factor for regex matching scores (0.0-1.0)
REGEX_WEIGHT: float = _get_float_env("REGEX_WEIGHT", 0.3)

#: Enable trigram shadow scoring comparison without changing final decisions.
ENABLE_TRIGRAM_SHADOW_MODE: bool = _get_bool_env("ENABLE_TRIGRAM_SHADOW_MODE", False)

#: Alert/log threshold for baseline vs shadow confidence score delta.
SHADOW_SCORE_DELTA_THRESHOLD: float = _get_float_env("SHADOW_SCORE_DELTA_THRESHOLD", 15.0)


# =============================================================================
# API Rate Limiting
# =============================================================================

#: Buffer of remaining requests before triggering rate limit wait
RATE_LIMIT_BUFFER: int = 10

#: Delay in seconds between API requests to avoid rate limiting
REQUEST_DELAY: float = 0.5

#: Minimum interval in seconds between calls to /rate_limit endpoint.
RATE_CHECK_INTERVAL: float = 30.0

#: Maximum number of comments before considering an issue "high activity"
COMMENT_THRESHOLD: int = 5

#: Maximum number of retry attempts for failed API requests
MAX_RETRIES: int = 3

#: Initial backoff time in seconds for exponential retry delay
INITIAL_BACKOFF: int = 2


# =============================================================================
# Output Configuration
# =============================================================================

#: Directory for storing generated reports
OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "analysis_results"))


def ensure_output_dir() -> None:
    """Create the output directory if it doesn't exist.

    Call this explicitly from main() rather than at import time to avoid
    side effects during testing, documentation builds, and REPL usage.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Email Configuration
# =============================================================================

#: SMTP server hostname
SMTP_SERVER: str = get_secret('SMTP_SERVER', 'smtp.gmail.com')

#: SMTP server port (587 for TLS, 465 for SSL)
SMTP_PORT: int = int(os.getenv('SMTP_PORT') or '587')

#: SMTP authentication username
SMTP_USERNAME: str = get_secret('SMTP_USERNAME', '')

#: SMTP authentication password (use app password for Gmail)
SMTP_PASSWORD: str = get_secret('SMTP_PASSWORD', '')

#: Email sender address (defaults to SMTP_USERNAME if not set)
EMAIL_FROM: str = get_secret('EMAIL_FROM', SMTP_USERNAME or '')


# =============================================================================
# Confidence Level Constants
# =============================================================================

class ConfidenceLevel:
    """Named constants for confidence levels to avoid magic numbers.
    
    These values represent the confidence scores assigned based on
    where a keyword match was found in an issue.
    
    Attributes:
        LABEL_MATCH: Confidence when keyword found in issue labels (90%)
        TITLE_MATCH: Confidence when keyword found in issue title (85%)
        BODY_MATCH: Confidence when keyword found in issue body (75%)
    """
    
    LABEL_MATCH: float = 90.0
    TITLE_MATCH: float = 85.0
    BODY_MATCH: float = 75.0


# =============================================================================
# Helper Functions
# =============================================================================

def get_team_emails() -> List[str]:
    """Get team email addresses from environment variable.
    
    The TEAM_EMAILS environment variable should contain a comma-separated
    list of email addresses.
    
    Returns:
        List of email addresses, or empty list if not configured.
        
    Example:
        >>> # With TEAM_EMAILS="alice@example.com, bob@example.com"
        >>> emails = get_team_emails()
        >>> print(emails)
        ['alice@example.com', 'bob@example.com']
    """
    emails_str = os.getenv('TEAM_EMAILS', '')
    if not emails_str:
        return []
    return [email.strip() for email in emails_str.split(',') if email.strip()]


def validate_config(raise_on_error: bool = False) -> Dict[str, Any]:
    """Validate required configuration settings.
    
    Checks that all required environment variables are set and have
    valid values.
    
    Args:
        raise_on_error: If True, raises ConfigurationError on validation
            failure instead of returning the error dict.
            
    Returns:
        Dictionary with:
        - valid (bool): True if all required config is present
        - errors (List[str]): List of error messages
        - warnings (List[str]): List of warning messages
        
    Example:
        >>> result = validate_config()
        >>> if not result['valid']:
        ...     for error in result['errors']:
        ...         print(f"Error: {error}")
    """
    from .exceptions import ConfigurationError
    
    errors: List[str] = []
    warnings: List[str] = []
    
    # Check GitHub token (warning, not error - can work without it)
    if not GITHUB_TOKEN:
        warnings.append(
            "GITHUB_TOKEN not set. API requests limited to 60/hour. "
            "Set GITHUB_TOKEN for 5000 requests/hour."
        )
    
    # Validate thresholds
    if not 0 <= MIN_CONFIDENCE_THRESHOLD <= 100:
        errors.append(
            f"MIN_CONFIDENCE_THRESHOLD must be 0-100, got {MIN_CONFIDENCE_THRESHOLD}"
        )
    
    # Validate weights
    if not (0 <= TFIDF_WEIGHT <= 1 and 0 <= REGEX_WEIGHT <= 1):
        errors.append("TFIDF_WEIGHT and REGEX_WEIGHT must be between 0 and 1")
    
    if abs(TFIDF_WEIGHT + REGEX_WEIGHT - 1.0) > 0.01:
        warnings.append(
            f"TFIDF_WEIGHT ({TFIDF_WEIGHT}) + REGEX_WEIGHT ({REGEX_WEIGHT}) "
            f"= {TFIDF_WEIGHT + REGEX_WEIGHT}, consider making them sum to 1.0"
        )
    
    # Check output directory
    if not OUTPUT_DIR.exists():
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            errors.append(f"Cannot create output directory {OUTPUT_DIR}: {e}")
    
    result = {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
    
    if raise_on_error and errors:
        raise ConfigurationError(
            f"Configuration validation failed: {'; '.join(errors)}",
            details={'errors': errors, 'warnings': warnings}
        )
    
    return result


def get_config_summary() -> Dict[str, Any]:
    """Get a summary of current configuration (excluding secrets).
    
    Returns:
        Dictionary with non-sensitive configuration values.
        Sensitive values like tokens and passwords are masked.
    """
    return {
        "target_repo": TARGET_REPO,
        "github_token_set": bool(GITHUB_TOKEN),
        "min_confidence_threshold": MIN_CONFIDENCE_THRESHOLD,
        "high_confidence_threshold": HIGH_CONFIDENCE_THRESHOLD,
        "tfidf_weight": TFIDF_WEIGHT,
        "regex_weight": REGEX_WEIGHT,
        "enable_trigram_shadow_mode": ENABLE_TRIGRAM_SHADOW_MODE,
        "shadow_score_delta_threshold": SHADOW_SCORE_DELTA_THRESHOLD,
        "rate_limit_buffer": RATE_LIMIT_BUFFER,
        "request_delay": REQUEST_DELAY,
        "comment_threshold": COMMENT_THRESHOLD,
        "max_retries": MAX_RETRIES,
        "output_dir": str(OUTPUT_DIR),
        "smtp_server": SMTP_SERVER,
        "smtp_port": SMTP_PORT,
        "smtp_username_set": bool(SMTP_USERNAME),
        "email_from": EMAIL_FROM or "(not set)",
        "team_emails_count": len(get_team_emails()),
    }
