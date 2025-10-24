#!/bin/bash
# Comprehensive Repository Analysis Script
# This script performs a deep analysis of the repository

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   TERRAFORM ISSUES ANALYZER - REPOSITORY ANALYSIS             ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

REPO_DIR="/home/acardinalli/dev/terraform/issues_analyzer"
cd "$REPO_DIR" || exit 1

echo "═══════════════════════════════════════════════════════════════"
echo "1. REPOSITORY STATUS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if git repository exists
if [ -d ".git" ]; then
    echo "✓ Git repository initialized"

    # Check remote
    REMOTE=$(git remote -v | grep origin | head -1)
    if [ -n "$REMOTE" ]; then
        echo "✓ Remote configured: $REMOTE"
    else
        echo "✗ No remote configured"
    fi

    # Check branch
    BRANCH=$(git branch --show-current 2>/dev/null)
    echo "✓ Current branch: ${BRANCH:-unknown}"

    # Check commits
    COMMIT_COUNT=$(git log --oneline 2>/dev/null | wc -l)
    echo "✓ Total commits: $COMMIT_COUNT"

    if [ "$COMMIT_COUNT" -gt 0 ]; then
        echo "  Latest commit:"
        git log --oneline -1 | sed 's/^/    /'
    fi

    # Check unpushed changes
    UNPUSHED=$(git status --short 2>/dev/null)
    if [ -n "$UNPUSHED" ]; then
        echo "⚠ Uncommitted changes found:"
        echo "$UNPUSHED" | sed 's/^/    /'
    else
        echo "✓ No uncommitted changes"
    fi
else
    echo "✗ Not a git repository"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "2. FILE STRUCTURE ANALYSIS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Core Python files
echo "📁 Core Python Modules:"
CORE_FILES=(
    "__init__.py"
    "config.py"
    "github_client.py"
    "issue_classifier.py"
    "availability_checker.py"
    "service_definitions.py"
    "report_generator.py"
    "types_definitions.py"
    "script.py"
)

for file in "${CORE_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(wc -l < "$file")
        echo "  ✓ $file ($SIZE lines)"
    else
        echo "  ✗ $file MISSING"
    fi
done

echo ""
echo "📧 Email Distribution:"
EMAIL_FILES=(
    "send_team_email.py"
    "email_report.sh"
)

for file in "${EMAIL_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(wc -l < "$file")
        if [ -x "$file" ]; then
            echo "  ✓ $file ($SIZE lines, executable)"
        else
            echo "  ✓ $file ($SIZE lines)"
        fi
    else
        echo "  ✗ $file MISSING"
    fi
done

echo ""
echo "🤖 Automation Scripts:"
SCRIPT_FILES=(
    "run_report.sh"
    "scheduled_report.sh"
    "push_to_github.sh"
    "setup_email.sh"
)

for file in "${SCRIPT_FILES[@]}"; do
    if [ -f "$file" ]; then
        if [ -x "$file" ]; then
            echo "  ✓ $file (executable)"
        else
            echo "  ⚠ $file (not executable)"
        fi
    else
        echo "  ✗ $file MISSING"
    fi
done

echo ""
echo "📝 Documentation:"
DOC_FILES=(
    "README.md"
    "CHANGELOG.md"
    "PROJECT_STATUS.md"
    "EMAIL_SETUP.md"
    "WHY_GITHUB_SECRETS.md"
    "SCHEDULING.md"
    "QUICKSTART_AUTOMATION.md"
    "AUTOMATION_SUMMARY.md"
    "PUSH_INSTRUCTIONS.md"
)

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(wc -l < "$file")
        echo "  ✓ $file ($SIZE lines)"
    else
        echo "  ⚠ $file missing"
    fi
done

echo ""
echo "🧪 Test Files:"
TEST_FILES=(
    "test_issue_classifier.py"
    "test_availability_checker.py"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(wc -l < "$file")
        echo "  ✓ $file ($SIZE lines)"
    else
        echo "  ✗ $file MISSING"
    fi
done

echo ""
echo "⚙️ GitHub Actions Workflows:"
if [ -d ".github/workflows" ]; then
    WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" | wc -l)
    echo "  ✓ .github/workflows directory exists"
    echo "  ✓ Found $WORKFLOW_COUNT workflow(s):"
    find .github/workflows -name "*.yml" -exec basename {} \; | sed 's/^/    - /'
else
    echo "  ✗ .github/workflows directory MISSING"
fi

echo ""
echo "📋 Configuration Files:"
CONFIG_FILES=(
    "requirements.txt"
    ".gitignore"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "3. CODE QUALITY CHECKS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "🐍 Python Syntax Validation:"
SYNTAX_ERRORS=0
for pyfile in *.py; do
    if [ -f "$pyfile" ]; then
        if python3 -m py_compile "$pyfile" 2>/dev/null; then
            echo "  ✓ $pyfile - Valid syntax"
        else
            echo "  ✗ $pyfile - SYNTAX ERROR"
            SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
        fi
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo ""
    echo "✅ All Python files have valid syntax"
else
    echo ""
    echo "❌ Found $SYNTAX_ERRORS file(s) with syntax errors"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "4. CONFIGURATION VALIDATION"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check team emails
if [ -f "send_team_email.py" ]; then
    TEAM_EMAIL_COUNT=$(grep -A 10 "TEAM_EMAILS = \[" send_team_email.py | grep "@" | wc -l)
    if [ "$TEAM_EMAIL_COUNT" -gt 0 ]; then
        echo "✓ Team emails configured: $TEAM_EMAIL_COUNT recipient(s)"
        grep -A 10 "TEAM_EMAILS = \[" send_team_email.py | grep "@" | sed 's/^/  /'
    else
        echo "⚠ Team emails not configured (still using placeholder emails)"
    fi
else
    echo "✗ send_team_email.py not found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "5. DEPENDENCIES CHECK"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [ -f "requirements.txt" ]; then
    echo "📦 Required packages:"
    cat requirements.txt | sed 's/^/  /'
    echo ""

    echo "Checking installed packages:"
    while read -r package; do
        PKG_NAME=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
        if python3 -c "import $PKG_NAME" 2>/dev/null; then
            echo "  ✓ $PKG_NAME installed"
        else
            # Handle special cases
            if [ "$PKG_NAME" = "scikit-learn" ]; then
                if python3 -c "import sklearn" 2>/dev/null; then
                    echo "  ✓ scikit-learn installed (as sklearn)"
                else
                    echo "  ✗ scikit-learn NOT installed"
                fi
            else
                echo "  ✗ $PKG_NAME NOT installed"
            fi
        fi
    done < requirements.txt
else
    echo "✗ requirements.txt not found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "6. GITHUB ACTIONS WORKFLOW ANALYSIS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [ -f ".github/workflows/weekly_report_email.yml" ]; then
    echo "✓ Email workflow exists"

    # Check schedule
    SCHEDULE=$(grep "cron:" .github/workflows/weekly_report_email.yml | head -1)
    if [ -n "$SCHEDULE" ]; then
        echo "  Schedule: $SCHEDULE"
    fi

    # Check required secrets
    echo ""
    echo "  Required GitHub Secrets:"
    echo "    - SMTP_USERNAME (your email address)"
    echo "    - SMTP_PASSWORD (Gmail app password)"
    echo ""
    echo "  ⚠ Make sure these are configured at:"
    echo "    https://github.com/SCSAndre/terraform-provider-google-issues-analyzer/settings/secrets/actions"
else
    echo "⚠ Email workflow not found"
fi

if [ -f ".github/workflows/weekly_report.yml" ]; then
    echo ""
    echo "✓ Basic report workflow exists"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "7. REPOSITORY SYNC STATUS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if we can reach GitHub
if git ls-remote origin &>/dev/null; then
    echo "✓ Can connect to GitHub repository"

    # Check if local is behind
    git fetch origin &>/dev/null
    LOCAL=$(git rev-parse @ 2>/dev/null)
    REMOTE=$(git rev-parse @{u} 2>/dev/null)

    if [ "$LOCAL" = "$REMOTE" ]; then
        echo "✓ Local repository is up to date with GitHub"
    else
        echo "⚠ Local repository differs from GitHub"

        AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null)
        BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null)

        if [ "$AHEAD" -gt 0 ]; then
            echo "  → $AHEAD commit(s) ahead (need to push)"
        fi
        if [ "$BEHIND" -gt 0 ]; then
            echo "  → $BEHIND commit(s) behind (need to pull)"
        fi
    fi
else
    echo "⚠ Cannot connect to GitHub repository"
    echo "  This might be normal if you haven't pushed yet"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "8. FUNCTIONAL TESTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if report exists
if [ -f "analysis_results/terraform_target_services_issues_report_en.md" ]; then
    REPORT_SIZE=$(wc -l < analysis_results/terraform_target_services_issues_report_en.md)
    REPORT_DATE=$(stat -c %y analysis_results/terraform_target_services_issues_report_en.md 2>/dev/null | cut -d' ' -f1)
    echo "✓ Sample report exists"
    echo "  Size: $REPORT_SIZE lines"
    echo "  Generated: $REPORT_DATE"

    # Extract summary
    TOTAL_ISSUES=$(grep "Total Issues Found:" analysis_results/terraform_target_services_issues_report_en.md | grep -oP '\d+')
    if [ -n "$TOTAL_ISSUES" ]; then
        echo "  Total issues found: $TOTAL_ISSUES"
    fi
else
    echo "ℹ No sample report found (run script.py to generate)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "9. FINAL ASSESSMENT"
echo "═══════════════════════════════════════════════════════════════"
echo ""

ISSUES=0
WARNINGS=0

# Critical checks
if [ ! -f "send_team_email.py" ]; then
    echo "❌ CRITICAL: send_team_email.py missing"
    ISSUES=$((ISSUES + 1))
fi

if [ ! -d ".github/workflows" ]; then
    echo "❌ CRITICAL: GitHub Actions workflows missing"
    ISSUES=$((ISSUES + 1))
fi

if [ $SYNTAX_ERRORS -gt 0 ]; then
    echo "❌ CRITICAL: Python syntax errors found"
    ISSUES=$((ISSUES + 1))
fi

# Check if changes need to be pushed
UNPUSHED_COUNT=$(git status --short 2>/dev/null | wc -l)
if [ "$UNPUSHED_COUNT" -gt 0 ]; then
    echo "⚠ WARNING: You have $UNPUSHED_COUNT uncommitted/unpushed changes"
    WARNINGS=$((WARNINGS + 1))
fi

# Check team emails
if grep -q "team-member1@company.com" send_team_email.py 2>/dev/null; then
    echo "⚠ WARNING: Placeholder emails still in send_team_email.py"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ EVERYTHING LOOKS GREAT!"
    echo ""
    echo "Your repository is ready for automated weekly reports!"
    echo ""
    echo "Next steps:"
    echo "  1. Make sure GitHub Secrets are configured"
    echo "  2. Push any remaining changes: git push"
    echo "  3. Emails will be sent automatically every Friday at noon"
elif [ $ISSUES -eq 0 ]; then
    echo "✅ REPOSITORY IS FUNCTIONAL (with $WARNINGS warning(s))"
    echo ""
    echo "Address the warnings above for optimal operation."
else
    echo "❌ ISSUES FOUND: $ISSUES critical issue(s), $WARNINGS warning(s)"
    echo ""
    echo "Please fix the critical issues above."
fi

echo "═══════════════════════════════════════════════════════════════"

