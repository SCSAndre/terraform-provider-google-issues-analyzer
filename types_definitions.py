"""Type definitions for GitHub issues."""
from typing import TypedDict, List, Optional

class GitHubUser(TypedDict, total=False):
    login: str
    id: int

class GitHubLabel(TypedDict, total=False):
    name: str
    color: str

class GitHubComment(TypedDict, total=False):
    body: str
    user: GitHubUser
    created_at: str

class GitHubIssue(TypedDict, total=False):
    number: int
    title: str
    body: Optional[str]
    html_url: str
    state: str
    created_at: str
    updated_at: str
    comments: int
    comments_url: str
    labels: List[GitHubLabel]
    assignees: List[GitHubUser]
    assignee: Optional[GitHubUser]
    reactions: dict


class EnrichedIssue(TypedDict, total=False):
    """Enriched issue data after classification."""
    number: int
    title: str
    url: str
    state: str
    category: str
    confidence: float
    created_at: str
    updated_at: str
    comments: int
    labels: List[str]
    label_types: dict  # {'bug': True, 'enhancement': False, ...}
    assignees: List[str]
    is_assigned: bool
    age_days: int
    days_since_update: int
    related_categories: List[str]  # For cross-category issues
    priority_score: float  # Calculated priority
