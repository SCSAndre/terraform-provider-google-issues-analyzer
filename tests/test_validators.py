"""Tests for input validation utilities."""
import unittest
from terraform_issues_analyzer.validators import sanitize_for_markdown


class TestSanitizeForMarkdown(unittest.TestCase):
    """Tests for markdown sanitization."""

    def test_empty_string(self):
        """Test empty string."""
        result = sanitize_for_markdown("")
        self.assertEqual(result, "")

    def test_normal_text(self):
        """Test normal text."""
        result = sanitize_for_markdown("Hello World")
        self.assertEqual(result, "Hello World")

    def test_escape_html(self):
        """Test HTML is escaped."""
        result = sanitize_for_markdown("<script>alert('xss')</script>")
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;", result)

    def test_escape_markdown_chars(self):
        """Test markdown characters are escaped."""
        result = sanitize_for_markdown("[link](url)")
        self.assertIn("\\[", result)
        self.assertIn("\\]", result)


if __name__ == "__main__":
    unittest.main()
