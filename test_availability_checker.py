"""Comprehensive tests for availability checking functionality."""
import unittest
from unittest.mock import Mock, patch
from availability_checker import AvailabilityChecker


class TestAvailabilityCheckerAssignees(unittest.TestCase):
    """Tests for assignee checking functionality."""

    def setUp(self):
        self.github_client = Mock()
        self.checker = AvailabilityChecker(self.github_client)

    def test_issue_with_assignee_is_unavailable(self):
        """Test that issues with assignees are unavailable."""
        issue = {
            "assignees": [{"login": "testuser"}],
            "labels": [],
            "comments": 0
        }
        is_available, reason = self.checker.is_issue_available(issue)
        self.assertFalse(is_available)
        self.assertEqual(reason, "assigned_to_testuser")

    def test_issue_with_multiple_assignees(self):
        """Test that issues with multiple assignees use first assignee."""
        issue = {
            "assignees": [{"login": "user1"}, {"login": "user2"}],
            "labels": [],
            "comments": 0
        }
        is_available, reason = self.checker.is_issue_available(issue)
        self.assertFalse(is_available)
        self.assertEqual(reason, "assigned_to_user1")

    def test_issue_without_assignee_is_available(self):
        """Test that issues without assignees pass assignee check."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 0
        }
        is_available, reason = self.checker.is_issue_available(issue)
        self.assertTrue(is_available)
        self.assertIsNone(reason)

    def test_issue_with_empty_assignee_list(self):
        """Test that empty assignee list is handled correctly."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 0
        }
        is_available, reason = self.checker._check_assignees(issue)
        self.assertTrue(is_available)

    def test_missing_assignees_field(self):
        """Test handling of missing assignees field."""
        issue = {"labels": [], "comments": 0}
        is_available, reason = self.checker._check_assignees(issue)
        self.assertTrue(is_available)


class TestAvailabilityCheckerLabels(unittest.TestCase):
    """Tests for label checking functionality."""

    def setUp(self):
        self.github_client = Mock()
        self.checker = AvailabilityChecker(self.github_client)

    def test_issue_with_wip_label_is_unavailable(self):
        """Test that WIP labeled issues are unavailable."""
        issue = {
            "assignees": [],
            "labels": [{"name": "wip"}],
            "comments": 0
        }
        is_available, reason = self.checker.is_issue_available(issue)
        self.assertFalse(is_available)
        self.assertIn("label_indicates_work_in_progress", reason)

    def test_issue_with_in_progress_label(self):
        """Test that in-progress labeled issues are unavailable."""
        issue = {
            "assignees": [],
            "labels": [{"name": "in-progress"}],
            "comments": 0
        }
        is_available, reason = self.checker._check_labels(issue)
        self.assertFalse(is_available)

    def test_issue_with_assigned_label(self):
        """Test that assigned labeled issues are unavailable."""
        issue = {
            "assignees": [],
            "labels": [{"name": "assigned"}],
            "comments": 0
        }
        is_available, reason = self.checker._check_labels(issue)
        self.assertFalse(is_available)

    def test_issue_with_claimed_label(self):
        """Test that claimed labeled issues are unavailable."""
        issue = {
            "assignees": [],
            "labels": [{"name": "claimed"}],
            "comments": 0
        }
        is_available, reason = self.checker._check_labels(issue)
        self.assertFalse(is_available)

    def test_issue_with_waiting_for_pr_label(self):
        """Test that waiting-for-pr labeled issues are unavailable."""
        issue = {
            "assignees": [],
            "labels": [{"name": "waiting-for-pr"}],
            "comments": 0
        }
        is_available, reason = self.checker._check_labels(issue)
        self.assertFalse(is_available)

    def test_issue_with_has_pr_label(self):
        """Test that has-pr labeled issues are unavailable."""
        issue = {
            "assignees": [],
            "labels": [{"name": "has-pr"}],
            "comments": 0
        }
        is_available, reason = self.checker._check_labels(issue)
        self.assertFalse(is_available)

    def test_issue_with_neutral_labels(self):
        """Test that neutral labels don't affect availability."""
        issue = {
            "assignees": [],
            "labels": [{"name": "bug"}, {"name": "enhancement"}, {"name": "help wanted"}],
            "comments": 0
        }
        is_available, reason = self.checker._check_labels(issue)
        self.assertTrue(is_available)

    def test_case_insensitive_label_check(self):
        """Test that label checking is case insensitive."""
        issue = {
            "assignees": [],
            "labels": [{"name": "WIP"}],
            "comments": 0
        }
        is_available, reason = self.checker._check_labels(issue)
        self.assertFalse(is_available)


class TestAvailabilityCheckerComments(unittest.TestCase):
    """Tests for comment checking functionality."""

    def setUp(self):
        self.github_client = Mock()
        self.checker = AvailabilityChecker(self.github_client)

    def test_issue_with_no_comments_is_available(self):
        """Test that issues without comments are available."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 0
        }
        is_available, reason = self.checker._check_comments(issue)
        self.assertTrue(is_available)

    def test_issue_with_commitment_comment(self):
        """Test that issues with commitment comments are unavailable."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 1,
            "comments_url": "https://api.github.com/repos/test/issues/1/comments"
        }
        self.github_client.fetch_issue_comments.return_value = [
            {"body": "I'll fix this issue", "user": {"login": "contributor"}}
        ]
        is_available, reason = self.checker._check_comments(issue)
        self.assertFalse(is_available)
        self.assertIn("comment_indicates_commitment", reason)

    def test_issue_with_working_on_comment(self):
        """Test commitment patterns: 'working on this'."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 1,
            "comments_url": "https://api.github.com/repos/test/issues/1/comments"
        }
        self.github_client.fetch_issue_comments.return_value = [
            {"body": "Working on this now", "user": {"login": "dev"}}
        ]
        is_available, reason = self.checker._check_comments(issue)
        self.assertFalse(is_available)

    def test_issue_with_pr_submitted_comment(self):
        """Test commitment patterns: 'submitted a PR'."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 1,
            "comments_url": "https://api.github.com/repos/test/issues/1/comments"
        }
        self.github_client.fetch_issue_comments.return_value = [
            {"body": "I've submitted a pull request for this", "user": {"login": "dev"}}
        ]
        is_available, reason = self.checker._check_comments(issue)
        self.assertFalse(is_available)

    def test_issue_with_taking_this_comment(self):
        """Test commitment patterns: 'taking this'."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 1,
            "comments_url": "https://api.github.com/repos/test/issues/1/comments"
        }
        self.github_client.fetch_issue_comments.return_value = [
            {"body": "Taking this one", "user": {"login": "dev"}}
        ]
        is_available, reason = self.checker._check_comments(issue)
        self.assertFalse(is_available)

    def test_issue_with_neutral_comment(self):
        """Test that neutral comments don't affect availability."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 1,
            "comments_url": "https://api.github.com/repos/test/issues/1/comments"
        }
        self.github_client.fetch_issue_comments.return_value = [
            {"body": "This is a bug in the latest release", "user": {"login": "user"}}
        ]
        is_available, reason = self.checker._check_comments(issue)
        self.assertTrue(is_available)

    def test_issue_with_many_comments(self):
        """Test that issues with too many comments are unavailable."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 10,
            "comments_url": "https://api.github.com/repos/test/issues/1/comments"
        }
        # Return many neutral comments
        self.github_client.fetch_issue_comments.return_value = [
            {"body": f"Comment {i}", "user": {"login": f"user{i}"}}
            for i in range(10)
        ]
        is_available, reason = self.checker._check_comments(issue)
        self.assertFalse(is_available)
        self.assertIn("many_discussion", reason)

    def test_missing_comments_url(self):
        """Test handling of missing comments_url."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 5
        }
        is_available, reason = self.checker._check_comments(issue)
        self.assertTrue(is_available)

    def test_api_returns_none(self):
        """Test handling when API returns None."""
        issue = {
            "assignees": [],
            "labels": [],
            "comments": 1,
            "comments_url": "https://api.github.com/repos/test/issues/1/comments"
        }
        self.github_client.fetch_issue_comments.return_value = None
        is_available, reason = self.checker._check_comments(issue)
        self.assertTrue(is_available)


class TestAvailabilityCheckerIntegration(unittest.TestCase):
    """Integration tests for the full availability check pipeline."""

    def setUp(self):
        self.github_client = Mock()
        self.checker = AvailabilityChecker(self.github_client)

    def test_fully_available_issue(self):
        """Test that a fully available issue passes all checks."""
        issue = {
            "assignees": [],
            "labels": [{"name": "bug"}, {"name": "good first issue"}],
            "comments": 2,
            "comments_url": "https://api.github.com/repos/test/issues/1/comments"
        }
        self.github_client.fetch_issue_comments.return_value = [
            {"body": "I can reproduce this bug", "user": {"login": "user1"}},
            {"body": "Same here", "user": {"login": "user2"}}
        ]
        is_available, reason = self.checker.is_issue_available(issue)
        self.assertTrue(is_available)
        self.assertIsNone(reason)

    def test_unavailable_due_to_multiple_reasons(self):
        """Test that first unavailable reason is returned."""
        issue = {
            "assignees": [{"login": "assigned_user"}],
            "labels": [{"name": "wip"}],
            "comments": 0
        }
        is_available, reason = self.checker.is_issue_available(issue)
        self.assertFalse(is_available)
        # Should return assignee reason first
        self.assertEqual(reason, "assigned_to_assigned_user")


class TestAvailabilityCheckerCommitmentPatterns(unittest.TestCase):
    """Tests for commitment pattern regex matching."""

    def setUp(self):
        self.github_client = Mock()
        self.checker = AvailabilityChecker(self.github_client)

    def test_commitment_patterns_exist(self):
        """Test that commitment patterns are defined."""
        patterns = self.checker._get_commitment_patterns()
        self.assertIsInstance(patterns, list)
        self.assertGreater(len(patterns), 0)

    def test_i_will_fix_pattern(self):
        """Test 'I will fix' pattern matches."""
        import re
        patterns = self.checker._get_commitment_patterns()
        test_text = "i will fix this issue"
        matched = any(re.search(p, test_text) for p in patterns)
        self.assertTrue(matched)

    def test_im_on_it_pattern(self):
        """Test 'I'm on it' pattern matches."""
        import re
        patterns = self.checker._get_commitment_patterns()
        test_text = "i'm on it"
        matched = any(re.search(p, test_text) for p in patterns)
        self.assertTrue(matched)


if __name__ == "__main__":
    unittest.main()