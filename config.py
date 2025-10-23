"""Configuration settings for the GitHub issue analyzer."""
import os
from pathlib import Path

# API Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
TARGET_REPO = "hashicorp/terraform-provider-google"

# Analysis Thresholds
MIN_CONFIDENCE_THRESHOLD = 30
HIGH_CONFIDENCE_THRESHOLD = 70
MEDIUM_CONFIDENCE_THRESHOLD = 50
TFIDF_WEIGHT = 0.7
REGEX_WEIGHT = 0.3

# API Rate Limiting
RATE_LIMIT_BUFFER = 10
REQUEST_DELAY = 0.5
COMMENT_THRESHOLD = 5
MAX_RETRIES = 3
INITIAL_BACKOFF = 2

# Output
OUTPUT_DIR = Path("analysis_results")
OUTPUT_DIR.mkdir(exist_ok=True)
