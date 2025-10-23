import unittest
from issue_classifier import IssueClassifier


class TestIssueClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = IssueClassifier()

    def test_load_balancer_keyword_in_title(self):
        issue = {
            "title": "Fix load balancer configuration",
            "body": "",
            "labels": []
        }
        is_match, category, confidence = self.classifier._quick_keyword_check(issue)
        self.assertTrue(is_match)
        self.assertEqual(category, "Load Balancers")
        self.assertGreaterEqual(confidence, 75.0)

    def test_cloud_armor_in_labels(self):
        issue = {
            "title": "Security issue",
            "body": "",
            "labels": [{"name": "cloud-armor"}]
        }
        is_match, category, confidence = self.classifier._quick_keyword_check(issue)
        self.assertTrue(is_match)
        self.assertEqual(category, "Cloud Armor")
        self.assertEqual(confidence, 90.0)
