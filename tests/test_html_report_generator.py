"""Tests for HTML Report Generator."""

import unittest
import tempfile
from pathlib import Path

from terraform_issues_analyzer.html_report_generator import (
    format_age,
    calculate_statistics,
    generate_html_report,
    generate_charts_html,
    get_confidence_badge,
    generate_executive_summary_html,
    generate_quick_wins_html,
    generate_attention_needed_html,
    generate_top_issues_html,
    generate_category_sections_html,
)


def make_base_issue() -> dict:
    """Return a minimal issue payload for badge rendering tests."""
    return {
        'number': 901,
        'title': 'Blocking label test issue',
        'url': 'https://github.com/test/901',
        'category': 'Cloud Armor',
        'confidence': 88.0,
        'confidence_band': 'HIGH',
        'label_types': {'bug': True},
        'is_assigned': False,
        'age_days': 120,
        'days_since_update': 20,
        'comments': 1,
        'priority_score': 70.0,
        'labels': ['bug'],
        'created_at': '2025-01-01T00:00:00Z',
        'updated_at': '2025-10-01T00:00:00Z',
        'assignees': [],
        'related_categories': [],
        'is_exempt': False,
        'is_upstream': False,
        'is_blocked': False,
        'is_crash': False,
        'is_breaking_change': False,
        'is_new_resource': False,
        'is_internally_tracked': False,
    }


def make_entry_point_issue() -> dict:
    """Return a HIGH-confidence issue that qualifies for entry points."""
    issue = make_base_issue()
    issue['number'] = 902
    issue['title'] = 'Contributor-friendly docs update for Cloud Armor'
    issue['labels'] = ['size/s', 'documentation']
    issue['label_types'] = {
        'bug': False,
        'documentation': True,
        'has_pr': False,
        'breaking_change': False,
    }
    issue['confidence_band'] = 'HIGH'
    issue['is_blocked'] = False
    issue['is_internally_tracked'] = False
    issue['priority_score'] = 72.0
    return issue


def _parse_entry_points_section(html: str) -> str:
    """Extract contributor entry points section content for targeted assertions."""
    section_start = html.find("Contributor Entry Points")
    if section_start == -1:
        return ""
    section_end = html.find("Quick Wins", section_start)
    if section_end == -1:
        section_end = len(html)
    return html[section_start:section_end]


def test_exempt_badge_rendered():
    issue = make_base_issue()
    issue["is_exempt"] = True
    issue["is_upstream"] = False
    issue["is_blocked"] = True

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "badge-exempt" in html
    assert "🚫" in html


def test_upstream_badge_rendered():
    issue = make_base_issue()
    issue["is_exempt"] = False
    issue["is_upstream"] = True
    issue["is_blocked"] = True

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "badge-upstream" in html
    assert "⛔" in html


def test_crash_badge_rendered():
    issue = make_base_issue()
    issue["is_crash"] = True

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "badge-crash" in html
    assert "🔴 Crash" in html


def test_breaking_change_badge_rendered():
    issue = make_base_issue()
    issue["is_breaking_change"] = True
    issue["is_new_resource"] = False

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "badge-breaking" in html
    assert "💥 Breaking" in html


def test_new_resource_badge_rendered():
    issue = make_base_issue()
    issue["is_breaking_change"] = False
    issue["is_new_resource"] = True

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "badge-new-resource" in html
    assert "🆕 New Resource" in html


def test_tracked_badge_rendered():
    issue = make_base_issue()
    issue["is_internally_tracked"] = True

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "badge-tracked" in html
    assert "🔖" in html


def test_executive_summary_has_tracked_card():
    issue = make_base_issue()

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "Tracked" in html
    assert "Orphaned" in html


def test_has_pr_card_present():
    issue = make_base_issue()
    issue["label_types"] = {"has_pr": True}

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "Has PR" in html


def test_active_card_present():
    issue = make_base_issue()
    issue["days_since_update"] = 3

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "Active" in html


def test_trend_chart_rendered_with_history():
    history = [
        {"date": "2026-03-17", "total": 33, "high_confidence": 26, "review": 7},
        {"date": "2026-03-23", "total": 31, "high_confidence": 25, "review": 6},
    ]
    html = generate_html_report([make_base_issue()], history=history)

    assert "trendChart" in html
    assert "2026-03-17" in html
    assert "HIGH Confidence" in html


def test_trend_placeholder_with_single_entry():
    history = [{"date": "2026-03-23", "total": 31, "high_confidence": 25, "review": 6}]
    html = generate_html_report([make_base_issue()], history=history)

    assert "trend-placeholder" in html
    assert '<canvas id="trendChart">' not in html


def test_trend_placeholder_with_no_history():
    html = generate_html_report([make_base_issue()], history=[])

    assert "trend-placeholder" in html


def test_entry_points_section_present():
    issue = make_entry_point_issue()

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "Contributor Entry Points" in html


def test_blocked_issue_excluded_from_entry_points():
    issue = make_entry_point_issue()
    issue["is_blocked"] = True

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "No entry-point issues" in html or issue["title"] not in _parse_entry_points_section(html)


def test_breaking_change_excluded_from_entry_points():
    issue = make_entry_point_issue()
    issue["labels"] = ["breaking-change", "size/s"]

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = generate_html_report([issue], Path(temp_dir))
        html = output_path.read_text()

    assert "No entry-point issues" in html or issue["title"] not in _parse_entry_points_section(html)


class TestFormatAge(unittest.TestCase):
    """Test the format_age helper function."""
    
    def test_format_days(self):
        """Test formatting for days."""
        self.assertEqual(format_age(0), "0d")
        self.assertEqual(format_age(15), "15d")
        self.assertEqual(format_age(29), "29d")
    
    def test_format_months(self):
        """Test formatting for months."""
        self.assertEqual(format_age(30), "1.0mo")
        self.assertEqual(format_age(60), "2.0mo")
        self.assertEqual(format_age(180), "6.0mo")
    
    def test_format_years(self):
        """Test formatting for years."""
        self.assertEqual(format_age(365), "1.0y")
        self.assertEqual(format_age(730), "2.0y")
        self.assertEqual(format_age(547), "1.5y")


class TestCalculateStatistics(unittest.TestCase):
    """Test statistics calculation."""
    
    def test_empty_issues(self):
        """Test with no issues."""
        stats = calculate_statistics([])
        self.assertEqual(stats['total'], 0)
        self.assertEqual(stats['bugs'], 0)
        self.assertEqual(stats['enhancements'], 0)
    
    def test_basic_statistics(self):
        """Test basic statistics calculation."""
        issues = [
            {
                'category': 'Load Balancers',
                'label_types': {'bug': True},
                'is_assigned': False,
                'age_days': 100,
                'days_since_update': 50,
                'comments': 3
            },
            {
                'category': 'Cloud Armor',
                'label_types': {'enhancement': True},
                'is_assigned': True,
                'age_days': 200,
                'days_since_update': 200,
                'comments': 5
            }
        ]
        
        stats = calculate_statistics(issues)
        
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['bugs'], 1)
        self.assertEqual(stats['enhancements'], 1)
        self.assertEqual(stats['assigned'], 1)
        self.assertEqual(stats['avg_age'], 150)
        self.assertEqual(stats['avg_comments'], 4)
        self.assertEqual(stats['active'], 0)  # neither issue has days_since_update < 30
        self.assertEqual(stats['stale'], 1)
    
    def test_age_distribution(self):
        """Test age distribution buckets."""
        issues = [
            {'category': 'A', 'label_types': {}, 'is_assigned': False, 'age_days': 15, 'days_since_update': 5, 'comments': 0},
            {'category': 'A', 'label_types': {}, 'is_assigned': False, 'age_days': 60, 'days_since_update': 5, 'comments': 0},
            {'category': 'A', 'label_types': {}, 'is_assigned': False, 'age_days': 120, 'days_since_update': 5, 'comments': 0},
            {'category': 'A', 'label_types': {}, 'is_assigned': False, 'age_days': 250, 'days_since_update': 5, 'comments': 0},
            {'category': 'A', 'label_types': {}, 'is_assigned': False, 'age_days': 500, 'days_since_update': 5, 'comments': 0},
            {'category': 'A', 'label_types': {}, 'is_assigned': False, 'age_days': 800, 'days_since_update': 5, 'comments': 0},
        ]
        
        stats = calculate_statistics(issues)
        
        # Age distribution: [<30d, 1-3mo, 3-6mo, 6-12mo, 1-2y, >2y]
        self.assertEqual(stats['age_distribution'], [1, 1, 1, 1, 1, 1])
    
    def test_category_breakdown(self):
        """Test category breakdown."""
        issues = [
            {'category': 'Load Balancers', 'label_types': {'bug': True}, 'is_assigned': False, 'age_days': 100, 'days_since_update': 200, 'comments': 0},
            {'category': 'Load Balancers', 'label_types': {'enhancement': True}, 'is_assigned': False, 'age_days': 100, 'days_since_update': 100, 'comments': 0},
            {'category': 'Cloud Armor', 'label_types': {'bug': True}, 'is_assigned': False, 'age_days': 100, 'days_since_update': 50, 'comments': 0},
        ]
        
        stats = calculate_statistics(issues)
        
        self.assertEqual(len(stats['categories']), 2)
        self.assertEqual(stats['categories']['Load Balancers']['total'], 2)
        self.assertEqual(stats['categories']['Load Balancers']['bugs'], 1)
        self.assertEqual(stats['categories']['Load Balancers']['enhancements'], 1)
        self.assertEqual(stats['categories']['Load Balancers']['stale'], 1)
        self.assertEqual(stats['categories']['Cloud Armor']['total'], 1)


class TestGenerateHtmlReport(unittest.TestCase):
    """Test HTML report generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.sample_issues = [
            {
                'number': 123,
                'title': 'Test Issue',
                'url': 'https://github.com/test/123',
                'category': 'Load Balancers',
                'confidence': 85.0,
                'label_types': {'bug': True},
                'is_assigned': False,
                'age_days': 100,
                'days_since_update': 50,
                'comments': 3,
                'priority_score': 75.0,
                'labels': ['bug'],
                'created_at': '2025-01-01T00:00:00Z',
                'updated_at': '2025-10-01T00:00:00Z',
                'assignees': [],
                'related_categories': []
            }
        ]
    
    def test_generates_html_file(self):
        """Test that HTML file is created."""
        output_path = generate_html_report(self.sample_issues, Path(self.temp_dir))
        
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.suffix, '.html')
    
    def test_html_contains_basic_structure(self):
        """Test HTML contains required elements."""
        output_path = generate_html_report(self.sample_issues, Path(self.temp_dir))
        
        content = output_path.read_text()
        
        self.assertIn('<!DOCTYPE html>', content)
        self.assertIn('<html', content)
        self.assertIn('</html>', content)
        self.assertIn('Terraform Provider Google', content)
        self.assertIn('chart.js', content)  # lowercase in CDN URL
    
    def test_html_contains_issue_data(self):
        """Test HTML contains issue information."""
        output_path = generate_html_report(self.sample_issues, Path(self.temp_dir))
        
        content = output_path.read_text()
        
        self.assertIn('#123', content)
        self.assertIn('Test Issue', content)
        self.assertIn('Load Balancers', content)

    def test_html_contains_confidence_and_trend_elements(self):
        """Test confidence badges and trend section are rendered."""
        output_path = generate_html_report(self.sample_issues, Path(self.temp_dir))
        content = output_path.read_text()

        self.assertIn('Confidence', content)
        self.assertIn('Backlog Trend', content)
        self.assertIn('trend-placeholder', content)


class TestHtmlHelpers(unittest.TestCase):
    """Test helper rendering methods."""

    def test_confidence_badge_styles(self):
        self.assertIn('badge-confidence-high', get_confidence_badge(90.0))
        self.assertIn('badge-confidence-review', get_confidence_badge(80.0))

    def test_chart_noscript_fallbacks(self):
        stats = {
            'age_distribution': [1, 2, 3, 4, 5, 6],
            'categories': {'Cloud Armor': {'bugs': 1, 'enhancements': 2}},
            'history': [{'date': '2026-03-17', 'total': 3, 'high_confidence': 1, 'review': 2}],
        }
        html = generate_charts_html(stats)
        self.assertIn('<noscript>', html)
        self.assertIn('Category', html)


class TestHtmlSections(unittest.TestCase):
    """Test individual HTML section generators."""
    
    def test_executive_summary_html(self):
        """Test executive summary generation."""
        stats = {
            'total': 100,
            'bugs': 40,
            'enhancements': 30,
            'assigned': 10,
            'avg_age': 200,
            'avg_comments': 2.5,
            'active': 15,
            'stale': 50,
            'has_pr': 8
        }
        
        html = generate_executive_summary_html(stats)
        
        self.assertIn('Executive Summary', html)
        self.assertIn('100', html)  # total
        self.assertIn('40', html)   # bugs
        self.assertIn('Bugs', html)
    
    def test_quick_wins_empty(self):
        """Test quick wins with no issues."""
        html = generate_quick_wins_html([])
        self.assertEqual(html, '')
    
    def test_quick_wins_with_issues(self):
        """Test quick wins with issues."""
        issues = [
            {
                'number': 1,
                'title': 'Quick Win Issue',
                'url': 'https://github.com/test/1',
                'category': 'Test',
                'label_types': {'has_pr': True, 'bug': True},
                'age_days': 30,
                'priority_score': 50
            }
        ]
        
        html = generate_quick_wins_html(issues)
        
        self.assertIn('Quick Wins', html)
        self.assertIn('#1', html)
        self.assertIn('Quick Win Issue', html)
    
    def test_attention_needed_empty(self):
        """Test attention needed with no issues."""
        html = generate_attention_needed_html([])
        self.assertEqual(html, '')
    
    def test_attention_needed_with_issues(self):
        """Test attention needed with issues."""
        issues = [
            {
                'number': 2,
                'title': 'Needs Attention',
                'url': 'https://github.com/test/2',
                'category': 'Test',
                'label_types': {'enhancement': True},
                'days_since_update': 200,
                'comments': 5
            }
        ]
        
        html = generate_attention_needed_html(issues)
        
        self.assertIn('Attention Needed', html)
        self.assertIn('#2', html)
    
    def test_top_issues_html(self):
        """Test top issues generation."""
        issues = [
            {
                'number': 3,
                'title': 'Top Priority Issue',
                'url': 'https://github.com/test/3',
                'category': 'Category A',
                'label_types': {'bug': True, 'has_pr': True},
                'age_days': 100,
                'days_since_update': 200,
                'priority_score': 85
            }
        ]
        
        html = generate_top_issues_html(issues)
        
        self.assertIn('Top 10 Priority', html)
        self.assertIn('#3', html)
        self.assertIn('Category A', html)
    
    def test_category_sections_html(self):
        """Test category sections generation."""
        by_category = {
            'Load Balancers': [
                {
                    'number': 4,
                    'title': 'LB Issue',
                    'url': 'https://github.com/test/4',
                    'category': 'Load Balancers',
                    'label_types': {'bug': True},
                    'age_days': 50,
                    'days_since_update': 10,
                    'priority_score': 60
                }
            ]
        }
        
        html = generate_category_sections_html(by_category)
        
        self.assertIn('Load Balancers', html)
        self.assertIn('#4', html)
        self.assertIn('details', html)


class TestHtmlEmpty(unittest.TestCase):
    """Test HTML generation with empty data."""
    
    def test_empty_report(self):
        """Test generation with no issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_html_report([], Path(temp_dir))
            
            self.assertTrue(output_path.exists())
            content = output_path.read_text()
            self.assertIn('Total Issues', content)
            self.assertIn('0', content)


class TestHtmlConfidenceToggle(unittest.TestCase):
    """Test confidence-band toggle markup and row attributes."""

    def test_toggle_button_present_in_html(self):
        """The generated HTML contains the toggle button."""
        by_category = {
            'Cloud Armor': [
                {
                    'number': 101,
                    'title': 'High confidence issue',
                    'url': 'https://github.com/test/101',
                    'confidence': 90.0,
                    'confidence_band': 'HIGH',
                    'label_types': {},
                    'age_days': 10,
                    'days_since_update': 3,
                    'priority_score': 80,
                },
                {
                    'number': 102,
                    'title': 'Review confidence issue',
                    'url': 'https://github.com/test/102',
                    'confidence': 75.0,
                    'confidence_band': 'REVIEW',
                    'label_types': {},
                    'age_days': 20,
                    'days_since_update': 5,
                    'priority_score': 60,
                },
            ]
        }

        html = generate_category_sections_html(by_category)

        self.assertIn('data-band="HIGH"', html)
        self.assertIn('data-band="REVIEW"', html)
        self.assertIn('Showing all issues', html)

    def test_review_rows_have_data_band_attribute(self):
        """Every REVIEW confidence issue row has data-band='REVIEW'."""
        by_category = {
            'Cloud Armor': [
                {
                    'number': 201,
                    'title': 'High confidence issue one',
                    'url': 'https://github.com/test/201',
                    'confidence': 92.0,
                    'confidence_band': 'HIGH',
                    'label_types': {},
                    'age_days': 10,
                    'days_since_update': 2,
                    'priority_score': 90,
                },
                {
                    'number': 202,
                    'title': 'High confidence issue two',
                    'url': 'https://github.com/test/202',
                    'confidence': 88.0,
                    'confidence_band': 'HIGH',
                    'label_types': {},
                    'age_days': 15,
                    'days_since_update': 4,
                    'priority_score': 70,
                },
                {
                    'number': 203,
                    'title': 'Review confidence issue',
                    'url': 'https://github.com/test/203',
                    'confidence': 76.0,
                    'confidence_band': 'REVIEW',
                    'label_types': {},
                    'age_days': 25,
                    'days_since_update': 8,
                    'priority_score': 55,
                },
            ]
        }

        html = generate_category_sections_html(by_category)

        self.assertEqual(html.count('data-band="REVIEW"'), 1)
        self.assertEqual(html.count('data-band="HIGH"'), 2)


class TestHtmlRecaptchaBadge(unittest.TestCase):
    """Tests for reCAPTCHA subcategory visuals."""

    def _make_base_issue(self):
        return {
            'number': 301,
            'title': 'Base issue title',
            'url': 'https://github.com/test/301',
            'category': 'Cloud Armor',
            'confidence': 90.0,
            'confidence_band': 'HIGH',
            'label_types': {'bug': True},
            'is_assigned': False,
            'age_days': 100,
            'days_since_update': 10,
            'comments': 2,
            'priority_score': 72.0,
            'labels': ['bug'],
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-10-01T00:00:00Z',
            'assignees': [],
            'related_categories': [],
        }

    def test_recaptcha_badge_present_for_recaptcha_issue(self):
        """reCAPTCHA issues get the subcategory badge in the rendered HTML."""
        issue = self._make_base_issue()
        issue["title"] = "reCAPTCHA does not return the Legacy secret key"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_html_report([issue], Path(temp_dir))
            html = output_path.read_text()

        assert "recaptcha-badge" in html
        assert "🔑 reCAPTCHA" in html

    def test_recaptcha_badge_absent_for_non_recaptcha_issue(self):
        """Non-reCAPTCHA issues do not get the badge."""
        issue = self._make_base_issue()
        issue["title"] = "google_compute_security_policy preconfigured_waf_config drift"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_html_report([issue], Path(temp_dir))
            html = output_path.read_text()

        assert "🔑 reCAPTCHA" not in html


class TestHtmlGlobalConfidenceToggle(unittest.TestCase):
    """Tests for confidence toggle coverage across all sections."""

    def _make_high_issue(self):
        return {
            'number': 401,
            'title': 'Cloud Armor high issue',
            'url': 'https://github.com/test/401',
            'category': 'Cloud Armor',
            'confidence': 90.0,
            'confidence_band': 'HIGH',
            'label_types': {'bug': True, 'has_pr': True},
            'is_assigned': False,
            'age_days': 500,
            'days_since_update': 200,
            'comments': 5,
            'priority_score': 80.0,
            'labels': ['bug', 'has-pr'],
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-10-01T00:00:00Z',
            'assignees': [],
            'related_categories': [],
        }

    def _make_review_issue(self):
        issue = self._make_high_issue()
        issue['number'] = 402
        issue['title'] = 'Cloud Armor review issue'
        issue['url'] = 'https://github.com/test/402'
        issue['confidence'] = 75.0
        issue['confidence_band'] = 'REVIEW'
        issue['priority_score'] = 60.0
        return issue

    def test_all_tables_have_data_band_attributes(self):
        """All four tables emit data-band attributes on issue rows."""
        issues = [self._make_high_issue(), self._make_review_issue()]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_html_report(issues, Path(temp_dir))
            html = output_path.read_text()

        assert html.count('data-band="HIGH"') >= 2
        assert html.count('data-band="REVIEW"') >= 2

    def test_section_counter_ids_present(self):
        """Section headers have the expected id attributes for JS targeting."""
        issues = [self._make_high_issue()]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_html_report(issues, Path(temp_dir))
            html = output_path.read_text()

        assert 'id="quick-wins-count"' in html
        assert 'id="attention-count"' in html
        assert 'id="detail-count"' in html


class TestHtmlRecentlyReactivated(unittest.TestCase):
    """Tests for the recently reactivated section in HTML report."""

    def _make_reactivated_issue(self):
        return {
            'number': 14896,
            'title': 'google_compute_security_policy block is broken after GA update',
            'url': 'https://github.com/test/14896',
            'category': 'Cloud Armor',
            'confidence': 90.0,
            'confidence_band': 'HIGH',
            'label_types': {'bug': True, 'has_pr': False, 'good_first_issue': False},
            'is_assigned': False,
            'age_days': 1000,
            'days_since_update': 60,
            'comments': 4,
            'priority_score': 80.0,
            'reactivation_bonus': 8,
            'labels': ['bug'],
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2026-01-01T00:00:00Z',
            'assignees': [],
            'related_categories': [],
        }

    def _make_high_issue(self):
        issue = self._make_reactivated_issue()
        issue['number'] = 50001
        issue['title'] = 'standard high confidence issue'
        issue['age_days'] = 30
        issue['days_since_update'] = 5
        issue['reactivation_bonus'] = 0
        return issue

    def test_reactivated_section_present_in_html(self):
        """HTML report contains the Recently Reactivated section header."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_html_report([self._make_reactivated_issue()], Path(temp_dir))
            html = output_path.read_text()
        assert "Recently Reactivated" in html

    def test_reactivated_section_empty_state(self):
        """When no issues qualify, placeholder text is shown."""
        issue = self._make_high_issue()
        issue["age_days"] = 30
        issue["reactivation_bonus"] = 0
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_html_report([issue], Path(temp_dir))
            html = output_path.read_text()
        assert "No recently reactivated issues" in html


if __name__ == '__main__':
    unittest.main()
