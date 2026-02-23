# Security Monitoring Guidelines

**Document Version:** 1.0
**Last Updated:** 2025-02-10
**Owner:** TelcoCLI Security Team

---

## Overview

This document defines security monitoring requirements for infrastructure deployed by TelcoCLI, including CloudWatch alarms, CloudTrail configuration, and incident response procedures.

> **WARNING:** This is sample code for demonstration purposes. Adapt monitoring configurations to your organization's requirements.

---

## 1. CloudTrail Configuration

### Required Settings

```bash
# Create trail for all regions
aws cloudtrail create-trail \
  --name telcocli-security-trail \
  --s3-bucket-name telcocli-cloudtrail-logs \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --kms-key-id arn:aws:kms:REGION:ACCOUNT:key/KEY-ID

# Start logging
aws cloudtrail start-logging --name telcocli-security-trail
```

### Events to Monitor

| Event | CloudTrail Event Name | Severity |
|-------|----------------------|----------|
| IAM role creation | CreateRole | High |
| IAM policy changes | PutRolePolicy, AttachRolePolicy | High |
| Cross-account role assumption | AssumeRole | Medium |
| Security group changes | AuthorizeSecurityGroupIngress | High |
| KMS key operations | CreateKey, DisableKey, ScheduleKeyDeletion | Critical |
| S3 bucket policy changes | PutBucketPolicy | High |
| Account creation | CreateAccount | High |
| VPN certificate operations | SendCommand (SSM) | Medium |
| Bedrock API calls | InvokeModel | Low |

---

## 2. CloudWatch Alarms

### IAM Security Alarms

```bash
# Alarm: Root account usage
aws cloudwatch put-metric-alarm \
  --alarm-name "RootAccountUsage" \
  --metric-name "RootAccountUsageCount" \
  --namespace "CloudTrailMetrics" \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:REGION:ACCOUNT:security-alerts

# Alarm: Unauthorized API calls
aws cloudwatch put-metric-alarm \
  --alarm-name "UnauthorizedAPICalls" \
  --metric-name "UnauthorizedAttemptCount" \
  --namespace "CloudTrailMetrics" \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:REGION:ACCOUNT:security-alerts
```

### Infrastructure Alarms

| Alarm | Metric | Threshold | Action |
|-------|--------|-----------|--------|
| IAM policy changes | IAMPolicyChangeCount | >= 1 | SNS notification |
| Security group changes | SecurityGroupChangeCount | >= 1 | SNS notification |
| Failed console logins | ConsoleSignInFailureCount | >= 3 in 5 min | SNS notification |
| KMS key deletion | KMSKeyDeletionCount | >= 1 | SNS + PagerDuty |
| S3 bucket public access | S3BucketPublicAccessCount | >= 1 | SNS + PagerDuty |

---

## 3. Incident Response Procedures

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P1 - Critical | Active breach or data exposure | 15 minutes | Credential leak, unauthorized access |
| P2 - High | Security control failure | 1 hour | IAM policy misconfiguration, public S3 bucket |
| P3 - Medium | Suspicious activity | 4 hours | Unusual API patterns, failed auth attempts |
| P4 - Low | Security improvement needed | Next business day | Missing logging, outdated dependencies |

### Response Steps

1. **Detect** — CloudWatch alarm or manual discovery
2. **Contain** — Revoke compromised credentials, isolate affected resources
3. **Investigate** — Review CloudTrail logs, identify scope of impact
4. **Remediate** — Fix root cause, patch vulnerabilities
5. **Recover** — Restore services, verify security controls
6. **Document** — Post-incident report with timeline and lessons learned

### Credential Compromise Response

```bash
# 1. Immediately disable compromised access keys
aws iam update-access-key --access-key-id AKIA... --status Inactive --user-name USER

# 2. Revoke all active sessions for the role
aws iam put-role-policy --role-name ROLE --policy-name DenyAll --policy-document '{
  "Version": "2012-10-17",
  "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]
}'

# 3. Review CloudTrail for unauthorized activity
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIA... \
  --start-time $(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ)

# 4. Rotate credentials
aws iam create-access-key --user-name USER
```

---

## 4. Log Retention

| Log Type | Retention | Storage |
|----------|-----------|---------|
| CloudTrail | 1 year | S3 + Glacier after 90 days |
| CloudWatch Logs | 90 days | CloudWatch |
| S3 access logs | 1 year | S3 + Glacier after 90 days |
| VPC flow logs | 90 days | CloudWatch |
| Application logs | 30 days | Local + CloudWatch |

---

## References

- [Security Testing Procedures](./SECURITY_TESTING_PROCEDURES.md)
- [Security Checklists](./SECURITY_CHECKLISTS.md)
- [Data Security Strategy](./DATA_SECURITY_STRATEGY.md)
