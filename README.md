# 🔍 Terraform Provider Google - Issue Analyzer

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-239%20passed-brightgreen.svg)](https://github.com/SCSAndre/terraform-provider-google-issues-analyzer)
[![Coverage](https://img.shields.io/badge/coverage-78%25-green.svg)](https://github.com/SCSAndre/terraform-provider-google-issues-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent issue analyzer that identifies **open and available** issues from the [Terraform Provider Google](https://github.com/hashicorp/terraform-provider-google) repository, focusing on specific GCP services. Perfect for finding contribution opportunities or tracking issues relevant to your infrastructure.

## 🎯 What It Does

This tool automatically:
- **Scans** 2,000+ open issues from the Terraform Provider Google repository
- **Classifies** issues using ML-based TF-IDF and pattern matching
- **Filters** to show only *truly available* issues (no assigned, claimed, or in-progress)
- **Generates** detailed markdown reports grouped by service category

### Target Services
| Service | Description |
|---------|-------------|
| 🔄 **Load Balancers** | Regional/Global LBs, URL Maps, Backend Services, Health Checks |
| 🛡️ **Cloud Armor** | Security policies, WAF rules, DDoS protection |
| 🔗 **Private Service Connect** | PSC endpoints, forwarding rules, service attachments |

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/SCSAndre/terraform-provider-google-issues-analyzer.git
cd terraform-provider-google-issues-analyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Recommended) Set GitHub token for higher rate limits
export GITHUB_TOKEN="your_github_token_here"

# Run the analysis
python script.py
```

## 📊 Sample Output

```
Starting Terraform Provider Google issue analysis
Fetching issues from GitHub API
Progress: fetched 2300 issues
Analyzing issues for relevance and availability
Analysis complete: 42 relevant available issues found

Report generated: analysis_results/terraform_target_services_issues_report_en.md
```

The generated report includes:
- 📈 Summary table with issue counts per category
- 🎯 Confidence scores for each classification
- 🔗 Direct links to GitHub issues
- 📅 Creation dates and comment counts

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         script.py                               │
│                    (Main Entry Point)                           │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────────────┐
    ▼             ▼             ▼                     ▼
┌─────────┐ ┌───────────┐ ┌────────────┐ ┌──────────────────┐
│ GitHub  │ │  Issue    │ │Availability│ │     Report       │
│ Client  │ │Classifier │ │  Checker   │ │    Generator     │
└────┬────┘ └─────┬─────┘ └─────┬──────┘ └────────┬─────────┘
     │            │             │                  │
     │     ┌──────┴──────┐      │                  │
     │     │ TF-IDF      │      │                  │
     │     │ + Regex     │      │                  │
     │     │ Scoring     │      │                  │
     │     └─────────────┘      │                  │
     ▼                          ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Definitions                          │
│         (Keywords, patterns, terms per service)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `github_client.py` | GitHub API client with rate limiting, retries, and caching |
| `issue_classifier.py` | TF-IDF + regex-based classification with confidence scoring |
| `availability_checker.py` | Determines if an issue is truly available for contribution |
| `report_generator.py` | Generates structured markdown reports |
| `config.py` | Configuration management with validation |
| `exceptions.py` | Custom exception hierarchy for precise error handling |
| `logging_config.py` | Structured logging with JSON/console output |
| `validators.py` | Input validation and sanitization |

## 🔧 Configuration

Environment variables:

```bash
# Required for higher API rate limits (optional but recommended)
export GITHUB_TOKEN="your_github_token"

# Classification settings
export MIN_CONFIDENCE_THRESHOLD=30  # Minimum confidence score (0-100)
export HIGH_CONFIDENCE_THRESHOLD=70 # High confidence threshold

# Output settings
export OUTPUT_DIR="analysis_results"
export LOG_LEVEL="INFO"             # DEBUG, INFO, WARNING, ERROR
export LOG_FORMAT="console"         # 'console' or 'json'
```

Configuration file (`config.py`) options:

| Setting | Default | Description |
|---------|---------|-------------|
| `MIN_CONFIDENCE_THRESHOLD` | 30 | Issues below this score are filtered out |
| `HIGH_CONFIDENCE_THRESHOLD` | 70 | Threshold for "high confidence" classification |
| `COMMENT_THRESHOLD` | 5 | Issues with more comments may be "in discussion" |
| `TFIDF_WEIGHT` | 0.7 | Weight for TF-IDF scoring in classification |
| `REGEX_WEIGHT` | 0.3 | Weight for regex pattern matching |

## 📅 Automation

### GitHub Actions (Recommended)

The repository includes pre-configured workflows for automated weekly reports:

1. Push to your GitHub repository
2. (Optional) Add secrets for email notifications:
   - `SMTP_USERNAME`: Sending email address
   - `SMTP_PASSWORD`: Email password or App Password
   - `EMAIL_RECIPIENTS`: Comma-separated recipient list

The workflow runs automatically every Friday at 12:00 UTC.

### Cron Job (Local/Server)

```bash
# Edit crontab
crontab -e

# Add: Run every Friday at noon
0 12 * * 5 /path/to/project/scheduled_report.sh
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=. --cov-report=term-missing

# Run specific test file
python -m pytest test_github_client.py -v
```

**Test Coverage:** 78% across 239 tests

| Module | Coverage |
|--------|----------|
| `script.py` | 100% |
| `report_generator.py` | 100% |
| `availability_checker.py` | 98% |
| `github_client.py` | 92% |
| `validators.py` | 95% |

## 📁 Project Structure

```
terraform-provider-google-issues-analyzer/
├── 📄 script.py                 # Main entry point
├── 📄 github_client.py          # GitHub API client
├── 📄 issue_classifier.py       # ML-based classification
├── 📄 availability_checker.py   # Availability determination
├── 📄 report_generator.py       # Report generation
├── 📄 service_definitions.py    # Service keywords/patterns
├── 📄 config.py                 # Configuration management
├── 📄 exceptions.py             # Custom exceptions
├── 📄 logging_config.py         # Logging setup
├── 📄 validators.py             # Input validation
├── 📄 types_definitions.py      # Type definitions
├── 🧪 test_*.py                 # Test files
├── 📄 requirements.txt          # Production dependencies
├── 📄 requirements-dev.txt      # Development dependencies
├── 📄 pyproject.toml            # Project configuration
├── 🔧 run_report.sh             # Manual run script
├── 🔧 scheduled_report.sh       # Automation script
├── 📧 send_team_email.py        # Email notifications
└── 📁 analysis_results/         # Generated reports
```

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Install** dev dependencies (`pip install -r requirements-dev.txt`)
4. **Write** tests for your changes
5. **Run** the test suite (`python -m pytest`)
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to the branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 .

# Run type checking
mypy .

# Run tests with coverage
pytest --cov=. --cov-report=html
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [HashiCorp](https://www.hashicorp.com/) for the Terraform Provider Google
- [GitHub API](https://docs.github.com/en/rest) for issue data access
- [scikit-learn](https://scikit-learn.org/) for TF-IDF implementation

---

<p align="center">
  Made with ❤️ for the Terraform community
</p>