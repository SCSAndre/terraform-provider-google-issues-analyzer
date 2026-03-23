"""
HTML Report Generator for Terraform Issues Analyzer.

Generates professional HTML reports with interactive charts and styling.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from config import HIGH_CONFIDENCE_THRESHOLD, MEDIUM_CONFIDENCE_THRESHOLD, MIN_CONFIDENCE_THRESHOLD
from types_definitions import IssueData
from utils import format_age


def generate_html_report(issues: List[IssueData], output_dir: Path) -> Path:
    """Generate an HTML report from the analyzed issues."""
    output_path = output_dir / "terraform_issues_report.html"
    history = load_history(output_dir / "history.json")

    # Calculate statistics
    stats = calculate_statistics(issues)
    stats["history"] = history
    generic_issues: List[Dict[str, Any]] = [dict(issue) for issue in issues]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(generate_html_content(generic_issues, stats))

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
        import json

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


def calculate_statistics(issues: List[IssueData]) -> Dict[str, Any]:
    """Calculate report statistics."""
    total = len(issues)
    if total == 0:
        return {
            'total': 0, 'bugs': 0, 'enhancements': 0, 'assigned': 0,
            'avg_age': 0, 'avg_comments': 0, 'active': 0, 'stale': 0, 'has_pr': 0,
            'age_distribution': [0, 0, 0, 0, 0, 0],
            'categories': {}
        }
    
    bugs = sum(1 for i in issues if i.get("label_types", {}).get("bug"))
    enhancements = sum(1 for i in issues if i.get("label_types", {}).get("enhancement"))
    assigned = sum(1 for i in issues if i.get("is_assigned"))
    avg_age = sum(i.get("age_days", 0) for i in issues) / total
    avg_comments = sum(i.get("comments", 0) for i in issues) / total
    active = sum(1 for i in issues if i.get("days_since_update", 0) < 30)
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
        'avg_age': avg_age,
        'avg_comments': avg_comments,
        'active': active,
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
        
        <div class="charts-row">
            {generate_charts_html(stats)}
        </div>
        
        {generate_quick_wins_html(quick_wins)}
        
        {generate_attention_needed_html(attention_needed)}
        
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
    assigned_pct = (stats['assigned'] / total * 100) if total else 0
    
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
                    <div class="value">{stats['assigned']}</div>
                    <div class="label">👤 Assigned ({assigned_pct:.0f}%)</div>
                </div>
                <div class="stat-card">
                    <div class="value">{format_age(int(stats['avg_age']))}</div>
                    <div class="label">📅 Avg Age</div>
                </div>
                <div class="stat-card">
                    <div class="value">{stats['avg_comments']:.1f}</div>
                    <div class="label">💬 Avg Comments</div>
                </div>
                <div class="stat-card active">
                    <div class="value">{stats['active']}</div>
                    <div class="label">🔥 Active (&lt;30d)</div>
                </div>
                <div class="stat-card stale">
                    <div class="value">{stats['stale']}</div>
                    <div class="label">💤 Stale (&gt;180d)</div>
                </div>
                <div class="stat-card">
                    <div class="value">{stats['has_pr']}</div>
                    <div class="label">🔗 Has PR</div>
                </div>
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
        <div class="chart-container">
            <h3>📈 Issue Trend</h3>
            <canvas id="trendChart"></canvas>
            <noscript>
                <table>
                    <thead><tr><th>Date</th><th>Total</th><th>High</th><th>Review</th></tr></thead>
                    <tbody>{history_rows}</tbody>
                </table>
            </noscript>
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
        reason = []
        if issue.get("label_types", {}).get("small"):
            reason.append("Small Size")
        if issue.get("label_types", {}).get("has_pr"):
            reason.append("Has PR")
        if issue.get("label_types", {}).get("good_first_issue"):
            reason.append("Good First Issue")
        reason_str = ", ".join(reason) if reason else "Low Complexity"
        
        type_badge = '<span class="badge badge-bug">🐛 Bug</span>' if issue.get("label_types", {}).get("bug") else '<span class="badge badge-enhancement">✨ Enhancement</span>'
        
        rows += f'''
            <tr data-band="{confidence_band}">
                <td><a href="{issue['url']}" target="_blank">#{issue['number']}</a></td>
                <td>{title}</td>
                <td><span class="category-badge">{issue['category']}</span></td>
                <td>{get_confidence_badge(issue.get('confidence', 0))}</td>
                <td>{reason_str}</td>
                <td>{format_age(issue.get('age_days', 0))}</td>
                <td>{type_badge}</td>
            </tr>'''
    
    return f'''
        <div class="card">
            <h3>🚀 Quick Wins</h3>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">Issues that may be easier to resolve (small size, has PR, or good first issue)</p>
            <table>
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


def generate_attention_needed_html(issues: List[Dict[str, Any]]) -> str:
    """Generate the attention needed section."""
    if not issues:
        return ''
    
    rows = ''
    for issue in issues:
        title = issue['title'][:60] + '...' if len(issue['title']) > 60 else issue['title']
        confidence_band = get_issue_confidence_band(issue)
        type_badge = '<span class="badge badge-bug">🐛 Bug</span>' if issue.get("label_types", {}).get("bug") else '<span class="badge badge-enhancement">✨ Enhancement</span>'
        
        rows += f'''
            <tr data-band="{confidence_band}">
                <td><a href="{issue['url']}" target="_blank">#{issue['number']}</a></td>
                <td>{title}</td>
                <td><span class="category-badge">{issue['category']}</span></td>
                <td>{get_confidence_badge(issue.get('confidence', 0))}</td>
                <td>{issue.get('comments', 0)}</td>
                <td>{format_age(issue.get('days_since_update', 0))} ago</td>
                <td>{type_badge}</td>
            </tr>'''
    
    return f'''
        <div class="card">
            <h3>⚠️ Attention Needed</h3>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">Stale issues (&gt;6 months) with significant community interest (3+ comments) but no assignee</p>
            <table>
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
        
        badges_html = ' '.join(badges)
        
        rows += f'''
            <tr data-band="{confidence_band}">
                <td>{i}</td>
                <td><a href="{issue['url']}" target="_blank">#{issue['number']}</a></td>
                <td>{title}</td>
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


def generate_category_sections_html(by_category: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate the collapsible category sections."""
    sections = ''
    total_issues = 0
    
    for category in sorted(by_category.keys()):
        issues = by_category[category]
        total_issues += len(issues)
        sorted_issues = sorted(issues, key=lambda x: x.get("priority_score", 0), reverse=True)
        
        rows = ''
        for issue in sorted_issues:
            title = issue['title'][:50] + '...' if len(issue['title']) > 50 else issue['title']
            priority = issue.get('priority_score', 0)
            confidence_band = get_issue_confidence_band(issue)
            
            type_icon = ''
            if issue.get("label_types", {}).get("bug"):
                type_icon = '🐛'
            elif issue.get("label_types", {}).get("enhancement"):
                type_icon = '✨'
            elif issue.get("label_types", {}).get("documentation"):
                type_icon = '📚'
            
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
                    <td>{title}</td>
                    <td>
                        <span class="priority-bar"><span class="priority-fill" style="width: {priority}%"></span></span>
                        {priority:.0f}
                    </td>
                    <td>{get_confidence_badge(issue.get('confidence', 0))}</td>
                    <td>{format_age(issue.get('age_days', 0))}</td>
                    <td>{format_age(issue.get('days_since_update', 0))} ago {status_html}</td>
                    <td>{type_icon}</td>
                </tr>'''
        
        sections += f'''
        <details>
            <summary>📁 {category} (<span class="section-issue-count">{len(issues)} issues</span>)</summary>
            <div class="content">
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
                <h3>📋 Detailed Issues by Category (<span id="detailed-issues-visible-count">{total_issues} issues</span>)</h3>
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
    trend_labels = [row.get('date', '') for row in history]
    trend_totals = [row.get('total', 0) for row in history]
    
    return f'''
    <script>
        let showingHighOnly = false;

        function updateVisibleIssueCounters() {{
            const detailedRows = document.querySelectorAll('details tbody tr[data-band]');
            const visibleDetailedRows = document.querySelectorAll('details tbody tr[data-band]:not([style*="display: none"])');
            const detailedCount = document.getElementById('detailed-issues-visible-count');
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

        function toggleReviewRows() {{
            showingHighOnly = !showingHighOnly;
            const reviewRows = document.querySelectorAll('tr[data-band="REVIEW"]');
            reviewRows.forEach((row) => {{
                row.style.display = showingHighOnly ? 'none' : '';
            }});

            const toggleButton = document.getElementById('issues-band-toggle');
            if (toggleButton) {{
                toggleButton.textContent = showingHighOnly ? 'HIGH confidence only  ▾' : 'Showing all issues  ▾';
            }}
            updateVisibleIssueCounters();
        }}

        const issuesBandToggle = document.getElementById('issues-band-toggle');
        if (issuesBandToggle) {{
            issuesBandToggle.addEventListener('click', toggleReviewRows);
        }}
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

        // Trend Chart
        const trendCanvas = document.getElementById('trendChart');
        if (trendCanvas) {{
            const trendCtx = trendCanvas.getContext('2d');
            new Chart(trendCtx, {{
                type: 'line',
                data: {{
                    labels: {trend_labels},
                    datasets: [{{
                        label: 'Total Issues',
                        data: {trend_totals},
                        borderColor: '#7c3aed',
                        backgroundColor: 'rgba(124, 58, 237, 0.2)',
                        fill: true,
                        tension: 0.2
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ legend: {{ display: true }} }},
                    scales: {{ y: {{ beginAtZero: true }} }}
                }}
            }});
        }}
        }}
    </script>'''
