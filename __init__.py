"""Terraform Provider Google - Issue Analyzer.

This package analyzes open issues from the Terraform Provider Google repository
to identify available issues related to GCP services including Load Balancers,
Cloud Armor, and Private Service Connect.

The package provides:
- GitHub API client with rate limiting and error handling
- ML-based issue classification using TF-IDF
- Issue availability checking
- Report generation in markdown format
- Structured logging with correlation IDs
- Custom exception hierarchy for precise error handling

Example:
    >>> from github_client import GitHubClient
    >>> from issue_classifier import IssueClassifier
    >>> 
    >>> client = GitHubClient()
    >>> classifier = IssueClassifier()
    >>> issues = client.fetch_all_issues()
    >>> for issue in issues:
    ...     is_relevant, category, confidence = classifier.classify_issue(issue)
    ...     if is_relevant:
    ...         print(f"#{issue['number']}: {category} ({confidence}%)")

Modules:
    config: Configuration settings and validation
    github_client: GitHub API client with rate limiting
    issue_classifier: ML-based issue classification
    availability_checker: Issue availability verification
    report_generator: Markdown report generation
    exceptions: Custom exception classes
    logging_config: Structured logging configuration
    validators: Input validation utilities
    service_definitions: GCP service definitions
    types_definitions: Type definitions and constants
"""

__version__ = "1.0.0"
__author__ = "SCSAndre"
__license__ = "MIT"

# Public API exports
from exceptions import (
    IssueAnalyzerError,
    GitHubAPIError,
    RateLimitExceededError,
    AuthenticationError,
    ClassificationError,
    ConfigurationError,
    ReportGenerationError,
    ValidationError,
)
from logging_config import (
    setup_logging,
    get_logger,
    log_performance,
    LogContext,
)
from config import (
    GITHUB_TOKEN,
    TARGET_REPO,
    MIN_CONFIDENCE_THRESHOLD,
    validate_config,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Exceptions
    "IssueAnalyzerError",
    "GitHubAPIError",
    "RateLimitExceededError",
    "AuthenticationError",
    "ClassificationError",
    "ConfigurationError",
    "ReportGenerationError",
    "ValidationError",
    # Logging
    "setup_logging",
    "get_logger",
    "log_performance",
    "LogContext",
    # Config
    "GITHUB_TOKEN",
    "TARGET_REPO",
    "MIN_CONFIDENCE_THRESHOLD",
    "validate_config",
]

