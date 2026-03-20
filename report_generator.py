"""Generates markdown and HTML reports for analyzed issues."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, TextIO

from config import OUTPUT_DIR
from html_report_generator import generate_html_report
from types_definitions import IssueData
from utils import format_age

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Handles report generation in various formats."""

    def generate_markdown_report(
        self,
        issues: List[Dict[str, Any]],
        output_file: str = "terraform_target_services_issues_report_en.md",
    ) -> None:
        """Generates markdown report of relevant issues."""
        report_path = OUTPUT_DIR / output_file

        with open(report_path, "w", encoding="utf-8") as report_file:
            self._write_header(report_file, len(issues))
            self._write_issues_by_category(report_file, issues)

        logger.info("Report generated at %s", report_path)

    def _write_header(self, report_file: TextIO, total_issues: int) -> None:
        """Writes report header."""
        report_file.write("# Terraform Provider Google - Available Issues Report\n\n")
        report_file.write(f"**Total Issues Found:** {total_issues}\n\n")

    def _write_issues_by_category(self, report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
        """Groups and writes issues by category."""
        by_category = self._group_by_category(issues)

        for category, cat_issues in by_category.items():
            report_file.write(f"## {category} ({len(cat_issues)} issues)\n\n")
            self._write_category_issues(report_file, cat_issues)

    def _group_by_category(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Groups issues by category."""
        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for issue in issues:
            category = issue["category"]
            by_category.setdefault(category, []).append(issue)
        return by_category

    def _write_category_issues(self, report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
        """Writes issues for a specific category."""
        sorted_issues = sorted(issues, key=lambda value: value["confidence"], reverse=True)

        for issue in sorted_issues:
            report_file.write(f"### #{issue['number']}: {issue['title']}\n\n")
            report_file.write(f"- **Confidence:** {issue['confidence']:.1f}%\n")
            report_file.write(f"- **URL:** {issue['url']}\n")
            report_file.write(f"- **Created:** {issue['created_at']}\n")
            report_file.write(f"- **Comments:** {issue['comments']}\n\n")


def generate_analysis_reports(
    issues: List[IssueData], output_dir: Path = OUTPUT_DIR
) -> Dict[str, Path]:
    """Generate the main markdown and HTML report artifacts.

    Args:
        issues: Enriched issue payloads ready for reporting.
        output_dir: Target directory for report files.

    Returns:
        Mapping with markdown and html report output paths.
    """
    report_path = output_dir / "terraform_target_services_issues_report_en.md"
    now = datetime.now()

    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write("# Terraform Provider Google - Issues Analysis Report\n\n")
        report_file.write(f"**Report Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        report_file.write(f"**Total Issues Analyzed:** {len(issues)}\n\n")
        report_file.write("**Confidence Threshold:** ≥75%\n\n")
        report_file.write("---\n\n")
        generic_issues: List[Dict[str, Any]] = [dict(issue) for issue in issues]
        write_executive_summary(report_file, generic_issues)
        write_quick_wins(report_file, generic_issues)
        write_attention_needed(report_file, generic_issues)
        write_priority_recommendations(report_file, generic_issues)
        write_age_analysis(report_file, generic_issues)
        write_label_distribution(report_file, generic_issues)
        write_category_summary(report_file, generic_issues)
        write_issues_by_category(report_file, generic_issues)

    html_path = generate_html_report(issues, output_dir)
    return {"markdown": report_path, "html": html_path}


def write_executive_summary(report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
    """Write executive summary section."""
    report_file.write("## 📊 Executive Summary\n\n")

    total = len(issues)
    if total == 0:
        report_file.write("No issues found matching the criteria.\n\n")
        return

    bugs = sum(1 for issue in issues if issue.get("label_types", {}).get("bug", False))
    enhancements = sum(1 for issue in issues if issue.get("label_types", {}).get("enhancement", False))
    assigned = sum(1 for issue in issues if issue.get("is_assigned", False))
    unassigned = total - assigned
    has_pr = sum(1 for issue in issues if issue.get("label_types", {}).get("has_pr", False))
    high_confidence = sum(1 for issue in issues if issue.get("confidence_band") == "HIGH")
    review_confidence = sum(1 for issue in issues if issue.get("confidence_band") == "REVIEW")

    avg_age = sum(issue.get("age_days", 0) for issue in issues) / total
    avg_comments = sum(issue.get("comments", 0) for issue in issues) / total

    stale_count = sum(1 for issue in issues if issue.get("days_since_update", 0) > 180)
    active_count = sum(1 for issue in issues if issue.get("days_since_update", 0) < 30)

    report_file.write("| Metric | Value |\n")
    report_file.write("|--------|-------|\n")
    report_file.write(f"| Total Issues | {total} |\n")
    report_file.write(f"| 🟢 High Confidence | {high_confidence} ({high_confidence*100//total}%) |\n")
    report_file.write(f"| 🟡 Review Confidence | {review_confidence} ({review_confidence*100//total}%) |\n")
    report_file.write(f"| 🐛 Bugs | {bugs} ({bugs*100//total}%) |\n")
    report_file.write(f"| ✨ Enhancements | {enhancements} ({enhancements*100//total}%) |\n")
    report_file.write(f"| 👤 Assigned | {assigned} ({assigned*100//total}%) |\n")
    report_file.write(f"| ⚠️ Unassigned | {unassigned} ({unassigned*100//total}%) |\n")
    report_file.write(f"| 📅 Average Age | {format_age(int(avg_age))} |\n")
    report_file.write(f"| 💬 Avg Comments | {avg_comments:.1f} |\n")
    report_file.write(f"| 🔥 Active (<30d) | {active_count} |\n")
    report_file.write(f"| 💤 Stale (>180d) | {stale_count} |\n")
    report_file.write(f"| 🔗 Has PR | {has_pr} |\n")
    report_file.write("\n")


def write_quick_wins(report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
    """Write quick wins section - easy issues to tackle."""
    quick_wins: List[Dict[str, Any]] = []
    for issue in issues:
        labels_lower = [label.lower() for label in issue.get("labels", [])]
        is_small = any(token in label for label in labels_lower for token in ["size/xs", "size/s"])
        has_pr = issue.get("label_types", {}).get("has_pr", False)
        is_good_first = issue.get("label_types", {}).get("good_first_issue", False)

        if is_small or has_pr or is_good_first:
            quick_wins.append(
                {
                    **issue,
                    "reason": (
                        "Has PR" if has_pr else ("Good First Issue" if is_good_first else "Small Size")
                    ),
                }
            )

    if not quick_wins:
        return

    report_file.write("## 🚀 Quick Wins\n\n")
    report_file.write("Issues that may be easier to resolve (small size, has PR, or good first issue).\n\n")

    quick_wins = sorted(quick_wins, key=lambda value: value.get("priority_score", 0), reverse=True)[:10]

    report_file.write("| Issue | Category | Confidence | Reason | Age | Priority |\n")
    report_file.write("|-------|----------|------------|--------|-----|----------|\n")

    for issue in quick_wins:
        title = issue["title"][:40] + "..." if len(issue["title"]) > 40 else issue["title"]
        report_file.write(
            f"| [#{issue['number']}]({issue['url']}) {title} | {issue['category']} | "
            f"{issue.get('confidence_band', 'EXCLUDED')} ({issue.get('confidence', 0):.1f}%) | "
            f"{issue['reason']} | {format_age(issue.get('age_days', 0))} | "
            f"{issue.get('priority_score', 0):.0f} |\n"
        )

    report_file.write("\n")


def write_attention_needed(report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
    """Write attention needed section - stale issues with high engagement."""
    attention_issues = [
        issue
        for issue in issues
        if issue.get("days_since_update", 0) > 180
        and issue.get("comments", 0) >= 3
        and not issue.get("is_assigned", False)
    ]

    if not attention_issues:
        return

    report_file.write("## ⚠️ Attention Needed\n\n")
    report_file.write("Stale issues (>6 months) with significant community interest (3+ comments) but no assignee.\n\n")

    attention_issues = sorted(attention_issues, key=lambda value: value.get("comments", 0), reverse=True)[:10]

    report_file.write("| Issue | Category | Confidence | Comments | Last Update | Type |\n")
    report_file.write("|-------|----------|------------|----------|-------------|------|\n")

    for issue in attention_issues:
        title = issue["title"][:40] + "..." if len(issue["title"]) > 40 else issue["title"]
        issue_type = "🐛" if issue.get("label_types", {}).get("bug") else "✨"
        last_update = format_age(issue.get("days_since_update", 0))
        report_file.write(
            f"| [#{issue['number']}]({issue['url']}) {title} | {issue['category']} | "
            f"{issue.get('confidence_band', 'EXCLUDED')} ({issue.get('confidence', 0):.1f}%) | "
            f"{issue.get('comments', 0)} | {last_update} ago | {issue_type} |\n"
        )

    report_file.write("\n")


def write_priority_recommendations(report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
    """Write top priority issues section."""
    report_file.write("## 🎯 Top 10 Priority Issues\n\n")
    top_issues = sorted(issues, key=lambda value: value.get("priority_score", 0), reverse=True)[:10]

    report_file.write("| # | Issue | Category | Confidence | Priority | Age | Status |\n")
    report_file.write("|---|-------|----------|------------|----------|-----|--------|\n")

    for idx, issue in enumerate(top_issues, 1):
        title = issue["title"][:45] + "..." if len(issue["title"]) > 45 else issue["title"]
        status_parts: List[str] = []
        if issue.get("label_types", {}).get("bug"):
            status_parts.append("🐛")
        if issue.get("is_assigned"):
            status_parts.append("👤")
        if issue.get("days_since_update", 0) > 180:
            status_parts.append("💤")
        elif issue.get("days_since_update", 0) < 30:
            status_parts.append("🔥")
        status = " ".join(status_parts) or "—"
        report_file.write(
            f"| {idx} | [#{issue['number']}]({issue['url']}) {title} | {issue['category']} | "
            f"{issue.get('confidence_band', 'EXCLUDED')} ({issue.get('confidence', 0):.1f}%) | "
            f"{issue.get('priority_score', 0):.0f} | {format_age(issue.get('age_days', 0))} | {status} |\n"
        )

    report_file.write("\n")
    report_file.write("**Legend:** 🐛 Bug | 👤 Assigned | 💤 Stale | 🔥 Active\n\n")


def write_age_analysis(report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
    """Write age distribution analysis in collapsible section."""
    report_file.write("<details>\n<summary><strong>📅 Age Analysis</strong> (click to expand)</summary>\n\n")

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

    report_file.write("| Age Range | Count | Distribution |\n")
    report_file.write("|-----------|-------|-------------|\n")
    total = len(issues)
    for bucket, count in buckets.items():
        pct = (count * 100 // total) if total else 0
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        report_file.write(f"| {bucket} | {count} | {bar} {pct}% |\n")

    report_file.write("\n")
    oldest = sorted(issues, key=lambda value: value.get("age_days", 0), reverse=True)[:5]
    if oldest:
        report_file.write("**🏚️ Oldest Open Issues:**\n\n")
        for issue in oldest:
            title = issue["title"][:50] + "..." if len(issue["title"]) > 50 else issue["title"]
            report_file.write(
                f"- [#{issue['number']}]({issue['url']}) ({issue.get('age_days', 0) / 365:.1f}y) - {title}\n"
            )
        report_file.write("\n")

    report_file.write("</details>\n\n")


def write_label_distribution(report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
    """Write label distribution analysis in collapsible section."""
    report_file.write("<details>\n<summary><strong>🏷️ Label Distribution</strong> (click to expand)</summary>\n\n")
    label_counts = {
        "🐛 Bug": sum(1 for issue in issues if issue.get("label_types", {}).get("bug")),
        "✨ Enhancement": sum(1 for issue in issues if issue.get("label_types", {}).get("enhancement")),
        "📚 Documentation": sum(1 for issue in issues if issue.get("label_types", {}).get("documentation")),
        "⬆️ Upstream": sum(1 for issue in issues if issue.get("label_types", {}).get("upstream")),
        "💥 Breaking Change": sum(
            1 for issue in issues if issue.get("label_types", {}).get("breaking_change")
        ),
        "🔗 Has PR": sum(1 for issue in issues if issue.get("label_types", {}).get("has_pr")),
        "⏳ Waiting/Blocked": sum(1 for issue in issues if issue.get("label_types", {}).get("waiting")),
        "👶 Good First Issue": sum(
            1 for issue in issues if issue.get("label_types", {}).get("good_first_issue")
        ),
    }
    report_file.write("| Label Type | Count |\n")
    report_file.write("|------------|-------|\n")
    for label, count in label_counts.items():
        if count > 0:
            report_file.write(f"| {label} | {count} |\n")
    report_file.write("\n</details>\n\n")


def write_category_summary(report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
    """Write category summary table."""
    report_file.write("## 📁 Category Summary\n\n")
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for issue in issues:
        by_category.setdefault(issue["category"], []).append(issue)

    report_file.write("| Category | Issues | Bugs | Enhancements | Avg Age | Stale |\n")
    report_file.write("|----------|--------|------|--------------|---------|-------|\n")
    for category in sorted(by_category.keys()):
        cat_issues = by_category[category]
        count = len(cat_issues)
        bugs = sum(1 for issue in cat_issues if issue.get("label_types", {}).get("bug"))
        enhancements = sum(1 for issue in cat_issues if issue.get("label_types", {}).get("enhancement"))
        avg_age = sum(issue.get("age_days", 0) for issue in cat_issues) / count if count else 0
        stale = sum(1 for issue in cat_issues if issue.get("days_since_update", 0) > 180)
        report_file.write(
            f"| {category} | {count} | {bugs} | {enhancements} | {format_age(int(avg_age))} | {stale} |\n"
        )
    report_file.write("\n")


def write_issues_by_category(report_file: TextIO, issues: List[Dict[str, Any]]) -> None:
    """Write detailed issues grouped by category in collapsible sections."""
    report_file.write("---\n\n")
    report_file.write("## 📋 Detailed Issues by Category\n\n")
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for issue in issues:
        by_category.setdefault(issue["category"], []).append(issue)

    for category in sorted(by_category.keys()):
        cat_issues = by_category[category]
        report_file.write(
            f"<details>\n<summary><strong>{category}</strong> ({len(cat_issues)} issues)</summary>\n\n"
        )
        sorted_issues = sorted(cat_issues, key=lambda value: value.get("priority_score", 0), reverse=True)
        report_file.write("| Issue | Confidence | Priority | Age | Updated | Type | Labels |\n")
        report_file.write("|-------|------------|----------|-----|---------|------|--------|\n")
        for issue in sorted_issues:
            write_issue_row(report_file, issue)
        report_file.write("\n</details>\n\n")


def write_issue_row(report_file: TextIO, issue: Dict[str, Any]) -> None:
    """Write a single issue as a table row."""
    title = issue["title"][:50] + "..." if len(issue["title"]) > 50 else issue["title"]
    type_icon = ""
    if issue.get("label_types", {}).get("bug"):
        type_icon = "🐛"
    elif issue.get("label_types", {}).get("enhancement"):
        type_icon = "✨"
    elif issue.get("label_types", {}).get("documentation"):
        type_icon = "📚"

    status_icons: List[str] = []
    if issue.get("is_assigned"):
        status_icons.append("👤")
    if issue.get("days_since_update", 0) > 180:
        status_icons.append("💤")
    elif issue.get("days_since_update", 0) < 30:
        status_icons.append("🔥")
    if issue.get("label_types", {}).get("has_pr"):
        status_icons.append("🔗")

    key_labels: List[str] = []
    for label in issue.get("labels", [])[:3]:
        label_lower = label.lower()
        if not any(token in label_lower for token in ["bug", "enhancement", "documentation", "size/"]):
            key_labels.append(label[:15])
    labels_str = ", ".join(key_labels) if key_labels else "—"
    status_str = " ".join(status_icons) if status_icons else ""

    report_file.write(
        f"| [#{issue['number']}]({issue['url']}) {title} | "
        f"{issue.get('confidence_band', 'EXCLUDED')} ({issue.get('confidence', 0):.1f}%) | "
        f"{issue.get('priority_score', 0):.0f} | {format_age(issue.get('age_days', 0))} | "
        f"{format_age(issue.get('days_since_update', 0))} ago {status_str} | {type_icon} | {labels_str} |\n"
    )
