"""Tests for priority scoring logic."""

import pytest
from terraform_issues_analyzer.priority_scorer import calculate_priority_score

class TestCalculatePriorityScore:
    """Tests for calculate_priority_score function."""

    def test_baseline_score_from_confidence(self):
        """Confidence contributes 40% of max score."""
        score = calculate_priority_score(
            confidence=100.0, confidence_band="HIGH", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False,
        )
        # 100% confidence -> 40 points + 10 unassigned bonus + 5 HIGH bonus = 55
        assert 50 <= score <= 60

    def test_bug_bonus_applied(self):
        """Bug issues get +5 points."""
        base = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False,
        )
        with_bug = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=True,
        )
        assert with_bug[0] - base[0] == 5 if isinstance(base, tuple) else with_bug - base == 5

    def test_crash_label_bonus(self):
        """Crash label adds +15 points."""
        base = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False, labels=[],
        )
        with_crash = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False, labels=[{"name": "crash"}],
        )
        if isinstance(base, tuple):
            assert with_crash[0] - base[0] == 15
        else:
            assert with_crash - base == 15

    def test_breaking_change_penalty(self):
        """Breaking change issues are penalized -5 points."""
        base = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False, labels=[],
        )
        with_breaking = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False, labels=[{"name": "breaking-change"}],
        )
        if isinstance(base, tuple):
            assert base[0] - with_breaking[0] == 5
        else:
            assert base - with_breaking == 5

    def test_unassigned_bonus(self):
        """Unassigned issues get +10 points."""
        assigned = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False, has_assignee=True,
        )
        unassigned = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False, has_assignee=False,
        )
        if isinstance(assigned, tuple):
            assert unassigned[0] - assigned[0] == 10
        else:
            assert unassigned - assigned == 10

    def test_score_clamped_to_0_95_range(self):
        """Score must always be between 0 and 95."""
        max_score = calculate_priority_score(
            confidence=100, confidence_band="HIGH", comments=20,
            reactions_plus_one=30, age_days=2000, days_since_update=0,
            is_bug=True, is_actionable=True, has_assignee=False,
            labels=[{"name": "crash"}, {"name": "size/xs"}],
        )
        assert (max_score[0] if isinstance(max_score, tuple) else max_score) <= 95

        min_score = calculate_priority_score(
            confidence=0, confidence_band="EXCLUDED", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False, has_assignee=True,
            labels=[{"name": "breaking-change"}, {"name": "new-resource"}],
        )
        assert (min_score[0] if isinstance(min_score, tuple) else min_score) >= 0

    def test_ultra_age_bonus_after_3_years(self):
        """Issues older than 3 years get a bonus capped at +8."""
        young = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=365, days_since_update=365,
            is_bug=False,
        )
        old = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=1500, days_since_update=1500,
            is_bug=False,
        )
        if isinstance(young, tuple):
            assert old[0] > young[0]
        else:
            assert old > young

    def test_reactivation_bonus_for_old_recently_updated(self):
        """Old issue (>1yr) with recent activity (<90d) gets reactivation bonus."""
        stale_old = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=500, days_since_update=200,
            is_bug=False,
        )
        reactivated = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=500, days_since_update=30,
            is_bug=False,
        )
        if isinstance(stale_old, tuple):
            assert reactivated[0] > stale_old[0]
        else:
            assert reactivated > stale_old

    def test_size_xs_gets_highest_size_bonus(self):
        """size/xs label gives +12 points."""
        base = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False, labels=[],
        )
        xs = calculate_priority_score(
            confidence=50, confidence_band="REVIEW", comments=0,
            reactions_plus_one=0, age_days=0, days_since_update=0,
            is_bug=False, labels=[{"name": "size/xs"}],
        )
        if isinstance(base, tuple):
            assert xs[0] - base[0] == 12
        else:
            assert xs - base == 12
