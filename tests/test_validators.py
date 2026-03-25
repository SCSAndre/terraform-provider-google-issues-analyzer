"""Tests for input validation utilities."""
import unittest
from terraform_issues_analyzer.validators import IssueValidator, sanitize_for_markdown


class TestIssueValidatorBasic(unittest.TestCase):
    """Basic validation tests."""

    def test_validate_valid_issue(self):
        """Test validation of a valid issue."""
        issue = {
            "number": 12345,
            "title": "Test Issue",
            "body": "This is a test body",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "testuser"}],
            "comments": 5,
            "comments_url": "https://api.github.com/repos/test/test/issues/1/comments",
            "html_url": "https://github.com/test/test/issues/1",
            "created_at": "2024-01-01T00:00:00Z",
            "state": "open"
        }
        validated = IssueValidator.validate_issue(issue)
        self.assertEqual(validated["number"], 12345)
        self.assertEqual(validated["title"], "Test Issue")
        self.assertEqual(validated["state"], "open")

    def test_validate_empty_issue(self):
        """Test validation of empty issue."""
        issue = {}
        validated = IssueValidator.validate_issue(issue)
        self.assertEqual(validated["number"], 0)
        self.assertEqual(validated["title"], "")
        self.assertEqual(validated["labels"], [])

    def test_validate_non_dict_issue(self):
        """Test validation of non-dict input."""
        validated = IssueValidator.validate_issue("not a dict")
        self.assertEqual(validated["number"], 0)
        self.assertEqual(validated["title"], "")

    def test_validate_none_issue(self):
        """Test validation of None input."""
        validated = IssueValidator.validate_issue(None)
        self.assertEqual(validated["number"], 0)


class TestIssueValidatorNumber(unittest.TestCase):
    """Tests for issue number validation."""

    def test_valid_number(self):
        """Test valid issue number."""
        result = IssueValidator._validate_number(12345)
        self.assertEqual(result, 12345)

    def test_string_number(self):
        """Test string number conversion."""
        result = IssueValidator._validate_number("12345")
        self.assertEqual(result, 12345)

    def test_zero_number(self):
        """Test zero is rejected."""
        result = IssueValidator._validate_number(0)
        self.assertEqual(result, 0)

    def test_negative_number(self):
        """Test negative number is rejected."""
        result = IssueValidator._validate_number(-1)
        self.assertEqual(result, 0)

    def test_none_number(self):
        """Test None is handled."""
        result = IssueValidator._validate_number(None)
        self.assertEqual(result, 0)


class TestIssueValidatorText(unittest.TestCase):
    """Tests for text sanitization."""

    def test_normal_text(self):
        """Test normal text passes through."""
        result = IssueValidator._sanitize_text("Normal text", 100)
        self.assertEqual(result, "Normal text")

    def test_none_text(self):
        """Test None becomes empty string."""
        result = IssueValidator._sanitize_text(None, 100)
        self.assertEqual(result, "")

    def test_truncate_long_text(self):
        """Test long text is truncated."""
        long_text = "a" * 200
        result = IssueValidator._sanitize_text(long_text, 100)
        self.assertEqual(len(result), 103)  # 100 + "..."
        self.assertTrue(result.endswith("..."))

    def test_remove_control_characters(self):
        """Test control characters are removed."""
        text = "Hello\x00\x01\x02World"
        result = IssueValidator._sanitize_text(text, 100)
        self.assertEqual(result, "HelloWorld")

    def test_preserve_newlines(self):
        """Test newlines are preserved."""
        text = "Hello\nWorld"
        result = IssueValidator._sanitize_text(text, 100)
        self.assertEqual(result, "Hello\nWorld")


class TestIssueValidatorLabels(unittest.TestCase):
    """Tests for label validation."""

    def test_valid_labels(self):
        """Test valid labels pass through."""
        labels = [{"name": "bug"}, {"name": "enhancement"}]
        result = IssueValidator._validate_labels(labels)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "bug")

    def test_none_labels(self):
        """Test None becomes empty list."""
        result = IssueValidator._validate_labels(None)
        self.assertEqual(result, [])

    def test_invalid_label_format(self):
        """Test invalid label format is skipped."""
        labels = [{"name": "valid"}, {"invalid": "no name"}, "string"]
        result = IssueValidator._validate_labels(labels)
        self.assertEqual(len(result), 1)

    def test_max_labels(self):
        """Test max labels limit."""
        labels = [{"name": f"label{i}"} for i in range(100)]
        result = IssueValidator._validate_labels(labels)
        self.assertLessEqual(len(result), 50)


class TestIssueValidatorUrl(unittest.TestCase):
    """Tests for URL validation."""

    def test_valid_github_url(self):
        """Test valid GitHub URL."""
        url = "https://github.com/owner/repo/issues/1"
        result = IssueValidator._validate_url(url)
        self.assertEqual(result, url)

    def test_valid_api_url(self):
        """Test valid GitHub API URL."""
        url = "https://api.github.com/repos/owner/repo/issues/1"
        result = IssueValidator._validate_url(url)
        self.assertEqual(result, url)

    def test_non_github_url(self):
        """Test non-GitHub URL is rejected."""
        url = "https://example.com/issues"
        result = IssueValidator._validate_url(url)
        self.assertEqual(result, "")

    def test_non_https_url(self):
        """Test non-HTTPS URL is rejected."""
        url = "ftp://github.com/issues"
        result = IssueValidator._validate_url(url)
        self.assertEqual(result, "")

    def test_none_url(self):
        """Test None is handled."""
        result = IssueValidator._validate_url(None)
        self.assertEqual(result, "")


class TestIssueValidatorAssignees(unittest.TestCase):
    """Tests for assignee validation."""

    def test_valid_assignee(self):
        """Test valid assignee passes through."""
        assignees = [{"login": "testuser"}]
        result = IssueValidator._validate_assignees(assignees)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["login"], "testuser")

    def test_invalid_username(self):
        """Test invalid username is rejected."""
        assignees = [{"login": "user with spaces"}]
        result = IssueValidator._validate_assignees(assignees)
        self.assertEqual(len(result), 0)

    def test_valid_username_with_hyphen(self):
        """Test username with hyphen is valid."""
        self.assertTrue(IssueValidator._is_valid_username("test-user"))

    def test_invalid_starting_hyphen(self):
        """Test username starting with hyphen is invalid."""
        self.assertFalse(IssueValidator._is_valid_username("-testuser"))


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
