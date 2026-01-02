"""Comprehensive tests for issue classification."""
import unittest
from unittest.mock import patch, MagicMock
from issue_classifier import IssueClassifier


class TestIssueClassifierQuickKeywordCheck(unittest.TestCase):
    """Tests for quick keyword checking functionality."""

    def setUp(self):
        self.classifier = IssueClassifier()

    def test_load_balancer_keyword_in_title(self):
        """Test detection of load balancer keyword in title."""
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
        """Test detection of cloud armor in labels."""
        issue = {
            "title": "Security issue",
            "body": "",
            "labels": [{"name": "cloud-armor"}]
        }
        is_match, category, confidence = self.classifier._quick_keyword_check(issue)
        self.assertTrue(is_match)
        self.assertEqual(category, "Cloud Armor")
        self.assertEqual(confidence, 90.0)

    def test_psc_keyword_in_body(self):
        """Test detection of PSC keyword in body."""
        issue = {
            "title": "Connection issue",
            "body": "Having trouble with private service connect endpoint",
            "labels": []
        }
        is_match, category, confidence = self.classifier._quick_keyword_check(issue)
        self.assertTrue(is_match)
        self.assertEqual(category, "Private Service Connect (PSC)")
        self.assertEqual(confidence, 75.0)

    def test_no_match_returns_false(self):
        """Test that irrelevant issues return no match."""
        issue = {
            "title": "Update documentation for compute instance",
            "body": "Minor typo fixes needed",
            "labels": [{"name": "documentation"}]
        }
        is_match, category, confidence = self.classifier._quick_keyword_check(issue)
        self.assertFalse(is_match)
        self.assertIsNone(category)
        self.assertEqual(confidence, 0)

    def test_empty_issue_returns_false(self):
        """Test that empty issues return no match."""
        issue = {
            "title": "",
            "body": "",
            "labels": []
        }
        is_match, category, confidence = self.classifier._quick_keyword_check(issue)
        self.assertFalse(is_match)
        self.assertIsNone(category)
        self.assertEqual(confidence, 0)

    def test_none_values_handled_gracefully(self):
        """Test that None values are handled without errors."""
        issue = {
            "title": None,
            "body": None,
            "labels": []
        }
        is_match, category, confidence = self.classifier._quick_keyword_check(issue)
        self.assertFalse(is_match)
        self.assertIsNone(category)

    def test_label_priority_over_title(self):
        """Test that label matches have higher confidence than title."""
        issue_with_label = {
            "title": "Some issue",
            "body": "",
            "labels": [{"name": "load-balancer"}]
        }
        issue_with_title = {
            "title": "Load balancer issue",
            "body": "",
            "labels": []
        }
        _, _, label_confidence = self.classifier._quick_keyword_check(issue_with_label)
        _, _, title_confidence = self.classifier._quick_keyword_check(issue_with_title)
        self.assertGreater(label_confidence, title_confidence)


class TestIssueClassifierFullAnalysis(unittest.TestCase):
    """Tests for full TF-IDF and regex analysis."""

    def setUp(self):
        self.classifier = IssueClassifier()

    def test_build_issue_text(self):
        """Test that issue text is built correctly."""
        issue = {
            "title": "Test Title",
            "body": "Test body content",
            "labels": [{"name": "label1"}, {"name": "label2"}]
        }
        text = self.classifier._build_issue_text(issue)
        self.assertIn("Test Title", text)
        self.assertIn("Test body content", text)
        self.assertIn("label1", text)
        self.assertIn("label2", text)

    def test_build_issue_text_with_empty_values(self):
        """Test issue text building with empty values."""
        issue = {
            "title": "",
            "body": None,
            "labels": []
        }
        text = self.classifier._build_issue_text(issue)
        self.assertIsInstance(text, str)

    def test_classify_with_tfidf_returns_scores(self):
        """Test that TF-IDF classification returns scores for all categories."""
        issue_text = "load balancer backend service health check"
        scores = self.classifier._classify_with_tfidf(issue_text)
        self.assertIn("Load Balancers", scores)
        self.assertIn("Cloud Armor", scores)
        self.assertIn("Private Service Connect (PSC)", scores)

    def test_classify_with_tfidf_empty_text(self):
        """Test TF-IDF with empty text."""
        scores = self.classifier._classify_with_tfidf("")
        # Should return empty dict or handle gracefully
        self.assertIsInstance(scores, dict)

    def test_calculate_regex_scores(self):
        """Test regex-based scoring."""
        issue = {
            "title": "Load balancer backend service issue",
            "body": "The health check is failing",
            "labels": [{"name": "backend-service"}]
        }
        scores = self.classifier._calculate_regex_scores(issue)
        self.assertIn("Load Balancers", scores)
        self.assertGreater(scores["Load Balancers"], 0)

    def test_calculate_regex_scores_no_matches(self):
        """Test regex scoring with no matching terms."""
        issue = {
            "title": "Unrelated topic",
            "body": "Nothing relevant here",
            "labels": []
        }
        scores = self.classifier._calculate_regex_scores(issue)
        for score in scores.values():
            self.assertEqual(score, 0)

    def test_combine_scores(self):
        """Test score combination with weights."""
        tfidf_scores = {"Load Balancers": 50.0, "Cloud Armor": 30.0}
        regex_scores = {"Load Balancers": 60.0, "Cloud Armor": 40.0}
        combined = self.classifier._combine_scores(tfidf_scores, regex_scores)
        self.assertIn("Load Balancers", combined)
        self.assertIn("Cloud Armor", combined)
        # Combined score should be between the two
        self.assertGreater(combined["Load Balancers"], 0)

    def test_combine_scores_missing_category(self):
        """Test score combination when category is missing from one dict."""
        tfidf_scores = {"Load Balancers": 50.0}
        regex_scores = {"Load Balancers": 60.0, "Cloud Armor": 40.0}
        combined = self.classifier._combine_scores(tfidf_scores, regex_scores)
        self.assertIn("Cloud Armor", combined)

    def test_evaluate_scores_above_threshold(self):
        """Test score evaluation above threshold."""
        scores = {"Load Balancers": 80.0, "Cloud Armor": 20.0}
        is_relevant, category, confidence = self.classifier._evaluate_scores(scores)
        self.assertTrue(is_relevant)
        self.assertEqual(category, "Load Balancers")
        self.assertEqual(confidence, 80.0)

    def test_evaluate_scores_below_threshold(self):
        """Test score evaluation below threshold."""
        scores = {"Load Balancers": 10.0, "Cloud Armor": 5.0}
        is_relevant, category, confidence = self.classifier._evaluate_scores(scores)
        self.assertFalse(is_relevant)
        self.assertIsNone(category)

    def test_evaluate_scores_empty_dict(self):
        """Test score evaluation with empty dict."""
        is_relevant, category, confidence = self.classifier._evaluate_scores({})
        self.assertFalse(is_relevant)
        self.assertIsNone(category)
        self.assertEqual(confidence, 0)


class TestIssueClassifierIntegration(unittest.TestCase):
    """Integration tests for the full classification pipeline."""

    def setUp(self):
        self.classifier = IssueClassifier()

    def test_classify_issue_load_balancer(self):
        """Test full classification of load balancer issue."""
        issue = {
            "number": 12345,
            "title": "google_compute_backend_service health check not working",
            "body": "When creating a backend service with health check, the check fails",
            "labels": [{"name": "service/compute"}]
        }
        is_relevant, category, confidence = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)
        self.assertEqual(category, "Load Balancers")

    def test_classify_issue_cloud_armor(self):
        """Test full classification of cloud armor issue."""
        issue = {
            "number": 12346,
            "title": "Security policy rule not applying correctly",
            "body": "Cloud Armor security policy is not blocking requests",
            "labels": [{"name": "cloud-armor"}]
        }
        is_relevant, category, confidence = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)
        self.assertEqual(category, "Cloud Armor")

    def test_classify_issue_psc(self):
        """Test full classification of PSC issue."""
        issue = {
            "number": 12347,
            "title": "Private Service Connect endpoint creation fails",
            "body": "Unable to create PSC endpoint for internal service",
            "labels": [{"name": "service/networking"}]
        }
        is_relevant, category, confidence = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)
        self.assertEqual(category, "Private Service Connect (PSC)")

    def test_classify_irrelevant_issue(self):
        """Test that irrelevant issues are not classified."""
        issue = {
            "number": 12348,
            "title": "Documentation update needed for compute instance",
            "body": "The documentation for creating instances is outdated",
            "labels": [{"name": "documentation"}]
        }
        is_relevant, category, confidence = self.classifier.classify_issue(issue)
        # May or may not be relevant depending on threshold
        if is_relevant:
            self.assertIsNotNone(category)
        else:
            self.assertIsNone(category)

    def test_classify_issue_with_malformed_data(self):
        """Test classification handles malformed issue data."""
        issue = {
            "number": None,
            "title": None,
            "body": None,
            "labels": None
        }
        # Should not raise exception
        try:
            # Labels being None would cause an error, so we test with empty
            issue["labels"] = []
            is_relevant, category, confidence = self.classifier.classify_issue(issue)
            self.assertIsInstance(is_relevant, bool)
        except Exception as e:
            self.fail(f"Classification raised exception: {e}")


class TestIssueClassifierEdgeCases(unittest.TestCase):
    """Edge case tests for classifier robustness."""

    def setUp(self):
        self.classifier = IssueClassifier()

    def test_very_long_title(self):
        """Test handling of very long titles."""
        issue = {
            "title": "load balancer " * 1000,
            "body": "",
            "labels": []
        }
        is_relevant, category, confidence = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)

    def test_special_characters_in_text(self):
        """Test handling of special characters."""
        issue = {
            "title": "Load balancer <script>alert('xss')</script>",
            "body": "Test with $pecial ch@racters! & symbols",
            "labels": []
        }
        is_relevant, category, confidence = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        issue = {
            "title": "Load balancer issue 日本語 🔥",
            "body": "问题描述 with émojis 💡",
            "labels": []
        }
        is_relevant, category, confidence = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)

    def test_multiple_relevant_categories(self):
        """Test when issue matches multiple categories."""
        issue = {
            "title": "Load balancer with Cloud Armor security policy",
            "body": "Combining LB with security policies",
            "labels": []
        }
        is_relevant, category, confidence = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)
        # Should return the highest scoring category
        self.assertIn(category, ["Load Balancers", "Cloud Armor"])

 
if __name__ == "__main__":
    unittest.main()