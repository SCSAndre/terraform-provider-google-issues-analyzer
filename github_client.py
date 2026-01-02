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
from datetime import datetime
from functools import lru_cache

from config import (
    GITHUB_TOKEN, TARGET_REPO, RATE_LIMIT_BUFFER,
    REQUEST_DELAY, MAX_RETRIES, INITIAL_BACKOFF
)
from exceptions import (
    GitHubAPIError,
    RateLimitExceededError,
    AuthenticationError,
    NetworkError,
    ResourceNotFoundError,
)
from logging_config import get_logger, log_performance

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

    def _handle_rate_limit(self) -> None:
        """Check and handle GitHub API rate limits.
        
        Queries the rate limit API and waits if necessary to avoid
        hitting rate limits.
        
        Raises:
            RateLimitExceededError: If rate limit is exhausted and cannot wait.
            NetworkError: If unable to check rate limit status.
        """
        try:
            response = requests.get(
                f"{self.base_url}/rate_limit",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            remaining = data['resources']['core']['remaining']
            reset_time = data['resources']['core']['reset']
            
            self._rate_limit_remaining = remaining
            self._rate_limit_reset = datetime.fromtimestamp(reset_time)

            if remaining < RATE_LIMIT_BUFFER:
                wait_time = (self._rate_limit_reset - datetime.now()).total_seconds()
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
            logger.warning(f"Could not check rate limit: {e}")

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
                    reset_time = datetime.fromtimestamp(int(reset_header))
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
                reset_time = datetime.fromtimestamp(int(reset_header))
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
        last_error: Optional[Exception] = None
        
        for attempt in range(MAX_RETRIES):
            try:
                self._handle_rate_limit()
                url = f"{self.base_url}/repos/{TARGET_REPO}/issues"
                params = {"state": state, "per_page": per_page, "page": page}

                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code >= 400:
                    self._handle_response_error(
                        response,
                        f"Fetching issues page {page}"
                    )
                
                issues = response.json()
                logger.debug(
                    f"Fetched page {page}",
                    extra={"issue_count": len(issues), "page": page}
                )
                return issues
                
            except (AuthenticationError, RateLimitExceededError):
                # Don't retry auth or rate limit errors
                raise
            except (NetworkError, GitHubAPIError) as e:
                last_error = e
                logger.warning(
                    f"Fetch attempt {attempt + 1}/{MAX_RETRIES} failed",
                    extra={
                        "page": page,
                        "error": str(e),
                        "attempt": attempt + 1
                    }
                )
                if attempt < MAX_RETRIES - 1:
                    sleep_time = INITIAL_BACKOFF ** attempt
                    time.sleep(sleep_time)
            except requests.RequestException as e:
                last_error = NetworkError(str(e), original_error=e)
                logger.warning(
                    f"Request error on attempt {attempt + 1}/{MAX_RETRIES}",
                    extra={"page": page, "error": str(e)}
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(INITIAL_BACKOFF ** attempt)
        
        logger.error(
            f"All {MAX_RETRIES} attempts failed for page {page}",
            extra={"last_error": str(last_error)}
        )
        return None

    @lru_cache(maxsize=100)
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
        last_error: Optional[Exception] = None
        
        for attempt in range(MAX_RETRIES):
            try:
                self._handle_rate_limit()
                response = requests.get(
                    comments_url,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code >= 400:
                    self._handle_response_error(
                        response,
                        "Fetching comments"
                    )
                
                return response.json()
                
            except (AuthenticationError, RateLimitExceededError):
                raise
            except (NetworkError, GitHubAPIError, requests.RequestException) as e:
                last_error = e
                logger.warning(
                    f"Comment fetch attempt {attempt + 1}/{MAX_RETRIES} failed",
                    extra={"error": str(e)}
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(INITIAL_BACKOFF ** attempt)
        
        logger.error(f"Failed to fetch comments after {MAX_RETRIES} attempts")
        return None

    @log_performance
    def fetch_all_issues(
        self,
        max_pages: Optional[int] = None,
        state: str = "open"
    ) -> List[Dict[str, Any]]:
        """Fetch all issues with pagination.
        
        Args:
            max_pages: Maximum number of pages to fetch (None for all)
            state: Issue state filter ("open", "closed", or "all")
            
        Returns:
            List of all fetched issue dictionaries.
        """
        all_issues: List[Dict[str, Any]] = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            issues = self.fetch_issues_page(page, state=state)
            
            if not issues:
                break
                
            all_issues.extend(issues)
            logger.info(
                f"Progress: {len(all_issues)} issues fetched",
                extra={"page": page, "total": len(all_issues)}
            )
            
            if len(issues) < 100:
                break
                
            page += 1
        
        logger.info(
            f"Completed fetching {len(all_issues)} issues",
            extra={"pages_fetched": page, "total_issues": len(all_issues)}
        )
        return all_issues

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
