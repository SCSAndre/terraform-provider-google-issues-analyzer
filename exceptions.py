"""Custom exceptions for the GitHub issue analyzer.

This module defines domain-specific exceptions to provide clear error handling
and meaningful error messages throughout the application.
"""

from typing import Optional, Dict, Any


class IssueAnalyzerError(Exception):
    """Base exception for all issue analyzer errors.
    
    All custom exceptions in this package should inherit from this class
    to allow catching all analyzer-specific errors with a single except clause.
    
    Attributes:
        message: Human-readable error description
        details: Optional dictionary with additional context
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message
    
    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        if self.details:
            return f"{class_name}(message={self.message!r}, details={self.details!r})"
        return f"{class_name}(message={self.message!r})"


class GitHubAPIError(IssueAnalyzerError):
    """Exception raised when GitHub API calls fail.
    
    Attributes:
        message: Error description
        status_code: HTTP status code (if available)
        response_body: The API response body (if available)
        endpoint: The API endpoint that failed
        details: Additional error context
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.response_body = response_body
        self.endpoint = endpoint
        super().__init__(message, details)
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")
        return " | ".join(parts)


class RateLimitExceededError(GitHubAPIError):
    """Exception raised when GitHub API rate limit is exceeded.
    
    Attributes:
        reset_time: Datetime when rate limit resets
        remaining: Number of requests remaining (usually 0)
    """
    
    def __init__(
        self, 
        message: str = "GitHub API rate limit exceeded",
        reset_time: Optional[Any] = None,
        remaining: Optional[int] = None
    ):
        from datetime import datetime
        self.reset_time = reset_time
        self.remaining = remaining
        
        # Build message with details
        parts = [message]
        if remaining is not None:
            parts.append(f"Remaining: {remaining}")
        if reset_time:
            if isinstance(reset_time, datetime):
                parts.append(f"Reset: {reset_time.isoformat()}")
            else:
                parts.append(f"Reset: {reset_time}")
        
        super().__init__(
            " | ".join(parts), 
            status_code=429,
            details={"reset_time": str(reset_time) if reset_time else None, "remaining": remaining}
        )


class AuthenticationError(GitHubAPIError):
    """Exception raised when GitHub authentication fails.
    
    This typically occurs when the GITHUB_TOKEN is invalid or expired.
    """
    
    def __init__(self, message: str = "GitHub authentication failed", status_code: int = 401):
        super().__init__(message, status_code=status_code)


class NetworkError(GitHubAPIError):
    """Exception raised when network communication fails.
    
    This covers connection errors, timeouts, DNS failures, etc.
    
    Attributes:
        original_error: The underlying network exception
    """
    
    def __init__(
        self, 
        message: str = "Network error occurred",
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.original_error = original_error
        super().__init__(message, details=details)


class ResourceNotFoundError(GitHubAPIError):
    """Exception raised when a requested resource is not found.
    
    Typically maps to HTTP 404 responses.
    """
    
    def __init__(self, message: str = "Resource not found", status_code: int = 404):
        super().__init__(message, status_code=status_code)


class ClassificationError(IssueAnalyzerError):
    """Exception raised when issue classification fails.
    
    Attributes:
        issue_number: The issue number that failed to classify
        classification_type: The type of classification that failed
    """
    
    def __init__(
        self, 
        message: str, 
        issue_number: Optional[int] = None,
        classification_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.issue_number = issue_number
        self.classification_type = classification_type
        
        # Include issue number in message if provided
        parts = [message]
        if issue_number is not None:
            parts.append(f"Issue: #{issue_number}")
        if classification_type:
            parts.append(f"Type: {classification_type}")
        
        super().__init__(" | ".join(parts), details)


class ConfigurationError(IssueAnalyzerError):
    """Exception raised when configuration is invalid or missing.
    
    Attributes:
        config_key: The configuration key that is problematic
        config_value: The problematic value (if safe to include)
    """
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.config_key = config_key
        self.config_value = config_value
        
        parts = [message]
        if config_key:
            parts.append(f"Key: {config_key}")
        
        super().__init__(" | ".join(parts), details)


class ReportGenerationError(IssueAnalyzerError):
    """Exception raised when report generation fails.
    
    Attributes:
        report_type: The type of report being generated (e.g., 'markdown', 'html')
        output_path: The path where the report was being written
    """
    
    def __init__(
        self, 
        message: str, 
        report_type: Optional[str] = None,
        output_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.report_type = report_type
        self.output_path = output_path
        
        parts = [message]
        if report_type:
            parts.append(f"Type: {report_type}")
        if output_path:
            parts.append(f"Path: {output_path}")
        
        super().__init__(" | ".join(parts), details)


class ValidationError(IssueAnalyzerError):
    """Exception raised when data validation fails.
    
    Attributes:
        field_name: The field that failed validation
        invalid_value: The invalid value (if safe to include)
        expected_type: Description of expected type/format
    """
    
    def __init__(
        self, 
        message: str, 
        field_name: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.field_name = field_name
        self.invalid_value = invalid_value
        self.expected_type = expected_type
        
        parts = [message]
        if field_name:
            parts.append(f"Field: {field_name}")
        if expected_type:
            parts.append(f"Expected: {expected_type}")
        
        super().__init__(" | ".join(parts), details)
