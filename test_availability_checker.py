import unittest
from unittest.mock import Mock
from availability_checker import AvailabilityChecker


class TestAvailabilityChecker(unittest.TestCase):
    def setUp(self):
        self.github_client = Mock()
        self.checker = AvailabilityChecker(self.github_client)

    def test_issue_with_assignee_is_unavailable(self):
        issue = {
            "assignees": [{"login": "testuser"}],
            "labels": [],
            "comments": 0
        }
        is_available, reason = self.checker.is_issue_available(issue)
        self.assertFalse(is_available)
        self.assertEqual(reason, "assigned_to_testuser")

    def test_issue_with_wip_label_is_unavailable(self):
        issue = {
            "assignees": [],
            "labels": [{"name": "wip"}],
            "comments": 0
        }
        is_available, reason = self.checker.is_issue_available(issue)
        self.assertFalse(is_available)
        self.assertIn("label_indicates_work_in_progress", reason)
