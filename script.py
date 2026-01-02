#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analysis of OPEN and AVAILABLE Issues from Terraform Provider Google.

This module serves as the main entry point for analyzing GitHub issues
from the Terraform Provider Google repository. It identifies issues related
to specific GCP services (Load Balancers, Cloud Armor, Private Service Connect)
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
from typing import Dict, List, Any

from config import OUTPUT_DIR, validate_config
from github_client import GitHubClient
from issue_classifier import IssueClassifier
from availability_checker import AvailabilityChecker
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
) -> List[Dict[str, Any]]:
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
    relevant_issues: List[Dict[str, Any]] = []
    stats = {
        "pull_requests_skipped": 0,
        "not_relevant": 0,
        "not_available": 0,
        "relevant_available": 0,
    }

    for issue in issues:
        # Skip pull requests
        if "pull_request" in issue:
            stats["pull_requests_skipped"] += 1
            continue

        # Check relevance
        is_relevant, category, confidence = classifier.classify_issue(issue)
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

        # Add to results
        issue_data = {
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "category": category,
            "confidence": confidence,
            "created_at": issue["created_at"],
            "comments": issue.get("comments", 0),
            "labels": [label["name"] for label in issue.get("labels", [])],
        }
        relevant_issues.append(issue_data)
        stats["relevant_available"] += 1

    logger.info(
        "Issue analysis complete",
        extra={"stats": stats}
    )
    
    return relevant_issues


def generate_report(issues: List[Dict[str, Any]]) -> None:
    """Generate markdown report of relevant issues.
    
    Creates a structured markdown report grouped by category with
    issues sorted by confidence score.
    
    Args:
        issues: List of enriched issue dictionaries
    """
    report_path = OUTPUT_DIR / "terraform_target_services_issues_report_en.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Terraform Provider Google - Available Issues Report\n\n")
        f.write(f"**Total Issues Found:** {len(issues)}\n\n")

        # Group by category
        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for issue in issues:
            category = issue["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)

        # Summary table
        f.write("## Summary\n\n")
        f.write("| Category | Count |\n")
        f.write("|----------|-------|\n")
        for category, cat_issues in sorted(by_category.items()):
            f.write(f"| {category} | {len(cat_issues)} |\n")
        f.write("\n")

        # Write each category
        for category, cat_issues in sorted(by_category.items()):
            f.write(f"## {category} ({len(cat_issues)} issues)\n\n")

            for issue in sorted(
                cat_issues,
                key=lambda x: x["confidence"],
                reverse=True
            ):
                f.write(f"### #{issue['number']}: {issue['title']}\n\n")
                f.write(f"- **Confidence:** {issue['confidence']:.1f}%\n")
                f.write(f"- **URL:** {issue['url']}\n")
                f.write(f"- **Created:** {issue['created_at']}\n")
                f.write(f"- **Comments:** {issue['comments']}\n")
                if issue.get('labels'):
                    f.write(f"- **Labels:** {', '.join(issue['labels'])}\n")
                f.write("\n")

    logger.info(
        "Report generated",
        extra={"path": str(report_path), "issue_count": len(issues)}
    )


if __name__ == "__main__":
    sys.exit(main())
