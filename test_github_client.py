"""Comprehensive tests for GitHub client functionality."""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests


class TestGitHubClientInitialization(unittest.TestCase):
    """Tests for GitHubClient initialization."""

    def test_init_with_token(self):
        """Test initialization with a token."""
        with patch('github_client.GITHUB_TOKEN', 'test_token'):
            from github_client import GitHubClient
            client = GitHubClient()
            self.assertEqual(client.headers['Authorization'], 'token test_token')
            self.assertEqual(client.base_url, 'https://api.github.com')

    def test_init_with_custom_token(self):
        """Test initialization with a custom token."""
        with patch('github_client.GITHUB_TOKEN', 'default_token'):
            from github_client import GitHubClient
            client = GitHubClient(token='custom_token')
            self.assertEqual(client.headers['Authorization'], 'token custom_token')

    def test_init_without_token(self):
        """Test initialization without a token logs warning."""
        with patch('github_client.GITHUB_TOKEN', None):
            from github_client import GitHubClient
            client = GitHubClient()
            self.assertEqual(client.headers, {})

    def test_initial_rate_limit_state(self):
        """Test initial rate limit state is None."""
        with patch('github_client.GITHUB_TOKEN', 'test_token'):
            from github_client import GitHubClient
            client = GitHubClient()
            self.assertIsNone(client._rate_limit_remaining)
            self.assertIsNone(client._rate_limit_reset)


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

    @patch('github_client.requests.get')
    @patch('github_client.time.sleep')
    def test_rate_limit_low_remaining_waits(self, mock_sleep, mock_get):
        """Test that low remaining requests triggers wait."""
        future_reset = int((datetime.now() + timedelta(seconds=30)).timestamp())
        mock_response = Mock()
        mock_response.json.return_value = {
            'resources': {
                'core': {
                    'remaining': 5,  # Below RATE_LIMIT_BUFFER
                    'reset': future_reset
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch('github_client.RATE_LIMIT_BUFFER', 10):
            self.client._handle_rate_limit()
        # Should have called sleep for waiting
        self.assertTrue(mock_sleep.called)

    @patch('github_client.requests.get')
    def test_rate_limit_timeout_raises_network_error(self, mock_get):
        """Test that timeout raises NetworkError."""
        from exceptions import NetworkError
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        with self.assertRaises(NetworkError):
            self.client._handle_rate_limit()

    @patch('github_client.requests.get')
    def test_rate_limit_connection_error_raises_network_error(self, mock_get):
        """Test that connection error raises NetworkError."""
        from exceptions import NetworkError
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with self.assertRaises(NetworkError):
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
    def test_fetch_issues_page_with_params(self, mock_get):
        """Test fetch issues with custom parameters."""
        mock_response = Mock()
        mock_response.json.return_value = [{"number": 1}]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with patch.object(self.client, '_handle_rate_limit'):
            self.client.fetch_issues_page(2, per_page=50, state="closed")
        
        # Verify URL params
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['page'], 2)
        self.assertEqual(call_args[1]['params']['per_page'], 50)
        self.assertEqual(call_args[1]['params']['state'], 'closed')

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

    @patch('github_client.requests.get')
    def test_fetch_issues_page_auth_error_not_retried(self, mock_get):
        """Test that authentication errors are not retried."""
        from exceptions import AuthenticationError
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'message': 'Bad credentials'}
        mock_response.text = 'Bad credentials'
        mock_get.return_value = mock_response

        with patch.object(self.client, '_handle_rate_limit'):
            with self.assertRaises(AuthenticationError):
                self.client.fetch_issues_page(1)
        
        # Should only be called once (no retry)
        self.assertEqual(mock_get.call_count, 1)

    @patch('github_client.requests.get')
    def test_fetch_issues_page_rate_limit_error(self, mock_get):
        """Test rate limit error handling."""
        from exceptions import RateLimitExceededError
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {'message': 'Rate limit exceeded'}
        mock_response.text = 'Rate limit exceeded'
        mock_response.headers = {'X-RateLimit-Reset': '1234567890'}
        mock_get.return_value = mock_response

        with patch.object(self.client, '_handle_rate_limit'):
            with self.assertRaises(RateLimitExceededError):
                self.client.fetch_issues_page(1)


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

    @patch('github_client.requests.get')
    @patch('github_client.time.sleep')
    def test_fetch_comments_retry_on_failure(self, mock_sleep, mock_get):
        """Test retry logic for comment fetching."""
        success_response = Mock()
        success_response.json.return_value = [{"body": "Comment"}]
        success_response.status_code = 200
        
        mock_get.side_effect = [
            requests.RequestException("Network error"),
            success_response
        ]

        with patch.object(self.client, '_handle_rate_limit'):
            result = self.client.fetch_issue_comments("https://api.github.com/test")
        self.assertIsNotNone(result)

    @patch('github_client.requests.get')
    @patch('github_client.time.sleep')
    def test_fetch_comments_all_retries_fail(self, mock_sleep, mock_get):
        """Test that None is returned when all retries fail."""
        mock_get.side_effect = requests.RequestException("Persistent error")

        with patch.object(self.client, '_handle_rate_limit'):
            result = self.client.fetch_issue_comments("https://api.github.com/test")
        self.assertIsNone(result)


class TestGitHubClientFetchAllIssues(unittest.TestCase):
    """Tests for fetch_all_issues functionality."""

    def setUp(self):
        with patch('github_client.GITHUB_TOKEN', 'test_token'):
            from github_client import GitHubClient
            self.client = GitHubClient()

    def test_fetch_all_issues_single_page(self):
        """Test fetching all issues when they fit in one page."""
        with patch.object(self.client, 'fetch_issues_page') as mock_fetch:
            mock_fetch.return_value = [{"number": i} for i in range(50)]
            result = self.client.fetch_all_issues()
        
        self.assertEqual(len(result), 50)
        mock_fetch.assert_called_once()

    def test_fetch_all_issues_multiple_pages(self):
        """Test fetching all issues across multiple pages."""
        with patch.object(self.client, 'fetch_issues_page') as mock_fetch:
            # First page full, second page partial
            mock_fetch.side_effect = [
                [{"number": i} for i in range(100)],
                [{"number": i} for i in range(100, 150)],
            ]
            result = self.client.fetch_all_issues()
        
        self.assertEqual(len(result), 150)
        self.assertEqual(mock_fetch.call_count, 2)

    def test_fetch_all_issues_with_max_pages(self):
        """Test fetching with max_pages limit."""
        with patch.object(self.client, 'fetch_issues_page') as mock_fetch:
            mock_fetch.return_value = [{"number": i} for i in range(100)]
            result = self.client.fetch_all_issues(max_pages=2)
        
        self.assertEqual(mock_fetch.call_count, 2)

    def test_fetch_all_issues_empty_response(self):
        """Test handling empty response."""
        with patch.object(self.client, 'fetch_issues_page') as mock_fetch:
            mock_fetch.return_value = []
            result = self.client.fetch_all_issues()
        
        self.assertEqual(len(result), 0)

    def test_fetch_all_issues_none_response(self):
        """Test handling None response (API failure)."""
        with patch.object(self.client, 'fetch_issues_page') as mock_fetch:
            mock_fetch.return_value = None
            result = self.client.fetch_all_issues()
        
        self.assertEqual(len(result), 0)


class TestGitHubClientResponseErrorHandling(unittest.TestCase):
    """Tests for _handle_response_error method."""

    def setUp(self):
        with patch('github_client.GITHUB_TOKEN', 'test_token'):
            from github_client import GitHubClient
            self.client = GitHubClient()

    def test_handle_401_raises_auth_error(self):
        """Test 401 response raises AuthenticationError."""
        from exceptions import AuthenticationError
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'message': 'Bad credentials'}
        mock_response.text = 'Bad credentials'

        with self.assertRaises(AuthenticationError):
            self.client._handle_response_error(mock_response, "Test context")

    def test_handle_403_rate_limit_raises_rate_limit_error(self):
        """Test 403 rate limit response raises RateLimitExceededError."""
        from exceptions import RateLimitExceededError
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {'message': 'API rate limit exceeded'}
        mock_response.text = 'API rate limit exceeded'
        mock_response.headers = {'X-RateLimit-Reset': '1234567890'}

        with self.assertRaises(RateLimitExceededError):
            self.client._handle_response_error(mock_response, "Test context")

    def test_handle_403_forbidden_raises_auth_error(self):
        """Test 403 forbidden (non-rate-limit) raises AuthenticationError."""
        from exceptions import AuthenticationError
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {'message': 'Repository access denied'}
        mock_response.text = 'Repository access denied'

        with self.assertRaises(AuthenticationError):
            self.client._handle_response_error(mock_response, "Test context")

    def test_handle_404_raises_not_found_error(self):
        """Test 404 response raises ResourceNotFoundError."""
        from exceptions import ResourceNotFoundError
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'message': 'Not Found'}
        mock_response.text = 'Not Found'

        with self.assertRaises(ResourceNotFoundError):
            self.client._handle_response_error(mock_response, "Test context")

    def test_handle_429_raises_rate_limit_error(self):
        """Test 429 response raises RateLimitExceededError."""
        from exceptions import RateLimitExceededError
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {'message': 'Too many requests'}
        mock_response.text = 'Too many requests'
        mock_response.headers = {'X-RateLimit-Reset': '1234567890'}

        with self.assertRaises(RateLimitExceededError):
            self.client._handle_response_error(mock_response, "Test context")

    def test_handle_500_raises_api_error(self):
        """Test 500 response raises GitHubAPIError."""
        from exceptions import GitHubAPIError
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'message': 'Internal Server Error'}
        mock_response.text = 'Internal Server Error'

        with self.assertRaises(GitHubAPIError):
            self.client._handle_response_error(mock_response, "Test context")

    def test_handle_invalid_json_response(self):
        """Test handling response with invalid JSON."""
        from exceptions import GitHubAPIError
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = 'Plain text error'

        with self.assertRaises(GitHubAPIError):
            self.client._handle_response_error(mock_response, "Test context")


class TestGitHubClientRateLimitStatus(unittest.TestCase):
    """Tests for get_rate_limit_status method."""

    def setUp(self):
        with patch('github_client.GITHUB_TOKEN', 'test_token'):
            from github_client import GitHubClient
            self.client = GitHubClient()

    def test_get_rate_limit_status_initial(self):
        """Test rate limit status before any API calls."""
        status = self.client.get_rate_limit_status()
        self.assertIsNone(status['remaining'])
        self.assertIsNone(status['reset_time'])

    def test_get_rate_limit_status_after_check(self):
        """Test rate limit status after checking rate limit."""
        self.client._rate_limit_remaining = 4500
        self.client._rate_limit_reset = datetime(2026, 1, 2, 12, 0, 0)
        
        status = self.client.get_rate_limit_status()
        self.assertEqual(status['remaining'], 4500)
        self.assertEqual(status['reset_time'], '2026-01-02T12:00:00')


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
