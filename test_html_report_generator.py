"""Tests for HTML Report Generator."""

import unittest
import tempfile
from pathlib import Path

from html_report_generator import (
    format_age,
    calculate_statistics,
    generate_html_report,
    generate_html_content,
    generate_executive_summary_html,
    generate_quick_wins_html,
    generate_attention_needed_html,
    generate_top_issues_html,
    generate_category_sections_html,
)


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


if __name__ == '__main__':
    unittest.main()
