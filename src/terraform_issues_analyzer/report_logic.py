"""Shared business logic for report generation.

Functions extracted from report_generator.py and html_report_generator.py
to eliminate duplication and ensure consistent behavior.
"""

from typing import Any, Dict, List
from .utils import extract_label_names_lower
def is_entry_point(issue: Dict[str, Any]) -> bool:
    """Return True if this issue qualifies as a contributor entry point.

    Criteria:
    - HIGH confidence band
    - Not blocked
    - Not a breaking change or new resource
    - Has at least one effort signal (size/xs, size/s, has_pr, documentation)
    - Either internally tracked or has priority score >= 65
    """
    if issue.get("confidence_band") != "HIGH":
        return False
    if issue.get("is_blocked", False):
        return False
    labels = extract_label_names_lower(issue.get("labels", []))
    if "breaking-change" in labels:
        return False
    lt = issue.get("label_types", {})
    if "new-resource" in labels or lt.get("new_resource", False):
        return False
    has_effort_signal = (
        any(size in labels for size in ("size/xs", "size/s"))
        or lt.get("has_pr", False)
        or lt.get("documentation", False)
    )
    if not has_effort_signal:
        return False
    return issue.get("is_internally_tracked", False) or issue.get("priority_score", 0) >= 65


def get_entry_point_reason(issue: Dict[str, Any]) -> str:
    """Return short qualifier text for contributor entry points."""
    labels = extract_label_names_lower(issue.get("labels", []))
    lt = issue.get("label_types", {})
    if lt.get("has_pr", False):
        return "Finish existing PR"
    if lt.get("documentation", False):
        return "Docs fix"
    if "size/xs" in labels:
        return "Tiny scope (xs)"
    if "size/s" in labels:
        return "Small scope (s)"
    return "Actionable"


def get_recently_reactivated_issues(
    issues: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return recently reactivated issues using report-specific business rules.

    An issue is "reactivated" when it is older than 1 year, has been updated
    within the last 90 days, received a reactivation bonus, and doesn't already
    have a PR or good-first-issue label.
    """
    reactivated = [
        issue
        for issue in issues
        if issue.get("age_days", 0) > 365
        and issue.get("days_since_update", 0) < 90
        and issue.get("reactivation_bonus", 0) > 0
        and not (
            issue.get("label_types", {}).get("has_pr")
            or issue.get("label_types", {}).get("good_first_issue")
        )
    ]
    return sorted(
        reactivated,
        key=lambda issue: (
            -issue.get("reactivation_bonus", 0),
            issue.get("days_since_update", 0),
        ),
    )[:10]


def is_contributor_safe(issue: Dict[str, Any]) -> bool:
    """Return True when issue is safe to present as a contributor entry point."""
    return not issue.get("is_blocked", False)
