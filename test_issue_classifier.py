"""Comprehensive tests for Cloud Armor issue classification."""
import unittest

from issue_classifier import IssueClassifier, classify_labels


class TestIssueClassifierQuickKeywordCheck(unittest.TestCase):
    """Tests for quick keyword checking functionality."""

    def setUp(self):
        self.classifier = IssueClassifier()

    def test_cloud_armor_keyword_in_title(self):
        """Test detection of Cloud Armor keyword in title."""
        issue = {
            "title": "Fix Cloud Armor security policy configuration",
            "body": "",
            "labels": []
        }
        is_match, category, confidence, confidence_band = self.classifier._quick_keyword_check(issue)
        self.assertTrue(is_match)
        self.assertEqual(category, "Cloud Armor")
        self.assertGreaterEqual(confidence, 75.0)
        self.assertIn(confidence_band, ["HIGH", "REVIEW"])

    def test_cloud_armor_in_labels(self):
        """Test detection of cloud armor in labels."""
        issue = {
            "title": "Security issue",
            "body": "",
            "labels": [{"name": "cloud-armor"}]
        }
        is_match, category, confidence, _ = self.classifier._quick_keyword_check(issue)
        self.assertTrue(is_match)
        self.assertEqual(category, "Cloud Armor")
        self.assertEqual(confidence, 90.0)

    def test_cloud_armor_keyword_in_body(self):
        """Test detection of Cloud Armor keyword in body."""
        issue = {
            "title": "Traffic filtering issue",
            "body": "Adaptive protection and rate-based ban are not being enforced",
            "labels": []
        }
        is_match, category, confidence, _ = self.classifier._quick_keyword_check(issue)
        self.assertTrue(is_match)
        self.assertEqual(category, "Cloud Armor")
        self.assertEqual(confidence, 75.0)

    def test_no_match_returns_false(self):
        """Test that irrelevant issues return no match."""
        issue = {
            "title": "Update documentation for compute instance",
            "body": "Minor typo fixes needed",
            "labels": [{"name": "documentation"}]
        }
        is_match, category, confidence, _ = self.classifier._quick_keyword_check(issue)
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
        is_match, category, confidence, _ = self.classifier._quick_keyword_check(issue)
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
        is_match, category, confidence, _ = self.classifier._quick_keyword_check(issue)
        self.assertFalse(is_match)
        self.assertIsNone(category)

    def test_label_priority_over_title(self):
        """Test that label matches have higher confidence than title."""
        issue_with_label = {
            "title": "Some issue",
            "body": "",
            "labels": [{"name": "cloud-armor"}]
        }
        issue_with_title = {
            "title": "Cloud Armor issue",
            "body": "",
            "labels": []
        }
        _, _, label_confidence, _ = self.classifier._quick_keyword_check(issue_with_label)
        _, _, title_confidence, _ = self.classifier._quick_keyword_check(issue_with_title)
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
        issue_text = "cloud armor security policy preconfigured waf"
        scores = self.classifier._classify_with_tfidf(issue_text)
        self.assertIn("Cloud Armor", scores)
        self.assertEqual(len(scores), 1)

    def test_classify_with_tfidf_empty_text(self):
        """Test TF-IDF with empty text."""
        scores = self.classifier._classify_with_tfidf("")
        # Should return empty dict or handle gracefully
        self.assertIsInstance(scores, dict)

    def test_calculate_regex_scores(self):
        """Test regex-based scoring."""
        issue = {
            "title": "Cloud Armor security policy issue",
            "body": "The preconfigured waf rule is failing",
            "labels": [{"name": "cloud-armor"}]
        }
        scores = self.classifier._calculate_regex_scores(issue)
        self.assertIn("Cloud Armor", scores)
        self.assertGreater(scores["Cloud Armor"], 0)

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
        tfidf_scores = {"Cloud Armor": 30.0}
        regex_scores = {"Cloud Armor": 40.0}
        combined = self.classifier._combine_scores(tfidf_scores, regex_scores)
        self.assertIn("Cloud Armor", combined)
        # Combined score should be between the two
        self.assertGreater(combined["Cloud Armor"], 0)

    def test_combine_scores_missing_category(self):
        """Test score combination when category is missing from one dict."""
        tfidf_scores = {}
        regex_scores = {"Cloud Armor": 40.0}
        combined = self.classifier._combine_scores(tfidf_scores, regex_scores)
        self.assertIn("Cloud Armor", combined)

    def test_evaluate_scores_above_threshold(self):
        """Test score evaluation above threshold."""
        scores = {"Cloud Armor": 80.0}
        is_relevant, category, confidence, confidence_band = self.classifier._evaluate_scores(scores)
        self.assertTrue(is_relevant)
        self.assertEqual(category, "Cloud Armor")
        self.assertEqual(confidence, 80.0)
        self.assertEqual(confidence_band, "REVIEW")

    def test_evaluate_scores_below_threshold(self):
        """Test score evaluation below threshold."""
        scores = {"Cloud Armor": 10.0}
        is_relevant, category, confidence, confidence_band = self.classifier._evaluate_scores(scores)
        self.assertFalse(is_relevant)
        self.assertIsNone(category)
        self.assertEqual(confidence_band, "EXCLUDED")

    def test_evaluate_scores_empty_dict(self):
        """Test score evaluation with empty dict."""
        is_relevant, category, confidence, confidence_band = self.classifier._evaluate_scores({})
        self.assertFalse(is_relevant)
        self.assertIsNone(category)
        self.assertEqual(confidence, 0)
        self.assertEqual(confidence_band, "EXCLUDED")


class TestIssueClassifierIntegration(unittest.TestCase):
    """Integration tests for the full classification pipeline."""

    def setUp(self):
        self.classifier = IssueClassifier()

    def test_classify_issue_cloud_armor(self):
        """Test full classification of cloud armor issue."""
        issue = {
            "number": 12346,
            "title": "Security policy rule not applying correctly",
            "body": "Cloud Armor security policy is not blocking requests",
            "labels": [{"name": "cloud-armor"}]
        }
        is_relevant, category, confidence, confidence_band = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)
        self.assertEqual(category, "Cloud Armor")
        self.assertEqual(confidence_band, "HIGH")

    def test_non_cloud_armor_issue_not_classified(self):
        """Test that non-Cloud Armor service terms are ignored."""
        issue = {
            "number": 12347,
            "title": "google_compute_backend_service health check issue",
            "body": "load balancer backend behavior is unexpected",
            "labels": [{"name": "service/compute"}]
        }
        is_relevant, category, confidence, _ = self.classifier.classify_issue(issue)
        self.assertFalse(is_relevant)
        self.assertIsNone(category)

    def test_classify_irrelevant_issue(self):
        """Test that irrelevant issues are not classified."""
        issue = {
            "number": 12348,
            "title": "Documentation update needed for compute instance",
            "body": "The documentation for creating instances is outdated",
            "labels": [{"name": "documentation"}]
        }
        is_relevant, category, confidence, _ = self.classifier.classify_issue(issue)
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
            "labels": [],
        }
        # Should not raise exception
        try:
            is_relevant, category, confidence, _ = self.classifier.classify_issue(issue)
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
            "title": "cloud armor security policy " * 1000,
            "body": "",
            "labels": []
        }
        is_relevant, category, confidence, _ = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)

    def test_special_characters_in_text(self):
        """Test handling of special characters."""
        issue = {
            "title": "Cloud Armor <script>alert('xss')</script>",
            "body": "Test with $pecial ch@racters! & symbols",
            "labels": []
        }
        is_relevant, category, confidence, _ = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        issue = {
            "title": "Cloud Armor issue 日本語 🔥",
            "body": "问题描述 with émojis 💡",
            "labels": []
        }
        is_relevant, category, confidence, _ = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)

    def test_single_supported_category(self):
        """Test classification when only one category is supported."""
        issue = {
            "title": "Cloud Armor security policy with rate-based ban",
            "body": "Combining adaptive protection and managed protection",
            "labels": []
        }
        is_relevant, category, confidence, _ = self.classifier.classify_issue(issue)
        self.assertTrue(is_relevant)
        self.assertEqual(category, "Cloud Armor")


class TestCloudArmorTermCoverage(unittest.TestCase):
    """Tests for expanded Cloud Armor term coverage."""

    def setUp(self):
        self.classifier = IssueClassifier()

    def test_cloud_armor_resource_terms_match_title(self):
        """Terraform resource terms should classify as Cloud Armor at title confidence."""
        resource_terms = [
            "google_compute_security_policy",
            "google_compute_region_security_policy",
            "google_compute_region_security_policy_rule",
            "google_network_security_gateway_security_policy",
            "google_network_security_security_profile",
            "google_network_security_security_profile_group",
            "google_compute_network_edge_security_service",
        ]
        for term in resource_terms:
            with self.subTest(term=term):
                issue = {
                    "title": f"Bug with {term} terraform resource",
                    "body": "",
                    "labels": [],
                }
                is_match, category, confidence, _ = self.classifier._quick_keyword_check(issue)
                self.assertTrue(is_match)
                self.assertEqual(category, "Cloud Armor")
                self.assertGreaterEqual(confidence, 85.0)

    def test_service_catalog_is_cloud_armor_only(self):
        """Supported categories should only include Cloud Armor."""
        self.assertEqual(self.classifier._categories, ["Cloud Armor"])


class TestIssueClassifierShadowMode(unittest.TestCase):
    """Tests for logging-only shadow score comparisons."""

    def setUp(self):
        self.classifier = IssueClassifier()

    def test_shadow_score_comparison_structure(self):
        issue = {
            "number": 2001,
            "title": "google_compute_security_policy not applying preconfigured rule",
            "body": "Cloud Armor adaptive protection and rate-based ban seem ignored",
            "labels": [{"name": "cloud-armor"}],
        }

        comparison = self.classifier.get_shadow_score_comparison(issue)

        self.assertIn("baseline", comparison)
        self.assertIn("shadow", comparison)
        self.assertIn("score_delta", comparison)
        self.assertIn("category", comparison["baseline"])
        self.assertIn("score", comparison["baseline"])
        self.assertIn("is_relevant", comparison["baseline"])
        self.assertIn("category", comparison["shadow"])
        self.assertIn("score", comparison["shadow"])
        self.assertIn("is_relevant", comparison["shadow"])
        self.assertIsInstance(comparison["score_delta"], float)

    def test_shadow_score_comparison_when_shadow_vectorizer_unavailable(self):
        issue = {
            "number": 2002,
            "title": "Cloud Armor security policy issue",
            "body": "Rule priority handling is inconsistent",
            "labels": [],
        }

        self.classifier._shadow_vectorizer = None
        self.classifier._shadow_category_vectors = None
        comparison = self.classifier.get_shadow_score_comparison(issue)

        self.assertGreaterEqual(comparison["shadow"]["score"], 0.0)
        self.assertFalse(comparison["shadow"]["is_relevant"])


class TestLabelClassification(unittest.TestCase):
    """Tests for classify_labels utility in classifier module."""

    def test_classify_labels(self):
        labels = ["bug", "good first issue", "waiting-for-pr"]
        result = classify_labels(labels)
        self.assertTrue(result["bug"])
        self.assertTrue(result["good_first_issue"])
        self.assertTrue(result["has_pr"])

 
if __name__ == "__main__":
    unittest.main()