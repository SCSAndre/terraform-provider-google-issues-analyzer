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

from config import (
    OUTPUT_DIR,
    ENABLE_TRIGRAM_SHADOW_MODE,
    SHADOW_SCORE_DELTA_THRESHOLD,
    validate_config,
)
from github_client import GitHubClient
from issue_classifier import IssueClassifier
from issue_classifier import classify_labels
from availability_checker import AvailabilityChecker
import report_generator
from exceptions import (
    IssueAnalyzerError,
    ConfigurationError,
    GitHubAPIError,
)
from logging_config import (
    setup_logging,
    get_logger,
    log_performance,
    LogContext,
)
from types_definitions import IssueData

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
        is_actionable = label_types.get("actionable", False)
        
        # Get assignees
        assignees = [a["login"] for a in issue.get("assignees", [])]
        
        # Calculate priority score
        priority_score = calculate_priority_score(
            confidence=confidence,
            confidence_band=confidence_band,
            comments=issue.get("comments", 0),
            reactions_plus_one=(issue.get("reactions") or {}).get("+1", 0),
            age_days=age_days,
            days_since_update=days_since_update,
            is_bug=label_types.get("bug", False),
            is_actionable=is_actionable,
            has_assignee=len(assignees) > 0
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
            "labels": labels,
            "label_types": label_types,
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
    has_assignee: bool = False
) -> float:
    """Calculate a priority score for issue ranking.

    Weight breakdown:
    - Confidence: 40 points max
    - Comments: 10 points max
    - Reactions: 15 points max
    - Neglect (age + staleness): 20 points max
    - Bug bonus: 5 points
    - Actionable bonus: 5 points
    - Unassigned bonus: 10 points
    - High-confidence bonus: 5 points

    Args:
        confidence: Relevance confidence score from classifier.
        confidence_band: Confidence band label (HIGH, REVIEW, EXCLUDED).
        comments: Number of issue comments.
        reactions_plus_one: Number of +1 reactions.
        age_days: Days since issue creation.
        days_since_update: Days since last issue update.
        is_bug: True when issue has bug-like labels.
        is_actionable: True when issue has newcomer-friendly actionable labels.
        has_assignee: True when issue already has an assignee.
    
    Returns:
        Priority score from 0-100
    """
    score = 0.0
    
    # Confidence contributes 40%
    score += (confidence / 100) * 40
    
    # Comments contribute 10% (cap at 20 comments)
    comment_factor = min(comments, 20) / 20
    score += comment_factor * 10

    # Reactions contribute 15% (cap at 30 upvotes)
    reactions_factor = min(reactions_plus_one, 30) / 30
    score += reactions_factor * 15
    
    # Neglect contributes 20% (weighted blend of age and staleness, cap at 2 years)
    neglect_days = min((age_days * 0.3) + (days_since_update * 0.7), 730)
    score += (neglect_days / 730) * 20
    
    # Bug bonus: 5%
    if is_bug:
        score += 5

    # Actionable bonus: 5%
    if is_actionable:
        score += 5
    
    # Unassigned bonus: 10% (needs someone to pick it up)
    if not has_assignee:
        score += 10

    # High-confidence issues get a small ranking bonus.
    if confidence_band == "HIGH":
        score += 5
    
    return min(score, 100)


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
