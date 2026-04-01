"""Shared utility helpers used across reporting modules."""


def format_age(days: int) -> str:
    """Format age in days to a compact human-readable value.

    Args:
        days: Number of days.

    Returns:
        Age string with day, month, or year suffix.
    """
    if days < 30:
        return f"{days}d"
    if days < 365:
        return f"{days / 30:.1f}mo"
    return f"{days / 365:.1f}y"


from typing import Any, Dict, List, Set


def extract_label_names(labels: Any) -> List[str]:
    """Extract label name strings from GitHub API label data.

    Handles both dict-style ({"name": "bug"}) and plain string labels.

    Args:
        labels: Raw labels from GitHub API or pre-processed list.

    Returns:
        List of label name strings (original case preserved).
    """
    if not isinstance(labels, list):
        return []
    result: List[str] = []
    for label in labels:
        if isinstance(label, dict):
            name = str(label.get("name") or "").strip()
        elif isinstance(label, str):
            name = label.strip()
        else:
            continue
        if name:
            result.append(name)
    return result


def extract_label_names_lower(labels: Any) -> List[str]:
    """Same as extract_label_names but returns lowercased names."""
    return [name.lower() for name in extract_label_names(labels)]


def has_label(labels: Any, target: str) -> bool:
    """Check if a label exists (case-insensitive)."""
    return target.lower() in extract_label_names_lower(labels)
