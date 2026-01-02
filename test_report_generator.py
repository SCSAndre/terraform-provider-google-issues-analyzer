"""Comprehensive tests for report generation functionality."""
import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from pathlib import Path

from report_generator import ReportGenerator


class TestReportGeneratorGrouping(unittest.TestCase):
    """Tests for issue grouping functionality."""

    def setUp(self):
        self.generator = ReportGenerator()

    def test_group_by_category(self):
        """Test that issues are correctly grouped by category."""
        issues = [
            {"category": "Load Balancers", "title": "Issue 1"},
            {"category": "Cloud Armor", "title": "Issue 2"},
            {"category": "Load Balancers", "title": "Issue 3"},
        ]
        grouped = self.generator._group_by_category(issues)
        self.assertEqual(len(grouped["Load Balancers"]), 2)
        self.assertEqual(len(grouped["Cloud Armor"]), 1)

    def test_group_empty_list(self):
        """Test grouping of empty issue list."""
        grouped = self.generator._group_by_category([])
        self.assertEqual(grouped, {})

    def test_group_single_category(self):
        """Test grouping when all issues are same category."""
        issues = [
            {"category": "PSC", "title": "Issue 1"},
            {"category": "PSC", "title": "Issue 2"},
        ]
        grouped = self.generator._group_by_category(issues)
        self.assertEqual(len(grouped), 1)
        self.assertEqual(len(grouped["PSC"]), 2)


class TestReportGeneratorOutput(unittest.TestCase):
    """Tests for report output generation."""

    def setUp(self):
        self.generator = ReportGenerator()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('report_generator.OUTPUT_DIR')
    def test_generate_markdown_report(self, mock_output_dir):
        """Test full markdown report generation."""
        mock_output_dir.__truediv__ = lambda self, x: Path(self.temp_dir) / x
        mock_output_dir.return_value = Path(self.temp_dir)

        issues = [
            {
                "number": 123,
                "title": "Test Issue",
                "category": "Load Balancers",
                "confidence": 85.5,
                "url": "https://github.com/test/123",
                "created_at": "2024-01-01",
                "comments": 5
            }
        ]

        with patch.object(Path, '__truediv__', return_value=Path(self.temp_dir) / "test_report.md"):
            # Use mock_open for file writing
            m = mock_open()
            with patch('builtins.open', m):
                self.generator.generate_markdown_report(issues, "test_report.md")

            # Verify file was opened for writing
            m.assert_called()

    def test_write_header(self):
        """Test header writing."""
        m = mock_open()
        with patch('builtins.open', m):
            with open('test.md', 'w') as f:
                self.generator._write_header(f, 10)

        written = ''.join(call.args[0] for call in m().write.call_args_list)
        self.assertIn("Terraform Provider Google", written)
        self.assertIn("10", written)


class TestReportGeneratorFormatting(unittest.TestCase):
    """Tests for report formatting."""

    def setUp(self):
        self.generator = ReportGenerator()

    def test_issues_sorted_by_confidence(self):
        """Test that issues are sorted by confidence descending."""
        issues = [
            {"confidence": 50.0, "number": 1, "title": "Low", "url": "", "created_at": "", "comments": 0},
            {"confidence": 90.0, "number": 2, "title": "High", "url": "", "created_at": "", "comments": 0},
            {"confidence": 70.0, "number": 3, "title": "Med", "url": "", "created_at": "", "comments": 0},
        ]

        m = mock_open()
        with patch('builtins.open', m):
            with open('test.md', 'w') as f:
                self.generator._write_category_issues(f, issues)

        written = ''.join(call.args[0] for call in m().write.call_args_list)
        # High confidence should appear before medium and low
        high_pos = written.find("#2")
        med_pos = written.find("#3")
        low_pos = written.find("#1")
        self.assertLess(high_pos, med_pos)
        self.assertLess(med_pos, low_pos)


if __name__ == "__main__":
    unittest.main()
