# Crontab Setup Instructions

## How to Schedule Weekly Reports (Every Monday at 10:00 AM PT)

### Option 1: Local Cron Job (Linux/Mac)

1. **Set up environment variables** (create or edit `~/.bashrc` or `~/.bash_profile`):
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
export TEAM_EMAILS="team1@company.com,team2@company.com"
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

**Every Monday at 10:00 AM PT (California time):**
```cron
0 10 * * 1 /home/acardinalli/dev/terraform/issues_analyzer/scheduled_report.sh
```

**Every Monday at 10:00 AM PT with email:**
```cron
0 10 * * 1 /home/acardinalli/dev/terraform/issues_analyzer/scheduled_report.sh && /home/acardinalli/dev/terraform/issues_analyzer/email_report.sh
```

**With environment variables loaded:**
```cron
0 10 * * 1 . $HOME/.bashrc; /home/acardinalli/dev/terraform/issues_analyzer/scheduled_report.sh
```

4. **Verify cron job is scheduled**:
```bash
crontab -l
```

### Option 2: GitHub Actions (Recommended for Teams)

This is set up via `.github/workflows/terraform_report.yml`.

Important: GitHub Actions `cron` uses UTC and does not support timezone names. The workflow uses a fixed UTC schedule, so it may drift by 1 hour during DST transitions.

1. **Push the repository to GitHub**:
```bash
git add .github/workflows/
git commit -m "Add automated weekly reporting"
git push
```

2. **Configure GitHub Secrets** (Settings → Secrets and variables → Actions):
   - `GITHUB_TOKEN` - Automatically available (no setup needed)
   - `SMTP_USERNAME` - Your SMTP username
   - `SMTP_PASSWORD` - Your SMTP password
   - `TEAM_EMAILS` - Comma-separated recipient emails

3. **Workflow used by this repository**:
   - `.github/workflows/terraform_report.yml` - Generates reports and optionally sends email

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
Description=Run Terraform Issues Report Every Monday at 10:00 AM PT

[Timer]
OnCalendar=Mon *-*-* 10:00:00
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
# Every Monday at 10:00 AM
0 10 * * 1

# Every Monday at 9:00 AM
0 9 * * 1

# Every Monday at 10:00 AM
0 10 * * 1

# Every day at noon
0 12 * * *

# Every weekday (Mon-Fri) at 10:00 AM
0 10 * * 1-5

# Twice a week: Monday and Thursday at 10:00 AM
0 10 * * 1,4
```

## Timezone Considerations

**GitHub Actions:** Uses UTC by default. Adjust the cron schedule accordingly.
- 10:00 AM PDT = 17:00 UTC
- 10:00 AM PST = 18:00 UTC

For exact "10:00 AM America/Los_Angeles" year-round execution, prefer a timezone-aware scheduler (for example, local/system cron with PT timezone, systemd timer on a PT host, or GCP Cloud Scheduler with timezone set).

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

## Secret Backends

For `SECRET_BACKEND=env|gcp` usage and GCP Secret Manager naming conventions, use the canonical guidance in `README.md`.

