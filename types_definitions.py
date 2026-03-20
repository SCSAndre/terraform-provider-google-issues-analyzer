from typing import TypedDict, Optional, List


class LabelTypes(TypedDict):
    bug: bool
    enhancement: bool
    documentation: bool
    upstream: bool
    breaking_change: bool
    has_pr: bool
    waiting: bool
    good_first_issue: bool
    actionable: bool  # added by Fix 5


class IssueData(TypedDict):
    number: int
    title: str
    url: str
    state: str
    category: Optional[str]
    confidence: float
    confidence_band: str
    created_at: str
    updated_at: str
    age_days: int
    days_since_update: int
    comments: int
    labels: List[str]
    label_types: LabelTypes
    assignees: List[str]
    is_assigned: bool
    related_categories: List[str]
    priority_score: float
