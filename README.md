# Terraform Provider Google Issues Analyzer

Cloud Armor-focused issue intelligence for `hashicorp/terraform-provider-google`.

This project scans open GitHub issues, identifies Cloud Armor-relevant items, checks whether they are truly available (not assigned/claimed/in progress), and generates Markdown + HTML reports for maintainers and stakeholders.

## Purpose

Use this analyzer to:
- Track Cloud Armor issue backlog quality and contributor opportunities.
- Prioritize issues with confidence scoring (TF-IDF + regex heuristics).
- Share regular report snapshots with engineering and client stakeholders.

## Current Scope

- Service scope: **Cloud Armor only**.
- Repository target default: `hashicorp/terraform-provider-google`.
- Output: `analysis_results/terraform_target_services_issues_report_en.md` and HTML report.

## How It Works

1. `github_client.py` fetches open issues from GitHub (paginated with retry/rate-limit handling).
2. `issue_classifier.py` classifies Cloud Armor relevance.
3. `availability_checker.py` validates that issues are claimable.
4. `report_generator.py` and `html_report_generator.py` build reports.

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GITHUB_TOKEN="your_github_token"
python script.py
```

Open generated outputs in `analysis_results/`.

## Configuration

Set environment variables as needed:

```bash
export GITHUB_TOKEN="your_github_token"
export TARGET_REPO="hashicorp/terraform-provider-google"
export MIN_CONFIDENCE_THRESHOLD=75
export OUTPUT_DIR="analysis_results"
```

Email settings (optional):

```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@example.com"
export SMTP_PASSWORD="your-app-password"
export EMAIL_FROM="your-email@example.com"
export TEAM_EMAILS="a@example.com,b@example.com"
```

## Secret Backends (Phase 2)

By default, secrets are read from environment variables (`SECRET_BACKEND=env`).

You can optionally use Google Cloud Secret Manager with env fallback during migration.

```bash
export SECRET_BACKEND="gcp"
export GCP_PROJECT_ID="your-gcp-project-id"
export GCP_SECRET_PREFIX="terraform-issues-analyzer-"
export SECRET_FALLBACK_TO_ENV="true"
```

### GCP Secret Naming Convention

The app requests secret names by key, optionally prefixed. With `GCP_SECRET_PREFIX="terraform-issues-analyzer-"`, these names are expected in Secret Manager:

- `terraform-issues-analyzer-GITHUB_TOKEN`
- `terraform-issues-analyzer-SMTP_USERNAME`
- `terraform-issues-analyzer-SMTP_PASSWORD`
- `terraform-issues-analyzer-TEAM_EMAILS`

Migration recommendation:
- Keep `SECRET_FALLBACK_TO_ENV=true` while onboarding.
- Switch to `SECRET_FALLBACK_TO_ENV=false` after validation in CI/production.

If `SECRET_BACKEND=gcp` is set but `GCP_PROJECT_ID` is missing, the app falls back safely and logs a warning.

## Weekly Automation (Monday 10:00 AM PT)

### Option A: Local cron (exact PT if host timezone is PT)

```bash
crontab -e
```

```cron
0 10 * * 1 /home/acardinalli/dev/terraform/issues_analyzer/scheduled_report.sh
```

### Option B: GitHub Actions

Workflow file: `.github/workflows/terraform_report.yml`.

Note: GitHub Actions cron is UTC and may shift by 1 hour in DST transitions.

## Testing

```bash
python -m pytest
```

## Offline Quality Evaluation (Phase 3 Step 2)

Use the offline harness to compare baseline vs shadow scoring against a labeled dataset.

### Labeled CSV schema

Required columns:
- `title`
- `body`
- `is_relevant` (`true`/`false`, also supports `1`/`0`, `yes`/`no`)

Optional columns:
- `labels` (delimiters: `|`, `,`, or `;`)
- `category` (for relevant issues, use `Cloud Armor`)
- `split` (`train`, `validation`, or `test`)

Example:

```csv
title,body,labels,is_relevant,category,split
Cloud Armor policy issue,Rule not applied,cloud-armor|bug,true,Cloud Armor,train
Compute docs typo,Minor text fix,documentation,false,,test
```

Run evaluation:

```bash
python3 evaluate_classifier_quality.py --input path/to/labeled_issues.csv
python3 evaluate_classifier_quality.py --input path/to/labeled_issues.csv --output analysis_results/shadow_eval.json
python3 evaluate_classifier_quality.py --input path/to/labeled_issues.csv --split test
```

Use the starter template at `docs/labeled_issues_template.txt` to begin labeling (CSV-formatted content).

Optional CI quality gate (fails with exit code `2` on unacceptable shadow regression):

```bash
python3 evaluate_classifier_quality.py \
  --input path/to/labeled_issues.csv \
  --fail-on-shadow-regression \
  --max-precision-drop 0.02 \
  --max-recall-drop 0.02 \
  --max-f1-drop 0.02 \
  --min-support 30 \
  --min-relevant-support 10 \
  --suggest-thresholds
```

Notes:
- Gate enforcement is skipped (pass with reason) when dataset support is too low.
- `--suggest-thresholds` emits recommended drop tolerances from observed deltas.

The command prints JSON metrics including baseline/shadow precision, recall, F1, accuracy, category accuracy, split distribution, per-label slices, and shadow classification flips.

Governance guidance is in `docs/dataset_governance.txt`.

### GitHub Actions quality workflow

The repository includes `.github/workflows/offline_shadow_quality.yml`:
- PR trigger: informational run with artifact output.
- Weekly schedule: Monday 16:30 UTC quality-gate run.
- Manual run: supports custom dataset path, split, and metric-drop thresholds.

Recommended manual gate run:

```bash
# GitHub UI: Actions -> Offline Shadow Quality -> Run workflow
# Set enforce_gate=true and split=test
```

## Observability Notes

- Use structured logging (`LOG_FORMAT=json`) in CI/prod for easier parsing.
- Use `LOG_LEVEL=INFO` in production and `LOG_LEVEL=DEBUG` for incident analysis.
- Startup config summary includes non-sensitive backend status (for example, whether `GCP_PROJECT_ID` is set).

### Optional NLP Shadow Mode (Phase 3 Scaffold)

Shadow mode compares baseline scoring vs experimental tri-gram TF-IDF scoring in logs only.

```bash
export ENABLE_TRIGRAM_SHADOW_MODE="true"
export SHADOW_SCORE_DELTA_THRESHOLD="15.0"
```

This does **not** change inclusion/exclusion decisions in reports.

## Optional GCP Analytics (BigQuery + Looker Studio)

Not required for core report generation.

- **BigQuery**: pay-as-you-go (storage + query bytes scanned), with free-tier quotas that vary by account/billing status.
- **Looker Studio**: generally free for dashboarding, but query costs still come from underlying BigQuery usage.
- **Recommendation**: enable billing budgets, alerts, table partitioning, and query limits before production rollout.

Always verify current quotas/pricing in your GCP project:
- BigQuery pricing/quota pages in Google Cloud Console
- Billing budgets and alerts in Cloud Billing

## Security Notes

- Prefer secrets from CI secret stores or cloud secret managers over local `.env` files.
- Use a GitHub token to avoid low unauthenticated API limits.
- Avoid committing generated reports if they contain sensitive operational metadata.

## Repository Hygiene

Suggested baseline:
- Keep generated outputs under `analysis_results/` (gitignored if not needed in history).
- Keep runtime scripts and CI workflows separated and minimal.
- Remove stale docs/scripts only after validating they are not referenced by automation.

## Project Layout

- `script.py`: orchestrator
- `github_client.py`: GitHub data fetching
- `issue_classifier.py`: ML + heuristic classifier
- `availability_checker.py`: assignment/claim checks
- `report_generator.py`: markdown reporting
- `html_report_generator.py`: HTML reporting
- `send_team_email.py`: email distribution
- `scheduled_report.sh`: automation entrypoint

## Contributing

```bash
pip install -r requirements-dev.txt
python -m pytest
```

For major changes, open an issue first with proposed design and rollout/rollback plan.
