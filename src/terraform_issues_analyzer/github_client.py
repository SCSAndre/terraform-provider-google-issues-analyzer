"""GitHub API client with rate limiting and comprehensive error handling.

This module provides a robust GitHub API client that handles:
- Rate limiting with automatic backoff
- Retry logic with exponential backoff
- Structured error handling with custom exceptions
- Request/response logging with correlation IDs

Example:
    >>> from github_client import GitHubClient
    >>> client = GitHubClient()
    >>> issues = client.fetch_all_issues()
    >>> print(f"Found {len(issues)} issues")
"""

import requests
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from functools import lru_cache
from tenacity import (
    RetryError,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from .config import (
    GITHUB_TOKEN, TARGET_REPO, RATE_LIMIT_BUFFER,
    REQUEST_DELAY, RATE_CHECK_INTERVAL, MAX_RETRIES, INITIAL_BACKOFF
)
from .exceptions import (
    GitHubAPIError,
    RateLimitExceededError,
    AuthenticationError,
    NetworkError,
    ResourceNotFoundError,
)
from .logging_config import get_logger, log_performance

logger = get_logger(__name__)


class GitHubClient:
    """Handles GitHub API interactions with rate limiting and error handling.
    
    This client provides methods for fetching issues and comments from the
    GitHub API, with built-in rate limit handling, retry logic, and
    comprehensive error handling.
    
    Attributes:
        headers: HTTP headers including authorization token
        base_url: Base URL for GitHub API
        
    Example:
        >>> client = GitHubClient()
        >>> page = client.fetch_issues_page(1)
        >>> if page:
        ...     print(f"Got {len(page)} issues")
    """

    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub client.
        
        Args:
            token: Optional GitHub token. If not provided, uses GITHUB_TOKEN
                from config.
        """
        self._token = token or GITHUB_TOKEN
        self.headers: Dict[str, str] = {}
        if self._token:
            self.headers["Authorization"] = f"token {self._token}"
        else:
            logger.warning(
                "No GitHub token provided. API rate limit is 60 requests/hour. "
                "Set GITHUB_TOKEN for 5000 requests/hour."
            )
        self.base_url = "https://api.github.com"
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset: Optional[datetime] = None
        self._last_rate_check: float = 0.0

    @staticmethod
    def _is_retryable_exception(exc: BaseException) -> bool:
        """Return True for transient exceptions that should be retried."""
        if isinstance(exc, (AuthenticationError, RateLimitExceededError)):
            return False
        return isinstance(exc, (NetworkError, GitHubAPIError))

    def _build_retrying(self, operation: str, page: Optional[int] = None) -> Retrying:
        """Create a retry policy for transient API failures."""

        def _before_sleep(retry_state: Any) -> None:
            exc = retry_state.outcome.exception() if retry_state.outcome else None
            logger.warning(
                "%s retry %d/%d",
                operation,
                retry_state.attempt_number,
                MAX_RETRIES,
                extra={"page": page, "error": str(exc) if exc else "unknown"},
            )

        return Retrying(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=INITIAL_BACKOFF, min=1),
            retry=retry_if_exception(self._is_retryable_exception),
            reraise=True,
            before_sleep=_before_sleep,
        )

    def _fetch_issues_page_once(
        self,
        page: int,
        per_page: int,
        state: str,
    ) -> List[Dict[str, Any]]:
        """Single API call for one issues page."""
        self._handle_rate_limit()
        url = f"{self.base_url}/repos/{TARGET_REPO}/issues"
        params = {"state": state, "per_page": per_page, "page": page}

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30,
            )
        except requests.exceptions.Timeout as exc:
            raise NetworkError("Timeout while fetching issues", original_error=exc) from exc
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError("Connection error while fetching issues", original_error=exc) from exc
        except requests.RequestException as exc:
            raise NetworkError("Request error while fetching issues", original_error=exc) from exc

        if response.status_code >= 400:
            self._handle_response_error(response, f"Fetching issues page {page}")

        issues = response.json()
        logger.debug(
            "Fetched page %d",
            page,
            extra={"issue_count": len(issues), "page": page},
        )
        return issues

    def _fetch_issue_comments_once(self, comments_url: str) -> List[Dict[str, Any]]:
        """Single API call for comments endpoint."""
        self._handle_rate_limit()
        try:
            response = requests.get(comments_url, headers=self.headers, timeout=30)
        except requests.exceptions.Timeout as exc:
            raise NetworkError("Timeout while fetching comments", original_error=exc) from exc
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError("Connection error while fetching comments", original_error=exc) from exc
        except requests.RequestException as exc:
            raise NetworkError("Request error while fetching comments", original_error=exc) from exc

        if response.status_code >= 400:
            self._handle_response_error(response, "Fetching comments")

        return response.json()

    def _handle_rate_limit(self) -> None:
        """Check and handle GitHub API rate limits.
        
        Queries the rate limit API and waits if necessary to avoid
        hitting rate limits.
        
        Raises:
            RateLimitExceededError: If rate limit is exhausted and cannot wait.
            NetworkError: If unable to check rate limit status.
        """
        now_epoch = time.time()
        if (now_epoch - self._last_rate_check) < RATE_CHECK_INTERVAL:
            time.sleep(REQUEST_DELAY)
            return

        try:
            response = requests.get(
                f"{self.base_url}/rate_limit",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            self._last_rate_check = time.time()

            data = response.json()
            remaining = data['resources']['core']['remaining']
            reset_time = data['resources']['core']['reset']
            
            self._rate_limit_remaining = remaining
            self._rate_limit_reset = datetime.fromtimestamp(reset_time, tz=timezone.utc)

            if remaining < RATE_LIMIT_BUFFER:
                wait_time = (self._rate_limit_reset - datetime.now(timezone.utc)).total_seconds()
                if wait_time > 0:
                    if wait_time > 3600:  # More than 1 hour
                        raise RateLimitExceededError(
                            remaining=remaining,
                            reset_time=self._rate_limit_reset,
                            message="Rate limit exceeded and reset time is too far in the future"
                        )
                    logger.info(
                        "Rate limit approaching",
                        extra={
                            "remaining": remaining,
                            "wait_seconds": wait_time,
                            "reset_time": self._rate_limit_reset.isoformat()
                        }
                    )
                    time.sleep(wait_time + RATE_LIMIT_BUFFER)

            time.sleep(REQUEST_DELAY)
            
        except requests.exceptions.Timeout as e:
            raise NetworkError(
                "Timeout while checking rate limit",
                original_error=e
            )
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(
                "Connection error while checking rate limit",
                original_error=e
            )
        except requests.RequestException as e:
            logger.warning("Could not check rate limit: %s", e)

    def _handle_response_error(
        self,
        response: requests.Response,
        context: str
    ) -> None:
        """Handle HTTP error responses with appropriate exceptions.
        
        Args:
            response: The HTTP response object
            context: Description of the operation for error messages
            
        Raises:
            AuthenticationError: For 401/403 responses
            ResourceNotFoundError: For 404 responses
            RateLimitExceededError: For 429 responses
            GitHubAPIError: For other error responses
        """
        status_code = response.status_code
        
        try:
            error_data = response.json()
            message = error_data.get('message', response.text)
        except ValueError:
            message = response.text
        
        if status_code == 401:
            raise AuthenticationError(
                "Invalid or missing GitHub token",
                status_code=status_code
            )
        elif status_code == 403:
            if 'rate limit' in message.lower():
                reset_header = response.headers.get('X-RateLimit-Reset')
                reset_time = None
                if reset_header:
                    reset_time = datetime.fromtimestamp(int(reset_header), tz=timezone.utc)
                raise RateLimitExceededError(
                    remaining=0,
                    reset_time=reset_time,
                    message=message
                )
            raise AuthenticationError(
                f"Access forbidden: {message}",
                status_code=status_code
            )
        elif status_code == 404:
            raise ResourceNotFoundError(
                f"{context}: Resource not found",
                status_code=status_code
            )
        elif status_code == 429:
            reset_header = response.headers.get('X-RateLimit-Reset')
            reset_time = None
            if reset_header:
                reset_time = datetime.fromtimestamp(int(reset_header), tz=timezone.utc)
            raise RateLimitExceededError(
                remaining=0,
                reset_time=reset_time,
                message=message
            )
        else:
            raise GitHubAPIError(
                f"{context}: {message}",
                status_code=status_code
            )

    @log_performance
    def fetch_issues_page(
        self,
        page: int,
        per_page: int = 100,
        state: str = "open"
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch a single page of issues with retry logic.
        
        Args:
            page: Page number to fetch (1-indexed)
            per_page: Number of issues per page (max 100)
            state: Issue state filter ("open", "closed", or "all")
            
        Returns:
            List of issue dictionaries, or None if all retries failed.
            
        Raises:
            AuthenticationError: If authentication fails
            RateLimitExceededError: If rate limit is exceeded
        """
        try:
            retrying = self._build_retrying("Fetch issues page", page=page)
            for attempt in retrying:
                with attempt:
                    return self._fetch_issues_page_once(page=page, per_page=per_page, state=state)
        except (AuthenticationError, RateLimitExceededError):
            raise
        except (NetworkError, GitHubAPIError, RetryError) as e:
            logger.error(
                "All retry attempts failed for page %d",
                page,
                extra={"last_error": str(e), "page": page},
            )
            return None

        return None

    @lru_cache(maxsize=500)
    def fetch_issue_comments(
        self,
        comments_url: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch issue comments with caching and retry logic.
        
        Results are cached to avoid redundant API calls for the same URL.
        
        Args:
            comments_url: The GitHub API URL for fetching comments
            
        Returns:
            List of comment dictionaries, or None if all retries failed.
        """
        try:
            retrying = self._build_retrying("Fetch issue comments")
            for attempt in retrying:
                with attempt:
                    return self._fetch_issue_comments_once(comments_url)
        except (AuthenticationError, RateLimitExceededError):
            raise
        except (NetworkError, GitHubAPIError, RetryError) as e:
            logger.error(
                "Failed to fetch comments after retries",
                extra={"error": str(e), "comments_url": comments_url},
            )
            return None

        return None

    def _fetch_issue_timeline_once(self, issue_number: int) -> List[Dict[str, Any]]:
        """Single API call for issue timeline endpoint."""
        self._handle_rate_limit()
        url = f"{self.base_url}/repos/{TARGET_REPO}/issues/{issue_number}/timeline"
        headers = {
            **self.headers,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
        except requests.exceptions.Timeout as exc:
            raise NetworkError("Timeout while fetching issue timeline", original_error=exc) from exc
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError("Connection error while fetching issue timeline", original_error=exc) from exc
        except requests.RequestException as exc:
            raise NetworkError("Request error while fetching issue timeline", original_error=exc) from exc

        if response.status_code >= 400:
            self._handle_response_error(response, f"Fetching timeline for issue {issue_number}")

        timeline = response.json()
        if isinstance(timeline, list):
            return timeline
        return []

    @lru_cache(maxsize=500)
    def fetch_issue_timeline(self, issue_number: int) -> Optional[List[Dict[str, Any]]]:
        """Fetch issue timeline events with retry logic.

        Args:
            issue_number: Numeric issue identifier.

        Returns:
            List of timeline events, or None if all retries fail.
        """
        try:
            retrying = self._build_retrying("Fetch issue timeline")
            for attempt in retrying:
                with attempt:
                    return self._fetch_issue_timeline_once(issue_number)
        except (AuthenticationError, RateLimitExceededError):
            raise
        except (NetworkError, GitHubAPIError, RetryError) as e:
            logger.error(
                "Failed to fetch issue timeline after retries",
                extra={"error": str(e), "issue_number": issue_number},
            )
            return None

        return None

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status.
        
        Returns:
            Dictionary with remaining requests and reset time.
        """
        return {
            "remaining": self._rate_limit_remaining,
            "reset_time": (
                self._rate_limit_reset.isoformat()
                if self._rate_limit_reset
                else None
            )
        }
