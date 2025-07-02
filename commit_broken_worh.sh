#!/bin/bash
# Git workflow to safely branch your PayPal integration work

echo "=== Git Branch Workflow for PayPal Integration ==="

# 1. Ensure you're on the main/master branch first
echo "1. Current branch status:"
git branch
echo ""

# 2. Stash any uncommitted changes (if any)
echo "2. Stashing any uncommitted changes..."
git stash save "WIP: PayPal integration with migration issues"

# 3. Create a new branch from your stable main branch
echo "3. Creating new branch for PayPal integration..."
git checkout main  # or 'master' if that's your default branch
git checkout -b feature/paypal-integration-fix

# 4. Apply the stashed changes to the new branch
echo "4. Applying stashed changes to new branch..."
git stash pop || echo "No stashed changes to apply"

# 5. Add all changes including new files
echo "5. Adding all changes..."
git add -A

# 6. Commit with a descriptive message
echo "6. Creating commit..."
git commit -m "WIP: PayPal integration with migration dependency issues

Current state:
- Added payments app with PayPal integration
- Encountered migration dependency issues
- event_management.0004_booking depends on deleted payments migration
- Migration files have been partially restored from backup
- Need to resolve migration graph inconsistencies

Files affected:
- payments/ (new app)
- event_management/migrations/
- booking/migrations/
- Docker configuration updates"

# 7. Push to GitHub
echo "7. Pushing to GitHub..."
echo "Run: git push -u origin feature/paypal-integration-fix"
