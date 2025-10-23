#!/bin/bash
# Script to push to GitHub with proper instructions

echo "========================================"
echo "  PUSH TO GITHUB - STEP BY STEP"
echo "========================================"
echo ""

cd /home/acardinalli/dev/terraform/issues_analyzer

# Check if we have commits
if ! git log --oneline -1 > /dev/null 2>&1; then
    echo "❌ No commits found. Please commit your changes first."
    exit 1
fi

echo "✓ Repository ready with commits"
echo ""
echo "Your repository: https://github.com/SCSAndre/terraform-provider-google-issues-analyzer"
echo ""
echo "========================================"
echo "CHOOSE YOUR AUTHENTICATION METHOD:"
echo "========================================"
echo ""
echo "Option 1: GitHub CLI (gh auth login)"
echo "Option 2: Personal Access Token"
echo "Option 3: SSH Key"
echo ""
echo "I'll try each method automatically..."
echo ""

# Try GitHub CLI first
if command -v gh &> /dev/null; then
    echo "→ Trying GitHub CLI..."
    if gh auth status &> /dev/null; then
        echo "✓ GitHub CLI authenticated!"
        echo ""
        echo "Pushing to GitHub..."
        git push -u origin main
        if [ $? -eq 0 ]; then
            echo ""
            echo "🎉 SUCCESS! Your code is now on GitHub!"
            echo "Visit: https://github.com/SCSAndre/terraform-provider-google-issues-analyzer"
            exit 0
        fi
    else
        echo "GitHub CLI found but not authenticated."
        echo ""
        echo "To authenticate with GitHub CLI, run:"
        echo "  gh auth login"
        echo ""
    fi
else
    echo "→ GitHub CLI not found"
fi

# Try regular git push
echo ""
echo "→ Attempting git push (will prompt for credentials)..."
echo ""
echo "INSTRUCTIONS:"
echo "1. Username: SCSAndre"
echo "2. Password: Use your GitHub Personal Access Token (NOT your GitHub password)"
echo ""
echo "Don't have a token? Create one at:"
echo "https://github.com/settings/tokens/new"
echo "  - Select 'repo' scope"
echo "  - Copy the token and use it as your password"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Your code is now on GitHub!"
    echo "Visit: https://github.com/acardinalli/terraform-provider-google-issues-analyzer"
else
    echo ""
    echo "❌ Push failed. Let's try SSH method..."
    echo ""
    echo "To use SSH (recommended for future):"
    echo "1. Generate SSH key (if you don't have one):"
    echo "   ssh-keygen -t ed25519 -C 'acardinalli@ciandt.com'"
    echo ""
    echo "2. Add to GitHub:"
    echo "   cat ~/.ssh/id_ed25519.pub"
    echo "   Copy output to: https://github.com/settings/ssh/new"
    echo ""
    echo "3. Change remote to SSH:"
    echo "   git remote set-url origin git@github.com:SCSAndre/terraform-provider-google-issues-analyzer.git"
    echo ""
    echo "4. Try push again:"
    echo "   git push -u origin main"
fi

