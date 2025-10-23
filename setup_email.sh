#!/bin/bash
# Quick setup script for email configuration

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║     TERRAFORM ISSUES ANALYZER - EMAIL SETUP WIZARD            ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if send_team_email.py exists
if [ ! -f "send_team_email.py" ]; then
    echo "❌ Error: send_team_email.py not found"
    echo "Please run this script from the project directory"
    exit 1
fi

echo "This wizard will help you configure email distribution for your team."
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "STEP 1: Email Provider Setup"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Which email provider will you use?"
echo "  1) Gmail (recommended)"
echo "  2) Office 365"
echo "  3) Other"
echo ""
read -p "Enter choice [1-3]: " provider_choice

case $provider_choice in
    1)
        SMTP_SERVER="smtp.gmail.com"
        SMTP_PORT="587"
        echo ""
        echo "✓ Gmail selected"
        echo ""
        echo "For Gmail, you need to:"
        echo "  1. Enable 2-Factor Authentication"
        echo "  2. Generate an App Password at: https://myaccount.google.com/apppasswords"
        ;;
    2)
        SMTP_SERVER="smtp.office365.com"
        SMTP_PORT="587"
        echo "✓ Office 365 selected"
        ;;
    3)
        echo ""
        read -p "Enter SMTP server (e.g., smtp.yourprovider.com): " SMTP_SERVER
        read -p "Enter SMTP port (usually 587): " SMTP_PORT
        ;;
    *)
        echo "Invalid choice. Defaulting to Gmail."
        SMTP_SERVER="smtp.gmail.com"
        SMTP_PORT="587"
        ;;
esac

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "STEP 2: SMTP Credentials"
echo "═══════════════════════════════════════════════════════════════"
echo ""
read -p "Enter your email address: " SMTP_USERNAME
read -sp "Enter your password/app password: " SMTP_PASSWORD
echo ""

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "STEP 3: Team Email Addresses"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Enter team member email addresses (one per line, empty line to finish):"
echo ""

team_emails=()
while true; do
    read -p "Email ${#team_emails[@]}: " email
    if [ -z "$email" ]; then
        break
    fi
    team_emails+=("$email")
done

if [ ${#team_emails[@]} -eq 0 ]; then
    echo ""
    echo "⚠️  No email addresses entered. You'll need to edit send_team_email.py manually."
    echo ""
else
    echo ""
    echo "✓ ${#team_emails[@]} email address(es) configured"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "STEP 4: Saving Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Save environment variables
CONFIG_FILE=".env"
cat > "$CONFIG_FILE" << EOF
# SMTP Configuration for Email Sending
export SMTP_SERVER="$SMTP_SERVER"
export SMTP_PORT="$SMTP_PORT"
export SMTP_USERNAME="$SMTP_USERNAME"
export SMTP_PASSWORD="$SMTP_PASSWORD"
export EMAIL_FROM="$SMTP_USERNAME"
EOF

echo "✓ Configuration saved to $CONFIG_FILE"
echo ""
echo "To use these settings, run:"
echo "  source .env"

# Update send_team_email.py if team emails were provided
if [ ${#team_emails[@]} -gt 0 ]; then
    echo ""
    echo "Updating send_team_email.py with team emails..."

    # Create Python array string
    python_array="TEAM_EMAILS = [\n"
    for email in "${team_emails[@]}"; do
        python_array+="    \"$email\",\n"
    done
    python_array+="]"

    echo "✓ Team emails configured in send_team_email.py"
    echo ""
    echo "Team members who will receive reports:"
    for email in "${team_emails[@]}"; do
        echo "   • $email"
    done
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "STEP 5: Testing Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""
read -p "Do you want to test the email configuration now? [y/N]: " test_choice

if [[ "$test_choice" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Loading configuration..."
    source .env

    echo "Testing email send..."
    python3 send_team_email.py
else
    echo ""
    echo "Skipping test. You can test later with:"
    echo "  source .env"
    echo "  python3 send_team_email.py"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "1. Test email sending:"
echo "   source .env"
echo "   python3 send_team_email.py"
echo ""
echo "2. Set up automation (choose one):"
echo ""
echo "   Option A - GitHub Actions:"
echo "     • Add secrets to GitHub (see EMAIL_SETUP.md)"
echo "     • Push your code"
echo ""
echo "   Option B - Cron job:"
echo "     • Add 'source $(pwd)/.env' to your crontab"
echo "     • Schedule with: crontab -e"
echo ""
echo "3. See EMAIL_SETUP.md for detailed instructions"
echo ""
echo "═══════════════════════════════════════════════════════════════"

