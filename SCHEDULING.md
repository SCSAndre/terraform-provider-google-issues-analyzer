# Crontab Setup Instructions

## How to Schedule Weekly Reports (Every Friday at Noon)

### Option 1: Local Cron Job (Linux/Mac)

1. **Set up environment variables** (create or edit `~/.bashrc` or `~/.bash_profile`):
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
export EMAIL_RECIPIENTS="team1@company.com,team2@company.com"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

2. **Open crontab editor**:
```bash
crontab -e
```

3. **Add one of these cron schedules**:

**Every Friday at 12:00 PM (noon):**
```cron
0 12 * * 5 /home/acardinalli/dev/terraform/issues_analyzer/scheduled_report.sh
```

**Every Friday at 12:00 PM with email:**
```cron
0 12 * * 5 /home/acardinalli/dev/terraform/issues_analyzer/scheduled_report.sh && /home/acardinalli/dev/terraform/issues_analyzer/email_report.sh
```

**With environment variables loaded:**
```cron
0 12 * * 5 . $HOME/.bashrc; /home/acardinalli/dev/terraform/issues_analyzer/scheduled_report.sh
```

4. **Verify cron job is scheduled**:
```bash
crontab -l
```

### Option 2: GitHub Actions (Recommended for Teams)

This is **already set up**! Just push to GitHub and configure secrets:

1. **Push the repository to GitHub**:
```bash
git add .github/workflows/
git commit -m "Add automated weekly reporting"
git push
```

2. **Configure GitHub Secrets** (Settings → Secrets and variables → Actions):
   - `GITHUB_TOKEN` - Automatically available (no setup needed)
   - `EMAIL_USERNAME` - Your SMTP username (only for email workflow)
   - `EMAIL_PASSWORD` - Your SMTP password (only for email workflow)
   - `EMAIL_RECIPIENTS` - Comma-separated emails (only for email workflow)

3. **Choose which workflow to enable**:
   - `weekly_report.yml` - Generates report, saves as artifact
   - `weekly_report_email.yml` - Generates report AND emails to team

### Option 3: Systemd Timer (Modern Linux)

1. **Create service file** `/etc/systemd/system/terraform-report.service`:
```ini
[Unit]
Description=Terraform Issues Weekly Report
After=network.target

[Service]
Type=oneshot
User=acardinalli
Environment="GITHUB_TOKEN=your_token_here"
WorkingDirectory=/home/acardinalli/dev/terraform/issues_analyzer
ExecStart=/home/acardinalli/dev/terraform/issues_analyzer/scheduled_report.sh
```

2. **Create timer file** `/etc/systemd/system/terraform-report.timer`:
```ini
[Unit]
Description=Run Terraform Issues Report Every Friday at Noon

[Timer]
OnCalendar=Fri *-*-* 12:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

3. **Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable terraform-report.timer
sudo systemctl start terraform-report.timer
```

4. **Check status**:
```bash
sudo systemctl status terraform-report.timer
```

## Cron Schedule Examples

```
# Every Friday at 12:00 PM
0 12 * * 5

# Every Friday at 9:00 AM
0 9 * * 5

# Every Monday at 8:00 AM
0 8 * * 1

# Every day at noon
0 12 * * *

# Every weekday (Mon-Fri) at 10:00 AM
0 10 * * 1-5

# Twice a week: Monday and Thursday at noon
0 12 * * 1,4
```

## Timezone Considerations

**GitHub Actions:** Uses UTC by default. Adjust the cron schedule accordingly.
- 12:00 PM EST = 17:00 UTC
- 12:00 PM PST = 20:00 UTC

**Local Cron:** Uses your system's timezone.

Check your timezone:
```bash
date
timedatectl  # On systems with systemd
```

## Testing Your Setup

**Test the report generation:**
```bash
./scheduled_report.sh
```

**Test email sending:**
```bash
./email_report.sh
```

**Test cron job manually:**
```bash
/bin/bash -c "$(crontab -l | grep scheduled_report)"
```

## Monitoring

**Check cron logs:**
```bash
# Ubuntu/Debian
grep CRON /var/log/syslog

# CentOS/RHEL
tail -f /var/log/cron

# Check your script logs
tail -f /home/acardinalli/dev/terraform/issues_analyzer/logs/report_*.log
```

## Email Provider Setup

### Gmail
1. Enable 2-factor authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password for SMTP_PASSWORD

### Office 365
- SMTP Server: smtp.office365.com
- Port: 587
- Use your email and password

### SendGrid
- SMTP Server: smtp.sendgrid.net
- Port: 587
- Username: apikey
- Password: Your SendGrid API key

## Troubleshooting

**Cron job not running:**
- Check cron service: `sudo systemctl status cron`
- Check permissions: `ls -la scheduled_report.sh`
- Check logs: `grep CRON /var/log/syslog`

**Email not sending:**
- Verify SMTP credentials
- Check firewall/network settings
- Test with: `telnet smtp.gmail.com 587`
- Review logs in `logs/` directory

**Rate limiting:**
- Set GITHUB_TOKEN environment variable
- Check rate limit: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit`

