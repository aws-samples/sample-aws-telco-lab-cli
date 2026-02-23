# Security Testing Procedures

**Document Version:** 1.0
**Last Updated:** 2025-02-10
**Owner:** TelcoCLI Security Team

---

## Overview

This document defines security testing procedures for TelcoCLI, covering static analysis, dependency scanning, infrastructure validation, and manual security review.

> **WARNING:** This is sample code for demonstration purposes. Adapt testing procedures to your organization's security requirements.

---

## 1. Static Analysis (Automated)

### Python Security Scanning (Bandit)

```bash
# Install
pip install bandit

# Run against source
bandit -r src/telco_cli/ -f json -o bandit_results.json

# Run with severity filter
bandit -r src/telco_cli/ -ll  # Medium and above only
```

**What Bandit checks:**
- Hardcoded passwords and secrets (B105, B106, B107)
- Use of `exec()` or `eval()` (B102)
- Subprocess with `shell=True` (B602, B603)
- SQL injection patterns (B608)
- Insecure temp file creation (B108)
- Weak cryptographic functions (B303, B304)

**Expected results:** See `doc/security/SECURITY_SCAN_RESULTS.md` for baseline.

### Terraform Security Scanning (Checkov)

```bash
# Install
pip install checkov

# Run against templates
checkov -d src/telco_cli/templates/terraform/ --framework terraform

# Run with specific checks
checkov -d src/telco_cli/templates/terraform/ --check CKV_AWS_24,CKV_AWS_79,CKV_AWS_8
```

**Key checks:**
- CKV_AWS_24: SSH from 0.0.0.0/0
- CKV_AWS_79: IMDSv1 enabled
- CKV_AWS_8: Unencrypted EBS volumes
- CKV_AWS_88: Public IP on instances
- CKV_AWS_355: IAM wildcard resources

### Linting and Type Checking

```bash
# Linting
flake8 .

# Type checking
mypy src/

# Import sorting
isort --check-only .
```

---

## 2. Dependency Scanning

### Check for Known Vulnerabilities

```bash
# Using pip-audit
pip install pip-audit
pip-audit -r requirements.txt

# Using safety
pip install safety
safety check -r requirements.txt
```

### License Compliance

```bash
# Check dependency licenses
pip install pip-licenses
pip-licenses --format=table --with-urls
```

Verify all licenses are compatible with MIT-0. See `NOTICE` for current attributions.

---

## 3. Manual Security Review

### Credential Audit

```bash
# Search for hardcoded credentials
grep -rn "AKIA\|password\|secret\|token" src/telco_cli/ --include="*.py" | grep -v test | grep -v __pycache__

# Search for hardcoded account IDs
grep -rn "[0-9]\{12\}" src/telco_cli/ --include="*.py" | grep -v test | grep -v __pycache__

# Search for internal references
grep -rn "@amazon.com\|\.amazon\.com\|internal" src/telco_cli/ --include="*.py" | grep -v __pycache__
```

### Subprocess Security Audit

```bash
# Find all subprocess calls
grep -rn "subprocess\|shell=True\|os.system\|os.popen" src/telco_cli/ --include="*.py" | grep -v __pycache__

# Verify no shell=True
grep -rn "shell=True" src/telco_cli/ --include="*.py" | grep -v __pycache__ | grep -v test
```

### File Permission Audit

```bash
# Find file write operations
grep -rn "write_text\|write_bytes\|open.*w\|chmod" src/telco_cli/ --include="*.py" | grep -v __pycache__

# Verify sensitive files use restrictive permissions
grep -rn "0o600\|0o400\|0o700" src/telco_cli/ --include="*.py" | grep -v __pycache__
```

---

## 4. Infrastructure Validation

### Terraform Validation

```bash
cd src/telco_cli/templates/terraform/eks/
terraform init -backend=false
terraform validate
terraform fmt -check -recursive
```

### Security Group Review

Manually verify:
- No 0.0.0.0/0 on SSH (port 22) without justification
- Egress rules are as restrictive as possible
- Security groups are tagged with purpose

---

## 5. Testing Schedule

| Test Type | Frequency | Automated? |
|-----------|-----------|------------|
| Bandit scan | Every build | Yes (brazil-build release) |
| Checkov scan | Every Terraform change | Manual |
| Dependency audit | Weekly | Recommended |
| Credential audit | Before each release | Manual |
| Full security review | Quarterly | Manual |

---

## References

- [Security Scan Results](./SECURITY_SCAN_RESULTS.md)
- [Security Checklists](./SECURITY_CHECKLISTS.md)
- [SECURITY.md](../../SECURITY.md)
