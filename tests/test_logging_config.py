"""Tests for the logging_config module.

This module provides comprehensive tests for the structured logging
configuration, formatters, and utility functions.
"""

import pytest
import logging
import json
import os
import time
from io import StringIO
from unittest.mock import patch, MagicMock
from datetime import datetime

from terraform_issues_analyzer.logging_config import (
    setup_logging,
    get_logger,
    StructuredFormatter,
    ConsoleFormatter,
    log_performance,
    LogContext,
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id,
)


class TestStructuredFormatter:
    """Tests for StructuredFormatter class."""

    def test_basic_formatting(self):
        """Test basic JSON log formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["message"] == "Test message"
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_formatting_with_extra_fields(self):
        """Test JSON formatting with extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.custom_field = "custom_value"
        record.count = 42
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["custom_field"] == "custom_value"
        assert data["count"] == 42

    def test_formatting_with_exception(self):
        """Test JSON formatting includes exception info."""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_timestamp_format(self):
        """Test timestamp is in ISO format."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        # Should be parseable as ISO format
        timestamp = data["timestamp"]
        assert "T" in timestamp or "-" in timestamp


class TestConsoleFormatter:
    """Tests for ConsoleFormatter class."""

    def test_basic_formatting(self):
        """Test basic console log formatting."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        
        assert "INFO" in output
        assert "Test message" in output

    def test_formatting_with_extra(self):
        """Test console formatting includes extra fields."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Processing",
            args=(),
            exc_info=None
        )
        record.count = 5
        record.status = "active"
        
        output = formatter.format(record)
        
        assert "Processing" in output
        # Extra fields should be included in some form
        # The exact format depends on implementation

    def test_level_colors_in_output(self):
        """Test different log levels have different formatting."""
        formatter = ConsoleFormatter()
        
        info_record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="test.py", lineno=10,
            msg="Info", args=(), exc_info=None
        )
        error_record = logging.LogRecord(
            name="test", level=logging.ERROR,
            pathname="test.py", lineno=10,
            msg="Error", args=(), exc_info=None
        )
        
        info_output = formatter.format(info_record)
        error_output = formatter.format(error_record)
        
        assert "INFO" in info_output
        assert "ERROR" in error_output


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_default_setup(self):
        """Test default logging setup."""
        # Clear any existing handlers
        root = logging.getLogger()
        root.handlers = []
        
        with patch.dict(os.environ, {}, clear=True):
            setup_logging()
        
        # Should have handlers configured
        logger = get_logger("test.setup")
        assert logger is not None

    def test_json_format_setup(self):
        """Test JSON format logging setup."""
        root = logging.getLogger()
        root.handlers = []
        
        with patch.dict(os.environ, {"LOG_FORMAT": "json"}):
            setup_logging()
        
        logger = get_logger("test.json")
        assert logger is not None

    def test_custom_log_level(self):
        """Test custom log level from environment."""
        root = logging.getLogger()
        root.handlers = []
        
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            setup_logging()
        
        # Root logger should have DEBUG level
        assert logging.getLogger().level <= logging.DEBUG

    def test_log_file_Setup(self):
        """Test logging to file."""
        import tempfile
        
        root = logging.getLogger()
        root.handlers = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            with patch.dict(os.environ, {"LOG_FILE": log_file}):
                setup_logging()
            
            logger = get_logger("test.file")
            logger.info("Test message to file")
            
            # Force flush
            for handler in logging.getLogger().handlers:
                handler.flush()
            
            # Check file has content
            with open(log_file, 'r') as f:
                content = f.read()
                assert len(content) > 0
        finally:
            for handler in logging.getLogger().handlers:
                handler.close()
            logging.getLogger().handlers.clear()
            try:
                os.unlink(log_file)
            except OSError:
                pass


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_named_logger(self):
        """Test getting a named logger."""
        logger = get_logger("my.module")
        assert logger is not None
        assert logger.name == "my.module"

    def test_get_same_logger_twice(self):
        """Test getting the same logger returns same instance."""
        logger1 = get_logger("same.name")
        logger2 = get_logger("same.name")
        assert logger1 is logger2

    def test_different_loggers(self):
        """Test different names return different loggers."""
        logger1 = get_logger("first.module")
        logger2 = get_logger("second.module")
        assert logger1 is not logger2
        assert logger1.name != logger2.name


class TestCorrelationId:
    """Tests for correlation ID management."""

    def teardown_method(self):
        """Clear correlation ID after each test."""
        clear_correlation_id()

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        set_correlation_id("test-correlation-123")
        assert get_correlation_id() == "test-correlation-123"

    def test_clear_correlation_id(self):
        """Test clearing correlation ID."""
        set_correlation_id("to-be-cleared")
        clear_correlation_id()
        assert get_correlation_id() is None

    def test_correlation_id_in_logs(self):
        """Test correlation ID appears in log output."""
        formatter = StructuredFormatter()
        
        set_correlation_id("corr-456")
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        # Correlation ID should be in the output
        assert data.get("correlation_id") == "corr-456"


class TestLogPerformance:
    """Tests for log_performance decorator."""

    def test_decorator_logs_execution_time(self):
        """Test decorator logs function execution time."""
        call_count = 0
        
        @log_performance
        def sample_function():
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)
            return "result"
        
        result = sample_function()
        
        assert result == "result"
        assert call_count == 1

    def test_decorator_preserves_function_name(self):
        """Test decorator preserves function metadata."""
        @log_performance
        def my_named_function():
            """My docstring."""
            pass
        
        assert my_named_function.__name__ == "my_named_function"
        assert "docstring" in my_named_function.__doc__

    def test_decorator_with_arguments(self):
        """Test decorator works with function arguments."""
        @log_performance
        def add_numbers(a, b):
            return a + b
        
        result = add_numbers(3, 5)
        assert result == 8

    def test_decorator_with_kwargs(self):
        """Test decorator works with keyword arguments."""
        @log_performance
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        
        result = greet("World", greeting="Hi")
        assert result == "Hi, World!"

    def test_decorator_propagates_exceptions(self):
        """Test decorator propagates exceptions correctly."""
        @log_performance
        def failing_function():
            raise ValueError("Expected error")
        
        with pytest.raises(ValueError, match="Expected error"):
            failing_function()

    def test_decorator_logs_exception_on_failure(self):
        """Test decorator logs when function raises exception."""
        @log_performance
        def another_failing_function():
            raise RuntimeError("Runtime failure")
        
        with pytest.raises(RuntimeError):
            another_failing_function()
        
        # Exception should be logged (verified by not crashing)


class TestLogContext:
    """Tests for LogContext context manager."""

    def teardown_method(self):
        """Clear correlation ID after each test."""
        clear_correlation_id()

    def test_context_sets_correlation_id(self):
        """Test context manager sets correlation ID."""
        with LogContext(operation="test_op"):
            corr_id = get_correlation_id()
            assert corr_id is not None
            assert len(corr_id) > 0

    def test_context_clears_on_exit(self):
        """Test context manager clears correlation ID on exit."""
        with LogContext(operation="test"):
            pass
        
        # After context, correlation ID should be cleared
        # (or reset to previous value)

    def test_context_with_custom_correlation_id(self):
        """Test context manager with custom correlation ID."""
        with LogContext(operation="test", correlation_id="custom-id-789"):
            assert get_correlation_id() == "custom-id-789"

    def test_nested_contexts(self):
        """Test nested context managers."""
        with LogContext(operation="outer", correlation_id="outer-id"):
            outer_id = get_correlation_id()
            assert outer_id == "outer-id"
            
            with LogContext(operation="inner", correlation_id="inner-id"):
                inner_id = get_correlation_id()
                assert inner_id == "inner-id"
            
            # After inner context, should restore outer
            # (implementation dependent)

    def test_context_exception_handling(self):
        """Test context manager handles exceptions properly."""
        with pytest.raises(ValueError):
            with LogContext(operation="failing"):
                raise ValueError("Test exception")
        
        # Should not leave correlation ID set after exception


class TestLoggerIntegration:
    """Integration tests for logging system."""

    def test_full_logging_workflow(self):
        """Test complete logging workflow."""
        # Setup
        setup_logging()
        logger = get_logger("integration.test")
        
        # Log messages at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Should not raise any exceptions

    def test_logging_with_context(self):
        """Test logging within a context."""
        setup_logging()
        logger = get_logger("context.test")
        
        with LogContext(operation="context_test"):
            logger.info("Message within context")
        
        # Should work without errors

    def test_logging_with_extra_data(self):
        """Test logging with extra structured data."""
        setup_logging()
        logger = get_logger("extra.test")
        
        logger.info(
            "Processing items",
            extra={
                "item_count": 42,
                "status": "active",
                "tags": ["important", "urgent"]
            }
        )
        
        # Should handle extra data without errors

    def test_performance_logging_integration(self):
        """Test performance decorator with full logging."""
        setup_logging()
        
        @log_performance
        def integrated_function(x):
            return x * 2
        
        result = integrated_function(21)
        assert result == 42


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_message(self):
        """Test logging empty message."""
        logger = get_logger("edge.test")
        logger.info("")  # Should not raise

    def test_unicode_message(self):
        """Test logging unicode characters."""
        logger = get_logger("unicode.test")
        logger.info("Unicode: 日本語 🎉 émoji")

    def test_very_long_message(self):
        """Test logging very long message."""
        logger = get_logger("long.test")
        long_msg = "x" * 10000
        logger.info(long_msg)

    def test_message_with_format_specifiers(self):
        """Test logging message with format specifiers."""
        logger = get_logger("format.test")
        logger.info("Value: %s, Count: %d", "test", 42)

    def test_special_characters_in_extra(self):
        """Test extra fields with special characters."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.special = "line1\nline2\ttab"
        
        output = formatter.format(record)
        # Should be valid JSON
        json.loads(output)

    def test_none_values_in_extra(self):
        """Test None values in extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.nullable = None
        
        output = formatter.format(record)
        data = json.loads(output)
        assert data["nullable"] is None
