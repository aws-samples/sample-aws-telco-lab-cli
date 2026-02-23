# Data Classification Guide

**Document Version:** 1.0
**Last Updated:** 2025-02-10
**Owner:** TelcoCLI Security Team

---

## Overview

This guide defines data classification levels and handling requirements for TelcoCLI. All data processed, stored, or transmitted by the CLI must be classified and handled according to these guidelines.

> **WARNING:** This is sample code for demonstration purposes. Adapt classification levels and handling requirements to your organization's data governance policies before production use.

---

## Classification Levels

| Level | Label | Description | Examples in TelcoCLI |
|-------|-------|-------------|---------------------|
| 1 | **PUBLIC** | Non-sensitive, freely shareable | CLI help text, command names, documentation, error codes |
| 2 | **INTERNAL** | Internal use only, low impact if disclosed | AWS region names, instance types, cluster names, log messages |
| 3 | **CONFIDENTIAL** | Business-sensitive, moderate impact | AWS account IDs, partner names, configuration files, IAM role names |
| 4 | **RESTRICTED** | Highly sensitive, significant impact | VPN private keys, certificates, AWS credentials, session tokens |

---

## Handling Requirements by Level

### PUBLIC (Level 1)

| Control | Requirement |
|---------|-------------|
| Storage | No restrictions |
| Transmission | No encryption required |
| Logging | Can be logged freely |
| Display | Can be displayed to any user |
| Retention | No restrictions |
| Disposal | No special handling |

**TelcoCLI examples:** Command help text, AWS service names, documentation content, exit codes.

### INTERNAL (Level 2)

| Control | Requirement |
|---------|-------------|
| Storage | Standard file permissions |
| Transmission | HTTPS recommended |
| Logging | Can be logged at INFO level |
| Display | Display to authenticated users |
| Retention | Follow standard retention policies |
| Disposal | Standard deletion |

**TelcoCLI examples:** AWS region, instance types, cluster names, outpost IDs, host IDs, non-sensitive configuration values.

### CONFIDENTIAL (Level 3)

| Control | Requirement |
|---------|-------------|
| Storage | Encrypted at rest recommended |
| Transmission | HTTPS/TLS required |
| Logging | Sanitize before logging (use `sanitize_for_logging()`) |
| Display | Display only to authorized users |
| Retention | Minimum necessary retention |
| Disposal | Secure deletion |

**TelcoCLI examples:** AWS account IDs, partner names, IAM role ARNs, configuration files with account references, email addresses.

### RESTRICTED (Level 4)

| Control | Requirement |
|---------|-------------|
| Storage | Encrypted at rest required, restrictive file permissions (0o600) |
| Transmission | TLS 1.2+ required, end-to-end encryption recommended |
| Logging | Never log — use `sanitize_for_logging()` to redact |
| Display | Mask or redact in output |
| Retention | Minimum possible, delete after use |
| Disposal | Secure overwrite or cryptographic erasure |

**TelcoCLI examples:** VPN private keys, VPN certificates, AWS access keys, secret keys, session tokens, Bedrock API responses containing sensitive context.

---

## Code Annotation Format

When handling data in code, annotate with classification comments:

```python
# DATA CLASSIFICATION: RESTRICTED — VPN private key material
private_key = generate_private_key()
file_path.write_text(private_key)
os.chmod(file_path, 0o600)  # Restrictive permissions required

# DATA CLASSIFICATION: CONFIDENTIAL — AWS account identifier
account_id = args.partner_account_id

# DATA CLASSIFICATION: INTERNAL — Cluster configuration
cluster_name = args.cluster_name

# DATA CLASSIFICATION: PUBLIC — Help text
description = "Deploy EKS cluster infrastructure"
```

---

## Classification by TelcoCLI Component

### VPN Operations (`commands/vpn/`)

| Data | Classification | Handling |
|------|---------------|----------|
| Partner name | CONFIDENTIAL | Sanitize in logs |
| Private keys | RESTRICTED | 0o600 permissions, never log |
| Certificates | RESTRICTED | 0o600 permissions, never log |
| .ovpn files | RESTRICTED | 0o600 permissions |
| Allowed subnets | INTERNAL | Standard handling |
| Certificate duration | PUBLIC | No restrictions |

### Partner Operations (`commands/create_partner.py`, etc.)

| Data | Classification | Handling |
|------|---------------|----------|
| Partner name | CONFIDENTIAL | Sanitize in logs |
| AWS account ID | CONFIDENTIAL | Validate format, sanitize in logs |
| Admin account IDs | CONFIDENTIAL | Validate format |
| Contact email | CONFIDENTIAL | Never log |
| IAM role ARNs | CONFIDENTIAL | Sanitize in logs |
| Account type | INTERNAL | Standard handling |

### EKS Operations (`commands/deploy_eks_full.py`)

| Data | Classification | Handling |
|------|---------------|----------|
| Cluster name | INTERNAL | Standard handling |
| VPC CIDR | INTERNAL | Standard handling |
| Grafana password | RESTRICTED | Auto-generated, never log |
| AWS profile | CONFIDENTIAL | Never hardcode |
| Terraform state | CONFIDENTIAL | Encrypt at rest |
| Key pair name | CONFIDENTIAL | Reference only, never store key material |

### Outpost Operations (`commands/describe_outpost.py`, etc.)

| Data | Classification | Handling |
|------|---------------|----------|
| Outpost ID | INTERNAL | Standard handling |
| Host ID | INTERNAL | Standard handling |
| Instance IDs | INTERNAL | Standard handling |
| Cross-account IDs | CONFIDENTIAL | Sanitize in logs |
| RAM share ARNs | CONFIDENTIAL | Sanitize in logs |
| Asset IDs | INTERNAL | Standard handling |

### AI Agent (`commands/ask_agent.py`)

| Data | Classification | Handling |
|------|---------------|----------|
| User queries | INTERNAL | Do not persist, warn about sensitive input |
| AI responses | INTERNAL | Do not persist, display disclaimer |
| Session IDs | INTERNAL | Memory only, no disk storage |
| Bedrock credentials | RESTRICTED | Standard AWS credential chain only |
| System prompts | INTERNAL | Do not expose to users |

---

## Implementation Checklist

### For New Features

- [ ] Identify all data elements the feature handles
- [ ] Classify each data element using the levels above
- [ ] Add `# DATA CLASSIFICATION:` comments to code
- [ ] Implement appropriate handling controls for each level
- [ ] Verify RESTRICTED data is never logged
- [ ] Verify CONFIDENTIAL data is sanitized before logging
- [ ] Test with `sanitize_for_logging()` for sensitive outputs

### For Code Reviews

- [ ] All data elements are classified
- [ ] RESTRICTED data has 0o600 file permissions
- [ ] RESTRICTED data is never in log output
- [ ] CONFIDENTIAL data uses `sanitize_for_logging()`
- [ ] No credentials hardcoded in source
- [ ] Encryption used for RESTRICTED data at rest

---

## References

- [Encryption Implementation Guide](./ENCRYPTION_IMPLEMENTATION_GUIDE.md)
- [Data Security Strategy](./DATA_SECURITY_STRATEGY.md)
- [SECURITY.md](../../SECURITY.md)
