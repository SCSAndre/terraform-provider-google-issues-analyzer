"""Input validation utilities for GitHub issue data."""
import re
import logging
from typing import Dict, List, Optional, Any
from html import escape

logger = logging.getLogger(__name__)


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
