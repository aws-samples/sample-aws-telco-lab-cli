#!/bin/bash
# Branch Protection Setup Script for TelcoCLI
# Requires: gh CLI (GitHub CLI) installed and authenticated

REPO="aws-samples/sample-aws-telco-lab-cli"
BRANCHES=("main")

echo "Setting up branch protection for $REPO..."

for BRANCH in "${BRANCHES[@]}"; do
  echo "Configuring protection for branch: $BRANCH"
  
  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/$REPO/branches/$BRANCH/protection" \
    -f required_status_checks[strict]=true \
    -f required_status_checks[contexts][]=lint \
    -f required_status_checks[contexts][]=type-check \
    -f required_status_checks[contexts][]=test \
    -f required_status_checks[contexts][]=security \
    -f required_status_checks[contexts][]=build \
    -f enforce_admins=true \
    -f required_pull_request_reviews[dismiss_stale_reviews]=true \
    -f required_pull_request_reviews[require_code_owner_reviews]=false \
    -f required_pull_request_reviews[required_approving_review_count]=1 \
    -f restrictions=null \
    -f allow_force_pushes=false \
    -f allow_deletions=false \
    -f block_creations=false \
    -f required_conversation_resolution=true \
    -f lock_branch=false \
    -f allow_fork_syncing=true
  
  echo "✓ Branch protection enabled for $BRANCH"
done

echo "Done! Branch protection configured."
