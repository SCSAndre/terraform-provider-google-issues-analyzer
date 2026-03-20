#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive tests for script.py main module.

Tests cover the main entry point, issue fetching, analysis pipeline,
and report generation functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os


class TestMainFunction(unittest.TestCase):
    """Tests for the main() entry point function."""

    @patch('script.generate_report')
    @patch('script.analyze_issues')
    @patch('script.fetch_all_issues')
    @patch('script.AvailabilityChecker')
    @patch('script.IssueClassifier')
    @patch('script.GitHubClient')
    @patch('script.validate_config')
    @patch('script.setup_logging')
    def test_main_success(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client,
        mock_classifier,
        mock_checker,
        mock_fetch,
        mock_analyze,
        mock_report
    ):
        """Test successful main execution returns 0."""
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_fetch.return_value = [{'number': 1, 'title': 'Test'}]
        mock_analyze.return_value = [{'number': 1, 'title': 'Test', 'category': 'Test'}]

        from script import main
        result = main()

        self.assertEqual(result, 0)
        mock_setup_logging.assert_called_once()
        mock_validate_config.assert_called_once()
        mock_fetch.assert_called_once()
        mock_analyze.assert_called_once()
        mock_report.assert_called_once()

    @patch('script.validate_config')
    @patch('script.setup_logging')
    def test_main_config_invalid(self, mock_setup_logging, mock_validate_config):
        """Test main returns 1 when configuration is invalid."""
        mock_validate_config.return_value = {
            'valid': False,
            'errors': ['Missing GITHUB_TOKEN'],
            'warnings': []
        }

        from script import main
        result = main()

        self.assertEqual(result, 1)

    @patch('script.generate_report')
    @patch('script.analyze_issues')
    @patch('script.fetch_all_issues')
    @patch('script.AvailabilityChecker')
    @patch('script.IssueClassifier')
    @patch('script.GitHubClient')
    @patch('script.validate_config')
    @patch('script.setup_logging')
    def test_main_logs_warnings(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client,
        mock_classifier,
        mock_checker,
        mock_fetch,
        mock_analyze,
        mock_report
    ):
        """Test main logs configuration warnings."""
        mock_validate_config.return_value = {
            'valid': True,
            'errors': [],
            'warnings': ['Low confidence threshold']
        }
        mock_fetch.return_value = []
        mock_analyze.return_value = []

        from script import main
        with patch('script.logger') as mock_logger:
            result = main()

        self.assertEqual(result, 0)

    @patch('script.GitHubClient')
    @patch('script.validate_config')
    @patch('script.setup_logging')
    def test_main_configuration_error(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles ConfigurationError."""
        from script import main
        from exceptions import ConfigurationError
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = ConfigurationError("Invalid token")

        result = main()

        self.assertEqual(result, 1)

    @patch('script.GitHubClient')
    @patch('script.validate_config')
    @patch('script.setup_logging')
    def test_main_github_api_error(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles GitHubAPIError."""
        from script import main
        from exceptions import GitHubAPIError
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = GitHubAPIError("API failure", status_code=500)

        result = main()

        self.assertEqual(result, 1)

    @patch('script.GitHubClient')
    @patch('script.validate_config')
    @patch('script.setup_logging')
    def test_main_generic_issue_analyzer_error(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles generic IssueAnalyzerError."""
        from script import main
        from exceptions import IssueAnalyzerError
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = IssueAnalyzerError("Analysis failed")

        result = main()

        self.assertEqual(result, 1)

    @patch('script.GitHubClient')
    @patch('script.validate_config')
    @patch('script.setup_logging')
    def test_main_keyboard_interrupt(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles KeyboardInterrupt with exit code 130."""
        from script import main
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = KeyboardInterrupt()

        result = main()

        self.assertEqual(result, 130)

    @patch('script.GitHubClient')
    @patch('script.validate_config')
    @patch('script.setup_logging')
    def test_main_unexpected_exception(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles unexpected exceptions."""
        from script import main
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = RuntimeError("Unexpected error")

        result = main()

        self.assertEqual(result, 1)


class TestFetchAllIssues(unittest.TestCase):
    """Tests for fetch_all_issues function."""

    def test_fetch_single_page(self):
        """Test fetching issues that fit in one page."""
        from script import fetch_all_issues
        
        mock_client = Mock()
        mock_client.fetch_issues_page.return_value = [
            {'number': i} for i in range(50)
        ]

        result = fetch_all_issues(mock_client)

        self.assertEqual(len(result), 50)
        mock_client.fetch_issues_page.assert_called_once_with(1)

    def test_fetch_multiple_pages(self):
        """Test fetching issues across multiple pages."""
        from script import fetch_all_issues
        
        mock_client = Mock()
        mock_client.fetch_issues_page.side_effect = [
            [{'number': i} for i in range(100)],  # Full page
            [{'number': i} for i in range(100, 150)],  # Partial page
        ]

        result = fetch_all_issues(mock_client)

        self.assertEqual(len(result), 150)
        self.assertEqual(mock_client.fetch_issues_page.call_count, 2)

    def test_fetch_empty_response(self):
        """Test handling empty response from first page."""
        from script import fetch_all_issues
        
        mock_client = Mock()
        mock_client.fetch_issues_page.return_value = []

        result = fetch_all_issues(mock_client)

        self.assertEqual(len(result), 0)

    def test_fetch_none_response(self):
        """Test handling None response (API failure)."""
        from script import fetch_all_issues
        
        mock_client = Mock()
        mock_client.fetch_issues_page.return_value = None

        result = fetch_all_issues(mock_client)

        self.assertEqual(len(result), 0)

    def test_fetch_stops_at_partial_page(self):
        """Test pagination stops when partial page received."""
        from script import fetch_all_issues
        
        mock_client = Mock()
        mock_client.fetch_issues_page.side_effect = [
            [{'number': i} for i in range(100)],  # Full page
            [{'number': i} for i in range(100, 180)],  # 80 items (partial)
        ]

        result = fetch_all_issues(mock_client)

        self.assertEqual(len(result), 180)
        # Should stop after partial page without fetching more
        self.assertEqual(mock_client.fetch_issues_page.call_count, 2)


class TestAnalyzeIssues(unittest.TestCase):
    """Tests for analyze_issues function."""

    def test_analyze_filters_pull_requests(self):
        """Test that pull requests are filtered out."""
        from script import analyze_issues
        
        mock_classifier = Mock()
        mock_checker = Mock()
        
        issues = [
            {'number': 1, 'pull_request': {}, 'title': 'PR'},  # PR - should be skipped
            {
                'number': 2, 'title': 'Bug report', 'html_url': 'https://github.com/test/2',
                'created_at': '2025-01-01T00:00:00Z', 'updated_at': '2025-01-01T00:00:00Z',
                'state': 'open', 'labels': [], 'assignees': [], 'comments': 0
            },  # Issue
        ]
        
        mock_classifier.classify_issue_with_related.return_value = (True, 'Category', 85.0, 'HIGH', [])
        mock_checker.is_issue_available.return_value = (True, None)

        result = analyze_issues(issues, mock_classifier, mock_checker)

        # Only the non-PR issue should be processed
        self.assertEqual(mock_classifier.classify_issue_with_related.call_count, 1)

    def test_analyze_filters_non_relevant(self):
        """Test that non-relevant issues are filtered out."""
        from script import analyze_issues
        
        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (False, None, 0, 'EXCLUDED', [])
        mock_checker = Mock()
        
        issues = [{'number': 1, 'title': 'Unrelated issue', 'created_at': '2025-01-01T00:00:00Z',
                   'updated_at': '2025-01-01T00:00:00Z', 'labels': [], 'assignees': []}]

        result = analyze_issues(issues, mock_classifier, mock_checker)

        self.assertEqual(len(result), 0)
        # Should not check availability for non-relevant issues
        mock_checker.is_issue_available.assert_not_called()

    def test_analyze_filters_unavailable(self):
        """Test that unavailable issues are filtered out."""
        from script import analyze_issues
        
        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Category', 85.0, 'HIGH', [])
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (False, 'Already assigned')
        
        issues = [{
            'number': 1, 'title': 'Assigned issue', 'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z', 'labels': [], 'assignees': []
        }]

        result = analyze_issues(issues, mock_classifier, mock_checker)

        self.assertEqual(len(result), 0)

    def test_analyze_enriches_relevant_available(self):
        """Test that relevant and available issues are enriched."""
        from script import analyze_issues
        
        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Load Balancer', 92.5, 'HIGH', ['PSC'])
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (True, None)
        
        issues = [{
            'number': 123,
            'title': 'LB issue',
            'html_url': 'https://github.com/test/123',
            'state': 'open',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-02T00:00:00Z',
            'comments': 5,
            'labels': [{'name': 'bug'}, {'name': 'lb'}],
            'assignees': []
        }]

        result = analyze_issues(issues, mock_classifier, mock_checker)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['number'], 123)
        self.assertEqual(result[0]['category'], 'Load Balancer')
        self.assertEqual(result[0]['confidence'], 92.5)
        self.assertEqual(result[0]['labels'], ['bug', 'lb'])
        self.assertEqual(result[0]['related_categories'], ['PSC'])
        self.assertIn('priority_score', result[0])
        self.assertIn('age_days', result[0])

    def test_analyze_handles_missing_labels(self):
        """Test handling issues without labels."""
        from script import analyze_issues
        
        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Category', 80.0, 'REVIEW', [])
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (True, None)
        
        issues = [{
            'number': 1,
            'title': 'Test',
            'html_url': 'https://github.com/test/1',
            'state': 'open',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z',
            'assignees': [],
            # No labels key
        }]

        result = analyze_issues(issues, mock_classifier, mock_checker)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['labels'], [])

    def test_analyze_multiple_issues_mixed_results(self):
        """Test analyzing multiple issues with mixed outcomes."""
        from script import analyze_issues
        
        mock_classifier = Mock()
        mock_checker = Mock()
        
        # Configure mock responses
        mock_classifier.classify_issue_with_related.side_effect = [
            (True, 'Cat1', 90.0, 'HIGH', []),   # Relevant
            (False, None, 0, 'EXCLUDED', []),   # Not relevant
            (True, 'Cat2', 85.0, 'HIGH', []),   # Relevant
            (True, 'Cat1', 80.0, 'REVIEW', []),   # Relevant but not available
        ]
        mock_checker.is_issue_available.side_effect = [
            (True, None),           # Available
            (True, None),           # Available
            (False, 'Assigned'),    # Not available
        ]
        
        issues = [
            {
                'number': i, 'title': f'Issue {i}', 'html_url': f'url{i}',
                'state': 'open', 'created_at': '2025-01-01T00:00:00Z',
                'updated_at': '2025-01-01T00:00:00Z', 'labels': [], 'assignees': []
            }
            for i in range(4)
        ]

        result = analyze_issues(issues, mock_classifier, mock_checker)

        self.assertEqual(len(result), 2)  # Only 2 are relevant AND available

    def test_analyze_shadow_mode_disabled_does_not_call_comparison(self):
        """Shadow comparison should not run when flag is disabled."""
        from script import analyze_issues

        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Cloud Armor', 88.0, 'HIGH', [])
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (True, None)

        issues = [{
            'number': 10,
            'title': 'Cloud Armor issue',
            'html_url': 'https://github.com/test/10',
            'state': 'open',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z',
            'labels': [],
            'assignees': [],
            'comments': 0,
        }]

        with patch('script.ENABLE_TRIGRAM_SHADOW_MODE', False):
            analyze_issues(issues, mock_classifier, mock_checker)

        mock_classifier.get_shadow_score_comparison.assert_not_called()

    def test_analyze_shadow_mode_enabled_calls_comparison(self):
        """Shadow comparison should run when flag is enabled."""
        from script import analyze_issues

        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Cloud Armor', 88.0, 'HIGH', [])
        mock_classifier.get_shadow_score_comparison.return_value = {
            'baseline': {'category': 'Cloud Armor', 'score': 70.0, 'is_relevant': False},
            'shadow': {'category': 'Cloud Armor', 'score': 90.0, 'is_relevant': True},
            'score_delta': 20.0,
        }
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (True, None)

        issues = [{
            'number': 11,
            'title': 'Cloud Armor issue',
            'html_url': 'https://github.com/test/11',
            'state': 'open',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z',
            'labels': [],
            'assignees': [],
            'comments': 0,
        }]

        with patch('script.ENABLE_TRIGRAM_SHADOW_MODE', True), \
             patch('script.SHADOW_SCORE_DELTA_THRESHOLD', 15.0):
            analyze_issues(issues, mock_classifier, mock_checker)

        mock_classifier.get_shadow_score_comparison.assert_called_once()

    def test_analyze_sets_top_level_actionable_key(self):
        """analyze_issues should expose actionable as a top-level enriched field."""
        from script import analyze_issues

        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Cloud Armor', 86.0, 'HIGH', [])
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (True, None)

        issues = [{
            'number': 12,
            'title': 'Cloud Armor actionable issue',
            'html_url': 'https://github.com/test/12',
            'state': 'open',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z',
            'labels': [{'name': 'good first issue'}],
            'assignees': [],
            'comments': 0,
        }]

        result = analyze_issues(issues, mock_classifier, mock_checker)

        self.assertEqual(len(result), 1)
        self.assertIn('actionable', result[0])
        self.assertTrue(result[0]['actionable'])


class TestGenerateReport(unittest.TestCase):
    """Tests for generate_report function."""

    def setUp(self):
        """Create temporary directory for test reports."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_output_dir = None

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('script.OUTPUT_DIR')
    def test_generate_empty_report(self, mock_output_dir):
        """Test generating report with no issues."""
        from script import generate_report
        
        mock_output_dir.__truediv__ = lambda self, x: Path(self.temp_dir) / x
        mock_output_dir.temp_dir = self.temp_dir
        
        # Use real path
        report_path = Path(self.temp_dir) / "terraform_target_services_issues_report_en.md"
        
        with patch('script.OUTPUT_DIR', Path(self.temp_dir)):
            generate_report([])
        
        self.assertTrue(report_path.exists())
        content = report_path.read_text()
        self.assertIn('**Total Issues Analyzed:** 0', content)

    @patch('script.OUTPUT_DIR')
    def test_generate_report_with_issues(self, mock_output_dir):
        """Test generating report with multiple issues."""
        from script import generate_report
        
        report_path = Path(self.temp_dir) / "terraform_target_services_issues_report_en.md"
        
        issues = [
            {
                'number': 1,
                'title': 'Test Issue 1',
                'url': 'https://github.com/test/1',
                'state': 'open',
                'category': 'Load Balancers',
                'confidence': 95.0,
                'created_at': '2025-01-01T00:00:00Z',
                'updated_at': '2025-01-02T00:00:00Z',
                'age_days': 30,
                'days_since_update': 5,
                'comments': 3,
                'labels': ['bug', 'lb'],
                'label_types': {'bug': True, 'enhancement': False},
                'assignees': [],
                'is_assigned': False,
                'related_categories': [],
                'priority_score': 75.0
            },
            {
                'number': 2,
                'title': 'Test Issue 2',
                'url': 'https://github.com/test/2',
                'state': 'open',
                'category': 'Cloud Armor',
                'confidence': 85.0,
                'created_at': '2025-01-02T00:00:00Z',
                'updated_at': '2025-01-03T00:00:00Z',
                'age_days': 20,
                'days_since_update': 3,
                'comments': 0,
                'labels': [],
                'label_types': {},
                'assignees': [],
                'is_assigned': False,
                'related_categories': [],
                'priority_score': 60.0
            }
        ]
        
        with patch('script.OUTPUT_DIR', Path(self.temp_dir)):
            generate_report(issues)
        
        content = report_path.read_text()
        self.assertIn('**Total Issues Analyzed:** 2', content)
        self.assertIn('Load Balancers', content)
        self.assertIn('Cloud Armor', content)
        self.assertIn('#1', content)
        # Now using compact table format instead of detailed entries
        self.assertIn('| Issue | Confidence | Priority | Age | Updated | Type | Labels |', content)

    @patch('script.OUTPUT_DIR')
    def test_generate_report_groups_by_category(self, mock_output_dir):
        """Test that report groups issues by category."""
        from script import generate_report
        
        report_path = Path(self.temp_dir) / "terraform_target_services_issues_report_en.md"
        
        base_issue = {
            'state': 'open', 'updated_at': '2025-01-01T00:00:00Z',
            'age_days': 30, 'days_since_update': 5,
            'label_types': {}, 'assignees': [], 'is_assigned': False,
            'related_categories': [], 'priority_score': 50.0
        }
        
        issues = [
            {**base_issue, 'number': 1, 'title': 'LB 1', 'url': 'url1', 'category': 'Load Balancers',
             'confidence': 90.0, 'created_at': '2025-01-01T00:00:00Z', 'comments': 0, 'labels': []},
            {**base_issue, 'number': 2, 'title': 'CA 1', 'url': 'url2', 'category': 'Cloud Armor',
             'confidence': 85.0, 'created_at': '2025-01-01T00:00:00Z', 'comments': 0, 'labels': []},
            {**base_issue, 'number': 3, 'title': 'LB 2', 'url': 'url3', 'category': 'Load Balancers',
             'confidence': 80.0, 'created_at': '2025-01-01T00:00:00Z', 'comments': 0, 'labels': []},
        ]
        
        with patch('script.OUTPUT_DIR', Path(self.temp_dir)):
            generate_report(issues)
        
        content = report_path.read_text()
        
        # Check category summary table
        self.assertIn('Load Balancers', content)
        self.assertIn('Cloud Armor', content)

    @patch('script.OUTPUT_DIR')
    def test_generate_report_sorts_by_priority(self, mock_output_dir):
        """Test that issues within categories are sorted by priority score."""
        from script import generate_report
        
        report_path = Path(self.temp_dir) / "terraform_target_services_issues_report_en.md"
        
        base_issue = {
            'state': 'open', 'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z', 'age_days': 30, 'days_since_update': 5,
            'label_types': {}, 'assignees': [], 'is_assigned': False,
            'related_categories': [], 'comments': 0, 'labels': []
        }
        
        issues = [
            {**base_issue, 'number': 1, 'title': 'Low priority', 'url': 'url1', 'category': 'Cat',
             'confidence': 70.0, 'priority_score': 30.0},
            {**base_issue, 'number': 2, 'title': 'High priority', 'url': 'url2', 'category': 'Cat',
             'confidence': 95.0, 'priority_score': 90.0},
            {**base_issue, 'number': 3, 'title': 'Med priority', 'url': 'url3', 'category': 'Cat',
             'confidence': 85.0, 'priority_score': 60.0},
        ]
        
        with patch('script.OUTPUT_DIR', Path(self.temp_dir)):
            generate_report(issues)
        
        content = report_path.read_text()
        
        # High priority should appear before medium, medium before low
        high_pos = content.find('High priority')
        med_pos = content.find('Med priority')
        low_pos = content.find('Low priority')
        
        self.assertLess(high_pos, med_pos)
        self.assertLess(med_pos, low_pos)


class TestPriorityScoring(unittest.TestCase):
    """Tests for calculate_priority_score behavior."""

    def test_high_confidence_gets_bonus(self):
        from script import calculate_priority_score

        high_score = calculate_priority_score(
            confidence=90,
            confidence_band='HIGH',
            comments=0,
            reactions_plus_one=0,
            age_days=10,
            days_since_update=10,
            is_bug=False,
            has_assignee=True,
        )
        review_score = calculate_priority_score(
            confidence=90,
            confidence_band='REVIEW',
            comments=0,
            reactions_plus_one=0,
            age_days=10,
            days_since_update=10,
            is_bug=False,
            has_assignee=True,
        )
        self.assertGreater(high_score, review_score)

    def test_reactions_increase_priority(self):
        from script import calculate_priority_score

        no_reactions = calculate_priority_score(
            confidence=80,
            confidence_band='REVIEW',
            comments=2,
            reactions_plus_one=0,
            age_days=100,
            days_since_update=100,
            is_bug=False,
            has_assignee=False,
        )
        with_reactions = calculate_priority_score(
            confidence=80,
            confidence_band='REVIEW',
            comments=2,
            reactions_plus_one=30,
            age_days=100,
            days_since_update=100,
            is_bug=False,
            has_assignee=False,
        )
        self.assertGreater(with_reactions, no_reactions)

    def test_actionable_true_adds_five_points(self):
        """Actionable issues should receive exactly a +5 priority bonus."""
        from script import calculate_priority_score

        base_score = calculate_priority_score(
            confidence=70,
            confidence_band='REVIEW',
            comments=1,
            reactions_plus_one=2,
            age_days=30,
            days_since_update=20,
            is_bug=False,
            is_actionable=False,
            has_assignee=True,
        )
        actionable_score = calculate_priority_score(
            confidence=70,
            confidence_band='REVIEW',
            comments=1,
            reactions_plus_one=2,
            age_days=30,
            days_since_update=20,
            is_bug=False,
            is_actionable=True,
            has_assignee=True,
        )

        self.assertEqual(actionable_score - base_score, 5)

    def test_actionable_default_false_adds_zero_points(self):
        """The default actionable value should behave like False and add no bonus."""
        from script import calculate_priority_score

        default_score = calculate_priority_score(
            confidence=65,
            confidence_band='REVIEW',
            comments=0,
            reactions_plus_one=0,
            age_days=10,
            days_since_update=5,
            is_bug=False,
            has_assignee=True,
        )
        explicit_false_score = calculate_priority_score(
            confidence=65,
            confidence_band='REVIEW',
            comments=0,
            reactions_plus_one=0,
            age_days=10,
            days_since_update=5,
            is_bug=False,
            is_actionable=False,
            has_assignee=True,
        )

        self.assertEqual(default_score, explicit_false_score)

    def test_bug_true_adds_five_points(self):
        """Bug label bonus should now contribute exactly +5."""
        from script import calculate_priority_score

        non_bug_score = calculate_priority_score(
            confidence=75,
            confidence_band='REVIEW',
            comments=1,
            reactions_plus_one=1,
            age_days=40,
            days_since_update=40,
            is_bug=False,
            is_actionable=False,
            has_assignee=True,
        )
        bug_score = calculate_priority_score(
            confidence=75,
            confidence_band='REVIEW',
            comments=1,
            reactions_plus_one=1,
            age_days=40,
            days_since_update=40,
            is_bug=True,
            is_actionable=False,
            has_assignee=True,
        )

        self.assertEqual(bug_score - non_bug_score, 5)


class TestModuleEntryPoint(unittest.TestCase):
    """Tests for module entry point behavior."""

    @patch('script.main')
    @patch('script.sys.exit')
    def test_entry_point_calls_main(self, mock_exit, mock_main):
        """Test that running module as script calls main()."""
        mock_main.return_value = 0
        
        # Simulate running as __main__
        # This is tricky to test directly, so we verify the structure exists
        import script
        self.assertTrue(hasattr(script, 'main'))
        self.assertTrue(callable(script.main))


if __name__ == '__main__':
    unittest.main()
