#!/bin/bash
# Cron job script for weekly report generation
# This script can be scheduled via crontab to run every Monday at 10:00 AM PT

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configuration
LOG_DIR="$SCRIPT_DIR/logs"
REPORT_DIR="$SCRIPT_DIR/analysis_results"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
LOG_FILE="$LOG_DIR/report_$DATE.log"

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================"
log "Starting Weekly Terraform Issues Report"
log "========================================"

# Check for GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    log "WARNING: GITHUB_TOKEN not set. API rate limiting may apply."
fi

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    log "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    log "Virtual environment not found. Creating..."
    python3 -m venv "$SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Install/update dependencies
log "Installing dependencies..."
pip install -q -r requirements.txt >> "$LOG_FILE" 2>&1

# Run the analyzer
log "Running issue analyzer..."
python3 -m terraform_issues_analyzer.cli >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "✓ Report generated successfully!"
    log "Report location: $REPORT_DIR/terraform_target_services_issues_report_en.md"

    # Copy report with timestamp
    cp "$REPORT_DIR/terraform_target_services_issues_report_en.md" \
       "$REPORT_DIR/terraform_target_services_issues_report_$DATE.md"
    log "Backup saved: terraform_target_services_issues_report_$DATE.md"

    # Send email to team if configured
    if [ -n "$SMTP_USERNAME" ] && [ -n "$SMTP_PASSWORD" ]; then
        log "Sending email to team..."
        python3 -m terraform_issues_analyzer.send_team_email >> "$LOG_FILE" 2>&1
        if [ $? -eq 0 ]; then
            log "✓ Email sent successfully!"
        else
            log "⚠ Email sending failed (check logs)"
        fi
    else
        log "ℹ Email not configured (set SMTP_USERNAME and SMTP_PASSWORD to enable)"
    fi

    # Clean up old logs (keep last 30 days)
    log "Cleaning up old logs..."
    find "$LOG_DIR" -name "report_*.log" -mtime +30 -delete
    find "$REPORT_DIR" -name "terraform_target_services_issues_report_*.md" -mtime +90 -delete

    log "✓ Report generation completed successfully!"
    exit 0
else
    log "✗ Error: Report generation failed!"
    exit 1
fi

