"""Input validation utilities for GitHub issue data."""
import re
import logging
from typing import Dict, List, Optional, Any
from html import escape

logger = logging.getLogger(__name__)


class IssueValidator:
    """Validates and sanitizes GitHub issue data."""
    
    # Maximum lengths for fields
    MAX_TITLE_LENGTH = 1000
    MAX_BODY_LENGTH = 100000
    MAX_LABEL_LENGTH = 100
    MAX_LABELS_COUNT = 50
    
    @classmethod
    def validate_issue(cls, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates and sanitizes an issue dictionary.
        
        Args:
            issue: Raw issue data from GitHub API
            
        Returns:
            Sanitized issue dictionary
        """
        if not isinstance(issue, dict):
            logger.warning("Invalid issue data: expected dict, got %s", type(issue))
            return cls._empty_issue()
        
        return {
            "number": cls._validate_number(issue.get("number")),
            "title": cls._sanitize_text(issue.get("title"), cls.MAX_TITLE_LENGTH),
            "body": cls._sanitize_text(issue.get("body"), cls.MAX_BODY_LENGTH),
            "labels": cls._validate_labels(issue.get("labels")),
            "assignees": cls._validate_assignees(issue.get("assignees")),
            "comments": cls._validate_count(issue.get("comments")),
            "comments_url": cls._validate_url(issue.get("comments_url")),
            "url": cls._validate_url(issue.get("html_url") or issue.get("url")),
            "created_at": cls._validate_date(issue.get("created_at")),
            "state": cls._validate_state(issue.get("state")),
        }
    
    @classmethod
    def _empty_issue(cls) -> Dict[str, Any]:
        """Returns an empty sanitized issue structure."""
        return {
            "number": 0,
            "title": "",
            "body": "",
            "labels": [],
            "assignees": [],
            "comments": 0,
            "comments_url": "",
            "url": "",
            "created_at": "",
            "state": "unknown",
        }
    
    @classmethod
    def _validate_number(cls, value: Any) -> int:
        """Validates issue number."""
        if isinstance(value, int) and value > 0:
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return 0
    
    @classmethod
    def _sanitize_text(cls, text: Any, max_length: int) -> str:
        """
        Sanitizes text content.
        
        - Converts to string
        - Truncates to max length
        - Removes control characters (except newlines, tabs)
        """
        if text is None:
            return ""
        
        if not isinstance(text, str):
            text = str(text)
        
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length] + "..."
            logger.debug("Text truncated to %d characters", max_length)
        
        # Remove control characters but keep newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        return text
    
    @classmethod
    def _validate_labels(cls, labels: Any) -> List[Dict[str, str]]:
        """Validates and sanitizes label list."""
        if not isinstance(labels, list):
            return []
        
        validated = []
        for label in labels[:cls.MAX_LABELS_COUNT]:
            if isinstance(label, dict) and "name" in label:
                name = cls._sanitize_text(label["name"], cls.MAX_LABEL_LENGTH)
                if name:
                    validated.append({"name": name})
        
        return validated
    
    @classmethod
    def _validate_assignees(cls, assignees: Any) -> List[Dict[str, str]]:
        """Validates assignee list."""
        if not isinstance(assignees, list):
            return []
        
        validated = []
        for assignee in assignees:
            if isinstance(assignee, dict) and "login" in assignee:
                login = cls._sanitize_text(assignee["login"], 100)
                if login and cls._is_valid_username(login):
                    validated.append({"login": login})
        
        return validated
    
    @classmethod
    def _is_valid_username(cls, username: str) -> bool:
        """Validates GitHub username format."""
        # GitHub usernames: alphanumeric and hyphens, max 39 chars
        return bool(re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$', username))
    
    @classmethod
    def _validate_count(cls, value: Any) -> int:
        """Validates count field (comments, etc.)."""
        if isinstance(value, int) and value >= 0:
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return 0
    
    @classmethod
    def _validate_url(cls, url: Any) -> str:
        """Validates URL format."""
        if not isinstance(url, str):
            return ""
        
        # Basic URL validation - must start with http(s)://
        if not re.match(r'^https?://', url):
            return ""
        
        # Check for GitHub domain
        if not re.match(r'^https?://(api\.)?github\.com/', url):
            logger.warning("URL is not a GitHub URL: %s", url[:100])
            return ""
        
        return url
    
    @classmethod
    def _validate_date(cls, date: Any) -> str:
        """Validates ISO date format."""
        if not isinstance(date, str):
            return ""
        
        # Basic ISO 8601 format check
        if not re.match(r'^\d{4}-\d{2}-\d{2}', date):
            return ""
        
        return date
    
    @classmethod
    def _validate_state(cls, state: Any) -> str:
        """Validates issue state."""
        valid_states = {"open", "closed"}
        if isinstance(state, str) and state.lower() in valid_states:
            return state.lower()
        return "unknown"


def sanitize_for_markdown(text: str) -> str:
    """
    Sanitizes text for safe inclusion in markdown output.
    
    Escapes characters that could be interpreted as markdown syntax
    or HTML injection.
    """
    if not text:
        return ""
    
    # Escape HTML entities
    text = escape(text)
    
    # Escape markdown special characters that could cause issues
    # But preserve basic formatting
    markdown_chars = ['[', ']', '(', ')', '#', '*', '_', '`', '|']
    for char in markdown_chars:
        text = text.replace(char, '\\' + char)
    
    return text
