#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis of OPEN and AVAILABLE Issues from Terraform Provider Google.

Analyzes issues related to Load Balancers, Cloud Armor, and Private Service Connect.
"""

import logging
from typing import Dict, List

from config import OUTPUT_DIR
from github_client import GitHubClient
from issue_classifier import IssueClassifier
from availability_checker import AvailabilityChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function."""
    logger.info("Starting issue analysis...")

    # Initialize components
    github_client = GitHubClient()
    classifier = IssueClassifier()
    availability_checker = AvailabilityChecker(github_client)

    # Fetch and analyze issues
    all_issues = fetch_all_issues(github_client)
    relevant_issues = analyze_issues(all_issues, classifier, availability_checker)

    # Generate report
    generate_report(relevant_issues)

    logger.info(f"Analysis complete. Found {len(relevant_issues)} relevant available issues.")


def fetch_all_issues(github_client: GitHubClient) -> List[Dict]:
    """Fetches all open issues from the repository."""
    all_issues = []
    page = 1

    while True:
        logger.info(f"Fetching page {page}...")
        issues = github_client.fetch_issues_page(page)

        if not issues:
            break

        all_issues.extend(issues)

        if len(issues) < 100:
            break

        page += 1

    logger.info(f"Fetched {len(all_issues)} total issues")
    return all_issues


def analyze_issues(issues: List[Dict], classifier: IssueClassifier,
                   availability_checker: AvailabilityChecker) -> List[Dict]:
    """Analyzes issues for relevance and availability."""
    relevant_issues = []

    for issue in issues:
        # Skip pull requests
        if "pull_request" in issue:
            continue

        # Check relevance
        is_relevant, category, confidence = classifier.classify_issue(issue)
        if not is_relevant:
            continue

        # Check availability
        is_available, reason = availability_checker.is_issue_available(issue)
        if not is_available:
            continue

        # Add to results
        issue_data = {
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "category": category,
            "confidence": confidence,
            "created_at": issue["created_at"],
            "comments": issue.get("comments", 0)
        }
        relevant_issues.append(issue_data)

    return relevant_issues


def generate_report(issues: List[Dict]) -> None:
    """Generates markdown report of relevant issues."""
    report_path = OUTPUT_DIR / "terraform_target_services_issues_report_en.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Terraform Provider Google - Available Issues Report\n\n")
        f.write(f"**Total Issues Found:** {len(issues)}\n\n")

        # Group by category
        by_category = {}
        for issue in issues:
            category = issue["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)

        # Write each category
        for category, cat_issues in by_category.items():
            f.write(f"## {category} ({len(cat_issues)} issues)\n\n")

            for issue in sorted(cat_issues, key=lambda x: x["confidence"], reverse=True):
                f.write(f"### #{issue['number']}: {issue['title']}\n\n")
                f.write(f"- **Confidence:** {issue['confidence']:.1f}%\n")
                f.write(f"- **URL:** {issue['url']}\n")
                f.write(f"- **Created:** {issue['created_at']}\n")
                f.write(f"- **Comments:** {issue['comments']}\n\n")

    logger.info(f"Report generated at {report_path}")


if __name__ == "__main__":
    main()
