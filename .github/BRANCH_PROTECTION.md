# Branch Protection Configuration

This document describes the branch protection rules for the TelcoCLI repository.

## Protected Branches

- `main`

## Protection Rules

### Required Status Checks
All checks must pass before merging:
- ✅ **lint** - Code formatting (black, isort, flake8)
- ✅ **type-check** - Static type checking (mypy)
- ✅ **test** - Unit tests across Python 3.9, 3.10, 3.11
- ✅ **security** - Security scanning (bandit, safety)
- ✅ **build** - Package build validation

### Pull Request Requirements
- **1 approving review** required before merge
- **Dismiss stale reviews** when new commits are pushed
- **Require conversation resolution** before merge

### Additional Protections
- ❌ **No force pushes** allowed
- ❌ **No branch deletion** allowed
- ✅ **Enforce for administrators** - admins must follow same rules
- ✅ **Require branches to be up to date** before merging

## Setup Instructions

### Option 1: Using GitHub CLI (Automated)

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Authenticate
gh auth login

# Run the setup script
cd .github
./setup-branch-protection.sh
```

### Option 2: Manual Configuration via GitHub UI

1. Go to repository **Settings** → **Branches**
2. Click **Add branch protection rule**
3. For branch `main`:

   **Branch name pattern:** `main`
   
   Enable:
   - ☑️ Require a pull request before merging
     - Required approvals: 1
     - ☑️ Dismiss stale pull request approvals when new commits are pushed
   - ☑️ Require status checks to pass before merging
     - ☑️ Require branches to be up to date before merging
     - Select status checks: `lint`, `type-check`, `test`, `security`, `build`
   - ☑️ Require conversation resolution before merging
   - ☑️ Do not allow bypassing the above settings
   - ☑️ Restrict who can push to matching branches (optional)

4. Click **Create** or **Save changes**

## Bypassing Protection (Emergency Only)

Repository administrators can temporarily disable protection rules in emergency situations:
1. Go to Settings → Branches
2. Edit the branch protection rule
3. Uncheck "Do not allow bypassing the above settings"
4. Make emergency changes
5. Re-enable protection immediately after

## Testing Branch Protection

After setup, verify by:
1. Creating a test branch
2. Making a change that fails linting (e.g., remove a newline)
3. Opening a PR
4. Confirm CI fails and merge is blocked
