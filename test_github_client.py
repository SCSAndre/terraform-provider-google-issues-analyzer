"""Comprehensive tests for GitHub client functionality."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import requests


class TestGitHubClientRateLimiting(unittest.TestCase):
    """Tests for rate limiting functionality."""

    def setUp(self):
        with patch('github_client.GITHUB_TOKEN', 'test_token'):
            from github_client import GitHubClient
            self.client = GitHubClient()

    @patch('github_client.requests.get')
    @patch('github_client.time.sleep')
    def test_rate_limit_check_with_remaining_requests(self, mock_sleep, mock_get):
        """Test rate limit handling when requests remain."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'resources': {
                'core': {
                    'remaining': 100,
                    'reset': 1234567890
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        self.client._handle_rate_limit()
        # Should only sleep for REQUEST_DELAY, not rate limit wait
        mock_sleep.assert_called()

    @patch('github_client.requests.get')
    def test_rate_limit_check_handles_error(self, mock_get):
        """Test that rate limit errors are handled gracefully."""
        mock_get.side_effect = requests.RequestException("API Error")
        # Should not raise exception
        self.client._handle_rate_limit()


class TestGitHubClientFetchIssues(unittest.TestCase):
    """Tests for issue fetching functionality."""

    def setUp(self):
        with patch('github_client.GITHUB_TOKEN', 'test_token'):
            from github_client import GitHubClient
            self.client = GitHubClient()
            self.GitHubClient = GitHubClient

    @patch('github_client.requests.get')
    def test_fetch_issues_page_success(self, mock_get):
        """Test successful issue page fetch."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"number": 1, "title": "Issue 1"},
            {"number": 2, "title": "Issue 2"}
        ]
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch.object(self.client, '_handle_rate_limit'):
            result = self.client.fetch_issues_page(1)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["number"], 1)

    @patch('github_client.requests.get')
    @patch('github_client.time.sleep')
    def test_fetch_issues_page_with_retry(self, mock_sleep, mock_get):
        """Test retry logic on fetch failure."""
        # First call fails, second succeeds
        success_response = Mock()
        success_response.json.return_value = [{"number": 1}]
        success_response.status_code = 200
        success_response.raise_for_status = Mock()
        
        mock_get.side_effect = [
            requests.RequestException("Timeout"),
            success_response
        ]

        with patch.object(self.client, '_handle_rate_limit'):
            result = self.client.fetch_issues_page(1)
        self.assertIsNotNone(result)

    @patch('github_client.requests.get')
    @patch('github_client.time.sleep')
    def test_fetch_issues_page_all_retries_fail(self, mock_sleep, mock_get):
        """Test that None is returned when all retries fail."""
        mock_get.side_effect = requests.RequestException("Persistent error")

        with patch.object(self.client, '_handle_rate_limit'):
            result = self.client.fetch_issues_page(1)
        self.assertIsNone(result)


class TestGitHubClientFetchComments(unittest.TestCase):
    """Tests for comment fetching functionality."""

    def setUp(self):
        with patch('github_client.GITHUB_TOKEN', 'test_token'):
            from github_client import GitHubClient
            self.client = GitHubClient()
            # Clear the cache for each test
            self.client.fetch_issue_comments.cache_clear()

    @patch('github_client.requests.get')
    def test_fetch_comments_success(self, mock_get):
        """Test successful comment fetch."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"body": "Comment 1", "user": {"login": "user1"}},
            {"body": "Comment 2", "user": {"login": "user2"}}
        ]
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch.object(self.client, '_handle_rate_limit'):
            result = self.client.fetch_issue_comments("https://api.github.com/test")
        self.assertEqual(len(result), 2)

    @patch('github_client.requests.get')
    def test_fetch_comments_caching(self, mock_get):
        """Test that comments are cached."""
        mock_response = Mock()
        mock_response.json.return_value = [{"body": "Comment"}]
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch.object(self.client, '_handle_rate_limit'):
            # Call twice with same URL
            url = "https://api.github.com/test/comments"
            self.client.fetch_issue_comments(url)
            self.client.fetch_issue_comments(url)

        # Should only make one API call due to caching
        self.assertEqual(mock_get.call_count, 1)


class TestGitHubClientHeaders(unittest.TestCase):
    """Tests for authentication headers."""

    def test_headers_with_token(self):
        """Test that headers include auth token when provided."""
        with patch('github_client.GITHUB_TOKEN', 'test_token'):
            from github_client import GitHubClient
            client = GitHubClient()
            self.assertIn('Authorization', client.headers)
            self.assertEqual(client.headers['Authorization'], 'token test_token')

    def test_headers_without_token(self):
        """Test that headers are empty when no token provided."""
        with patch('github_client.GITHUB_TOKEN', None):
            from github_client import GitHubClient
            client = GitHubClient()
            self.assertEqual(client.headers, {})


if __name__ == "__main__":
    unittest.main()
