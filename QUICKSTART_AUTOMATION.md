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

2. **That's it!** The workflow is already configured to run every Friday at 12:00 PM UTC.

3. **Optional - Enable Email Notifications**:
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `EMAIL_USERNAME`: Your SMTP email (e.g., reports@yourcompany.com)
     - `EMAIL_PASSWORD`: Your SMTP password or app password
     - `EMAIL_RECIPIENTS`: team1@company.com,team2@company.com
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
3. Use this app password for `EMAIL_PASSWORD` secret

### For other providers:
See SCHEDULING.md for Office 365, SendGrid, and other options.

---

## 🖥️ Local/Server Setup (Alternative)

### Method 1: Simple Cron Job

1. **Edit your crontab**:
```bash
crontab -e
```

2. **Add this line** (runs every Friday at noon):
```cron
0 12 * * 5 cd /home/acardinalli/dev/terraform/issues_analyzer && ./scheduled_report.sh
```

3. **Set your GitHub token**:
```bash
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

4. **Done!** Check logs in the `logs/` directory.

### Method 2: With Email Distribution

```cron
0 12 * * 5 cd /home/acardinalli/dev/terraform/issues_analyzer && ./scheduled_report.sh && ./email_report.sh
```

Set email environment variables:
```bash
export EMAIL_RECIPIENTS="team@company.com"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

---

## 🔍 Verify It's Working

### GitHub Actions:
- Go to your repo → Actions tab
- You should see "Weekly Terraform Issues Report" workflow
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
0 12 * * 1 /path/to/scheduled_report.sh

# In GitHub Actions (.github/workflows/weekly_report.yml):
- cron: '0 12 * * 1'  # Change 5 to 1
```

### Change from noon to 9 AM:
```cron
# In crontab: Change '12' to '9'
0 9 * * 5 /path/to/scheduled_report.sh

# In GitHub Actions:
- cron: '0 9 * * 5'  # Change 12 to 9 (UTC time!)
```

### Timezone Notes:
- **GitHub Actions uses UTC**
  - 12:00 PM EST = 17:00 UTC → Use `cron: '0 17 * * 5'`
  - 12:00 PM PST = 20:00 UTC → Use `cron: '0 20 * * 5'`
- **Local cron uses system timezone**

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

