"""Integration tests for the cli.py analysis pipeline."""
import unittest
from unittest.mock import Mock, patch, MagicMock

from terraform_issues_analyzer.cli import analyze_issues
from terraform_issues_analyzer.issue_classifier import IssueClassifier
from terraform_issues_analyzer.availability_checker import AvailabilityChecker


class TestAnalyzeIssues(unittest.TestCase):
    """Tests for the analyze_issues pipeline."""

    def setUp(self):
        self.classifier = IssueClassifier()
        self.mock_github_client = Mock()
        self.availability_checker = AvailabilityChecker(self.mock_github_client)

    def _make_issue(self, number=1, title="Cloud Armor security policy bug",
                    body="google_compute_security_policy fails", labels=None,
                    comments=0, assignees=None):
        return {
            "number": number,
            "title": title,
            "body": body,
            "html_url": f"https://github.com/test/{number}",
            "state": "open",
            "labels": labels or [],
            "assignees": assignees or [],
            "comments": comments,
            "comments_url": f"https://api.github.com/repos/test/issues/{number}/comments",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "reactions": {"+1": 5},
        }

    def test_relevant_available_issue_included(self):
        """A relevant and available Cloud Armor issue should be in results."""
        issue = self._make_issue(labels=[{"name": "cloud-armor"}])
        self.mock_github_client.fetch_issue_comments.return_value = []
        self.mock_github_client.fetch_issue_timeline.return_value = []

        result = analyze_issues([issue], self.classifier, self.availability_checker)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["number"], 1)
        self.assertEqual(result[0]["category"], "Cloud Armor")

    def test_pull_request_skipped(self):
        """Issues with pull_request key should be skipped."""
        issue = self._make_issue()
        issue["pull_request"] = {"url": "..."}

        result = analyze_issues([issue], self.classifier, self.availability_checker)
        self.assertEqual(len(result), 0)

    def test_irrelevant_issue_excluded(self):
        """Non-Cloud-Armor issue should be excluded."""
        issue = self._make_issue(
            title="google_storage_bucket lifecycle bug",
            body="Storage lifecycle not working",
        )

        result = analyze_issues([issue], self.classifier, self.availability_checker)
        self.assertEqual(len(result), 0)

    def test_assigned_issue_excluded(self):
        """Assigned issues should be excluded by availability checker."""
        issue = self._make_issue(
            labels=[{"name": "cloud-armor"}],
            assignees=[{"login": "someone"}],
        )

        result = analyze_issues([issue], self.classifier, self.availability_checker)
        self.assertEqual(len(result), 0)

    def test_result_has_required_fields(self):
        """Returned IssueData should have all required fields."""
        issue = self._make_issue(labels=[{"name": "cloud-armor"}])
        self.mock_github_client.fetch_issue_comments.return_value = []
        self.mock_github_client.fetch_issue_timeline.return_value = []

        result = analyze_issues([issue], self.classifier, self.availability_checker)
        self.assertEqual(len(result), 1)

        data = result[0]
        required_fields = [
            "number", "title", "url", "category", "confidence",
            "confidence_band", "priority_score", "age_days",
            "days_since_update", "labels", "label_types",
        ]
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")
