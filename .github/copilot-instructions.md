# Terraform Provider Google Issues Analyzer - AI Development Guide

## Architecture Overview

**Purpose**: Analyzes Terraform Provider Google issues to identify open, unassigned issues relevant to Cloud Armor.

**Data Flow**: GitHub API → Issue Classification → Availability Check → Report Generation
- `script.py`: Main orchestrator calling the pipeline
- `github_client.py`: Handles API calls, rate limiting, retries with exponential backoff
- `issue_classifier.py`: ML-based relevance filtering using TF-IDF + regex patterns
- `availability_checker.py`: Checks if issues are truly unassigned/unclaimed
- `report_generator.py`, `html_report_generator.py`: Output formatting (markdown & HTML)

## Key Design Patterns

### Exception Handling Hierarchy
All custom exceptions inherit from `IssueAnalyzerError` in `exceptions.py` for unified error handling:
```python
try:
    # code
except IssueAnalyzerError as e:
    logger.error(f"{e.__class__.__name__}: {e.message}")
```

### Configuration via Environment Variables
Use `config.py` constants (e.g., `GITHUB_TOKEN`, `MIN_CONFIDENCE_THRESHOLD`). All env-var loading happens at import time. Access via `from config import SETTING_NAME`.

### Logging with Context
Use `logging_config.py` for structured logging with correlation IDs:
```python
from logging_config import get_logger, LogContext
logger = get_logger(__name__)
with LogContext(operation="my_operation"):
    logger.info("Message", extra={"key": "value"})
```

### Type Safety
- Use TypedDict from `types_definitions.py` (`GitHubIssue`, `EnrichedIssue`) for issue data
- All functions should declare return types; use Optional for nullable values
- Leverage `config.ConfidenceLevel` enum for confidence categorization

## Critical Workflows

### Service Scope
- Current supported service category is **Cloud Armor only**.
- Keep `service_definitions.py` and `README.md` aligned when changing scope.
- Validate scope changes with `test_service_definitions.py` and `test_issue_classifier.py`.

### Running Analysis
```bash
export GITHUB_TOKEN="your_token"  # 5000 req/hour, vs 60 without
export MIN_CONFIDENCE_THRESHOLD=75  # 0-100 score
python script.py
```

### Testing
- Unit tests use mocked GitHub responses in `test_*.py` files
- Run all tests: `python -m pytest` or included scripts
- Test file naming: `test_[module_name].py` (mirror structure)

## Important Quirks & Conventions

### Rate Limiting
- `GitHubClient` includes automatic rate limit detection and backoff (see `_handle_rate_limit()`)
- Never make concurrent API requests; use pagination with `fetch_issues_page(page_num)`
- Always include `REQUEST_DELAY` (config.py) between requests

### Availability Check Logic
`availability_checker.py` checks multiple signals beyond assignee (claimed in comments, PR linked, in-progress label) because issues may be abandoned but technically "available".

### Confidence Scoring
TF-IDF (80% weight) + Regex patterns (20% weight, `config.TFIDF_WEIGHT` / `REGEX_WEIGHT`). Two-stage classification: fast keyword check first, then full TF-IDF analysis if needed (see `classify_issue()` in `issue_classifier.py`).

### Email Reports
Templates in `send_team_email.py`; SMTP config via environment variables (`SMTP_SERVER`, `SMTP_USERNAME`, etc.). Scheduled via `scheduled_report.sh`.

## Common Modifications

- **Adjust classification sensitivity**: Change `MIN_CONFIDENCE_THRESHOLD` in config
- **Add report fields**: Extend `EnrichedIssue` TypedDict, update classifiers & generators
- **Change GitHub repo**: Update `TARGET_REPO` in config
- **Modify output format**: Edit `report_generator.py` or `html_report_generator.py`

## Testing Patterns

Test files mock GitHub API responses using `unittest.mock`. Example:
```python
with patch('github_client.requests.get') as mock_get:
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"items": [...]}
    # test code
```

## Dependencies
- `requests`: HTTP library (GitHub API calls)
- `scikit-learn`: TF-IDF vectorization for classification
- `typing-extensions`: Type hints compatibility

---
*Python 3.11+ required. See README.md for full setup instructions.*
