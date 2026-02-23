# Amazon Bedrock Security Guidelines

**Document Version:** 1.0
**Last Updated:** 2025-02-10
**Owner:** TelcoCLI Security Team

---

## Overview

TelcoCLI integrates Amazon Bedrock via the `ask-agent` command to provide an AI-powered assistant for CLI operations. This document covers the IAM permissions required, data handling practices, prompt injection prevention, and security warnings for AI-generated content.

> **WARNING:** This is sample code for demonstration purposes. Review all Bedrock configurations and IAM policies before production use. AI-generated responses should always be verified by a human before execution.

---

## Table of Contents

1. [IAM Permissions](#iam-permissions)
2. [Credential Management](#credential-management)
3. [Data Handling](#data-handling)
4. [Prompt Injection Prevention](#prompt-injection-prevention)
5. [AI-Generated Content Warnings](#ai-generated-content-warnings)
6. [Security Controls](#security-controls)
7. [Operational Guidelines](#operational-guidelines)

---

## IAM Permissions

### Minimum Required Permissions

The `ask-agent` command requires the following IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
        "arn:aws:bedrock:*::foundation-model/us.anthropic.claude-*"
      ]
    }
  ]
}
```

### Recommended Restrictions

For production use, scope permissions further:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeModelRestricted",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-west-2::foundation-model/us.anthropic.claude-sonnet-4-20250514-v1:0"
      ],
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": ["us-west-2", "us-east-1"]
        }
      }
    }
  ]
}
```

### Permissions NOT Required

The `ask-agent` command does NOT need:
- `bedrock:CreateModelCustomizationJob` — no fine-tuning
- `bedrock:CreateProvisionedModelThroughput` — uses on-demand
- `bedrock:*` — never use wildcard permissions for Bedrock
- `bedrock:GetFoundationModel` — not needed for invocation

---

## Credential Management

### How Credentials Are Used

TelcoCLI uses the standard AWS credential chain for Bedrock access:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS CLI profile (`--profile` flag or `AWS_PROFILE` env var)
3. IAM instance profile (when running on EC2)
4. AWS SSO / IAM Identity Center

### Security Guarantees

- No credentials are hardcoded in the source code
- No API keys or tokens are stored to disk by the agent
- Credentials are never sent to the AI model as part of prompts
- Session tokens are temporary (STS-based)
- Credential validation occurs before any Bedrock API call

### What Is NOT Sent to Bedrock

The following are explicitly excluded from Bedrock API calls:

| Data Type | Sent to Bedrock? |
|-----------|-----------------|
| AWS access keys | Never |
| AWS secret keys | Never |
| Session tokens | Never |
| Account IDs | Never |
| VPN private keys | Never |
| Partner credentials | Never |
| User passwords | Never |

---

## Data Handling

### Data Flow

```
User Query → TelcoCLI Agent → Amazon Bedrock API → Response → Terminal Display
                  │                                      │
                  │ (no storage)                          │ (no storage)
                  ▼                                      ▼
           Local context only                    Displayed to user only
```

### What IS Sent to Bedrock

- User's natural language query
- CLI context (available commands, help text)
- Knowledge base context (command descriptions, usage patterns)

### What IS NOT Sent to Bedrock

- AWS credentials or tokens
- Account IDs or resource ARNs
- VPN certificates or private keys
- Partner-specific configuration data
- Any data from AWS API responses

### Data Retention

- TelcoCLI does not store queries or responses to disk
- Session history is kept in memory only during the session
- Amazon Bedrock's data retention policies apply to API calls
- See [Amazon Bedrock Data Privacy](https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html)

---

## Prompt Injection Prevention

### Current Controls

| Control | Description | Status |
|---------|-------------|--------|
| System prompt isolation | System instructions separated from user input | ✅ Implemented |
| No auto-execution | AI cannot execute commands directly | ✅ Implemented |
| Input length limits | Queries bounded by Bedrock API limits | ✅ Implemented |
| Output display only | Responses shown in terminal, not executed | ✅ Implemented |
| Human-in-the-loop | User must manually execute any suggestions | ✅ Implemented |

### Recommended Additional Controls

For production deployments, consider:

1. **Input sanitization** — Strip control characters and escape sequences before sending to Bedrock
2. **Output validation** — Check AI responses for suspicious patterns (e.g., encoded commands, URLs to unknown domains)
3. **Query logging** — Log queries (without sensitive data) for audit purposes
4. **Rate limiting** — Implement application-level rate limiting beyond Bedrock's built-in limits
5. **Content filtering** — Use Bedrock Guardrails to filter inappropriate content

### Attack Vectors to Monitor

| Vector | Risk | Mitigation |
|--------|------|------------|
| Direct prompt injection | User crafts input to override system prompt | System prompt isolation, no auto-execution |
| Indirect prompt injection | Malicious content in knowledge base | Knowledge base is read-only, built from trusted sources |
| Data exfiltration via prompt | User tries to extract system prompt | System prompt does not contain secrets |
| Command injection via response | AI suggests malicious commands | Human review required before execution |

---

## AI-Generated Content Warnings

### Warnings Displayed to Users

1. AI responses may contain inaccuracies — always verify before executing
2. AI suggestions are advisory only — the user is responsible for all actions taken
3. Do not include sensitive information (credentials, private keys, PII) in queries
4. Amazon Bedrock charges apply when using the `ask-agent` command

### Limitations of AI Responses

- Responses may be outdated (model knowledge cutoff applies)
- Complex AWS configurations may be incomplete or incorrect
- Region-specific features may not be accurately reflected
- Cost estimates in responses are approximate

### User Responsibilities

- Verify all AI-suggested commands before execution
- Review IAM policies suggested by AI for least privilege
- Test AI-suggested configurations in non-production environments first
- Do not rely on AI for security-critical decisions without human review

---

## Security Controls

### Control Matrix

| Control | Description | Status |
|---------|-------------|--------|
| Authentication | AWS credentials required | ✅ |
| Authorization | Bedrock IAM permissions required | ✅ |
| Encryption in transit | HTTPS/TLS to Bedrock API | ✅ (AWS SDK default) |
| No credential storage | Agent does not cache credentials | ✅ |
| No data persistence | Queries/responses not stored to disk | ✅ |
| Audit logging | CloudTrail logs Bedrock API calls | ✅ (AWS default) |
| Human-in-the-loop | No autonomous command execution | ✅ |
| Input validation | Basic query validation | ✅ |
| Output sanitization | Terminal-safe display | ⚠️ Basic |
| Bedrock Guardrails | Content filtering | 📋 Recommended |

### Model Configuration

TelcoCLI uses the following Bedrock model configuration:

- **Model:** `us.anthropic.claude-sonnet-4-20250514-v1:0`
- **Regions:** `us-west-2` (primary), `us-east-1` (fallback)
- **Framework:** strands-agents SDK
- **Invocation:** On-demand (no provisioned throughput)

---

## Operational Guidelines

### Before Enabling Bedrock Access

- [ ] Verify Bedrock is available in your target region
- [ ] Create IAM policy with minimum required permissions
- [ ] Test credential chain works (`aws bedrock list-foundation-models`)
- [ ] Review Bedrock pricing for your expected usage
- [ ] Enable CloudTrail logging for Bedrock API calls

### Monitoring

- Monitor Bedrock API usage via CloudWatch metrics
- Review CloudTrail logs for unexpected Bedrock invocations
- Set up billing alerts for Bedrock charges
- Track error rates for credential or permission issues

### Incident Response

If you suspect misuse of the Bedrock integration:

1. Revoke the IAM permissions for Bedrock access
2. Review CloudTrail logs for the affected time period
3. Check for unauthorized queries or unusual patterns
4. Rotate any credentials that may have been exposed
5. Report the incident per your organization's security procedures

---

## References

- [Amazon Bedrock Security](https://docs.aws.amazon.com/bedrock/latest/userguide/security.html)
- [Amazon Bedrock Data Protection](https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html)
- [Amazon Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)
- [AWS Responsible AI](https://aws.amazon.com/machine-learning/responsible-ai/)
- [GenAI Use Case Documentation](../ai/GENAI_USE_CASE.md)
- [Third-Party Components](../ai/THIRD_PARTY_COMPONENTS.md)
