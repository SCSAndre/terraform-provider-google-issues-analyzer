"""GitHub API client with rate limiting and error handling."""
import requests
import time
import logging
from typing import Optional, List, Dict
from datetime import datetime
from functools import lru_cache

from config import (
    GITHUB_TOKEN, TARGET_REPO, RATE_LIMIT_BUFFER,
    REQUEST_DELAY, MAX_RETRIES, INITIAL_BACKOFF
)

logger = logging.getLogger(__name__)


class GitHubClient:
    """Handles GitHub API interactions with rate limiting."""

    def __init__(self):
        self.headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        self.base_url = "https://api.github.com"

    def _handle_rate_limit(self) -> None:
        """Manages GitHub API rate limits."""
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

            if remaining < RATE_LIMIT_BUFFER:
                reset_datetime = datetime.fromtimestamp(reset_time)
                wait_time = (reset_datetime - datetime.now()).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit approaching. Waiting {wait_time:.2f}s...")
                    time.sleep(wait_time + RATE_LIMIT_BUFFER)

            time.sleep(REQUEST_DELAY)
        except requests.RequestException as e:
            logger.error(f"Error checking rate limit: {e}")

    def fetch_issues_page(self, page: int) -> Optional[List[Dict]]:
        """Fetches a single page of issues with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                self._handle_rate_limit()
                url = f"{self.base_url}/repos/{TARGET_REPO}/issues"
                params = {"state": "open", "per_page": 100, "page": page}

                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching page {page} (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(INITIAL_BACKOFF ** attempt)
        return None

    @lru_cache(maxsize=100)
    def fetch_issue_comments(self, comments_url: str) -> Optional[List[Dict]]:
        """Fetches issue comments with caching and retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                self._handle_rate_limit()
                response = requests.get(comments_url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching comments (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(INITIAL_BACKOFF ** attempt)
        return None
