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
    MIN_CONFIDENCE_THRESHOLD: Minimum confidence score (default: 75)
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
    TARGET_REPO,
    ENABLE_TRIGRAM_SHADOW_MODE,
    SHADOW_SCORE_DELTA_THRESHOLD,
    validate_config,
    ensure_output_dir,
)
from .github_client import GitHubClient
from .issue_classifier import IssueClassifier
from .availability_checker import AvailabilityChecker
from .priority_scorer import enrich_issue_data
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
            logger.error("Configuration error: %s", error)
        return 1
    
    # Log warnings
    for warning in config_result.get('warnings', []):
        logger.warning(warning)
    
    try:
        with LogContext(operation="issue_analysis"):
            # Initialize components
            logger.info("Initializing components")
            github_client = GitHubClient(repo=TARGET_REPO)
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
            "Configuration error: %s", e,
            extra={"error_type": "configuration"}
        )
        return 1
    except GitHubAPIError as e:
        logger.error(
            "GitHub API error: %s", e,
            extra={"error_type": "github_api", "status_code": e.status_code}
        )
        return 1
    except IssueAnalyzerError as e:
        logger.error(
            "Analysis error: %s", e,
            extra={"error_type": "analysis"}
        )
        return 1
    except KeyboardInterrupt:
        logger.warning("Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.exception(
            "Unexpected error during analysis: %s", e,
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
        logger.debug("Fetching page %d", page)
        issues = github_client.fetch_issues_page(page)

        if not issues:
            break

        all_issues.extend(issues)
        logger.info(
            "Progress: fetched %d issues", len(all_issues),
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
        classifier_result = classifier.classify_issue_with_related(issue)
        (
            is_relevant,
            category,
            confidence,
            confidence_band,
            related_categories,
        ) = classifier_result

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
                "Issue #%s not available: %s", issue['number'], reason
            )
            continue

        # Enrich issue data
        issue_data = enrich_issue_data(issue, classifier_result)
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
