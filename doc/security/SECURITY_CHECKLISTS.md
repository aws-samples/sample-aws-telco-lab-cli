# Security Checklists

**Document Version:** 1.0
**Last Updated:** 2025-02-10
**Owner:** TelcoCLI Security Team

---

## 1. Pre-Deployment Security Checklist

Complete before deploying TelcoCLI or its managed infrastructure to any environment.

### Credential Security
- [ ] No hardcoded AWS credentials in source code
- [ ] No hardcoded API keys or tokens
- [ ] No hardcoded passwords (including Grafana)
- [ ] AWS profiles use standard credential chain (env vars, CLI config, instance profile)
- [ ] VPN private keys have 0o600 file permissions

### IAM Policy Review
- [ ] No `Action: "*"` with `Resource: "*"` in IAM policies
- [ ] No `iam:*` wildcard actions
- [ ] Permission boundaries attached to all created roles
- [ ] Cross-account roles use ExternalId conditions
- [ ] Admin roles follow least-privilege principle

### Encryption
- [ ] TLS 1.2+ enforced for all API calls (boto3 default)
- [ ] S3 buckets have server-side encryption enabled
- [ ] S3 bucket policies deny unencrypted transport (`aws:SecureTransport`)
- [ ] Terraform state stored in encrypted S3 bucket
- [ ] KMS keys configured with automatic rotation

### Input Validation
- [ ] All CLI inputs validated before processing
- [ ] AWS account IDs validated (12-digit format)
- [ ] ARNs validated against expected format
- [ ] Subprocess calls use list-based arguments (no shell=True)
- [ ] Command length limits enforced

### Content Sanitization
- [ ] No internal email addresses in source code
- [ ] No internal hostnames or URLs
- [ ] No internal account IDs or ARNs
- [ ] MIT-0 copyright headers on all source files
- [ ] NOTICE file lists all third-party dependencies

### Security Scanning
- [ ] Bandit scan completed (Python security)
- [ ] Checkov scan completed (Terraform security)
- [ ] All critical/high findings addressed or documented
- [ ] Security scan results documented in SECURITY_SCAN_RESULTS.md

---

## 2. Post-Deployment Security Checklist

Complete after deploying infrastructure managed by TelcoCLI.

### Logging and Monitoring
- [ ] CloudTrail enabled in all accounts
- [ ] CloudTrail logs encrypted with KMS
- [ ] CloudTrail log file validation enabled
- [ ] CloudWatch alarms configured for security events
- [ ] VPC flow logs enabled for all VPCs
- [ ] S3 access logging enabled for sensitive buckets

### Network Security
- [ ] Security groups restrict inbound access to required ports only
- [ ] No 0.0.0.0/0 on SSH (port 22) without explicit justification
- [ ] Bastion hosts use IMDSv2 (http_tokens = "required")
- [ ] EKS control plane endpoint access restricted
- [ ] VPN server security groups properly configured

### Account Security
- [ ] AWS Organizations SCPs applied
- [ ] Management account protected (no workloads)
- [ ] Partner accounts have permission boundaries
- [ ] Cross-account roles audited and documented
- [ ] RAM resource shares reviewed

### Data Protection
- [ ] EBS volumes encrypted
- [ ] S3 Block Public Access enabled on all buckets
- [ ] Terraform state bucket versioning enabled
- [ ] Backup strategy documented and tested
- [ ] Data classification applied per DATA_CLASSIFICATION_GUIDE.md

### Operational Readiness
- [ ] Incident response procedures documented
- [ ] On-call rotation established
- [ ] Runbooks created for common operations
- [ ] Credential rotation schedule established
- [ ] VPN certificate expiration monitoring in place

---

## 3. Code Review Security Checklist

Use during code reviews for TelcoCLI changes.

### Credential Handling
- [ ] No hardcoded credentials, API keys, or tokens
- [ ] No AWS account IDs in source (use variables/config)
- [ ] Credentials use standard AWS credential chain
- [ ] Sensitive data not logged (use `sanitize_for_logging()`)

### Input Validation
- [ ] All user inputs validated before use
- [ ] Account IDs validated with `validate_aws_account_id()`
- [ ] ARNs validated with `validate_aws_arn()`
- [ ] Resource names validated with `validate_resource_name()`
- [ ] No unsanitized input in subprocess calls

### Subprocess Security
- [ ] No `shell=True` in subprocess calls
- [ ] Commands use list-based arguments
- [ ] Command length limits enforced
- [ ] Terraform variables validated before use

### Error Handling
- [ ] Exceptions don't leak sensitive information
- [ ] Error messages are user-friendly and actionable
- [ ] `TelcoCLIException` used with appropriate `ErrorCode`
- [ ] No bare `except:` clauses (catch specific exceptions)

### File Operations
- [ ] Private keys written with 0o600 permissions
- [ ] Temporary files cleaned up after use
- [ ] File paths validated (no path traversal)
- [ ] No sensitive data written to world-readable locations

### Logging
- [ ] No credentials in log output
- [ ] No private keys in log output
- [ ] `sanitize_for_logging()` used for sensitive context
- [ ] Log levels appropriate (no DEBUG in production)

### Dependencies
- [ ] New dependencies reviewed for security
- [ ] License compatibility verified (MIT-0 compatible)
- [ ] NOTICE file updated with new attributions
- [ ] No known vulnerabilities in added packages

---

## References

- [Data Classification Guide](./DATA_CLASSIFICATION_GUIDE.md)
- [Encryption Implementation Guide](./ENCRYPTION_IMPLEMENTATION_GUIDE.md)
- [IAM Least Privilege Guide](./IAM_LEAST_PRIVILEGE_GUIDE.md)
- [SECURITY.md](../../SECURITY.md)
