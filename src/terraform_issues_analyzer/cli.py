#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analysis of OPEN and AVAILABLE Issues from Terraform Provider Google.

This module serves as the main entry point for analyzing GitHub issues
from the Terraform Provider Google repository. It identifies issues related
to Cloud Armor
and generates structured reports.

Usage:
    python script.py
    
Environment Variables:
    GITHUB_TOKEN: GitHub API token for authentication
    MIN_CONFIDENCE_THRESHOLD: Minimum confidence score (default: 30)
    OUTPUT_DIR: Directory for generated reports (default: analysis_results)
    LOG_LEVEL: Logging level (default: INFO)
    LOG_FORMAT: Logging format - 'json' or 'console' (default: console)

Example:
    $ export GITHUB_TOKEN="your-token-here"
    $ python script.py
    
    Starting issue analysis...
    Analysis complete. Found 42 relevant available issues.
"""

import sys
import json
from datetime import date
from typing import Dict, List, Any

from .config import (
    OUTPUT_DIR,
    ENABLE_TRIGRAM_SHADOW_MODE,
    SHADOW_SCORE_DELTA_THRESHOLD,
    validate_config,
    ensure_output_dir,
)
from .github_client import GitHubClient
from .issue_classifier import IssueClassifier
from .issue_classifier import classify_labels
from .issue_classifier import get_blocking_label_info
from .availability_checker import AvailabilityChecker
from . import report_generator
from .exceptions import (
    IssueAnalyzerError,
    ConfigurationError,
    GitHubAPIError,
)
from .logging_config import (
    setup_logging,
    get_logger,
    log_performance,
    LogContext,
)
from .types_definitions import IssueData

# Initialize logging
logger = get_logger(__name__)


@log_performance
def main() -> int:
    """Main execution function.
    
    Orchestrates the issue analysis workflow:
    1. Validates configuration
    2. Fetches issues from GitHub
    3. Classifies issues for relevance
    4. Checks issue availability
    5. Generates report
    
    Returns:
        Exit code: 0 for success, 1 for errors.
    """
    # Setup logging based on environment
    setup_logging()
    ensure_output_dir()
    
    logger.info("Starting Terraform Provider Google issue analysis")
    
    # Validate configuration
    config_result = validate_config()
    if not config_result['valid']:
        for error in config_result['errors']:
            logger.error(f"Configuration error: {error}")
        return 1
    
    # Log warnings
    for warning in config_result.get('warnings', []):
        logger.warning(warning)
    
    try:
        with LogContext(operation="issue_analysis"):
            # Initialize components
            logger.info("Initializing components")
            github_client = GitHubClient()
            classifier = IssueClassifier()
            availability_checker = AvailabilityChecker(github_client)

            # Fetch and analyze issues
            logger.info("Fetching issues from GitHub API")
            all_issues = fetch_all_issues(github_client)
            
            logger.info(
                "Analyzing issues for relevance and availability",
                extra={"total_issues": len(all_issues)}
            )
            relevant_issues = analyze_issues(
                all_issues,
                classifier,
                availability_checker
            )

            # Generate report
            logger.info(
                "Generating report",
                extra={"relevant_issues": len(relevant_issues)}
            )
            generate_report(relevant_issues)

            logger.info(
                "Analysis complete",
                extra={
                    "total_fetched": len(all_issues),
                    "relevant_available": len(relevant_issues),
                }
            )
            
        return 0
        
    except ConfigurationError as e:
        logger.error(
            f"Configuration error: {e}",
            extra={"error_type": "configuration"}
        )
        return 1
    except GitHubAPIError as e:
        logger.error(
            f"GitHub API error: {e}",
            extra={"error_type": "github_api", "status_code": e.status_code}
        )
        return 1
    except IssueAnalyzerError as e:
        logger.error(
            f"Analysis error: {e}",
            extra={"error_type": "analysis"}
        )
        return 1
    except KeyboardInterrupt:
        logger.warning("Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.exception(
            f"Unexpected error during analysis: {e}",
            extra={"error_type": "unexpected"}
        )
        return 1


@log_performance
def fetch_all_issues(github_client: GitHubClient) -> List[Dict[str, Any]]:
    """Fetch all open issues from the repository.
    
    Args:
        github_client: Configured GitHub API client
        
    Returns:
        List of issue dictionaries from the GitHub API.
        
    Raises:
        GitHubAPIError: If API requests fail
    """
    all_issues: List[Dict[str, Any]] = []
    page = 1

    while True:
        logger.debug(f"Fetching page {page}")
        issues = github_client.fetch_issues_page(page)

        if not issues:
            break

        all_issues.extend(issues)
        logger.info(
            f"Progress: fetched {len(all_issues)} issues",
            extra={"page": page, "page_size": len(issues)}
        )

        if len(issues) < 100:
            break

        page += 1

    logger.info(
        "Issue fetch complete",
        extra={"total_issues": len(all_issues), "pages_fetched": page}
    )
    return all_issues


def analyze_issues(
    issues: List[Dict[str, Any]],
    classifier: IssueClassifier,
    availability_checker: AvailabilityChecker
) -> List[IssueData]:
    """Analyze issues for relevance and availability.
    
    Filters issues through the classification pipeline and availability
    checks to identify issues that are both relevant and available for
    work.
    
    Args:
        issues: List of raw issue dictionaries from GitHub API
        classifier: Configured issue classifier instance
        availability_checker: Configured availability checker instance
        
    Returns:
        List of enriched issue dictionaries for relevant, available issues.
    """
    from datetime import datetime
    
    relevant_issues: List[IssueData] = []
    stats = {
        "pull_requests_skipped": 0,
        "not_relevant": 0,
        "not_available": 0,
        "relevant_available": 0,
        "below_confidence_threshold": 0,
    }
    shadow_stats = {
        "checked": 0,
        "classification_flips": 0,
        "large_score_deltas": 0,
    }

    for issue in issues:
        # Skip pull requests
        if "pull_request" in issue:
            stats["pull_requests_skipped"] += 1
            continue

        # Check relevance - get all matching categories
        (
            is_relevant,
            category,
            confidence,
            confidence_band,
            related_categories,
        ) = classifier.classify_issue_with_related(issue)

        # Shadow-mode comparison is logging-only and does not alter classification outcomes.
        if ENABLE_TRIGRAM_SHADOW_MODE:
            shadow_stats["checked"] += 1
            comparison = classifier.get_shadow_score_comparison(issue)
            baseline = comparison["baseline"]
            shadow = comparison["shadow"]
            score_delta = abs(comparison["score_delta"])

            if baseline["is_relevant"] != shadow["is_relevant"]:
                shadow_stats["classification_flips"] += 1
                logger.info(
                    "Shadow mode classification flip detected",
                    extra={
                        "issue_number": issue.get("number"),
                        "baseline": baseline,
                        "shadow": shadow,
                    },
                )

            if score_delta >= SHADOW_SCORE_DELTA_THRESHOLD:
                shadow_stats["large_score_deltas"] += 1
                logger.info(
                    "Shadow mode score delta exceeded threshold",
                    extra={
                        "issue_number": issue.get("number"),
                        "score_delta": round(score_delta, 3),
                        "threshold": SHADOW_SCORE_DELTA_THRESHOLD,
                        "baseline": baseline,
                        "shadow": shadow,
                    },
                )

        if not is_relevant:
            stats["not_relevant"] += 1
            continue

        # Check availability
        is_available, reason = availability_checker.is_issue_available(issue)
        if not is_available:
            stats["not_available"] += 1
            logger.debug(
                f"Issue #{issue['number']} not available: {reason}"
            )
            continue

        # Parse dates for age calculation
        created_at = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00"))
        now = datetime.now(created_at.tzinfo)
        age_days = (now - created_at).days
        days_since_update = (now - updated_at).days
        
        # Extract label types
        labels = [label["name"] for label in issue.get("labels", [])]
        label_types = classify_labels(labels)
        blocking_info = get_blocking_label_info(labels)
        is_crash = "crash" in [label.lower() for label in labels]
        is_breaking_change = "breaking-change" in [label.lower() for label in labels]
        is_new_resource = "new-resource" in [label.lower() for label in labels]
        is_internally_tracked = "forward/linked" in [label.lower() for label in labels]
        is_actionable = label_types.get("actionable", False)
        
        # Get assignees
        assignees = [a["login"] for a in issue.get("assignees", [])]

        reactions_data = issue.get("reactions", {})
        thumbs_up = reactions_data.get("+1", 0) if isinstance(reactions_data, dict) else 0
        
        # Calculate priority score
        priority_score = calculate_priority_score(
            confidence=confidence,
            confidence_band=confidence_band,
            comments=issue.get("comments", 0),
            reactions_plus_one=thumbs_up,
            age_days=age_days,
            days_since_update=days_since_update,
            is_bug=label_types.get("bug", False),
            is_actionable=is_actionable,
            has_assignee=len(assignees) > 0,
            labels=issue.get("labels", []),
        )

        # Add to results with enriched data
        issue_data: IssueData = {
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "state": issue.get("state", "open"),
            "category": category,
            "confidence": confidence,
            "confidence_band": confidence_band,
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "age_days": age_days,
            "days_since_update": days_since_update,
            "comments": issue.get("comments", 0),
            "thumbs_up": thumbs_up,
            "labels": labels,
            "label_types": label_types,
            "is_exempt": blocking_info["is_exempt"],
            "is_upstream": blocking_info["is_upstream"],
            "is_blocked": blocking_info["is_blocked"],
            "is_crash": is_crash,
            "is_breaking_change": is_breaking_change,
            "is_new_resource": is_new_resource,
            "is_internally_tracked": is_internally_tracked,
            "assignees": assignees,
            "is_assigned": len(assignees) > 0,
            "actionable": is_actionable,
            "related_categories": related_categories,
            "priority_score": priority_score,
        }
        relevant_issues.append(issue_data)
        stats["relevant_available"] += 1

    logger.info(
        "Issue analysis complete",
        extra={"stats": stats}
    )

    if ENABLE_TRIGRAM_SHADOW_MODE:
        logger.info(
            "Shadow mode summary",
            extra={"shadow_stats": shadow_stats},
        )
    
    return relevant_issues


def calculate_priority_score(
    confidence: float,
    confidence_band: str,
    comments: int,
    reactions_plus_one: int,
    age_days: int,
    days_since_update: int,
    is_bug: bool,
    is_actionable: bool = False,
    has_assignee: bool = False,
    labels: List[Any] | None = None,
) -> float:
    """Calculate a priority score for issue ranking.

    Weight breakdown:
    - Confidence: 40 points max
    - Comments: 15 points max
    - Reactions: 15 points max
    - Neglect (age + staleness): 20 points max
    - ultra-age bonus: +3 to +8 for issues older than 3 years
    - reactivation: old issue (>1y) with recent activity (<90d), max +15
    - Bug bonus: 5 points
    - Breaking change penalty: -5 points
    - New resource penalty: -3 points
    - crash bonus: +15 points when issue has the "crash" label
    - Actionable bonus: 5 points
    - size: maintainer effort estimate label (size/xs=+12, size/s=+10, size/m=+5)
    - Unassigned bonus: 10 points
    - High-confidence bonus: 5 points

    Args:
        confidence: Relevance confidence score from classifier.
        confidence_band: Confidence band label (HIGH, REVIEW, EXCLUDED).
        comments: Number of issue comments.
        reactions_plus_one: Community thumbs-up count (+1 reactions), capped at 30.
        age_days: Days since issue creation.
        days_since_update: Days since last issue update.
        is_bug: True when issue has bug-like labels.
        is_actionable: True when issue has newcomer-friendly actionable labels.
        has_assignee: True when issue already has an assignee.
        labels: Raw GitHub labels list (dicts with name or plain strings).
    
    Returns:
        Priority score from 0-100
    """
    score = 0.0
    
    # Confidence contributes 40%
    score += (confidence / 100) * 40
    
    # Comments contribute 15% (cap at 20 comments)
    comment_factor = min(comments, 20) / 20
    score += comment_factor * 15

    thumbs_up = max(int(reactions_plus_one), 0)
    # Reactions factor: community demand signal (+1 count), weight 15%
    # Cap at 30 reactions to avoid a single viral issue dominating
    reactions_factor = min(thumbs_up, 30) / 30 * 15
    score += reactions_factor
    
    # Neglect contributes 20% (weighted blend of age and staleness, cap at 2 years)
    neglect_days = min((age_days * 0.3) + (days_since_update * 0.7), 730)
    score += (neglect_days / 730) * 20

    # Ultra-age bonus: issues that have survived multiple major releases
    # deserve extra visibility. Soft bonus to avoid over-penalizing new issues.
    ultra_age_bonus = 0
    if age_days > 1095:  # > 3 years
        # Scale: 3y=+3, 4y=+6, 5y=+8 (diminishing returns)
        years_beyond_3 = (age_days - 1095) / 365
        ultra_age_bonus = round(min(years_beyond_3 * 3, 8))
    score += ultra_age_bonus

    # Reactivation bonus: old issue that recently got new activity
    # Signals upstream API changes, GA announcements, or renewed urgency.
    # Formula scales by issue age and update recency with a max bonus of +15.
    reactivation_bonus = 0
    if age_days > 365 and days_since_update < 90:
        age_factor = min(age_days / 730, 1.0)
        recency_factor = 1.0 - (days_since_update / 90)
        reactivation_bonus = round(age_factor * recency_factor * 15)
    score += reactivation_bonus
    
    # Bug bonus: 5%
    if is_bug:
        score += 5

    is_breaking_change = any(
        (label.get("name", label) if isinstance(label, dict) else label).lower() == "breaking-change"
        for label in (labels or [])
    )
    is_new_resource = any(
        (label.get("name", label) if isinstance(label, dict) else label).lower() == "new-resource"
        for label in (labels or [])
    )

    # Breaking change: deprioritize slightly - requires maintainer oversight
    if is_breaking_change:
        score -= 5

    # New resource: deprioritize - large scope, not a quick fix
    if is_new_resource:
        score -= 3

    # Crash severity bonus: panics and crashes are critical regardless of age
    is_crash = any(
        (label.get("name", label) if isinstance(label, dict) else label).lower() == "crash"
        for label in (labels or [])
    )
    if is_crash:
        score += 15

    # Actionable bonus: 5%
    if is_actionable:
        score += 5
    
    # Unassigned bonus: 10% (needs someone to pick it up)
    if not has_assignee:
        score += 10

    # High-confidence issues get a small ranking bonus.
    if confidence_band == "HIGH":
        score += 5

    # Size bonus: maintainer effort estimate from size/* labels
    size_bonus = 0
    label_names: List[str] = []
    for label in labels or []:
        if isinstance(label, dict):
            label_name = str(label.get("name") or "").strip().lower()
        elif isinstance(label, str):
            label_name = label.strip().lower()
        else:
            label_name = ""
        if label_name:
            label_names.append(label_name)

    if "size/xs" in label_names:
        size_bonus = 12
    elif "size/s" in label_names:
        size_bonus = 10
    elif "size/m" in label_names:
        size_bonus = 5
    elif "size/xl" in label_names:
        size_bonus = -3

    score += size_bonus
    
    return max(0, min(score, 95))


def generate_report(issues: List[IssueData]) -> None:
    """Generate reports by delegating report writing to report_generator.py."""
    report_paths = report_generator.generate_analysis_reports(issues=issues, output_dir=OUTPUT_DIR)
    _append_history_entry(issues)
    logger.info(
        "Reports generated",
        extra={
            "markdown_path": str(report_paths["markdown"]),
            "html_path": str(report_paths["html"]),
            "issue_count": len(issues),
        },
    )


def _append_history_entry(issues: List[IssueData]) -> None:
    """Append one run summary to history.json for trend rendering.

    Args:
        issues: List of enriched issues included in the report.
    """
    history_path = OUTPUT_DIR / "history.json"
    existing: List[Dict[str, Any]] = []

    if history_path.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as history_file:
                parsed = json.load(history_file)
                if isinstance(parsed, list):
                    existing = parsed
        except (OSError, ValueError) as exc:
            logger.warning("Could not read existing history file", extra={"error": str(exc)})

    entry = {
        "date": date.today().isoformat(),
        "total": len(issues),
        "high_confidence": sum(1 for issue in issues if issue.get("confidence_band") == "HIGH"),
        "review": sum(1 for issue in issues if issue.get("confidence_band") == "REVIEW"),
    }
    existing.append(entry)

    with open(history_path, "w", encoding="utf-8") as history_file:
        json.dump(existing, history_file, indent=2)


if __name__ == "__main__":
    sys.exit(main())
