"""Checks if issues are available (unclaimed) for work."""
import re
from typing import Dict, List, Tuple, Optional

from .github_client import GitHubClient
from .logging_config import get_logger

logger = get_logger(__name__)


class AvailabilityChecker:
    """Determines if an issue is available or already claimed."""

    def __init__(self, github_client: GitHubClient):
        self.github_client = github_client
        self.commitment_patterns = self._get_commitment_patterns()

    def is_issue_available(self, issue: Dict) -> Tuple[bool, Optional[str]]:
        """
        Checks if issue is available for work.

        Returns:
            Tuple of (is_available, reason_if_unavailable)
        """
        # Check assignees
        is_available, reason = self._check_assignees(issue)
        if not is_available:
            return False, reason

        # Check labels
        is_available, reason = self._check_labels(issue)
        if not is_available:
            return False, reason

        # Check comments
        is_available, reason = self._check_comments(issue)
        if not is_available:
            return False, reason

        # Check linked pull requests from issue timeline events.
        is_available, reason = self._check_linked_prs(issue)
        if not is_available:
            return False, reason

        return True, None

    def _check_assignees(self, issue: Dict) -> Tuple[bool, Optional[str]]:
        """Checks if issue has assignees."""
        assignees = issue.get("assignees", [])
        if assignees:
            assignee = assignees[0].get("login", "someone")
            return False, f"assigned_to_{assignee}"
        return True, None

    def _check_labels(self, issue: Dict) -> Tuple[bool, Optional[str]]:
        """Checks if labels indicate work in progress."""
        claimed_labels = ["in-progress", "wip", "assigned", "claimed", "waiting-for-pr", "has-pr"]

        for label in issue.get("labels", []):
            label_name = label["name"].lower()
            if any(claim_term in label_name for claim_term in claimed_labels):
                return False, f"label_indicates_work_in_progress_{label['name']}"

        return True, None

    def _check_comments(self, issue: Dict) -> Tuple[bool, Optional[str]]:
        """Checks comments for commitment indicators."""
        if issue.get("comments", 0) == 0:
            return True, None

        comments_url = issue.get("comments_url")
        if not comments_url:
            return True, None

        comments = self.github_client.fetch_issue_comments(comments_url)
        if not comments:
            return True, None

        # Check for commitment patterns
        for comment in comments:
            comment_body = (comment.get("body") or "").lower()
            user = comment.get("user", {}).get("login", "someone")

            for pattern in self.commitment_patterns:
                if re.search(pattern, comment_body):
                    return False, f"comment_indicates_commitment_by_{user}"

        return True, None

    def _check_linked_prs(self, issue: Dict) -> Tuple[bool, Optional[str]]:
        """Checks issue timeline for cross-referenced open pull requests."""
        issue_number = issue.get("number")
        if not issue_number:
            return True, None

        timeline = self.github_client.fetch_issue_timeline(int(issue_number))
        if not timeline:
            return True, None

        for event in timeline:
            if event.get("event") != "cross-referenced":
                continue
            source = event.get("source") or {}
            source_issue = source.get("issue") or {}
            if "pull_request" in source_issue and source_issue.get("state") == "open":
                return False, "linked_open_pr"

        return True, None

    def _get_commitment_patterns(self) -> List[str]:
        """Returns regex patterns indicating work commitment."""
        return [
            r"(?i)i('ll| will) (fix|work on|implement|address|look into|check|solve)",
            r"(?i)(working on|fixing|implementing|addressing) this",
            r"(?i)(submitted|created|opened|sending) (a )?(pr|pull request)",
            r"(?i)i('m| am) on it",
            r"(?i)(assigned|assigning) (to )?me",
            r"(?i)taking this( one)?",
            r"(?i)i can (do|fix|handle|work on) this",
            r"(?i)let me (fix|work on|handle)",
            r"(?i)currently working",
            r"(?i)in progress",
            r"(?i)pr submitted",
            r"(?i)i have a fix",
            r"(?i)i started (working|looking)",
            r"(?i)(my|the) (pr|pull request) (is|will be|should be)",
            r"(?i)i have been (working|coding|developing)",
            r"(?i)i already (fixed|implemented|addressed)",
            r"(?i)i'm planning to",
            r"(?i)i've been working",
            r"(?i)going to submit",
            r"(?i)expect to have (this|a fix|a pr) (ready|done)"
        ]
