# Security Responsibilities

**Document Version:** 1.0
**Last Updated:** 2025-02-10
**Owner:** TelcoCLI Security Team

---

## Overview

This document defines the security responsibility boundaries between TelcoCLI (the tool), AWS services, and the customer/operator. It follows the AWS shared responsibility model.

---

## TelcoCLI Responsibilities (Tool Provider)

TelcoCLI is responsible for:

| Area | Responsibility |
|------|---------------|
| Input validation | Validate CLI inputs before passing to AWS APIs |
| Credential handling | Use standard AWS credential chain, never hardcode or cache secrets |
| Subprocess security | Use list-based subprocess calls, no shell=True |
| File permissions | Set restrictive permissions (0o600) on sensitive files (VPN keys, certs) |
| Logging safety | Sanitize sensitive data before logging via `sanitize_for_logging()` |
| Sample code quality | Provide secure defaults and security warnings in documentation |
| Dependency management | Use permissive-licensed dependencies, document in NOTICE |
| AI safety | Human-in-the-loop design for Bedrock integration, no auto-execution |

TelcoCLI is NOT responsible for:

- Runtime AWS credential management (customer's responsibility)
- AWS account security configuration
- Network security of deployed infrastructure
- Monitoring and alerting of deployed resources
- Compliance with regulatory requirements

---

## AWS Service Responsibilities

AWS manages security OF the cloud:

| Service | AWS Responsibility |
|---------|-------------------|
| Bedrock | Model hosting, API security, data isolation between tenants |
| Organizations | Account isolation, SCP enforcement |
| IAM | Authentication infrastructure, credential signing |
| EC2 | Hypervisor security, physical infrastructure |
| EKS | Control plane security, Kubernetes API server |
| S3 | Storage infrastructure, encryption at rest (SSE-S3) |
| SSM | Agent security, session encryption |
| KMS | Key material protection, HSM management |
| CloudTrail | Log integrity, API event capture |

---

## Customer/Operator Responsibilities

The customer manages security IN the cloud:

| Area | Responsibility |
|------|---------------|
| AWS credentials | Configure, rotate, and protect AWS credentials |
| IAM policies | Review and tighten IAM policies created by TelcoCLI for production |
| Network security | Configure security groups, NACLs, and VPC settings |
| Encryption | Enable and manage KMS keys, S3 encryption, EBS encryption |
| Monitoring | Set up CloudWatch alarms, CloudTrail, and alerting |
| Patching | Keep EC2 instances, EKS nodes, and dependencies updated |
| Access control | Manage who can run TelcoCLI and with what permissions |
| VPN security | Distribute VPN certificates securely, rotate regularly |
| Compliance | Ensure deployments meet regulatory requirements |
| Cost management | Monitor AWS costs and set billing alerts |
| AI oversight | Review all AI-generated suggestions before execution |
| Incident response | Detect, respond to, and recover from security incidents |

---

## Responsibility Matrix

| Security Control | TelcoCLI | AWS | Customer |
|-----------------|----------|-----|----------|
| Input validation | ✅ Primary | | |
| Credential storage | | ✅ Infrastructure | ✅ Configuration |
| Transport encryption (TLS) | | ✅ Enforced | |
| Encryption at rest | | ✅ Available | ✅ Must enable |
| IAM least privilege | ✅ Sample policies | | ✅ Must review/tighten |
| Network security | ✅ Sample configs | ✅ VPC infrastructure | ✅ Must configure |
| Logging | ✅ App-level | ✅ CloudTrail/CloudWatch | ✅ Must enable |
| Monitoring/alerting | | ✅ Available | ✅ Must configure |
| Patching | ✅ Dependencies | ✅ Managed services | ✅ EC2/EKS nodes |
| Incident response | | ✅ AWS infrastructure | ✅ Customer resources |
| AI content accuracy | ✅ Warnings/disclaimers | ✅ Model quality | ✅ Must verify |

---

## References

- [SECURITY.md](../../SECURITY.md) — Section 10: Shared Responsibility Model
- [Security Checklists](./SECURITY_CHECKLISTS.md)
- [Security Monitoring Guidelines](./SECURITY_MONITORING_GUIDELINES.md)
