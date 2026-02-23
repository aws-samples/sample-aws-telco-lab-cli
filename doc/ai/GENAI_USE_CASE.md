# Generative AI Use Case Documentation

This document describes the Generative AI capabilities in TelcoCLI and their compliance with AWS AI/ML guidelines.

---

## Overview

TelcoCLI includes an AI-powered assistant feature (`ask-agent` command) that uses Amazon Bedrock to help users with CLI operations, AWS configurations, and troubleshooting.

---

## Use Case Classification

### Primary Use Case

| Attribute | Value |
|-----------|-------|
| **Feature Name** | TelcoCLI AI Assistant |
| **Command** | `telco-cli ask-agent` |
| **AI Service** | Amazon Bedrock (Claude models) |
| **Classification** | Developer Productivity Tool |
| **Risk Level** | Low |

### Use Case Description

The AI assistant helps telecommunications engineers:

1. **Command Discovery**: Find relevant CLI commands for tasks
2. **Configuration Help**: Generate AWS configurations
3. **Troubleshooting**: Diagnose issues with deployments
4. **Documentation**: Explain CLI features and options

---

## Risk Assessment

### Risk Classification: LOW

| Risk Factor | Assessment | Justification |
|-------------|------------|---------------|
| Data Sensitivity | Low | No PII or customer data processed |
| Decision Impact | Low | Advisory only, no automated actions |
| Reversibility | High | All suggestions require user confirmation |
| Human Oversight | Required | User must execute suggested commands |

### Prohibited Use Confirmation

This AI implementation does NOT:

- ❌ Make autonomous decisions affecting production systems
- ❌ Process personally identifiable information (PII)
- ❌ Generate content for external customers
- ❌ Make financial or legal decisions
- ❌ Operate without human oversight
- ❌ Store or retain user queries

---

## Human Review Process

### Required Human Actions

1. **Query Review**: User formulates and submits query
2. **Response Review**: User reviews AI-generated response
3. **Execution Decision**: User decides whether to execute suggestions
4. **Command Execution**: User manually runs any suggested commands

### Safeguards

| Safeguard | Implementation |
|-----------|----------------|
| No Auto-Execution | AI cannot execute commands directly |
| Confirmation Prompts | Destructive operations require confirmation |
| Audit Logging | All AI interactions logged (debug mode) |
| Rate Limiting | Bedrock API rate limits apply |

---

## Data Handling

### Input Data

| Data Type | Handling | Retention |
|-----------|----------|-----------|
| User queries | Sent to Bedrock API | No retention |
| CLI context | Included in prompts | No retention |
| AWS account info | Not sent to AI | N/A |
| Credentials | Never sent to AI | N/A |

### Output Data

| Data Type | Handling | Storage |
|-----------|----------|---------|
| AI responses | Displayed to user | No storage |
| Suggested commands | Shown in terminal | No storage |
| Error messages | Logged locally | Debug logs only |

### Data Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│  TelcoCLI   │────▶│   Bedrock   │
│   Query     │     │   Agent     │     │   Claude    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Local     │     │   AWS API   │
                    │   Display   │     │   (No Store)│
                    └─────────────┘     └─────────────┘
```

---

## Compliance Checklist

### AWS AI/ML Guidelines

- ✅ Use case documented
- ✅ Risk level assessed (Low)
- ✅ Human oversight required
- ✅ No autonomous actions
- ✅ Data handling documented
- ✅ No PII processing
- ✅ Prohibited uses confirmed absent

### AWS Samples Requirements

- ✅ AI feature clearly documented
- ✅ User warnings provided
- ✅ No hardcoded credentials
- ✅ Standard AWS authentication used
- ✅ Rate limiting via Bedrock

---

## User Warnings

### Displayed to Users

The following warnings are shown to users:

1. **First Use Warning**:
   ```
   This feature uses Amazon Bedrock AI. Queries are sent to AWS.
   Do not include sensitive information in your queries.
   ```

2. **Response Disclaimer**:
   ```
   AI-generated suggestions should be reviewed before execution.
   ```

3. **Cost Warning**:
   ```
   Using this feature incurs Amazon Bedrock charges.
   ```

---

## Security Considerations

### Prompt Injection Prevention

| Control | Implementation |
|---------|----------------|
| Input Sanitization | Basic input validation |
| Context Isolation | System prompts separated |
| Output Filtering | No code execution from responses |

### Access Control

| Control | Implementation |
|---------|----------------|
| Authentication | AWS credentials required |
| Authorization | Bedrock IAM permissions |
| Audit | CloudTrail logging |

---

## Limitations

### Known Limitations

1. **Accuracy**: AI responses may contain errors
2. **Currency**: Knowledge cutoff applies
3. **Context**: Limited to CLI-related queries
4. **Availability**: Requires Bedrock access

### User Responsibilities

1. Verify AI suggestions before execution
2. Do not share sensitive information
3. Monitor Bedrock costs
4. Report inaccurate responses

---

## Updates and Maintenance

This document should be updated when:

1. AI capabilities are added or modified
2. New models are integrated
3. Data handling changes
4. Risk assessment changes

**Last Updated:** 2026-02-03
**Maintainer:** TelcoCLI Team

---

## References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS Responsible AI](https://aws.amazon.com/machine-learning/responsible-ai/)
- [AWS AI Service Terms](https://aws.amazon.com/service-terms/)
