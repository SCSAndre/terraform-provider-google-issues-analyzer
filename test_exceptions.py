"""Tests for the exceptions module.

This module provides comprehensive tests for custom exception classes,
ensuring proper initialization, message formatting, and inheritance.
"""

import pytest
from datetime import datetime

from exceptions import (
    IssueAnalyzerError,
    GitHubAPIError,
    RateLimitExceededError,
    AuthenticationError,
    NetworkError,
    ResourceNotFoundError,
    ClassificationError,
    ConfigurationError,
    ReportGenerationError,
    ValidationError,
)


class TestIssueAnalyzerError:
    """Tests for the base IssueAnalyzerError class."""

    def test_basic_initialization(self):
        """Test basic exception initialization with message."""
        error = IssueAnalyzerError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details is None

    def test_initialization_with_details(self):
        """Test exception initialization with details dictionary."""
        details = {"key": "value", "count": 42}
        error = IssueAnalyzerError("Test error", details=details)
        assert error.details == details
        assert error.details["key"] == "value"

    def test_repr_basic(self):
        """Test __repr__ for basic exception."""
        error = IssueAnalyzerError("Test error")
        repr_str = repr(error)
        assert "IssueAnalyzerError" in repr_str
        assert "Test error" in repr_str

    def test_repr_with_details(self):
        """Test __repr__ with details included."""
        error = IssueAnalyzerError("Test error", details={"foo": "bar"})
        repr_str = repr(error)
        assert "details=" in repr_str

    def test_inheritance(self):
        """Test that IssueAnalyzerError inherits from Exception."""
        error = IssueAnalyzerError("Test")
        assert isinstance(error, Exception)


class TestGitHubAPIError:
    """Tests for GitHubAPIError class."""

    def test_basic_initialization(self):
        """Test basic API error initialization."""
        error = GitHubAPIError("API request failed")
        assert str(error) == "API request failed"
        assert error.status_code is None
        assert error.response_body is None

    def test_with_status_code(self):
        """Test API error with HTTP status code."""
        error = GitHubAPIError("Server error", status_code=500)
        assert error.status_code == 500
        assert "500" in str(error)

    def test_with_response_body(self):
        """Test API error with response body."""
        body = {"message": "Not found", "documentation_url": "..."}
        error = GitHubAPIError(
            "Resource not found",
            status_code=404,
            response_body=body
        )
        assert error.response_body == body
        assert error.status_code == 404

    def test_inheritance(self):
        """Test that GitHubAPIError inherits correctly."""
        error = GitHubAPIError("Test")
        assert isinstance(error, IssueAnalyzerError)
        assert isinstance(error, Exception)


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError class."""

    def test_basic_initialization(self):
        """Test rate limit error with defaults."""
        error = RateLimitExceededError()
        assert "rate limit" in str(error).lower()
        assert error.remaining is None
        assert error.reset_time is None

    def test_with_remaining_requests(self):
        """Test rate limit error with remaining count."""
        error = RateLimitExceededError(remaining=5)
        assert error.remaining == 5
        assert "5" in str(error)

    def test_with_reset_time(self):
        """Test rate limit error with reset time."""
        reset_time = datetime(2024, 1, 15, 12, 0, 0)
        error = RateLimitExceededError(reset_time=reset_time)
        assert error.reset_time == reset_time
        assert "2024" in str(error)

    def test_with_custom_message(self):
        """Test rate limit error with custom message."""
        error = RateLimitExceededError(
            remaining=0,
            reset_time=datetime.now(),
            message="Custom rate limit message"
        )
        assert "Custom rate limit message" in str(error)

    def test_inheritance(self):
        """Test inheritance chain."""
        error = RateLimitExceededError()
        assert isinstance(error, GitHubAPIError)
        assert isinstance(error, IssueAnalyzerError)


class TestAuthenticationError:
    """Tests for AuthenticationError class."""

    def test_basic_initialization(self):
        """Test basic authentication error."""
        error = AuthenticationError("Invalid token")
        assert "Invalid token" in str(error)

    def test_with_status_code(self):
        """Test authentication error with 401 status."""
        error = AuthenticationError(
            "Token expired",
            status_code=401
        )
        assert error.status_code == 401

    def test_with_403_forbidden(self):
        """Test authentication error for forbidden access."""
        error = AuthenticationError(
            "Access forbidden",
            status_code=403
        )
        assert error.status_code == 403

    def test_inheritance(self):
        """Test inheritance chain."""
        error = AuthenticationError("Test")
        assert isinstance(error, GitHubAPIError)


class TestNetworkError:
    """Tests for NetworkError class."""

    def test_basic_initialization(self):
        """Test basic network error."""
        error = NetworkError("Connection failed")
        assert "Connection failed" in str(error)
        assert error.original_error is None

    def test_with_original_error(self):
        """Test network error wrapping original exception."""
        original = ConnectionError("Connection refused")
        error = NetworkError(
            "Failed to connect",
            original_error=original
        )
        assert error.original_error == original
        assert isinstance(error.original_error, ConnectionError)

    def test_repr_with_original(self):
        """Test repr includes original error info."""
        original = TimeoutError("Timeout")
        error = NetworkError("Request timeout", original_error=original)
        repr_str = repr(error)
        assert "NetworkError" in repr_str

    def test_inheritance(self):
        """Test inheritance chain."""
        error = NetworkError("Test")
        assert isinstance(error, GitHubAPIError)


class TestResourceNotFoundError:
    """Tests for ResourceNotFoundError class."""

    def test_basic_initialization(self):
        """Test basic resource not found error."""
        error = ResourceNotFoundError("Issue #123 not found")
        assert "123" in str(error)

    def test_with_status_code(self):
        """Test resource not found with 404 status."""
        error = ResourceNotFoundError(
            "Repository not found",
            status_code=404
        )
        assert error.status_code == 404

    def test_inheritance(self):
        """Test inheritance chain."""
        error = ResourceNotFoundError("Test")
        assert isinstance(error, GitHubAPIError)


class TestClassificationError:
    """Tests for ClassificationError class."""

    def test_basic_initialization(self):
        """Test basic classification error."""
        error = ClassificationError("Classification failed")
        assert "Classification failed" in str(error)
        assert error.issue_number is None
        assert error.classification_type is None

    def test_with_issue_number(self):
        """Test classification error with issue number."""
        error = ClassificationError(
            "Failed to classify",
            issue_number=12345
        )
        assert error.issue_number == 12345
        assert "12345" in str(error)

    def test_with_classification_type(self):
        """Test classification error with type."""
        error = ClassificationError(
            "TF-IDF error",
            classification_type="tfidf"
        )
        assert error.classification_type == "tfidf"

    def test_full_initialization(self):
        """Test classification error with all parameters."""
        error = ClassificationError(
            "Complete failure",
            issue_number=999,
            classification_type="regex",
            details={"pattern": "test.*"}
        )
        assert error.issue_number == 999
        assert error.classification_type == "regex"
        assert error.details["pattern"] == "test.*"

    def test_inheritance(self):
        """Test inheritance chain."""
        error = ClassificationError("Test")
        assert isinstance(error, IssueAnalyzerError)


class TestConfigurationError:
    """Tests for ConfigurationError class."""

    def test_basic_initialization(self):
        """Test basic configuration error."""
        error = ConfigurationError("Missing required setting")
        assert "Missing" in str(error)
        assert error.config_key is None
        assert error.config_value is None

    def test_with_config_key(self):
        """Test configuration error with key."""
        error = ConfigurationError(
            "Invalid value",
            config_key="GITHUB_TOKEN"
        )
        assert error.config_key == "GITHUB_TOKEN"
        assert "GITHUB_TOKEN" in str(error)

    def test_with_config_value(self):
        """Test configuration error with value (masked)."""
        error = ConfigurationError(
            "Invalid port",
            config_key="SMTP_PORT",
            config_value="invalid"
        )
        assert error.config_value == "invalid"

    def test_inheritance(self):
        """Test inheritance chain."""
        error = ConfigurationError("Test")
        assert isinstance(error, IssueAnalyzerError)


class TestReportGenerationError:
    """Tests for ReportGenerationError class."""

    def test_basic_initialization(self):
        """Test basic report generation error."""
        error = ReportGenerationError("Report failed")
        assert "Report failed" in str(error)
        assert error.report_type is None
        assert error.output_path is None

    def test_with_report_type(self):
        """Test report error with type."""
        error = ReportGenerationError(
            "Failed to generate",
            report_type="markdown"
        )
        assert error.report_type == "markdown"
        assert "markdown" in str(error)

    def test_with_output_path(self):
        """Test report error with output path."""
        error = ReportGenerationError(
            "Cannot write file",
            output_path="/tmp/report.md"
        )
        assert error.output_path == "/tmp/report.md"
        assert "/tmp/report.md" in str(error)

    def test_full_initialization(self):
        """Test report error with all parameters."""
        error = ReportGenerationError(
            "Complete failure",
            report_type="html",
            output_path="/var/reports/out.html",
            details={"issues_count": 100}
        )
        assert error.report_type == "html"
        assert error.output_path == "/var/reports/out.html"
        assert error.details["issues_count"] == 100

    def test_inheritance(self):
        """Test inheritance chain."""
        error = ReportGenerationError("Test")
        assert isinstance(error, IssueAnalyzerError)


class TestValidationError:
    """Tests for ValidationError class."""

    def test_basic_initialization(self):
        """Test basic validation error."""
        error = ValidationError("Invalid input")
        assert "Invalid input" in str(error)
        assert error.field_name is None
        assert error.invalid_value is None
        assert error.expected_type is None

    def test_with_field_name(self):
        """Test validation error with field name."""
        error = ValidationError(
            "Invalid field",
            field_name="email"
        )
        assert error.field_name == "email"
        assert "email" in str(error)

    def test_with_invalid_value(self):
        """Test validation error with invalid value."""
        error = ValidationError(
            "Invalid type",
            field_name="count",
            invalid_value="not-a-number"
        )
        assert error.invalid_value == "not-a-number"

    def test_with_expected_type(self):
        """Test validation error with expected type."""
        error = ValidationError(
            "Type mismatch",
            field_name="count",
            invalid_value="abc",
            expected_type="int"
        )
        assert error.expected_type == "int"
        assert "int" in str(error)

    def test_full_initialization(self):
        """Test validation error with all parameters."""
        error = ValidationError(
            "Complete validation failure",
            field_name="threshold",
            invalid_value=-5,
            expected_type="positive int",
            details={"min_value": 0, "max_value": 100}
        )
        assert error.field_name == "threshold"
        assert error.invalid_value == -5
        assert error.expected_type == "positive int"
        assert error.details["min_value"] == 0

    def test_inheritance(self):
        """Test inheritance chain."""
        error = ValidationError("Test")
        assert isinstance(error, IssueAnalyzerError)


class TestExceptionChaining:
    """Tests for exception chaining and wrapping."""

    def test_raise_from_another_exception(self):
        """Test raising exception from another."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise GitHubAPIError("Wrapped error") from e
        except GitHubAPIError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)

    def test_network_error_wrapping(self):
        """Test NetworkError wrapping connection error."""
        try:
            original = ConnectionError("Connection refused")
            raise NetworkError(
                "Failed to connect to GitHub",
                original_error=original
            )
        except NetworkError as e:
            assert e.original_error is not None
            assert "Connection refused" in str(e.original_error)


class TestExceptionRaising:
    """Tests for exception raising scenarios."""

    def test_raise_and_catch_base(self):
        """Test catching base exception."""
        with pytest.raises(IssueAnalyzerError):
            raise IssueAnalyzerError("Test")

    def test_catch_derived_as_base(self):
        """Test catching derived exception as base."""
        with pytest.raises(IssueAnalyzerError):
            raise GitHubAPIError("API Error")

    def test_catch_github_error_chain(self):
        """Test catching GitHub error inheritance chain."""
        with pytest.raises(GitHubAPIError):
            raise RateLimitExceededError()

        with pytest.raises(IssueAnalyzerError):
            raise RateLimitExceededError()

    def test_specific_exception_not_caught_by_sibling(self):
        """Test that sibling exceptions don't catch each other."""
        with pytest.raises(ClassificationError):
            raise ClassificationError("Test")
        
        # This should NOT be caught by ConfigurationError handler
        try:
            raise ClassificationError("Test")
        except ConfigurationError:
            pytest.fail("ClassificationError should not be caught by ConfigurationError")
        except ClassificationError:
            pass  # Expected
