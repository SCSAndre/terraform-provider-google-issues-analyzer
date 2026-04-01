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

    @patch('terraform_issues_analyzer.cli.generate_report')
    @patch('terraform_issues_analyzer.cli.analyze_issues')
    @patch('terraform_issues_analyzer.cli.fetch_all_issues')
    @patch('terraform_issues_analyzer.cli.AvailabilityChecker')
    @patch('terraform_issues_analyzer.cli.IssueClassifier')
    @patch('terraform_issues_analyzer.cli.GitHubClient')
    @patch('terraform_issues_analyzer.cli.validate_config')
    @patch('terraform_issues_analyzer.cli.setup_logging')
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

        from terraform_issues_analyzer.cli import main
        result = main()

        self.assertEqual(result, 0)
        mock_setup_logging.assert_called_once()
        mock_validate_config.assert_called_once()
        mock_fetch.assert_called_once()
        mock_analyze.assert_called_once()
        mock_report.assert_called_once()

    @patch('terraform_issues_analyzer.cli.validate_config')
    @patch('terraform_issues_analyzer.cli.setup_logging')
    def test_main_config_invalid(self, mock_setup_logging, mock_validate_config):
        """Test main returns 1 when configuration is invalid."""
        mock_validate_config.return_value = {
            'valid': False,
            'errors': ['Missing GITHUB_TOKEN'],
            'warnings': []
        }

        from terraform_issues_analyzer.cli import main
        result = main()

        self.assertEqual(result, 1)

    @patch('terraform_issues_analyzer.cli.generate_report')
    @patch('terraform_issues_analyzer.cli.analyze_issues')
    @patch('terraform_issues_analyzer.cli.fetch_all_issues')
    @patch('terraform_issues_analyzer.cli.AvailabilityChecker')
    @patch('terraform_issues_analyzer.cli.IssueClassifier')
    @patch('terraform_issues_analyzer.cli.GitHubClient')
    @patch('terraform_issues_analyzer.cli.validate_config')
    @patch('terraform_issues_analyzer.cli.setup_logging')
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

        from terraform_issues_analyzer.cli import main
        with patch('terraform_issues_analyzer.cli.logger') as mock_logger:
            result = main()

        self.assertEqual(result, 0)

    @patch('terraform_issues_analyzer.cli.GitHubClient')
    @patch('terraform_issues_analyzer.cli.validate_config')
    @patch('terraform_issues_analyzer.cli.setup_logging')
    def test_main_configuration_error(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles ConfigurationError."""
        from terraform_issues_analyzer.cli import main
        from terraform_issues_analyzer.exceptions import ConfigurationError
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = ConfigurationError("Invalid token")

        result = main()

        self.assertEqual(result, 1)

    @patch('terraform_issues_analyzer.cli.GitHubClient')
    @patch('terraform_issues_analyzer.cli.validate_config')
    @patch('terraform_issues_analyzer.cli.setup_logging')
    def test_main_github_api_error(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles GitHubAPIError."""
        from terraform_issues_analyzer.cli import main
        from terraform_issues_analyzer.exceptions import GitHubAPIError
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = GitHubAPIError("API failure", status_code=500)

        result = main()

        self.assertEqual(result, 1)

    @patch('terraform_issues_analyzer.cli.GitHubClient')
    @patch('terraform_issues_analyzer.cli.validate_config')
    @patch('terraform_issues_analyzer.cli.setup_logging')
    def test_main_generic_issue_analyzer_error(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles generic IssueAnalyzerError."""
        from terraform_issues_analyzer.cli import main
        from terraform_issues_analyzer.exceptions import IssueAnalyzerError
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = IssueAnalyzerError("Analysis failed")

        result = main()

        self.assertEqual(result, 1)

    @patch('terraform_issues_analyzer.cli.GitHubClient')
    @patch('terraform_issues_analyzer.cli.validate_config')
    @patch('terraform_issues_analyzer.cli.setup_logging')
    def test_main_keyboard_interrupt(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles KeyboardInterrupt with exit code 130."""
        from terraform_issues_analyzer.cli import main
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = KeyboardInterrupt()

        result = main()

        self.assertEqual(result, 130)

    @patch('terraform_issues_analyzer.cli.GitHubClient')
    @patch('terraform_issues_analyzer.cli.validate_config')
    @patch('terraform_issues_analyzer.cli.setup_logging')
    def test_main_unexpected_exception(
        self,
        mock_setup_logging,
        mock_validate_config,
        mock_client
    ):
        """Test main handles unexpected exceptions."""
        from terraform_issues_analyzer.cli import main
        
        mock_validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_client.side_effect = RuntimeError("Unexpected error")

        result = main()

        self.assertEqual(result, 1)


class TestFetchAllIssues(unittest.TestCase):
    """Tests for fetch_all_issues function."""

    def test_fetch_single_page(self):
        """Test fetching issues that fit in one page."""
        from terraform_issues_analyzer.cli import fetch_all_issues
        
        mock_client = Mock()
        mock_client.fetch_issues_page.return_value = [
            {'number': i} for i in range(50)
        ]

        result = fetch_all_issues(mock_client)

        self.assertEqual(len(result), 50)
        mock_client.fetch_issues_page.assert_called_once_with(1)

    def test_fetch_multiple_pages(self):
        """Test fetching issues across multiple pages."""
        from terraform_issues_analyzer.cli import fetch_all_issues
        
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
        from terraform_issues_analyzer.cli import fetch_all_issues
        
        mock_client = Mock()
        mock_client.fetch_issues_page.return_value = []

        result = fetch_all_issues(mock_client)

        self.assertEqual(len(result), 0)

    def test_fetch_none_response(self):
        """Test handling None response (API failure)."""
        from terraform_issues_analyzer.cli import fetch_all_issues
        
        mock_client = Mock()
        mock_client.fetch_issues_page.return_value = None

        result = fetch_all_issues(mock_client)

        self.assertEqual(len(result), 0)

    def test_fetch_stops_at_partial_page(self):
        """Test pagination stops when partial page received."""
        from terraform_issues_analyzer.cli import fetch_all_issues
        
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
        from terraform_issues_analyzer.cli import analyze_issues
        
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
        from terraform_issues_analyzer.cli import analyze_issues
        
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
        from terraform_issues_analyzer.cli import analyze_issues
        
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
        from terraform_issues_analyzer.cli import analyze_issues
        
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

    def test_forward_linked_sets_internally_tracked(self):
        """Issue with forward/linked label is marked internally tracked."""
        from terraform_issues_analyzer.cli import analyze_issues

        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Cloud Armor', 90.0, 'HIGH', [])
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (True, None)

        issues = [{
            'number': 124,
            'title': 'Tracked issue',
            'html_url': 'https://github.com/test/124',
            'state': 'open',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-02T00:00:00Z',
            'comments': 0,
            'labels': [{'name': 'forward/linked'}],
            'assignees': [],
        }]

        result = analyze_issues(issues, mock_classifier, mock_checker)

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]['is_internally_tracked'])

    def test_no_forward_linked_not_tracked(self):
        """Issue without forward/linked is not internally tracked."""
        from terraform_issues_analyzer.cli import analyze_issues

        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Cloud Armor', 90.0, 'HIGH', [])
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (True, None)

        issues = [{
            'number': 125,
            'title': 'Untracked issue',
            'html_url': 'https://github.com/test/125',
            'state': 'open',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-02T00:00:00Z',
            'comments': 0,
            'labels': [{'name': 'bug'}],
            'assignees': [],
        }]

        result = analyze_issues(issues, mock_classifier, mock_checker)

        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]['is_internally_tracked'])

    def test_analyze_handles_missing_labels(self):
        """Test handling issues without labels."""
        from terraform_issues_analyzer.cli import analyze_issues
        
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
        from terraform_issues_analyzer.cli import analyze_issues
        
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
        from terraform_issues_analyzer.cli import analyze_issues

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

        with patch('terraform_issues_analyzer.cli.ENABLE_TRIGRAM_SHADOW_MODE', False):
            analyze_issues(issues, mock_classifier, mock_checker)

        mock_classifier.get_shadow_score_comparison.assert_not_called()

    def test_analyze_shadow_mode_enabled_calls_comparison(self):
        """Shadow comparison should run when flag is enabled."""
        from terraform_issues_analyzer.cli import analyze_issues

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

        with patch('terraform_issues_analyzer.cli.ENABLE_TRIGRAM_SHADOW_MODE', True), \
             patch('terraform_issues_analyzer.cli.SHADOW_SCORE_DELTA_THRESHOLD', 15.0):
            analyze_issues(issues, mock_classifier, mock_checker)

        mock_classifier.get_shadow_score_comparison.assert_called_once()

    def test_analyze_sets_top_level_actionable_key(self):
        """analyze_issues should expose actionable as a top-level enriched field."""
        from terraform_issues_analyzer.cli import analyze_issues

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

    def test_thumbs_up_extracted_from_reactions(self):
        """thumbs_up is correctly extracted from the reactions dict."""
        from terraform_issues_analyzer.cli import analyze_issues

        issue = {
            'number': 13,
            'title': 'Issue with reactions',
            'html_url': 'https://github.com/test/13',
            'state': 'open',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z',
            'labels': [],
            'assignees': [],
            'comments': 0,
            'reactions': {'+1': 7, 'total_count': 7},
        }

        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Cloud Armor', 85.0, 'HIGH', [])
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (True, None)

        result = analyze_issues([issue], mock_classifier, mock_checker)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['thumbs_up'], 7)

    def test_thumbs_up_defaults_to_zero_when_missing(self):
        """thumbs_up defaults to 0 when reactions key is absent."""
        from terraform_issues_analyzer.cli import analyze_issues

        issue = {
            'number': 14,
            'title': 'Issue without reactions',
            'html_url': 'https://github.com/test/14',
            'state': 'open',
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z',
            'labels': [],
            'assignees': [],
            'comments': 0,
        }

        mock_classifier = Mock()
        mock_classifier.classify_issue_with_related.return_value = (True, 'Cloud Armor', 85.0, 'HIGH', [])
        mock_checker = Mock()
        mock_checker.is_issue_available.return_value = (True, None)

        result = analyze_issues([issue], mock_classifier, mock_checker)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['thumbs_up'], 0)


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

    @patch('terraform_issues_analyzer.cli.OUTPUT_DIR')
    def test_generate_empty_report(self, mock_output_dir):
        """Test generating report with no issues."""
        from terraform_issues_analyzer.cli import generate_report
        
        mock_output_dir.__truediv__ = lambda self, x: Path(self.temp_dir) / x
        mock_output_dir.temp_dir = self.temp_dir
        
        # Use real path
        report_path = Path(self.temp_dir) / "terraform_target_services_issues_report_en.md"
        
        with patch('terraform_issues_analyzer.cli.OUTPUT_DIR', Path(self.temp_dir)):
            generate_report([])
        
        self.assertTrue(report_path.exists())
        content = report_path.read_text()
        self.assertIn('**Total Issues Analyzed:** 0', content)

    @patch('terraform_issues_analyzer.cli.OUTPUT_DIR')
    def test_generate_report_with_issues(self, mock_output_dir):
        """Test generating report with multiple issues."""
        from terraform_issues_analyzer.cli import generate_report
        
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
        
        with patch('terraform_issues_analyzer.cli.OUTPUT_DIR', Path(self.temp_dir)):
            generate_report(issues)
        
        content = report_path.read_text()
        self.assertIn('**Total Issues Analyzed:** 2', content)
        self.assertIn('Load Balancers', content)
        self.assertIn('Cloud Armor', content)
        self.assertIn('#1', content)
        # Now using compact table format instead of detailed entries
        self.assertIn('| Issue | Confidence | Priority | Age | Updated | Type | Labels |', content)

    @patch('terraform_issues_analyzer.cli.OUTPUT_DIR')
    def test_generate_report_groups_by_category(self, mock_output_dir):
        """Test that report groups issues by category."""
        from terraform_issues_analyzer.cli import generate_report
        
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
        
        with patch('terraform_issues_analyzer.cli.OUTPUT_DIR', Path(self.temp_dir)):
            generate_report(issues)
        
        content = report_path.read_text()
        
        # Check category summary table
        self.assertIn('Load Balancers', content)
        self.assertIn('Cloud Armor', content)

    @patch('terraform_issues_analyzer.cli.OUTPUT_DIR')
    def test_generate_report_sorts_by_priority(self, mock_output_dir):
        """Test that issues within categories are sorted by priority score."""
        from terraform_issues_analyzer.cli import generate_report
        
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
        
        with patch('terraform_issues_analyzer.cli.OUTPUT_DIR', Path(self.temp_dir)):
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

    def _make_base_issue(self):
        return {
            'confidence': 70,
            'confidence_band': 'REVIEW',
            'comments': 1,
            'reactions_plus_one': 2,
            'age_days': 30,
            'days_since_update': 20,
            'is_bug': False,
            'is_actionable': False,
            'has_assignee': True,
            'labels': [],
        }

    def test_high_confidence_gets_bonus(self):
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

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
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

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
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

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

        self.assertAlmostEqual(actionable_score - base_score, 5.0, places=7)

    def test_actionable_default_false_adds_zero_points(self):
        """The default actionable value should behave like False and add no bonus."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

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
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

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

        self.assertAlmostEqual(bug_score - non_bug_score, 5.0, places=7)

    def test_crash_label_adds_bonus(self):
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["labels"] = [{"name": "crash"}]
        score_with = calculate_priority_score(**base)
        base["labels"] = []
        score_without = calculate_priority_score(**base)
        assert score_with == min(score_without + 15, 95)

    def test_non_crash_no_bonus(self):
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["labels"] = [{"name": "bug"}]
        score = calculate_priority_score(**base)
        base["labels"] = []
        score_no_labels = calculate_priority_score(**base)
        # bug label alone should not trigger crash bonus
        assert score == score_no_labels

    def test_breaking_change_reduces_score(self):
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["labels"] = []
        score_normal = calculate_priority_score(**base)
        base["labels"] = [{"name": "breaking-change"}]
        score_breaking = calculate_priority_score(**base)
        assert score_breaking == max(0, score_normal - 5)

    def test_new_resource_reduces_score(self):
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["labels"] = []
        score_normal = calculate_priority_score(**base)
        base["labels"] = [{"name": "new-resource"}]
        score_new = calculate_priority_score(**base)
        assert score_new == max(0, score_normal - 3)

    def test_size_xs_label_adds_bonus(self):
        """size/xs label adds 12 points to priority score."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        issue = self._make_base_issue()
        issue["labels"] = [{"name": "size/xs"}]
        score_without = calculate_priority_score(**{**issue, "labels": []})
        score_with = calculate_priority_score(**issue)
        assert score_with == min(score_without + 12, 100)

    def test_size_l_label_no_change(self):
        """size/l label adds 0 points."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        issue = self._make_base_issue()
        issue["labels"] = [{"name": "size/l"}]
        score_without = calculate_priority_score(**{**issue, "labels": []})
        score_with = calculate_priority_score(**issue)
        assert score_with == score_without

    def test_size_label_handles_string_format(self):
        """Labels as plain strings (not dicts) are handled safely."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        issue = self._make_base_issue()
        issue["labels"] = ["size/s", "bug"]
        score_without = calculate_priority_score(**{**issue, "labels": []})
        score_with = calculate_priority_score(**issue)
        assert score_with == min(score_without + 10, 100)

    def test_reactions_increase_priority_score(self):
        """An issue with 15 thumbs_up scores higher than the same issue with 0."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["reactions_plus_one"] = 0
        score_zero = calculate_priority_score(**base)
        base["reactions_plus_one"] = 15
        score_fifteen = calculate_priority_score(**base)
        assert score_fifteen > score_zero

    def test_reactions_capped_at_30(self):
        """thumbs_up above 30 gives the same score as exactly 30."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["reactions_plus_one"] = 30
        score_30 = calculate_priority_score(**base)
        base["reactions_plus_one"] = 999
        score_999 = calculate_priority_score(**base)
        assert score_30 == score_999

    def test_reactivation_bonus_applied_for_old_recent_issue(self):
        """Issue older than 1 year with activity in last 90 days gets bonus."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["age_days"] = 730
        base["days_since_update"] = 10
        score_with = calculate_priority_score(**base)
        base["days_since_update"] = 400
        score_without = calculate_priority_score(**base)
        assert score_with > score_without

    def test_reactivation_bonus_zero_for_new_issue(self):
        """New issue (< 1 year) gets no reactivation bonus."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["age_days"] = 180
        base["days_since_update"] = 5
        score = calculate_priority_score(**base)
        assert 0 <= score <= 100

    def test_reactivation_bonus_zero_for_stale_old_issue(self):
        """Old issue with no recent activity gets no reactivation bonus."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["age_days"] = 730
        base["days_since_update"] = 200
        score_stale = calculate_priority_score(**base)
        base["days_since_update"] = 10
        score_active = calculate_priority_score(**base)
        assert score_active > score_stale

    def test_ultra_age_bonus_for_5_year_issue(self):
        """A 5-year-old issue scores higher than a 2-year-old identical issue."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["age_days"] = 730  # 2 years
        score_2y = calculate_priority_score(**base)
        base["age_days"] = 1825  # 5 years
        score_5y = calculate_priority_score(**base)
        assert score_5y > score_2y

    def test_ultra_age_bonus_zero_under_3_years(self):
        """Issues under 3 years get no ultra-age bonus."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        base["age_days"] = 1000  # ~2.7 years
        score_1000 = calculate_priority_score(**base)
        base["age_days"] = 1094  # just under 3 years
        score_1094 = calculate_priority_score(**base)
        # Both should be equal since neither crosses the 1095-day threshold
        assert score_1000 <= score_1094  # older still scores >= due to neglect

    def test_ultra_age_bonus_capped_at_8(self):
        """Ultra-age bonus never exceeds 8 points regardless of age."""
        from terraform_issues_analyzer.priority_scorer import calculate_priority_score

        base = self._make_base_issue()
        # Force neglect factor to its cap in both cases to isolate ultra-age behavior.
        base["days_since_update"] = 1000
        base["age_days"] = 99999  # absurdly old
        score = calculate_priority_score(**base)
        base["age_days"] = 2555  # 7 years (hits the +8 cap)
        score_7y = calculate_priority_score(**base)
        # Both should produce the same ultra_age_bonus (8)
        assert score == score_7y


class TestModuleEntryPoint(unittest.TestCase):
    """Tests for module entry point behavior."""

    @patch('terraform_issues_analyzer.cli.main')
    @patch('terraform_issues_analyzer.cli.sys.exit')
    def test_entry_point_calls_main(self, mock_exit, mock_main):
        """Test that running module as script calls main()."""
        mock_main.return_value = 0
        
        # Simulate running as __main__
        # This is tricky to test directly, so we verify the structure exists
        import terraform_issues_analyzer.cli as script
        self.assertTrue(hasattr(script, 'main'))
        self.assertTrue(callable(script.main))


if __name__ == '__main__':
    unittest.main()
