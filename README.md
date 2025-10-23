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

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Set GitHub token for higher API rate limits:
```bash
export GITHUB_TOKEN="your_github_token_here"
```

## Usage

### Quick Start

Run the analysis using the provided shell script:
```bash
./run_report.sh
```

### Manual Execution

Alternatively, run the Python script directly:
```bash
python3 script.py
```

### Automated Weekly Reports

**Want automated weekly reports every Friday at noon?** See [SCHEDULING.md](SCHEDULING.md) for:
- GitHub Actions automation (recommended for teams)
- Cron job setup (for local/server deployment)
- Email distribution to team members
- Multiple scheduling options

## Output

The analysis generates a markdown report in the `analysis_results/` directory:
- `terraform_target_services_issues_report_en.md` - Main report with categorized issues

Each issue includes:
- Issue number and title
- Confidence score
- Direct URL to GitHub issue
- Creation date
- Number of comments

## Configuration

Edit `config.py` to customize:
- `MIN_CONFIDENCE_THRESHOLD` - Minimum confidence score (default: 30)
- `HIGH_CONFIDENCE_THRESHOLD` - High confidence threshold (default: 70)
- `COMMENT_THRESHOLD` - Max comments for "available" issues (default: 5)
- `TFIDF_WEIGHT` - Weight for TF-IDF scoring (default: 0.7)
- `REGEX_WEIGHT` - Weight for regex scoring (default: 0.3)

## Testing

Run unit tests:
```bash
python3 -m pytest test_*.py -v
```

Or using unittest:
```bash
python3 -m unittest test_availability_checker.py test_issue_classifier.py -v
```

## Project Structure

```
issues_analyzer/
├── config.py                    # Configuration settings
├── github_client.py             # GitHub API client
├── issue_classifier.py          # Issue classification logic
├── availability_checker.py      # Availability checking logic
├── service_definitions.py       # Service keywords and terms
├── report_generator.py          # Report generation
├── types_definitions.py         # Type definitions
├── script.py                    # Main execution script
├── run_report.sh               # Convenience shell script
├── test_*.py                   # Unit tests
└── requirements.txt            # Python dependencies
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
