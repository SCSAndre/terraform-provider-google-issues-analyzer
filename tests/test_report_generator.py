"""Comprehensive tests for report generation functionality."""
import unittest
from io import StringIO
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from pathlib import Path

from terraform_issues_analyzer.report_generator import generate_analysis_reports, write_executive_summary


class TestReportGeneratorRecentlyReactivated(unittest.TestCase):
    """Tests for recently reactivated markdown section rendering."""

    def _make_reactivated_issue(self):
        return {
            "number": 14896,
            "title": "google_compute_security_policy block is broken after GA update",
            "url": "https://github.com/test/14896",
            "state": "open",
            "category": "Cloud Armor",
            "confidence": 90.0,
            "confidence_band": "HIGH",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "age_days": 1000,
            "days_since_update": 60,
            "comments": 4,
            "labels": ["bug"],
            "label_types": {"bug": True, "has_pr": False, "good_first_issue": False},
            "assignees": [],
            "is_assigned": False,
            "related_categories": [],
            "priority_score": 80.0,
            "reactivation_bonus": 8,
        }

    @patch('terraform_issues_analyzer.report_generator.generate_html_report')
    def test_markdown_reactivated_section_present(self, mock_generate_html_report):
        """Markdown report contains the Recently Reactivated section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mock_generate_html_report.return_value = temp_path / "terraform_issues_report.html"

            paths = generate_analysis_reports([self._make_reactivated_issue()], output_dir=temp_path)
            report = paths["markdown"].read_text(encoding="utf-8")

        assert "Recently Reactivated" in report


class TestReportGeneratorContributorEntryPoints(unittest.TestCase):
    """Tests for contributor entry points markdown section rendering."""

    def _make_entry_point_issue(self):
        return {
            "number": 17062,
            "title": "Cloud Armor docs improvement for adaptive protection",
            "url": "https://github.com/test/17062",
            "state": "open",
            "category": "Cloud Armor",
            "confidence": 90.0,
            "confidence_band": "HIGH",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "age_days": 200,
            "days_since_update": 10,
            "comments": 2,
            "labels": ["size/s", "documentation"],
            "label_types": {"documentation": True, "has_pr": False, "bug": False},
            "is_blocked": False,
            "is_internally_tracked": True,
            "is_assigned": False,
            "assignees": [],
            "related_categories": [],
            "priority_score": 70.0,
        }

    @patch('terraform_issues_analyzer.report_generator.generate_html_report')
    def test_markdown_contributor_entry_points_present(self, mock_generate_html_report):
        """Markdown report contains the Contributor Entry Points section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mock_generate_html_report.return_value = temp_path / "terraform_issues_report.html"

            paths = generate_analysis_reports([self._make_entry_point_issue()], output_dir=temp_path)
            report = paths["markdown"].read_text(encoding="utf-8")

        assert "Contributor Entry Points" in report


class TestExecutiveSummaryMetrics(unittest.TestCase):
    """Tests for executive summary markdown metrics."""

    def test_executive_summary_has_pr_and_active_7d_rows(self):
        issues = [
            {
                "number": 1,
                "title": "Issue with linked PR",
                "url": "https://github.com/test/1",
                "category": "Cloud Armor",
                "confidence": 85.0,
                "confidence_band": "HIGH",
                "label_types": {"bug": True, "has_pr": True},
                "is_internally_tracked": False,
                "is_blocked": False,
                "is_assigned": False,
                "age_days": 10,
                "days_since_update": 3,
                "comments": 2,
            }
        ]

        output = StringIO()
        write_executive_summary(output, issues)
        content = output.getvalue()

        self.assertIn("| 🔗 Has Linked PR | 1 |", content)
        self.assertIn("| ⚡ Active (7d) | 1 |", content)
        self.assertNotIn("Assigned", content)


if __name__ == "__main__":
    unittest.main()
