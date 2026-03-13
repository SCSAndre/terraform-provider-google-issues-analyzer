# Quick Start Guide for Automated Weekly Reports

## 🚀 Easiest Method: GitHub Actions

This is the **recommended approach** for teams!

### Setup (5 minutes):

1. **Push your code to GitHub**:
```bash
git add .
git commit -m "Add automated weekly reporting"
git push origin main
```

2. **That's it!** The workflow is already configured for a weekly Monday schedule (see UTC/DST note in `README.md`).

3. **Optional - Enable Email Notifications**:
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `SMTP_USERNAME`: Your SMTP email (e.g., reports@yourcompany.com)
     - `SMTP_PASSWORD`: Your SMTP password or app password
     - `TEAM_EMAILS`: team1@company.com,team2@company.com
   - The email workflow will automatically send reports!

4. **Download reports**:
   - Go to Actions tab → Latest workflow run
   - Download the report from Artifacts section
   - Or check your email inbox!

---

## 📧 Email Setup (Gmail Example)

### For Gmail:
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Create password for "Mail" on "Other (Custom name)"
3. Use this app password for `SMTP_PASSWORD`

### For other providers:
See SCHEDULING.md for Office 365, SendGrid, and other options.

---

## 🖥️ Local/Server Setup (Alternative)

### Method 1: Simple Cron Job

1. **Edit your crontab**:
```bash
crontab -e
```

2. **Add this line** (runs every Monday at 10:00 AM PT):
```cron
0 10 * * 1 cd /home/acardinalli/dev/terraform/issues_analyzer && ./scheduled_report.sh
```

3. **Set your GitHub token**:
```bash
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

4. **Done!** Check logs in the `logs/` directory.

### Method 2: With Email Distribution

```cron
0 10 * * 1 cd /home/acardinalli/dev/terraform/issues_analyzer && ./scheduled_report.sh && ./email_report.sh
```

Set email environment variables:
```bash
export TEAM_EMAILS="team@company.com"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

---

## 🔍 Verify It's Working

### GitHub Actions:
- Go to your repo → Actions tab
- You should see "Terraform Issues Report" workflow
- Click "Run workflow" to test manually

### Cron Job:
```bash
# Check if cron job is scheduled
crontab -l

# Test manually
./scheduled_report.sh

# Check logs
tail -f logs/report_*.log
```

---

## ⏰ Customizing the Schedule

### Change from Friday to Monday:
```cron
# In crontab: Change '5' to '1'
0 10 * * 1 /path/to/scheduled_report.sh

# In GitHub Actions (.github/workflows/terraform_report.yml):
- cron: '0 17 * * 1'  # Monday at 17:00 UTC
```

### Change from noon to 9 AM:
```cron
# In crontab: Change '10' to '9'
0 9 * * 1 /path/to/scheduled_report.sh

# In GitHub Actions:
- cron: '0 16 * * 1'  # 9 AM PT when observing daylight time
```

### Timezone Notes:
- **GitHub Actions uses UTC**
  - 10:00 AM PDT = 17:00 UTC
  - 10:00 AM PST = 18:00 UTC
- **Local cron uses system timezone**

For exact year-round California time execution, use a timezone-aware scheduler.

---

## 🎯 Summary

| Method | Best For | Setup Time | Maintenance |
|--------|----------|------------|-------------|
| **GitHub Actions** | Teams, cloud-based | 5 min | None |
| **Cron + Email** | Local servers | 10 min | Low |
| **Systemd Timer** | Modern Linux servers | 15 min | Low |

**Recommendation**: Use GitHub Actions for the easiest, most reliable solution!

---

## 📞 Need Help?

See [SCHEDULING.md](SCHEDULING.md) for:
- Detailed setup instructions
- Troubleshooting guide
- Multiple email provider configurations
- Advanced scheduling options

See [README.md](README.md) for secret backend configuration (`SECRET_BACKEND=env|gcp`) and GCP secret naming conventions.

