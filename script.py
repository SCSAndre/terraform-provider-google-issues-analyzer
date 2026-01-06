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
    from datetime import datetime
    
    relevant_issues: List[Dict[str, Any]] = []
    stats = {
        "pull_requests_skipped": 0,
        "not_relevant": 0,
        "not_available": 0,
        "relevant_available": 0,
        "below_confidence_threshold": 0,
    }

    for issue in issues:
        # Skip pull requests
        if "pull_request" in issue:
            stats["pull_requests_skipped"] += 1
            continue

        # Check relevance - get all matching categories
        is_relevant, category, confidence, related_categories = classifier.classify_issue_with_related(issue)
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
        
        # Get assignees
        assignees = [a["login"] for a in issue.get("assignees", [])]
        
        # Calculate priority score
        priority_score = calculate_priority_score(
            confidence=confidence,
            comments=issue.get("comments", 0),
            age_days=age_days,
            days_since_update=days_since_update,
            is_bug=label_types.get("bug", False),
            has_assignee=len(assignees) > 0
        )

        # Add to results with enriched data
        issue_data = {
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "state": issue.get("state", "open"),
            "category": category,
            "confidence": confidence,
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "age_days": age_days,
            "days_since_update": days_since_update,
            "comments": issue.get("comments", 0),
            "labels": labels,
            "label_types": label_types,
            "assignees": assignees,
            "is_assigned": len(assignees) > 0,
            "related_categories": related_categories,
            "priority_score": priority_score,
        }
        relevant_issues.append(issue_data)
        stats["relevant_available"] += 1

    logger.info(
        "Issue analysis complete",
        extra={"stats": stats}
    )
    
    return relevant_issues


def classify_labels(labels: List[str]) -> Dict[str, bool]:
    """Classify labels into semantic types.
    
    Args:
        labels: List of label names
        
    Returns:
        Dictionary with label type flags
    """
    labels_lower = [l.lower() for l in labels]
    
    return {
        "bug": any("bug" in l for l in labels_lower),
        "enhancement": any(l in ["enhancement", "feature", "feature-request"] for l in labels_lower),
        "documentation": any("doc" in l for l in labels_lower),
        "upstream": any("upstream" in l for l in labels_lower),
        "breaking_change": any("breaking" in l for l in labels_lower),
        "has_pr": any("pr" in l or "pull" in l for l in labels_lower),
        "waiting": any("waiting" in l or "blocked" in l for l in labels_lower),
        "good_first_issue": any("good first" in l or "beginner" in l for l in labels_lower),
    }


def calculate_priority_score(
    confidence: float,
    comments: int,
    age_days: int,
    days_since_update: int,
    is_bug: bool,
    has_assignee: bool
) -> float:
    """Calculate a priority score for issue ranking.
    
    Priority considers:
    - Confidence (higher = more relevant)
    - Comments (more = more interest/importance)
    - Age (older unresolved = higher priority)
    - Activity (recently updated = actively being worked)
    - Type (bugs typically higher priority)
    - Assignment (unassigned = needs attention)
    
    Returns:
        Priority score from 0-100
    """
    score = 0.0
    
    # Confidence contributes 30%
    score += (confidence / 100) * 30
    
    # Comments contribute 20% (cap at 20 comments)
    comment_factor = min(comments, 20) / 20
    score += comment_factor * 20
    
    # Age contributes 15% (older issues get more priority, cap at 2 years)
    age_factor = min(age_days, 730) / 730
    score += age_factor * 15
    
    # Recent activity contributes 15% (recently active = lower priority as it's being worked)
    # Inverse: more days since update = higher priority (neglected)
    if days_since_update < 30:
        activity_factor = 0.3  # Recently active, lower priority
    elif days_since_update < 180:
        activity_factor = 0.6  # Moderately stale
    else:
        activity_factor = 1.0  # Very stale, needs attention
    score += activity_factor * 15
    
    # Bug bonus: 10%
    if is_bug:
        score += 10
    
    # Unassigned bonus: 10% (needs someone to pick it up)
    if not has_assignee:
        score += 10
    
    return min(score, 100)


def generate_report(issues: List[Dict[str, Any]]) -> None:
    """Generate comprehensive markdown report of relevant issues.
    
    Creates a structured markdown report with:
    - Executive summary with key metrics
    - Quick wins and attention needed sections
    - Priority recommendations
    - Age analysis
    - Label distribution
    - Collapsible detailed issues by category
    
    Args:
        issues: List of enriched issue dictionaries
    """
    from datetime import datetime
    
    report_path = OUTPUT_DIR / "terraform_target_services_issues_report_en.md"
    now = datetime.now()

    with open(report_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("# Terraform Provider Google - Issues Analysis Report\n\n")
        f.write(f"**Report Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Issues Analyzed:** {len(issues)}\n\n")
        f.write(f"**Confidence Threshold:** ≥75%\n\n")
        f.write("---\n\n")
        
        # Executive Summary
        write_executive_summary(f, issues)
        
        # Quick Wins Section
        write_quick_wins(f, issues)
        
        # Attention Needed Section
        write_attention_needed(f, issues)
        
        # Priority Recommendations
        write_priority_recommendations(f, issues)
        
        # Age Analysis (collapsible)
        write_age_analysis(f, issues)
        
        # Label Distribution (collapsible)
        write_label_distribution(f, issues)
        
        # Category Summary Table
        write_category_summary(f, issues)
        
        # Detailed Issues by Category (collapsible)
        write_issues_by_category(f, issues)

    logger.info(
        "Report generated",
        extra={"path": str(report_path), "issue_count": len(issues)}
    )


def format_age(days: int) -> str:
    """Format age in days to human-readable string."""
    if days < 30:
        return f"{days}d"
    elif days < 365:
        months = days / 30
        return f"{months:.1f}mo"
    else:
        years = days / 365
        return f"{years:.1f}y"


def write_executive_summary(f, issues: List[Dict[str, Any]]) -> None:
    """Write executive summary section."""
    f.write("## 📊 Executive Summary\n\n")
    
    # Calculate key metrics
    total = len(issues)
    if total == 0:
        f.write("No issues found matching the criteria.\n\n")
        return
        
    bugs = sum(1 for i in issues if i.get("label_types", {}).get("bug", False))
    enhancements = sum(1 for i in issues if i.get("label_types", {}).get("enhancement", False))
    assigned = sum(1 for i in issues if i.get("is_assigned", False))
    unassigned = total - assigned
    has_pr = sum(1 for i in issues if i.get("label_types", {}).get("has_pr", False))
    
    avg_age = sum(i.get("age_days", 0) for i in issues) / total
    avg_comments = sum(i.get("comments", 0) for i in issues) / total
    
    stale_count = sum(1 for i in issues if i.get("days_since_update", 0) > 180)
    active_count = sum(1 for i in issues if i.get("days_since_update", 0) < 30)
    
    f.write("| Metric | Value |\n")
    f.write("|--------|-------|\n")
    f.write(f"| Total Issues | {total} |\n")
    f.write(f"| 🐛 Bugs | {bugs} ({bugs*100//total}%) |\n")
    f.write(f"| ✨ Enhancements | {enhancements} ({enhancements*100//total}%) |\n")
    f.write(f"| 👤 Assigned | {assigned} ({assigned*100//total}%) |\n")
    f.write(f"| ⚠️ Unassigned | {unassigned} ({unassigned*100//total}%) |\n")
    f.write(f"| 📅 Average Age | {format_age(int(avg_age))} |\n")
    f.write(f"| 💬 Avg Comments | {avg_comments:.1f} |\n")
    f.write(f"| 🔥 Active (<30d) | {active_count} |\n")
    f.write(f"| 💤 Stale (>180d) | {stale_count} |\n")
    f.write(f"| 🔗 Has PR | {has_pr} |\n")
    f.write("\n")


def write_quick_wins(f, issues: List[Dict[str, Any]]) -> None:
    """Write quick wins section - easy issues to tackle."""
    # Find issues that are small and/or have PRs
    quick_wins = []
    for issue in issues:
        labels_lower = [l.lower() for l in issue.get("labels", [])]
        is_small = any(s in l for l in labels_lower for s in ["size/xs", "size/s"])
        has_pr = issue.get("label_types", {}).get("has_pr", False)
        is_good_first = issue.get("label_types", {}).get("good_first_issue", False)
        
        if is_small or has_pr or is_good_first:
            quick_wins.append({
                **issue,
                "reason": "Has PR" if has_pr else ("Good First Issue" if is_good_first else "Small Size")
            })
    
    if not quick_wins:
        return
    
    f.write("## 🚀 Quick Wins\n\n")
    f.write("Issues that may be easier to resolve (small size, has PR, or good first issue).\n\n")
    
    # Sort by priority and take top 10
    quick_wins = sorted(quick_wins, key=lambda x: x.get("priority_score", 0), reverse=True)[:10]
    
    f.write("| Issue | Category | Reason | Age | Priority |\n")
    f.write("|-------|----------|--------|-----|----------|\n")
    
    for issue in quick_wins:
        title = issue["title"][:40] + "..." if len(issue["title"]) > 40 else issue["title"]
        f.write(f"| [#{issue['number']}]({issue['url']}) {title} | {issue['category']} | {issue['reason']} | {format_age(issue.get('age_days', 0))} | {issue.get('priority_score', 0):.0f} |\n")
    
    f.write("\n")


def write_attention_needed(f, issues: List[Dict[str, Any]]) -> None:
    """Write attention needed section - stale issues with high engagement."""
    # Find stale issues with significant comments (community interest)
    attention_issues = [
        i for i in issues 
        if i.get("days_since_update", 0) > 180 
        and i.get("comments", 0) >= 3
        and not i.get("is_assigned", False)
    ]
    
    if not attention_issues:
        return
    
    f.write("## ⚠️ Attention Needed\n\n")
    f.write("Stale issues (>6 months) with significant community interest (3+ comments) but no assignee.\n\n")
    
    # Sort by comments (most interest first)
    attention_issues = sorted(attention_issues, key=lambda x: x.get("comments", 0), reverse=True)[:10]
    
    f.write("| Issue | Category | Comments | Last Update | Type |\n")
    f.write("|-------|----------|----------|-------------|------|\n")
    
    for issue in attention_issues:
        title = issue["title"][:40] + "..." if len(issue["title"]) > 40 else issue["title"]
        issue_type = "🐛" if issue.get("label_types", {}).get("bug") else "✨"
        last_update = format_age(issue.get("days_since_update", 0))
        f.write(f"| [#{issue['number']}]({issue['url']}) {title} | {issue['category']} | {issue.get('comments', 0)} | {last_update} ago | {issue_type} |\n")
    
    f.write("\n")


def write_priority_recommendations(f, issues: List[Dict[str, Any]]) -> None:
    """Write top priority issues section."""
    f.write("## 🎯 Top 10 Priority Issues\n\n")
    
    # Sort by priority score
    sorted_issues = sorted(issues, key=lambda x: x.get("priority_score", 0), reverse=True)
    top_issues = sorted_issues[:10]
    
    f.write("| # | Issue | Category | Priority | Age | Status |\n")
    f.write("|---|-------|----------|----------|-----|--------|\n")
    
    for i, issue in enumerate(top_issues, 1):
        number = issue["number"]
        title = issue["title"][:45] + "..." if len(issue["title"]) > 45 else issue["title"]
        category = issue["category"]
        priority = issue.get("priority_score", 0)
        age = format_age(issue.get("age_days", 0))
        
        status_parts = []
        if issue.get("label_types", {}).get("bug"):
            status_parts.append("🐛")
        if issue.get("is_assigned"):
            status_parts.append("👤")
        if issue.get("days_since_update", 0) > 180:
            status_parts.append("💤")
        elif issue.get("days_since_update", 0) < 30:
            status_parts.append("🔥")
        status = " ".join(status_parts) or "—"
        
        f.write(f"| {i} | [#{number}]({issue['url']}) {title} | {category} | {priority:.0f} | {age} | {status} |\n")
    
    f.write("\n")
    f.write("**Legend:** 🐛 Bug | 👤 Assigned | 💤 Stale | 🔥 Active\n\n")


def write_age_analysis(f, issues: List[Dict[str, Any]]) -> None:
    """Write age distribution analysis in collapsible section."""
    f.write("<details>\n<summary><strong>📅 Age Analysis</strong> (click to expand)</summary>\n\n")
    
    # Age buckets
    buckets = {
        "< 30 days": 0,
        "1-3 months": 0,
        "3-6 months": 0,
        "6-12 months": 0,
        "1-2 years": 0,
        "> 2 years": 0,
    }
    
    for issue in issues:
        age = issue.get("age_days", 0)
        if age < 30:
            buckets["< 30 days"] += 1
        elif age < 90:
            buckets["1-3 months"] += 1
        elif age < 180:
            buckets["3-6 months"] += 1
        elif age < 365:
            buckets["6-12 months"] += 1
        elif age < 730:
            buckets["1-2 years"] += 1
        else:
            buckets["> 2 years"] += 1
    
    f.write("| Age Range | Count | Distribution |\n")
    f.write("|-----------|-------|-------------|\n")
    
    total = len(issues)
    for bucket, count in buckets.items():
        pct = (count * 100 // total) if total else 0
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        f.write(f"| {bucket} | {count} | {bar} {pct}% |\n")
    
    f.write("\n")
    
    # Oldest issues callout
    oldest = sorted(issues, key=lambda x: x.get("age_days", 0), reverse=True)[:5]
    if oldest:
        f.write("**🏚️ Oldest Open Issues:**\n\n")
        for issue in oldest:
            age_years = issue.get("age_days", 0) / 365
            title = issue['title'][:50] + "..." if len(issue['title']) > 50 else issue['title']
            f.write(f"- [#{issue['number']}]({issue['url']}) ({age_years:.1f}y) - {title}\n")
        f.write("\n")
    
    f.write("</details>\n\n")


def write_label_distribution(f, issues: List[Dict[str, Any]]) -> None:
    """Write label distribution analysis in collapsible section."""
    f.write("<details>\n<summary><strong>🏷️ Label Distribution</strong> (click to expand)</summary>\n\n")
    
    # Count label types
    label_counts = {
        "🐛 Bug": sum(1 for i in issues if i.get("label_types", {}).get("bug")),
        "✨ Enhancement": sum(1 for i in issues if i.get("label_types", {}).get("enhancement")),
        "📚 Documentation": sum(1 for i in issues if i.get("label_types", {}).get("documentation")),
        "⬆️ Upstream": sum(1 for i in issues if i.get("label_types", {}).get("upstream")),
        "💥 Breaking Change": sum(1 for i in issues if i.get("label_types", {}).get("breaking_change")),
        "🔗 Has PR": sum(1 for i in issues if i.get("label_types", {}).get("has_pr")),
        "⏳ Waiting/Blocked": sum(1 for i in issues if i.get("label_types", {}).get("waiting")),
        "👶 Good First Issue": sum(1 for i in issues if i.get("label_types", {}).get("good_first_issue")),
    }
    
    f.write("| Label Type | Count |\n")
    f.write("|------------|-------|\n")
    for label, count in label_counts.items():
        if count > 0:
            f.write(f"| {label} | {count} |\n")
    
    f.write("\n</details>\n\n")


def write_category_summary(f, issues: List[Dict[str, Any]]) -> None:
    """Write category summary table."""
    f.write("## 📁 Category Summary\n\n")
    
    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for issue in issues:
        category = issue["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(issue)
    
    f.write("| Category | Issues | Bugs | Enhancements | Avg Age | Stale |\n")
    f.write("|----------|--------|------|--------------|---------|-------|\n")
    
    for category in sorted(by_category.keys()):
        cat_issues = by_category[category]
        count = len(cat_issues)
        bugs = sum(1 for i in cat_issues if i.get("label_types", {}).get("bug"))
        enhancements = sum(1 for i in cat_issues if i.get("label_types", {}).get("enhancement"))
        avg_age = sum(i.get("age_days", 0) for i in cat_issues) / count if count else 0
        stale = sum(1 for i in cat_issues if i.get("days_since_update", 0) > 180)
        
        f.write(f"| {category} | {count} | {bugs} | {enhancements} | {format_age(int(avg_age))} | {stale} |\n")
    
    f.write("\n")


def write_issues_by_category(f, issues: List[Dict[str, Any]]) -> None:
    """Write detailed issues grouped by category in collapsible sections."""
    f.write("---\n\n")
    f.write("## 📋 Detailed Issues by Category\n\n")
    
    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for issue in issues:
        category = issue["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(issue)
    
    for category in sorted(by_category.keys()):
        cat_issues = by_category[category]
        
        # Collapsible category section
        f.write(f"<details>\n<summary><strong>{category}</strong> ({len(cat_issues)} issues)</summary>\n\n")
        
        # Sort by priority score within category
        sorted_issues = sorted(cat_issues, key=lambda x: x.get("priority_score", 0), reverse=True)
        
        # Write as a compact table
        f.write("| Issue | Priority | Age | Updated | Type | Labels |\n")
        f.write("|-------|----------|-----|---------|------|--------|\n")
        
        for issue in sorted_issues:
            write_issue_row(f, issue)
        
        f.write("\n</details>\n\n")


def write_issue_row(f, issue: Dict[str, Any]) -> None:
    """Write a single issue as a table row."""
    number = issue["number"]
    title = issue["title"][:50] + "..." if len(issue["title"]) > 50 else issue["title"]
    priority = issue.get("priority_score", 0)
    age = format_age(issue.get("age_days", 0))
    updated = format_age(issue.get("days_since_update", 0))
    
    # Type indicator
    type_icon = ""
    if issue.get("label_types", {}).get("bug"):
        type_icon = "🐛"
    elif issue.get("label_types", {}).get("enhancement"):
        type_icon = "✨"
    elif issue.get("label_types", {}).get("documentation"):
        type_icon = "📚"
    
    # Status indicators
    status_icons = []
    if issue.get("is_assigned"):
        status_icons.append("👤")
    if issue.get("days_since_update", 0) > 180:
        status_icons.append("💤")
    elif issue.get("days_since_update", 0) < 30:
        status_icons.append("🔥")
    if issue.get("label_types", {}).get("has_pr"):
        status_icons.append("🔗")
    
    # Key labels (excluding type labels)
    key_labels = []
    for label in issue.get("labels", [])[:3]:
        label_lower = label.lower()
        if not any(x in label_lower for x in ["bug", "enhancement", "documentation", "size/"]):
            key_labels.append(label[:15])
    labels_str = ", ".join(key_labels) if key_labels else "—"
    
    status_str = " ".join(status_icons) if status_icons else ""
    
    f.write(f"| [#{number}]({issue['url']}) {title} | {priority:.0f} | {age} | {updated} ago {status_str} | {type_icon} | {labels_str} |\n")


def write_issue_entry(f, issue: Dict[str, Any]) -> None:
    """Write a single issue entry with full details (legacy, kept for compatibility)."""
    f.write(f"#### #{issue['number']}: {issue['title']}\n\n")
    
    # Status badges
    badges = []
    if issue.get("label_types", {}).get("bug"):
        badges.append("🐛 Bug")
    if issue.get("label_types", {}).get("enhancement"):
        badges.append("✨ Enhancement")
    if issue.get("is_assigned"):
        badges.append(f"👤 Assigned: {', '.join(issue.get('assignees', []))}")
    else:
        badges.append("⚠️ Unassigned")
    
    if issue.get("days_since_update", 0) > 180:
        badges.append("💤 Stale")
    elif issue.get("days_since_update", 0) < 30:
        badges.append("🔥 Active")
    
    if badges:
        f.write(f"**Status:** {' | '.join(badges)}\n\n")
    
    # Core details
    f.write(f"- **URL:** {issue['url']}\n")
    f.write(f"- **Confidence:** {issue['confidence']:.1f}%\n")
    f.write(f"- **Priority Score:** {issue.get('priority_score', 0):.0f}/100\n")
    f.write(f"- **Created:** {issue['created_at'][:10]} ({format_age(issue.get('age_days', 0))} ago)\n")
    f.write(f"- **Last Updated:** {issue.get('updated_at', 'N/A')[:10]} ({format_age(issue.get('days_since_update', 0))} ago)\n")
    f.write(f"- **Comments:** {issue.get('comments', 0)}\n")
    
    # Labels
    if issue.get('labels'):
        f.write(f"- **Labels:** {', '.join(issue['labels'])}\n")
    
    # Related categories (cross-reference)
    if issue.get('related_categories'):
        f.write(f"- **Also Related To:** {', '.join(issue['related_categories'])}\n")
    
    f.write("\n")


if __name__ == "__main__":
    sys.exit(main())
