# Terraform Provider Google - Issue Analyzer

Analyzes open issues from the Terraform Provider Google repository to identify available issues related to:
- Load Balancers
- Cloud Armor
- Private Service Connect (PSC)

## Features

- **Intelligent Classification**: Uses TF-IDF and regex matching to identify relevant issues
- **Availability Checking**: Filters out issues that are already assigned or claimed
- **Confidence Scoring**: Provides confidence scores for issue categorization
- **Rate Limiting**: Respects GitHub API rate limits with automatic backoff
- **Comprehensive Reports**: Generates detailed markdown reports
- **Automated Reporting**: Built-in support for GitHub Actions and Cron jobs

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
(Optional) Set GitHub token for higher API rate limits:

Bash

export GITHUB_TOKEN="your_github_token_here"
Usage
1. Manual Execution
Quick Start: Run the provided shell script:

Bash

./run_report.sh
Python Direct: Alternatively, run the Python script directly:

Bash

python3 script.py
2. Automated Weekly Reports
You can schedule this tool to run automatically every Friday at 12:00 PM.

Option A: GitHub Actions (Recommended for Teams)
The project includes pre-configured workflows in .github/workflows/.

Push the code to your GitHub repository.

(Optional) Enable Email Reports:

Go to your Repository Settings → Secrets and variables → Actions.

Add the following repository secrets:

SMTP_USERNAME: Your sending email address (e.g., reports@company.com)

SMTP_PASSWORD: Your email password (or App Password for Gmail)

EMAIL_RECIPIENTS: Comma-separated list of recipients (e.g., team@company.com)

The workflow will run automatically every Friday at 12:00 UTC.

Option B: Local Cron Job (Linux/Mac)
To run this on a local server:

Edit your crontab:

Bash

crontab -e
Add the following line to run every Friday at noon:

Snippet de código

0 12 * * 5 /absolute/path/to/project/scheduled_report.sh
Note: Ensure scheduled_report.sh is executable (chmod +x scheduled_report.sh).

Output
The analysis generates a markdown report in the analysis_results/ directory:

terraform_target_services_issues_report_en.md - Main report with categorized issues

Each issue entry includes:

Issue number and title

Confidence score

Direct URL to GitHub issue

Creation date

Number of comments

Configuration
Edit config.py to customize:

MIN_CONFIDENCE_THRESHOLD - Minimum confidence score (default: 30)

HIGH_CONFIDENCE_THRESHOLD - High confidence threshold (default: 70)

COMMENT_THRESHOLD - Max comments for "available" issues (default: 5)

TFIDF_WEIGHT - Weight for TF-IDF scoring (default: 0.7)

REGEX_WEIGHT - Weight for regex scoring (default: 0.3)

Testing
Run unit tests:

Bash

python3 -m unittest discover -v
Project Structure
issues_analyzer/
├── config.py                    # Configuration settings
├── github_client.py             # GitHub API client
├── issue_classifier.py          # Issue classification logic
├── availability_checker.py      # Availability checking logic
├── service_definitions.py       # Service keywords and terms
├── report_generator.py          # Report generation
├── types_definitions.py         # Type definitions
├── script.py                    # Main execution script
├── run_report.sh               # Helper script for manual runs
├── scheduled_report.sh         # Helper script for Cron jobs
├── send_team_email.py          # Email distribution logic
└── requirements.txt            # Python dependencies
License
MIT License

Contributing
Contributions are welcome! Please feel free to submit a Pull Request.