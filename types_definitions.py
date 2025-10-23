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
    created_at: str
    comments: int
    comments_url: str
    labels: List[GitHubLabel]
    assignees: List[GitHubUser]
