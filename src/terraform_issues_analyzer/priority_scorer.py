from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

from .types_definitions import IssueData
from .issue_classifier import classify_labels, get_blocking_label_info
from .utils import extract_label_names, extract_label_names_lower, has_label


def calculate_priority_score(
    confidence: float,
    confidence_band: str,
    comments: int,
    reactions_plus_one: int,
    age_days: int,
    days_since_update: int,
    is_bug: bool,
    is_actionable: bool = False,
    has_assignee: bool = False,
    labels: List[Any] | None = None,
) -> float:
    """Calculate a priority score for issue ranking.

    Weight breakdown:
    - Confidence: 40 points max
    - Comments: 15 points max
    - Reactions: 15 points max
    - Neglect (age + staleness): 20 points max
    - ultra-age bonus: +3 to +8 for issues older than 3 years
    - reactivation: old issue (>1y) with recent activity (<90d), max +15
    - Bug bonus: 5 points
    - Breaking change penalty: -5 points
    - New resource penalty: -3 points
    - crash bonus: +15 points when issue has the "crash" label
    - Actionable bonus: 5 points
    - size: maintainer effort estimate label (size/xs=+12, size/s=+10, size/m=+5)
    - Unassigned bonus: 10 points
    - High-confidence bonus: 5 points

    Args:
        confidence: Relevance confidence score from classifier.
        confidence_band: Confidence band label (HIGH, REVIEW, EXCLUDED).
        comments: Number of issue comments.
        reactions_plus_one: Community thumbs-up count (+1 reactions), capped at 30.
        age_days: Days since issue creation.
        days_since_update: Days since last issue update.
        is_bug: True when issue has bug-like labels.
        is_actionable: True when issue has newcomer-friendly actionable labels.
        has_assignee: True when issue already has an assignee.
        labels: Raw GitHub labels list (dicts with name or plain strings).
    
    Returns:
        Priority score from 0-100
    """
    score = 0.0
    
    # Confidence contributes 40%
    score += (confidence / 100) * 40
    
    # Comments contribute 15% (cap at 20 comments)
    comment_factor = min(comments, 20) / 20
    score += comment_factor * 15

    thumbs_up = max(int(reactions_plus_one), 0)
    # Reactions factor: community demand signal (+1 count), weight 15%
    # Cap at 30 reactions to avoid a single viral issue dominating
    reactions_factor = min(thumbs_up, 30) / 30 * 15
    score += reactions_factor
    
    # Neglect contributes 20% (weighted blend of age and staleness, cap at 2 years)
    neglect_days = min((age_days * 0.3) + (days_since_update * 0.7), 730)
    score += (neglect_days / 730) * 20

    # Ultra-age bonus: issues that have survived multiple major releases
    # deserve extra visibility. Soft bonus to avoid over-penalizing new issues.
    ultra_age_bonus = 0
    if age_days > 1095:  # > 3 years
        # Scale: 3y=+3, 4y=+6, 5y=+8 (diminishing returns)
        years_beyond_3 = (age_days - 1095) / 365
        ultra_age_bonus = round(min(years_beyond_3 * 3, 8))
    score += ultra_age_bonus

    # Reactivation bonus: old issue that recently got new activity
    # Signals upstream API changes, GA announcements, or renewed urgency.
    # Formula scales by issue age and update recency with a max bonus of +15.
    reactivation_bonus = 0
    if age_days > 365 and days_since_update < 90:
        age_factor = min(age_days / 730, 1.0)
        recency_factor = 1.0 - (days_since_update / 90)
        reactivation_bonus = round(age_factor * recency_factor * 15)
    score += reactivation_bonus
    
    # Bug bonus: 5%
    if is_bug:
        score += 5

    is_breaking_change = has_label(labels, "breaking-change")
    is_new_resource = has_label(labels, "new-resource")

    # Breaking change: deprioritize slightly - requires maintainer oversight
    if is_breaking_change:
        score -= 5

    # New resource: deprioritize - large scope, not a quick fix
    if is_new_resource:
        score -= 3

    # Crash severity bonus: panics and crashes are critical regardless of age
    is_crash = has_label(labels, "crash")
    if is_crash:
        score += 15

    # Actionable bonus: 5%
    if is_actionable:
        score += 5
    
    # Unassigned bonus: 10% (needs someone to pick it up)
    if not has_assignee:
        score += 10

    # High-confidence issues get a small ranking bonus.
    if confidence_band == "HIGH":
        score += 5

    # Size bonus: maintainer effort estimate from size/* labels
    size_bonus = 0
    label_names = extract_label_names_lower(labels)

    if "size/xs" in label_names:
        size_bonus = 12
    elif "size/s" in label_names:
        size_bonus = 10
    elif "size/m" in label_names:
        size_bonus = 5
    elif "size/xl" in label_names:
        size_bonus = -3

    score += size_bonus
    
    return max(0, min(score, 95))


def enrich_issue_data(
    raw_issue: Dict[str, Any],
    classifier_result: Tuple[bool, Optional[str], float, str, List[str]],
    availability_result: Optional[Tuple[bool, str]] = None,
) -> IssueData:
    """Parse extra dates, extract issue labels, and calculate bonuses to construct an IssueData entry.
    
    Args:
        raw_issue: Raw issue dictionary from GitHub API.
        classifier_result: The result from `classify_issue_with_related`.
        availability_result: Included for signature consistency, not strictly required here.
        
    Returns:
        Structured IssueData dictionary ready for reporting.
    """
    (
        is_relevant,
        category,
        confidence,
        confidence_band,
        related_categories,
    ) = classifier_result

    # Parse dates for age calculation
    created_at = datetime.fromisoformat(raw_issue["created_at"].replace("Z", "+00:00"))
    updated_at = datetime.fromisoformat(raw_issue["updated_at"].replace("Z", "+00:00"))
    now = datetime.now(created_at.tzinfo)
    age_days = (now - created_at).days
    days_since_update = (now - updated_at).days
    
    # Extract label types
    labels = extract_label_names(raw_issue.get("labels", []))
    label_types = classify_labels(labels)
    blocking_info = get_blocking_label_info(labels)
    labels_lower = extract_label_names_lower(labels)
    is_crash = "crash" in labels_lower
    is_breaking_change = "breaking-change" in labels_lower
    is_new_resource = "new-resource" in labels_lower
    is_internally_tracked = "forward/linked" in labels_lower
    is_actionable = label_types.get("actionable", False)
    
    # Get assignees
    assignees = [a["login"] for a in raw_issue.get("assignees", [])]

    reactions_data = raw_issue.get("reactions", {})
    thumbs_up = reactions_data.get("+1", 0) if isinstance(reactions_data, dict) else 0

    # Calculate reactivation bonus
    reactivation_bonus = 0
    if age_days > 365 and days_since_update < 90:
        age_factor = min(age_days / 730, 1.0)
        recency_factor = 1.0 - (days_since_update / 90)
        reactivation_bonus = round(age_factor * recency_factor * 15)
    
    # Calculate priority score
    priority_score = calculate_priority_score(
        confidence=confidence,
        confidence_band=confidence_band,
        comments=raw_issue.get("comments", 0),
        reactions_plus_one=thumbs_up,
        age_days=age_days,
        days_since_update=days_since_update,
        is_bug=label_types.get("bug", False),
        is_actionable=is_actionable,
        has_assignee=len(assignees) > 0,
        labels=raw_issue.get("labels", []),
    )

    # Add to results with enriched data
    issue_data: IssueData = {
        "number": raw_issue["number"],
        "title": raw_issue["title"],
        "url": raw_issue["html_url"],
        "state": raw_issue.get("state", "open"),
        "category": category,
        "confidence": confidence,
        "confidence_band": confidence_band,
        "created_at": raw_issue["created_at"],
        "updated_at": raw_issue["updated_at"],
        "age_days": age_days,
        "days_since_update": days_since_update,
        "comments": raw_issue.get("comments", 0),
        "thumbs_up": thumbs_up,
        "labels": labels,
        "label_types": label_types,
        "is_exempt": blocking_info["is_exempt"],
        "is_upstream": blocking_info["is_upstream"],
        "is_blocked": blocking_info["is_blocked"],
        "is_crash": is_crash,
        "is_breaking_change": is_breaking_change,
        "is_new_resource": is_new_resource,
        "is_internally_tracked": is_internally_tracked,
        "assignees": assignees,
        "is_assigned": len(assignees) > 0,
        "actionable": is_actionable,
        "related_categories": related_categories,
        "priority_score": priority_score,
        "reactivation_bonus": reactivation_bonus,
    }
    return issue_data
