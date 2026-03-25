"""
HTML Report Generator for Terraform Issues Analyzer.

Generates professional HTML reports with interactive charts and styling.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config import HIGH_CONFIDENCE_THRESHOLD, MEDIUM_CONFIDENCE_THRESHOLD, MIN_CONFIDENCE_THRESHOLD
from types_definitions import IssueData
from utils import format_age


def generate_html_report(
    issues: List[IssueData],
    output_dir: Optional[Path] = None,
    history: Optional[List[Dict[str, Any]]] = None,
) -> Union[Path, str]:
    """Generate an HTML report from the analyzed issues."""
    resolved_history = history
    if resolved_history is None:
        if output_dir is not None:
            resolved_history = load_history(output_dir / "history.json")
        else:
            resolved_history = []

    # Calculate statistics
    stats = calculate_statistics(issues)
    stats["history"] = resolved_history
    generic_issues: List[Dict[str, Any]] = [dict(issue) for issue in issues]
    html_content = generate_html_content(generic_issues, stats)

    if output_dir is None:
        return html_content

    output_path = output_dir / "terraform_issues_report.html"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_path


def load_history(history_path: Path) -> List[Dict[str, Any]]:
    """Load historical run summaries for trend visualization.

    Args:
        history_path: Path to history.json.

    Returns:
        List of historical summary rows sorted in file order.
    """
    if not history_path.exists():
        return []

    try:
        with open(history_path, "r", encoding="utf-8") as history_file:
            parsed = json.load(history_file)
            if isinstance(parsed, list):
                return [row for row in parsed if isinstance(row, dict)]
    except (OSError, ValueError):
        return []

    return []


def get_confidence_badge(score: float) -> str:
    """Render a confidence score badge for issue tables.

    Args:
        score: Confidence score for an issue.

    Returns:
        HTML span element for confidence badge.
    """
    if score >= HIGH_CONFIDENCE_THRESHOLD:
        css_class = "badge-confidence-high"
        band = "HIGH"
    elif score >= MEDIUM_CONFIDENCE_THRESHOLD:
        css_class = "badge-confidence-review"
        band = "REVIEW"
    else:
        css_class = "badge-confidence-review"
        band = "EXCLUDED"
    return f'<span class="badge {css_class}">{band} {score:.1f}%</span>'


def get_issue_confidence_band(issue: Dict[str, Any]) -> str:
    """Return normalized confidence band for issue row filtering."""
    band = str(issue.get("confidence_band", "")).upper()
    if band in {"HIGH", "REVIEW", "EXCLUDED"}:
        return band

    score = float(issue.get("confidence", 0))
    if score >= HIGH_CONFIDENCE_THRESHOLD:
        return "HIGH"
    if score >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "REVIEW"
    return "EXCLUDED"


def _is_recaptcha_issue(issue: Dict[str, Any]) -> bool:
    """Return True when issue title indicates reCAPTCHA Enterprise resources."""
    title = str(issue.get("title") or "").lower()
    return any(
        term in title
        for term in ("recaptcha", "recaptcha_enterprise", "google_recaptcha")
    )


def _is_contributor_safe(issue: Dict[str, Any]) -> bool:
    """Return True when issue is safe to present as a contributor entry point."""
    return not issue.get("is_blocked", False)


def _is_entry_point(issue: Dict[str, Any]) -> bool:
    """Return True if this issue qualifies as a contributor entry point."""
    if issue.get("confidence_band") != "HIGH":
        return False
    if issue.get("is_blocked", False):
        return False
    labels = [label.lower() for label in issue.get("labels", [])]
    if "breaking-change" in labels:
        return False
    lt = issue.get("label_types", {})
    if "new-resource" in labels or lt.get("new_resource", False):
        return False
    has_effort_signal = (
        any(size in labels for size in ("size/xs", "size/s"))
        or lt.get("has_pr", False)
        or lt.get("documentation", False)
    )
    if not has_effort_signal:
        return False
    return issue.get("is_internally_tracked", False) or issue.get("priority_score", 0) >= 65


def _get_entry_point_reason(issue: Dict[str, Any]) -> str:
    """Return short qualifier text for contributor entry points."""
    labels = [label.lower() for label in issue.get("labels", [])]
    lt = issue.get("label_types", {})
    if lt.get("has_pr", False):
        return "Finish existing PR"
    if lt.get("documentation", False):
        return "Docs fix"
    if "size/xs" in labels:
        return "Tiny scope (xs)"
    if "size/s" in labels:
        return "Small scope (s)"
    return "Actionable"


def _get_blocking_badges(issue: Dict[str, Any]) -> List[str]:
    """Return blocking badges for issues with permanent external blockers."""
    badges: List[str] = []
    if issue.get("is_crash"):
        badges.append(
            '<span class="badge badge-crash" title="This issue causes a crash or panic">🔴 Crash</span>'
        )
    if issue.get("is_breaking_change"):
        badges.append(
            '<span class="badge badge-breaking" title="Requires a breaking change - major version bump needed">💥 Breaking</span>'
        )
    if issue.get("is_new_resource"):
        badges.append(
            '<span class="badge badge-new-resource" title="Requires implementing a new Terraform resource from scratch">🆕 New Resource</span>'
        )
    if issue.get("is_exempt"):
        badges.append(
            '<span class="badge badge-exempt" title="HashiCorp will not fix - depends on upstream GCP API">🚫 Exempt</span>'
        )
    if issue.get("is_upstream"):
        badges.append(
            '<span class="badge badge-upstream" title="Blocked on GCP API - Terraform fix not possible until Google acts">⛔ GCP Blocked</span>'
        )
    return badges


def _get_tracking_badges(issue: Dict[str, Any]) -> List[str]:
    """Return ownership badges that indicate internal tracking state."""
    badges: List[str] = []
    if issue.get("is_internally_tracked"):
        badges.append(
            '<span class="badge badge-tracked" title="Tracked in HashiCorp internal backlog">🔖 Tracked</span>'
        )
    return badges


def _get_recently_reactivated_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return recently reactivated issues using report-specific business rules."""
    reactivated = [
        issue
        for issue in issues
        if issue.get("age_days", 0) > 365
        and issue.get("days_since_update", 0) < 90
        and issue.get("reactivation_bonus", 0) > 0
        and not (
            issue.get("label_types", {}).get("has_pr")
            or issue.get("label_types", {}).get("good_first_issue")
        )
    ]
    return sorted(
        reactivated,
        key=lambda issue: (-issue.get("reactivation_bonus", 0), issue.get("days_since_update", 0)),
    )[:10]


def calculate_statistics(issues: List[IssueData]) -> Dict[str, Any]:
    """Calculate report statistics."""
    total = len(issues)
    if total == 0:
        return {
            'total': 0, 'bugs': 0, 'enhancements': 0, 'assigned': 0,
            'tracked': 0, 'orphaned': 0,
            'avg_age': 0, 'avg_comments': 0, 'active': 0, 'active_week': 0, 'stale': 0, 'has_pr': 0,
            'age_distribution': [0, 0, 0, 0, 0, 0],
            'categories': {}
        }
    
    bugs = sum(1 for i in issues if i.get("label_types", {}).get("bug"))
    enhancements = sum(1 for i in issues if i.get("label_types", {}).get("enhancement"))
    assigned = sum(1 for i in issues if i.get("is_assigned"))
    tracked = sum(1 for i in issues if i.get("is_internally_tracked", False))
    orphaned = sum(
        1
        for i in issues
        if not i.get("is_internally_tracked", False)
        and not i.get("is_blocked", False)
        and not i.get("label_types", {}).get("has_pr", False)
    )
    avg_age = sum(i.get("age_days", 0) for i in issues) / total
    avg_comments = sum(i.get("comments", 0) for i in issues) / total
    active = sum(1 for i in issues if i.get("days_since_update", 0) < 30)
    active_week = sum(1 for i in issues if i.get("days_since_update", 0) < 7)
    stale = sum(1 for i in issues if i.get("days_since_update", 0) > 180)
    has_pr = sum(1 for i in issues if i.get("label_types", {}).get("has_pr"))
    
    # Age distribution
    age_ranges = [
        sum(1 for i in issues if i.get("age_days", 0) < 30),
        sum(1 for i in issues if 30 <= i.get("age_days", 0) < 90),
        sum(1 for i in issues if 90 <= i.get("age_days", 0) < 180),
        sum(1 for i in issues if 180 <= i.get("age_days", 0) < 365),
        sum(1 for i in issues if 365 <= i.get("age_days", 0) < 730),
        sum(1 for i in issues if i.get("age_days", 0) >= 730),
    ]
    
    # Category breakdown
    categories: Dict[str, Dict[str, int]] = {}
    for issue in issues:
        cat = issue.get("category", "Unknown")
        if cat not in categories:
            categories[cat] = {"total": 0, "bugs": 0, "enhancements": 0, "stale": 0}
        categories[cat]["total"] += 1
        if issue.get("label_types", {}).get("bug"):
            categories[cat]["bugs"] += 1
        if issue.get("label_types", {}).get("enhancement"):
            categories[cat]["enhancements"] += 1
        if issue.get("days_since_update", 0) > 180:
            categories[cat]["stale"] += 1
    
    return {
        'total': total,
        'bugs': bugs,
        'enhancements': enhancements,
        'assigned': assigned,
        'tracked': tracked,
        'orphaned': orphaned,
        'avg_age': avg_age,
        'avg_comments': avg_comments,
        'active': active,
        'active_week': active_week,
        'stale': stale,
        'has_pr': has_pr,
        'age_distribution': age_ranges,
        'categories': categories
    }


def generate_html_content(issues: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
    """Generate the full HTML content."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get top issues
    top_issues = sorted(issues, key=lambda x: x.get("priority_score", 0), reverse=True)[:10]
    
    # Get quick wins
    quick_wins = [i for i in issues if 
        i.get("label_types", {}).get("small") or 
        i.get("label_types", {}).get("has_pr") or
        i.get("label_types", {}).get("good_first_issue")][:10]
    
    # Get attention needed
    attention_needed = [i for i in issues if 
        i.get("days_since_update", 0) > 180 and 
        i.get("comments", 0) >= 3 and 
        not i.get("is_assigned")]
    attention_needed = sorted(attention_needed, key=lambda x: x.get("comments", 0), reverse=True)[:10]
    
    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for issue in issues:
        cat = issue.get("category", "Unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(issue)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform Provider Google - Issues Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    {get_css_styles()}
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Terraform Provider Google</h1>
            <h2>Issues Analysis Report</h2>
            <p class="timestamp">Generated: {timestamp}</p>
            <p class="meta">Total Issues Analyzed: <strong>{stats['total']}</strong> | Confidence Threshold: ≥{MIN_CONFIDENCE_THRESHOLD}%</p>
        </header>

        {generate_executive_summary_html(stats)}

        {generate_backlog_trend_html(stats.get('history', []))}
        
        <div class="charts-row">
            {generate_charts_html(stats)}
        </div>

        {generate_contributor_entry_points_html(issues)}

        <div class="report-toggle-row">
            <button id="issues-band-toggle-global" class="issues-toggle-button" type="button">Showing all issues  ▾</button>
        </div>
        
        {generate_quick_wins_html(quick_wins)}
        
        {generate_attention_needed_html(attention_needed)}

        {generate_recently_reactivated_html(issues)}
        
        {generate_top_issues_html(top_issues)}
        
        {generate_category_sections_html(by_category)}
        
        <footer>
            <p>Report generated by <strong>Terraform Issues Analyzer</strong></p>
            <p>Data source: <a href="https://github.com/hashicorp/terraform-provider-google/issues" target="_blank">GitHub Issues</a></p>
        </footer>
    </div>
    
    {get_chart_scripts(stats)}
</body>
</html>'''
    
    return html


def get_css_styles() -> str:
    """Return the CSS styles for the report."""
    return '''<style>
        :root {
            --primary-color: #7c3aed;
            --primary-light: #a78bfa;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --info-color: #3b82f6;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-color: #1e293b;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
            color: white;
            border-radius: 16px;
        }
        
        header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        header h2 {
            font-size: 1.5rem;
            font-weight: 400;
            opacity: 0.9;
        }
        
        header .timestamp {
            margin-top: 1rem;
            opacity: 0.8;
        }
        
        header .meta {
            margin-top: 0.5rem;
            font-size: 1.1rem;
        }
        
        .card {
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .card h3 {
            color: var(--primary-color);
            margin-bottom: 1rem;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }
        
        .stat-card {
            background: var(--bg-color);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        
        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
        }
        
        .stat-card .label {
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        
        .stat-card.bugs .value { color: var(--danger-color); }
        .stat-card.enhancements .value { color: var(--success-color); }
        .stat-card.stale .value { color: var(--warning-color); }
        .stat-card.active .value { color: var(--info-color); }
        .stat-card.has-pr .value { color: var(--success-color); }
        .stat-card.active-week .value { color: var(--primary-color); }
        .stat-card.active-week-zero .value { color: var(--text-muted); }
        .stat-card.orphaned-warning .value { color: #b45309; }

        .trend-placeholder {
            text-align: center;
            color: #94a3b8;
            font-style: italic;
            padding: 2rem;
        }

        .trend-chart-wrapper {
            height: 220px;
        }

        .entry-points-card {
            border-left: 4px solid #22c55e;
        }
        
        .charts-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .chart-container {
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 1.5rem;
        }
        
        .chart-container h3 {
            color: var(--primary-color);
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        th {
            background: var(--bg-color);
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }
        
        tr:hover {
            background: var(--bg-color);
        }
        
        a {
            color: var(--primary-color);
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .badge-bug {
            background: #fef2f2;
            color: var(--danger-color);
        }
        
        .badge-enhancement {
            background: #ecfdf5;
            color: var(--success-color);
        }
        
        .badge-stale {
            background: #fffbeb;
            color: var(--warning-color);
        }
        
        .badge-active {
            background: #eff6ff;
            color: var(--info-color);
        }
        
        .badge-pr {
            background: #f3e8ff;
            color: var(--primary-color);
        }

        .badge-tracked {
            background: #eff6ff;
            color: #1e40af;
            border: 1px solid #bfdbfe;
        }

        .badge-crash {
            background: #fef2f2;
            color: #7f1d1d;
            border: 1px solid #fca5a5;
            font-weight: 700;
        }

        .badge-breaking {
            background: #fff1f2;
            color: #9f1239;
            border: 1px solid #fda4af;
            font-weight: 700;
        }

        .badge-new-resource {
            background: #f0fdf4;
            color: #166534;
            border: 1px solid #86efac;
        }

        .badge-exempt {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fca5a5;
        }

        .badge-upstream {
            background: #fef9c3;
            color: #854d0e;
            border: 1px solid #fde047;
        }

        .badge-confidence-high {
            background: #dcfce7;
            color: #166534;
        }

        .badge-confidence-review {
            background: #fef3c7;
            color: #92400e;
        }

        .detailed-issues-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .detailed-issues-header h3 {
            margin-bottom: 0;
        }

        .issues-toggle-button {
            background: var(--primary-color);
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 0.4rem 1rem;
            cursor: pointer;
            font-size: 0.9rem;
            white-space: nowrap;
        }

        .report-toggle-row {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 1rem;
        }

        .subcategory-badge {
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            margin-left: 0.4rem;
            vertical-align: middle;
        }

        .recaptcha-badge {
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
        }

        .subcategory-note {
            font-size: 0.85rem;
            color: #64748b;
            margin: -0.5rem 0 1rem 0;
            padding: 0.5rem 0.75rem;
            border-left: 3px solid #fde68a;
            background: #fffbeb;
        }

        .reactivated-card {
            border-left: 4px solid #f59e0b;
        }
        
        .priority-bar {
            width: 60px;
            height: 8px;
            background: var(--border-color);
            border-radius: 4px;
            overflow: hidden;
            display: inline-block;
            vertical-align: middle;
            margin-right: 0.5rem;
        }
        
        .priority-fill {
            height: 100%;
            border-radius: 4px;
            background: linear-gradient(90deg, var(--success-color), var(--warning-color), var(--danger-color));
        }
        
        details {
            margin-bottom: 1rem;
        }
        
        details summary {
            cursor: pointer;
            padding: 1rem;
            background: var(--bg-color);
            border-radius: 8px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        details summary:hover {
            background: var(--border-color);
        }
        
        details[open] summary {
            border-radius: 8px 8px 0 0;
            margin-bottom: 0;
        }
        
        details .content {
            padding: 1rem;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-top: none;
            border-radius: 0 0 8px 8px;
        }
        
        .category-badge {
            display: inline-block;
            padding: 0.125rem 0.5rem;
            background: var(--bg-color);
            border-radius: 4px;
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        
        footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            margin-top: 2rem;
        }
        
        @media print {
            body {
                background: white;
            }
            
            .container {
                max-width: none;
                padding: 0;
            }
            
            header {
                background: var(--primary-color) !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            .card, .chart-container {
                box-shadow: none;
                border: 1px solid var(--border-color);
                break-inside: avoid;
            }
            
            details {
                display: block !important;
            }
            
            details summary {
                display: none;
            }
            
            details .content {
                display: block !important;
                border: none;
                padding: 0;
            }
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            header h1 {
                font-size: 1.75rem;
            }
            
            .charts-row {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            table {
                font-size: 0.8rem;
            }
            
            th, td {
                padding: 0.5rem;
            }
        }
    </style>'''


def generate_executive_summary_html(stats: Dict[str, Any]) -> str:
    """Generate the executive summary section."""
    total = stats['total']
    bugs_pct = (stats['bugs'] / total * 100) if total else 0
    enh_pct = (stats['enhancements'] / total * 100) if total else 0
    tracked = stats.get('tracked', 0)
    orphaned = stats.get('orphaned', 0)
    has_pr_count = stats.get('has_pr', 0)
    active_week_count = stats.get('active_week', 0)
    tracked_pct = (tracked / total * 100) if total else 0
    orphaned_card_class = "stat-card orphaned-warning" if orphaned > 20 else "stat-card"
    has_pr_card_class = "stat-card has-pr" if has_pr_count > 0 else "stat-card"
    active_week_card_class = "stat-card active-week" if active_week_count > 0 else "stat-card active-week-zero"
    
    return f'''
        <div class="card">
            <h3>📊 Executive Summary</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">{stats['total']}</div>
                    <div class="label">Total Issues</div>
                </div>
                <div class="stat-card bugs">
                    <div class="value">{stats['bugs']}</div>
                    <div class="label">🐛 Bugs ({bugs_pct:.0f}%)</div>
                </div>
                <div class="stat-card enhancements">
                    <div class="value">{stats['enhancements']}</div>
                    <div class="label">✨ Enhancements ({enh_pct:.0f}%)</div>
                </div>
                <div class="stat-card">
                    <div class="value">{tracked}</div>
                    <div class="label">🔖 Tracked ({tracked_pct:.0f}%)<br><small>HashiCorp backlog</small></div>
                </div>
                <div class="{orphaned_card_class}">
                    <div class="value">{orphaned}</div>
                    <div class="label">👻 Orphaned<br><small>Needs a champion</small></div>
                </div>
                <div class="stat-card">
                    <div class="value">{format_age(int(stats['avg_age']))}</div>
                    <div class="label">📅 Avg Age</div>
                </div>
                <div class="{has_pr_card_class}">
                    <div class="value">{has_pr_count}</div>
                    <div class="label">🔗 Has PR<br><small>Work already started</small></div>
                </div>
                <div class="stat-card active">
                    <div class="value">{stats['active']}</div>
                    <div class="label">🔥 Active (&lt;30d)</div>
                </div>
                <div class="{active_week_card_class}">
                    <div class="value">{active_week_count}</div>
                    <div class="label">⚡ Active<br><small>Updated last 7 days</small></div>
                </div>
                <div class="stat-card stale">
                    <div class="value">{stats['stale']}</div>
                    <div class="label">💤 Stale (&gt;180d)</div>
                </div>
            </div>
        </div>'''


def generate_backlog_trend_html(history: List[Dict[str, Any]]) -> str:
    """Generate backlog trend section using historical snapshots."""
    if len(history) < 2:
        return '''
        <div class="card">
            <h3>📈 Backlog Trend</h3>
            <p class="trend-placeholder">Trend data will appear after 2+ report runs.</p>
        </div>'''

    return '''
        <div class="card">
            <h3>📈 Backlog Trend</h3>
            <div class="trend-chart-wrapper">
                <canvas id="trendChart"></canvas>
            </div>
        </div>'''


def generate_charts_html(stats: Dict[str, Any]) -> str:
    """Generate the charts section."""
    history_rows = ""
    category_rows = ""
    for row in stats.get("history", []):
        history_rows += (
            f"<tr><td>{row.get('date', '')}</td><td>{row.get('total', 0)}</td>"
            f"<td>{row.get('high_confidence', 0)}</td><td>{row.get('review', 0)}</td></tr>"
        )

    for category, values in stats.get("categories", {}).items():
        category_rows += (
            f"<tr><td>{category}</td><td>{values.get('bugs', 0)}</td>"
            f"<td>{values.get('enhancements', 0)}</td></tr>"
        )

    return '''
        <div class="chart-container">
            <h3>📅 Issue Age Distribution</h3>
            <canvas id="ageChart"></canvas>
            <noscript>
                <table>
                    <thead><tr><th>Range</th><th>Count</th></tr></thead>
                    <tbody>
                        <tr><td>&lt; 30 days</td><td>{age_0}</td></tr>
                        <tr><td>1-3 months</td><td>{age_1}</td></tr>
                        <tr><td>3-6 months</td><td>{age_2}</td></tr>
                        <tr><td>6-12 months</td><td>{age_3}</td></tr>
                        <tr><td>1-2 years</td><td>{age_4}</td></tr>
                        <tr><td>&gt; 2 years</td><td>{age_5}</td></tr>
                    </tbody>
                </table>
            </noscript>
        </div>
        <div class="chart-container">
            <h3>📁 Issues by Category</h3>
            <canvas id="categoryChart"></canvas>
            <noscript>
                <table>
                    <thead><tr><th>Category</th><th>Bugs</th><th>Enhancements</th></tr></thead>
                    <tbody>{category_rows}</tbody>
                </table>
            </noscript>
        </div>
        </div>'''.format(
        age_0=stats["age_distribution"][0],
        age_1=stats["age_distribution"][1],
        age_2=stats["age_distribution"][2],
        age_3=stats["age_distribution"][3],
        age_4=stats["age_distribution"][4],
        age_5=stats["age_distribution"][5],
        history_rows=history_rows,
        category_rows=category_rows,
    )


def generate_quick_wins_html(issues: List[Dict[str, Any]]) -> str:
    """Generate the quick wins section."""
    if not issues:
        return ''
    
    rows = ''
    for issue in issues:
        title = issue['title'][:60] + '...' if len(issue['title']) > 60 else issue['title']
        confidence_band = get_issue_confidence_band(issue)
        subcategory_badge = '<span class="subcategory-badge recaptcha-badge">🔑 reCAPTCHA</span>' if _is_recaptcha_issue(issue) else ''
        reason = []
        if issue.get("label_types", {}).get("small"):
            reason.append("Small Size")
        if issue.get("label_types", {}).get("has_pr"):
            reason.append("Has PR")
        if issue.get("label_types", {}).get("good_first_issue"):
            reason.append("Good First Issue")
        reason_str = ", ".join(reason) if reason else "Low Complexity"
        
        type_badges = [
            '<span class="badge badge-bug">🐛 Bug</span>'
            if issue.get("label_types", {}).get("bug")
            else '<span class="badge badge-enhancement">✨ Enhancement</span>'
        ]
        type_badges.extend(_get_blocking_badges(issue))
        
        rows += f'''
            <tr data-band="{confidence_band}">
                <td><a href="{issue['url']}" target="_blank">#{issue['number']}</a></td>
                <td>{title}{subcategory_badge}</td>
                <td><span class="category-badge">{issue['category']}</span></td>
                <td>{get_confidence_badge(issue.get('confidence', 0))}</td>
                <td>{reason_str}</td>
                <td>{format_age(issue.get('age_days', 0))}</td>
                <td>{' '.join(type_badges)}</td>
            </tr>'''
    
    return f'''
        <div class="card">
            <h3>🚀 Quick Wins (<span id="quick-wins-count">{len(issues)} issues</span>)</h3>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">Issues that may be easier to resolve (small size, has PR, or good first issue)</p>
            <table id="quick-wins-table">
                <thead>
                    <tr>
                        <th>Issue</th>
                        <th>Title</th>
                        <th>Category</th>
                        <th>Confidence</th>
                        <th>Reason</th>
                        <th>Age</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>'''


def generate_contributor_entry_points_html(issues: List[Dict[str, Any]]) -> str:
    """Generate curated contributor entry points section."""
    entry_points = [issue for issue in issues if _is_entry_point(issue)]
    entry_points = sorted(entry_points, key=lambda issue: issue.get("priority_score", 0), reverse=True)[:8]

    if not entry_points:
        return '''
        <div class="card entry-points-card">
            <h3>✅ 🎯 Contributor Entry Points</h3>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">Issues that are safe, scoped, and ready for a community contribution</p>
            <p>No entry-point issues identified this week.</p>
        </div>'''

    rows = ''
    for issue in entry_points:
        title = issue['title'][:60] + '...' if len(issue['title']) > 60 else issue['title']
        confidence_band = get_issue_confidence_band(issue)
        subcategory_badge = '<span class="subcategory-badge recaptcha-badge">🔑 reCAPTCHA</span>' if _is_recaptcha_issue(issue) else ''
        why = _get_entry_point_reason(issue)

        type_badges = [
            '<span class="badge badge-bug">🐛 Bug</span>'
            if issue.get("label_types", {}).get("bug")
            else '<span class="badge badge-enhancement">✨ Enhancement</span>'
        ]
        if issue.get("label_types", {}).get("documentation"):
            type_badges = ['<span class="badge badge-enhancement">📚 Docs</span>']
        type_badges.extend(_get_tracking_badges(issue))
        type_badges.extend(_get_blocking_badges(issue))

        rows += f'''
            <tr data-band="{confidence_band}">
                <td><a href="{issue['url']}" target="_blank">#{issue['number']}</a></td>
                <td>{title}{subcategory_badge}</td>
                <td>{why}</td>
                <td>{get_confidence_badge(issue.get('confidence', 0))}</td>
                <td>{issue.get('priority_score', 0):.0f}</td>
                <td>{format_age(issue.get('age_days', 0))}</td>
                <td>{' '.join(type_badges)}</td>
            </tr>'''

    return f'''
        <div class="card entry-points-card">
            <h3>✅ 🎯 Contributor Entry Points</h3>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">Issues that are safe, scoped, and ready for a community contribution</p>
            <table id="entry-points-table">
                <thead>
                    <tr>
                        <th>Issue</th>
                        <th>Title</th>
                        <th>Why</th>
                        <th>Confidence</th>
                        <th>Priority</th>
                        <th>Age</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>'''


def generate_attention_needed_html(issues: List[Dict[str, Any]]) -> str:
    """Generate the attention needed section."""
    if not issues:
        return ''
    
    rows = ''
    for issue in issues:
        title = issue['title'][:60] + '...' if len(issue['title']) > 60 else issue['title']
        confidence_band = get_issue_confidence_band(issue)
        subcategory_badge = '<span class="subcategory-badge recaptcha-badge">🔑 reCAPTCHA</span>' if _is_recaptcha_issue(issue) else ''
        type_badges = [
            '<span class="badge badge-bug">🐛 Bug</span>'
            if issue.get("label_types", {}).get("bug")
            else '<span class="badge badge-enhancement">✨ Enhancement</span>'
        ]
        type_badges.extend(_get_blocking_badges(issue))
        
        rows += f'''
            <tr data-band="{confidence_band}">
                <td><a href="{issue['url']}" target="_blank">#{issue['number']}</a></td>
                <td>{title}{subcategory_badge}</td>
                <td><span class="category-badge">{issue['category']}</span></td>
                <td>{get_confidence_badge(issue.get('confidence', 0))}</td>
                <td>{issue.get('comments', 0)}</td>
                <td>{format_age(issue.get('days_since_update', 0))} ago</td>
                <td>{' '.join(type_badges)}</td>
            </tr>'''
    
    return f'''
        <div class="card">
            <h3>⚠️ Attention Needed (<span id="attention-count">{len(issues)} issues</span>)</h3>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">Stale issues (&gt;6 months) with significant community interest (3+ comments) but no assignee</p>
            <table id="attention-table">
                <thead>
                    <tr>
                        <th>Issue</th>
                        <th>Title</th>
                        <th>Category</th>
                        <th>Confidence</th>
                        <th>Comments</th>
                        <th>Last Update</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>'''


def generate_top_issues_html(issues: List[Dict[str, Any]]) -> str:
    """Generate the top priority issues section."""
    rows = ''
    for i, issue in enumerate(issues, 1):
        title = issue['title'][:55] + '...' if len(issue['title']) > 55 else issue['title']
        priority = issue.get('priority_score', 0)
        confidence_band = get_issue_confidence_band(issue)
        subcategory_badge = '<span class="subcategory-badge recaptcha-badge">🔑 reCAPTCHA</span>' if _is_recaptcha_issue(issue) else ''
        
        badges = []
        if issue.get("label_types", {}).get("bug"):
            badges.append('<span class="badge badge-bug">🐛 Bug</span>')
        if issue.get("label_types", {}).get("enhancement"):
            badges.append('<span class="badge badge-enhancement">✨</span>')
        if issue.get("days_since_update", 0) > 180:
            badges.append('<span class="badge badge-stale">💤 Stale</span>')
        elif issue.get("days_since_update", 0) < 30:
            badges.append('<span class="badge badge-active">🔥 Active</span>')
        if issue.get("label_types", {}).get("has_pr"):
            badges.append('<span class="badge badge-pr">🔗 PR</span>')
        badges.extend(_get_blocking_badges(issue))
        
        badges_html = ' '.join(badges)
        
        rows += f'''
            <tr data-band="{confidence_band}">
                <td>{i}</td>
                <td><a href="{issue['url']}" target="_blank">#{issue['number']}</a></td>
                <td>{title}{subcategory_badge}</td>
                <td><span class="category-badge">{issue['category']}</span></td>
                <td>{get_confidence_badge(issue.get('confidence', 0))}</td>
                <td>
                    <span class="priority-bar"><span class="priority-fill" style="width: {priority}%"></span></span>
                    {priority:.0f}
                </td>
                <td>{format_age(issue.get('age_days', 0))}</td>
                <td>{badges_html}</td>
            </tr>'''
    
    return f'''
        <div class="card">
            <h3>🎯 Top 10 Priority Issues</h3>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Issue</th>
                        <th>Title</th>
                        <th>Category</th>
                        <th>Confidence</th>
                        <th>Priority</th>
                        <th>Age</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>'''


def generate_recently_reactivated_html(issues: List[Dict[str, Any]]) -> str:
    """Generate the recently reactivated section."""
    reactivated_issues = _get_recently_reactivated_issues(issues)

    rows = ''
    for issue in reactivated_issues:
        title = issue['title'][:60] + '...' if len(issue['title']) > 60 else issue['title']
        confidence_band = get_issue_confidence_band(issue)
        type_badges = [
            '<span class="badge badge-bug">🐛 Bug</span>'
            if issue.get("label_types", {}).get("bug")
            else '<span class="badge badge-enhancement">✨ Enhancement</span>'
        ]
        type_badges.extend(_get_blocking_badges(issue))

        rows += f'''
            <tr data-band="{confidence_band}">
                <td><a href="{issue['url']}" target="_blank">#{issue['number']}</a> 🔄</td>
                <td>{title}</td>
                <td><span class="category-badge">{issue['category']}</span></td>
                <td>{get_confidence_badge(issue.get('confidence', 0))}</td>
                <td>{format_age(issue.get('age_days', 0))}</td>
                <td>{format_age(issue.get('days_since_update', 0))} ago</td>
                <td>{' '.join(type_badges)}</td>
            </tr>'''

    if not rows:
        rows = '''
            <tr>
                <td colspan="7">No recently reactivated issues found this week.</td>
            </tr>'''

    return f'''
        <div class="card reactivated-card">
            <h3>🔄 Recently Reactivated</h3>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">Old issues (&gt;1 year) with significant new activity in the last 90 days - may indicate upstream API changes or newly GA features</p>
            <table>
                <thead>
                    <tr>
                        <th>Issue</th>
                        <th>Title</th>
                        <th>Category</th>
                        <th>Confidence</th>
                        <th>Age</th>
                        <th>Last Update</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>'''


def generate_category_sections_html(by_category: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate the collapsible category sections."""
    sections = ''
    total_issues = 0
    
    for category in sorted(by_category.keys()):
        issues = by_category[category]
        total_issues += len(issues)
        sorted_issues = sorted(issues, key=lambda x: x.get("priority_score", 0), reverse=True)
        subcategory_note = ''
        if category == "Cloud Armor":
            subcategory_note = (
                '<p class="subcategory-note">'
                '🔑 Issues tagged <strong>reCAPTCHA</strong> involve the reCAPTCHA Enterprise '
                'integration with Cloud Armor bot management - they use '
                '<code>google_recaptcha_enterprise_*</code> resources.'
                '</p>'
            )
        
        rows = ''
        for issue in sorted_issues:
            title = issue['title'][:50] + '...' if len(issue['title']) > 50 else issue['title']
            priority = issue.get('priority_score', 0)
            confidence_band = get_issue_confidence_band(issue)
            subcategory_badge = '<span class="subcategory-badge recaptcha-badge">🔑 reCAPTCHA</span>' if _is_recaptcha_issue(issue) else ''
            
            type_badges: List[str] = []
            if issue.get("label_types", {}).get("bug"):
                type_badges.append('<span class="badge badge-bug">🐛 Bug</span>')
            elif issue.get("label_types", {}).get("enhancement"):
                type_badges.append('<span class="badge badge-enhancement">✨ Enhancement</span>')
            elif issue.get("label_types", {}).get("documentation"):
                type_badges.append('<span class="badge badge-enhancement">📚 Docs</span>')
            type_badges.extend(_get_tracking_badges(issue))
            type_badges.extend(_get_blocking_badges(issue))
            
            status_icons = []
            if issue.get("days_since_update", 0) > 180:
                status_icons.append('💤')
            elif issue.get("days_since_update", 0) < 30:
                status_icons.append('🔥')
            if issue.get("label_types", {}).get("has_pr"):
                status_icons.append('🔗')
            
            status_html = ' '.join(status_icons)
            
            rows += f'''
                <tr data-band="{confidence_band}">
                    <td><a href="{issue['url']}" target="_blank">#{issue['number']}</a></td>
                    <td>{title}{subcategory_badge}</td>
                    <td>
                        <span class="priority-bar"><span class="priority-fill" style="width: {priority}%"></span></span>
                        {priority:.0f}
                    </td>
                    <td>{get_confidence_badge(issue.get('confidence', 0))}</td>
                    <td>{format_age(issue.get('age_days', 0))}</td>
                    <td>{format_age(issue.get('days_since_update', 0))} ago {status_html}</td>
                    <td>{' '.join(type_badges)}</td>
                </tr>'''
        
        sections += f'''
        <details>
            <summary>📁 {category} (<span class="section-issue-count">{len(issues)} issues</span>)</summary>
            <div class="content">
                {subcategory_note}
                <table>
                    <thead>
                        <tr>
                            <th>Issue</th>
                            <th>Title</th>
                            <th>Priority</th>
                            <th>Confidence</th>
                            <th>Age</th>
                            <th>Updated</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </details>'''
    
    return f'''
        <div class="card">
            <div class="detailed-issues-header">
                <h3>📋 Detailed Issues by Category (<span id="detail-count">{total_issues} issues</span>)</h3>
                <button id="issues-band-toggle" class="issues-toggle-button" type="button">Showing all issues  ▾</button>
            </div>
            {sections}
        </div>'''


def get_chart_scripts(stats: Dict[str, Any]) -> str:
    """Generate the Chart.js initialization scripts."""
    age_data = stats['age_distribution']
    
    # Category data
    cat_labels = list(stats['categories'].keys())
    cat_bugs = [stats['categories'][c]['bugs'] for c in cat_labels]
    cat_enhancements = [stats['categories'][c]['enhancements'] for c in cat_labels]
    history = stats.get('history', [])
    trend_data = json.dumps(history)
    
    return f'''
    <script>
        let highOnlyMode = false;
        const trendData = {trend_data};

        function updateToggleLabels() {{
            const text = highOnlyMode ? 'HIGH confidence only  ▾' : 'Showing all issues  ▾';
            const globalToggle = document.getElementById('issues-band-toggle-global');
            const detailToggle = document.getElementById('issues-band-toggle');
            if (globalToggle) {{
                globalToggle.textContent = text;
            }}
            if (detailToggle) {{
                detailToggle.textContent = text;
            }}
        }}

        function updateVisibleIssueCounters() {{
            const quickWinsVisible = document.querySelectorAll('#quick-wins-table tbody tr[data-band]:not([style*="display: none"])').length;
            const quickWinsCount = document.getElementById('quick-wins-count');
            if (quickWinsCount) {{
                quickWinsCount.textContent = `${{quickWinsVisible}} issues`;
            }}

            const attentionVisible = document.querySelectorAll('#attention-table tbody tr[data-band]:not([style*="display: none"])').length;
            const attentionCount = document.getElementById('attention-count');
            if (attentionCount) {{
                attentionCount.textContent = `${{attentionVisible}} issues`;
            }}

            const visibleDetailedRows = document.querySelectorAll('details tbody tr[data-band]:not([style*="display: none"])');
            const detailedCount = document.getElementById('detail-count');
            if (detailedCount) {{
                detailedCount.textContent = `${{visibleDetailedRows.length}} issues`;
            }}

            document.querySelectorAll('details').forEach((detailsEl) => {{
                const summaryCount = detailsEl.querySelector('.section-issue-count');
                if (!summaryCount) {{
                    return;
                }}
                const visibleRows = detailsEl.querySelectorAll('tbody tr[data-band]:not([style*="display: none"])').length;
                summaryCount.textContent = `${{visibleRows}} issues`;
            }});
        }}

        function toggleConfidenceBand() {{
            highOnlyMode = !highOnlyMode;
            const reviewRows = document.querySelectorAll('tr[data-band="REVIEW"]');
            reviewRows.forEach((row) => {{
                row.style.display = highOnlyMode ? 'none' : '';
            }});

            updateToggleLabels();
            updateVisibleIssueCounters();
        }}

        const issuesBandToggleGlobal = document.getElementById('issues-band-toggle-global');
        if (issuesBandToggleGlobal) {{
            issuesBandToggleGlobal.addEventListener('click', toggleConfidenceBand);
        }}
        const issuesBandToggle = document.getElementById('issues-band-toggle');
        if (issuesBandToggle) {{
            issuesBandToggle.addEventListener('click', toggleConfidenceBand);
        }}
        updateToggleLabels();
        updateVisibleIssueCounters();

        if (typeof window.Chart === 'undefined') {{
            document.querySelectorAll('canvas').forEach((canvas) => {{
                const message = document.createElement('p');
                message.style.color = '#92400e';
                message.textContent = 'Chart.js unavailable; showing table fallback where provided.';
                canvas.replaceWith(message);
            }});
        }} else {{
        // Age Distribution Chart
        const ageCtx = document.getElementById('ageChart').getContext('2d');
        new Chart(ageCtx, {{
            type: 'bar',
            data: {{
                labels: ['< 30 days', '1-3 months', '3-6 months', '6-12 months', '1-2 years', '> 2 years'],
                datasets: [{{
                    label: 'Issues',
                    data: {age_data},
                    backgroundColor: [
                        '#10b981',
                        '#3b82f6',
                        '#8b5cf6',
                        '#f59e0b',
                        '#ef4444',
                        '#6b7280'
                    ],
                    borderRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 10
                        }}
                    }}
                }}
            }}
        }});
        
        // Category Chart
        const catCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(catCtx, {{
            type: 'bar',
            data: {{
                labels: {cat_labels},
                datasets: [
                    {{
                        label: 'Bugs',
                        data: {cat_bugs},
                        backgroundColor: '#ef4444',
                        borderRadius: 6
                    }},
                    {{
                        label: 'Enhancements',
                        data: {cat_enhancements},
                        backgroundColor: '#10b981',
                        borderRadius: 6
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }},
                scales: {{
                    x: {{
                        stacked: true
                    }},
                    y: {{
                        stacked: true,
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Backlog Trend Chart
        const trendCanvas = document.getElementById('trendChart');
        if (trendCanvas && trendData.length >= 2) {{
            const trendCtx = trendCanvas.getContext('2d');
            const trendLabels = trendData.map((row) => row.date || '');
            const totalSeries = trendData.map((row) => row.total || 0);
            const highSeries = trendData.map((row) => row.high_confidence || 0);
            const reviewSeries = trendData.map((row) => row.review || 0);
            new Chart(trendCtx, {{
                type: 'line',
                data: {{
                    labels: trendLabels,
                    datasets: [
                        {{
                            label: 'Total Issues',
                            data: totalSeries,
                            borderColor: '#7c3aed',
                            backgroundColor: 'rgba(124, 58, 237, 0.08)',
                            pointRadius: 4,
                            tension: 0.3,
                            fill: false
                        }},
                        {{
                            label: 'HIGH Confidence',
                            data: highSeries,
                            borderColor: '#22c55e',
                            backgroundColor: 'rgba(34, 197, 94, 0.08)',
                            pointRadius: 4,
                            tension: 0.3,
                            fill: false
                        }},
                        {{
                            label: 'REVIEW Confidence',
                            data: reviewSeries,
                            borderColor: '#f59e0b',
                            backgroundColor: 'rgba(245, 158, 11, 0.08)',
                            pointRadius: 4,
                            tension: 0.3,
                            fill: false
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: false,
                            ticks: {{
                                stepSize: 1
                            }}
                        }}
                    }}
                }}
            }});
        }}
        }}
    </script>'''
