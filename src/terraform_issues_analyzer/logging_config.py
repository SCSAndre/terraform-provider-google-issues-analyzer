"""Structured logging configuration for the GitHub issue analyzer.

This module provides centralized logging setup with support for:
- Structured JSON logging for production
- Human-readable console logging for development
- Correlation IDs for request tracing
- Performance metrics logging
"""

import logging
import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from contextvars import ContextVar
from functools import wraps
import time

# Context variable for correlation ID (thread-safe)
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')
log_context_var: ContextVar[Dict[str, Any]] = ContextVar('log_context', default={})

_old_factory = logging.getLogRecordFactory()
def _thread_safe_record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    for key, value in log_context_var.get().items():
        setattr(record, key, value)
    return record

logging.setLogRecordFactory(_thread_safe_record_factory)

def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID.
    
    Returns:
        The current correlation ID, or None if not set.
    """
    cid = correlation_id_var.get()
    return cid if cid else None


def set_correlation_id(cid: Optional[str] = None) -> str:
    """Set a correlation ID for the current context.
    
    Args:
        cid: Optional correlation ID. If None, generates a new one.
        
    Returns:
        The correlation ID that was set.
    """
    if cid is None:
        cid = str(uuid.uuid4())[:8]
    correlation_id_var.set(cid)
    return cid


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging.
    
    Produces log entries in JSON format suitable for log aggregation
    systems like ELK, Splunk, or CloudWatch.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add correlation ID if set
        cid = get_correlation_id()
        if cid:
            log_entry["correlation_id"] = cid
        
        # Add location info
        log_entry["location"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'created', 'filename', 
                          'funcName', 'levelname', 'levelno', 'lineno',
                          'module', 'msecs', 'pathname', 'process',
                          'processName', 'relativeCreated', 'stack_info',
                          'exc_info', 'exc_text', 'thread', 'threadName',
                          'message', 'taskName'):
                try:
                    # Ensure the value is JSON serializable
                    json.dumps(value)
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)
        
        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output.
    
    Includes correlation ID and color coding for different log levels.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record for console output."""
        cid = get_correlation_id()
        cid_str = f"[{cid}] " if cid else ""
        
        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, '')
            level = f"{color}{level}{self.RESET}"
        
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        return f"{timestamp} | {level:8} | {cid_str}{record.name}: {record.getMessage()}"


def setup_logging(
    level: Optional[str] = None,
    structured: Optional[bool] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Configure application logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to LOG_LEVEL env var or INFO.
        structured: If True, use JSON format; otherwise use console format.
                   Defaults to LOG_FORMAT env var == 'json'.
        log_file: Optional file path for logging output.
                 Defaults to LOG_FILE env var.
        
    Returns:
        The root logger configured for the application
    """
    import os
    
    # Get values from environment if not provided
    if level is None:
        level = os.environ.get('LOG_LEVEL', 'INFO')
    if structured is None:
        structured = os.environ.get('LOG_FORMAT', '').lower() == 'json'
    if log_file is None:
        log_file = os.environ.get('LOG_FILE')
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler (always structured for easier parsing)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: The logger name, typically __name__ of the calling module
        
    Returns:
        A configured Logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)


def clear_correlation_id() -> None:
    """Clear the current correlation ID from context."""
    correlation_id_var.set('')


def log_performance(func):
    """Decorator to log function execution time.
    
    Usage:
        @log_performance
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Local logger to avoid global overshadowing if this wrapper is reused
        log = logging.getLogger(func.__module__)
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            log.debug(
                "%s completed in %.2fms", func.__name__, elapsed * 1000
            )
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            log.error(
                "%s failed after %.2fms: %s", func.__name__, elapsed * 1000, e
            )
            raise
    
    return wrapper


class LogContext:
    """Context manager for adding contextual information to logs.
    
    Usage:
        with LogContext(operation="process_issue", issue_number=123):
            logger.info("Processing issue")  # Will include context
    """
    
    def __init__(self, operation: str = "", correlation_id: Optional[str] = None, **context):
        self.operation = operation
        self.correlation_id = correlation_id
        self.context = context
        self.context['operation'] = operation
        self.old_correlation_id: str = ''
        self.token = None
    
    def __enter__(self):
        # Save and set correlation ID
        self.old_correlation_id = correlation_id_var.get()
        if self.correlation_id:
            correlation_id_var.set(self.correlation_id)
        elif not self.old_correlation_id:
            correlation_id_var.set(str(uuid.uuid4())[:8])
        
        # Update context
        current_ctx = log_context_var.get().copy()
        current_ctx.update(self.context)
        self.token = log_context_var.set(current_ctx)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            log_context_var.reset(self.token)
        # Restore old correlation ID
        correlation_id_var.set(self.old_correlation_id)
        return False
