"""Generates markdown reports for analyzed issues."""
import logging
from typing import List, Dict
from config import OUTPUT_DIR

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Handles report generation in various formats."""

    def generate_markdown_report(self, issues: List[Dict],
                                 output_file: str = "terraform_target_services_issues_report_en.md") -> None:
        """Generates markdown report of relevant issues."""
        report_path = OUTPUT_DIR / output_file

        with open(report_path, 'w', encoding='utf-8') as f:
            self._write_header(f, len(issues))
            self._write_issues_by_category(f, issues)

        logger.info(f"Report generated at {report_path}")

    def _write_header(self, f, total_issues: int) -> None:
        """Writes report header."""
        f.write("# Terraform Provider Google - Available Issues Report\n\n")
        f.write(f"**Total Issues Found:** {total_issues}\n\n")

    def _write_issues_by_category(self, f, issues: List[Dict]) -> None:
        """Groups and writes issues by category."""
        by_category = self._group_by_category(issues)

        for category, cat_issues in by_category.items():
            f.write(f"## {category} ({len(cat_issues)} issues)\n\n")
            self._write_category_issues(f, cat_issues)

    def _group_by_category(self, issues: List[Dict]) -> Dict[str, List[Dict]]:
        """Groups issues by category."""
        by_category = {}
        for issue in issues:
            category = issue["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)
        return by_category

    def _write_category_issues(self, f, issues: List[Dict]) -> None:
        """Writes issues for a specific category."""
        sorted_issues = sorted(issues, key=lambda x: x["confidence"], reverse=True)

        for issue in sorted_issues:
            f.write(f"### #{issue['number']}: {issue['title']}\n\n")
            f.write(f"- **Confidence:** {issue['confidence']:.1f}%\n")
            f.write(f"- **URL:** {issue['url']}\n")
            f.write(f"- **Created:** {issue['created_at']}\n")
            f.write(f"- **Comments:** {issue['comments']}\n\n")
