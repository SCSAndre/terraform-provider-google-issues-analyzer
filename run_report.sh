#!/bin/bash
# Script to run the Terraform Provider Google issues analyzer

# Exit on error
set -e

echo "Starting Terraform Provider Google Issue Analyzer..."
echo ""

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "WARNING: GITHUB_TOKEN environment variable is not set."
    echo "API requests will be rate-limited. Consider setting it for higher limits."
    echo ""
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the analysis
echo ""
echo "Running issue analysis..."
python3 -m terraform_issues_analyzer.cli

echo ""
echo "Analysis complete! Check the analysis_results directory for the report."

