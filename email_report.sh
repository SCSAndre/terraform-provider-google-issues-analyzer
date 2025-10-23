#!/bin/bash
# Email distribution script for weekly reports
# Sends the generated report to team members via email

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPORT_FILE="$SCRIPT_DIR/analysis_results/terraform_target_services_issues_report_en.md"

# Email configuration - EDIT THESE VALUES
EMAIL_FROM="${EMAIL_FROM:-terraform-reports@yourcompany.com}"
EMAIL_RECIPIENTS="${EMAIL_RECIPIENTS:-team@yourcompany.com}"
EMAIL_SUBJECT="Terraform Issues Weekly Report - $(date +%Y-%m-%d)"

# Check if report exists
if [ ! -f "$REPORT_FILE" ]; then
    echo "Error: Report file not found at $REPORT_FILE"
    exit 1
fi

# Send email using mail command (requires mailutils or sendmail)
if command -v mail &> /dev/null; then
    echo "Sending report via mail command..."
    cat << EOF | mail -s "$EMAIL_SUBJECT" -a "$REPORT_FILE" "$EMAIL_RECIPIENTS"
Hello Team,

The weekly Terraform Provider Google issues report is ready!

Please find the report attached. This report includes:
- Available issues related to Load Balancers
- Available issues related to Cloud Armor
- Available issues related to Private Service Connect (PSC)

All issues have been filtered to show only those that are:
✓ Currently open
✓ Not assigned
✓ Not marked as work-in-progress
✓ Not claimed in comments

Best regards,
Terraform Issues Analyzer
EOF
    echo "✓ Email sent successfully!"

# Alternative: Send using Python smtplib
elif command -v python3 &> /dev/null; then
    echo "Sending report via Python..."
    python3 - << PYTHON_SCRIPT
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# Email configuration from environment variables
smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
smtp_username = os.getenv('SMTP_USERNAME', '')
smtp_password = os.getenv('SMTP_PASSWORD', '')
email_from = '$EMAIL_FROM'
email_to = '$EMAIL_RECIPIENTS'.split(',')

if not smtp_username or not smtp_password:
    print("Error: SMTP_USERNAME and SMTP_PASSWORD environment variables must be set")
    exit(1)

# Create message
msg = MIMEMultipart()
msg['From'] = email_from
msg['To'] = ', '.join(email_to)
msg['Subject'] = '$EMAIL_SUBJECT'

# Email body
body = """Hello Team,

The weekly Terraform Provider Google issues report is ready!

Please find the report attached. This report includes:
- Available issues related to Load Balancers
- Available issues related to Cloud Armor
- Available issues related to Private Service Connect (PSC)

All issues have been filtered to show only those that are:
✓ Currently open
✓ Not assigned
✓ Not marked as work-in-progress
✓ Not claimed in comments

Best regards,
Terraform Issues Analyzer
"""

msg.attach(MIMEText(body, 'plain'))

# Attach report
try:
    with open('$REPORT_FILE', 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename=terraform_issues_report_{datetime.now().strftime("%Y-%m-%d")}.md')
        msg.attach(part)
except Exception as e:
    print(f"Error attaching file: {e}")
    exit(1)

# Send email
try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.send_message(msg)
    server.quit()
    print("✓ Email sent successfully via Python!")
except Exception as e:
    print(f"Error sending email: {e}")
    exit(1)
PYTHON_SCRIPT

else
    echo "Error: No email sending method available (mail command or Python not found)"
    exit 1
fi

