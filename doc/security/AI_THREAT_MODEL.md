# AI-Specific Threat Model

**Document Version:** 1.0
**Last Updated:** 2025-02-10
**Owner:** TelcoCLI Security Team
**Generated with:** Threat Modeling MCP Server

---

## Overview

This document covers AI-specific attack vectors and mitigations for the TelcoCLI `ask-agent` command, which uses Amazon Bedrock (Claude models) via the strands-agents SDK. The threat model focuses on risks unique to the AI integration, not general application security.

> **WARNING:** This is sample code for demonstration purposes. AI-generated responses should always be verified by a human before execution.

---

## System Context

| Attribute | Value |
|-----------|-------|
| AI Service | Amazon Bedrock (Claude Sonnet) |
| Model ID | `us.anthropic.claude-sonnet-4-20250514-v1:0` |
| Framework | strands-agents SDK |
| Command | `telcocli ask` / `telcocli ask --interactive` |
| Design | Human-in-the-loop (no autonomous execution) |
| Data Sensitivity | Internal |
| Risk Classification | Low (advisory only, no automated actions) |

---

## Threat Summary

| ID | Threat | Severity | Likelihood | Mitigated? |
|----|--------|----------|------------|------------|
| T1 | Prompt injection | High | Possible | ✅ Mitigated |
| T2 | Sensitive data leakage to Bedrock | High | Possible | ✅ Mitigated |
| T3 | AI hallucination / incorrect commands | Medium | Likely | ✅ Mitigated |
| T4 | Indirect injection via knowledge base | Medium | Unlikely | ✅ Mitigated |
| T5 | API abuse / cost exhaustion | Medium | Unlikely | ⚠️ Partial |
| T6 | Privilege escalation via AI suggestions | High | Unlikely | ✅ Mitigated |

---

## Detailed Threats and Mitigations

### T1: Prompt Injection

A malicious user with access to the ask-agent command crafts input designed to override system instructions, extract system prompts, or manipulate the AI into generating harmful commands.

**Impact:** AI generates misleading or dangerous CLI commands that the user might execute, potentially causing infrastructure damage or data loss.

**Mitigations:**
- System prompt isolation separates system instructions from user input
- AI cannot execute commands directly — all suggestions require manual user execution (human-in-the-loop)
- No secrets or credentials in system prompts (nothing valuable to extract)

**Residual Risk:** Low. Even if prompt injection succeeds, the user must still manually execute any suggested commands.

---

### T2: Sensitive Data Leakage to Bedrock

A user includes sensitive information (AWS credentials, private keys, account IDs) in queries sent to the Bedrock API.

**Impact:** Sensitive data is transmitted to the Bedrock API endpoint and potentially logged or retained per AWS data handling policies.

**Mitigations:**
- Agent code explicitly excludes AWS credentials, private keys, and account IDs from AI context
- All communication uses HTTPS/TLS via the AWS SDK (enforced by default)
- User warnings advise against including sensitive data in queries
- Credentials are never injected into prompts programmatically

**Residual Risk:** Medium. Users can still manually type sensitive data into queries. Consider adding input sanitization to detect and warn about credential patterns.

---

### T3: AI Hallucination / Incorrect Commands

The AI model generates incorrect, outdated, or hallucinated CLI commands, IAM policies, or infrastructure configurations that appear authoritative.

**Impact:** User executes incorrect commands leading to misconfigured infrastructure, security vulnerabilities, or service disruption.

**Mitigations:**
- User warnings displayed that AI responses may contain inaccuracies
- All AI-suggested commands require manual review and execution
- Knowledge base provides accurate CLI context to reduce hallucination
- Response disclaimer shown to users

**Residual Risk:** Medium. Hallucination is inherent to LLMs. The human-in-the-loop design is the primary defense.

---

### T4: Indirect Injection via Knowledge Base

A malicious actor modifies the agent's knowledge base files to inject content that gets included in AI prompts, causing harmful outputs.

**Impact:** AI responses contain malicious commands disguised as legitimate guidance from the knowledge base context.

**Mitigations:**
- Knowledge base is read-only and built from trusted internal sources (command definitions, help text)
- Knowledge base is not user-modifiable at runtime
- Knowledge base rebuild requires explicit `--build-kb` flag

**Residual Risk:** Low. Requires filesystem access to modify knowledge base files.

---

### T5: API Abuse / Cost Exhaustion

An attacker or automated script sends excessive queries to the Bedrock API through the ask-agent command to exhaust API quotas or generate unexpected costs.

**Impact:** Denial of service for legitimate users and unexpected AWS billing charges.

**Mitigations:**
- Bedrock API rate limits provide built-in protection
- IAM permissions required for Bedrock access
- AWS billing alerts recommended for production

**Residual Risk:** Medium. No application-level rate limiting is currently implemented. Recommend adding rate limiting and billing alerts for production deployments.

---

### T6: Privilege Escalation via AI Suggestions

A malicious user uses prompt injection to trick the AI into suggesting commands that escalate IAM privileges, create backdoor roles, or modify security configurations.

**Impact:** Unauthorized privilege escalation if user blindly executes AI-suggested IAM policy changes.

**Mitigations:**
- Human-in-the-loop design — user must manually execute all suggestions
- AI cannot directly call AWS APIs or execute commands
- System prompt instructs the model to follow least-privilege principles

**Residual Risk:** Low. Requires both successful prompt injection AND user blindly executing the suggested commands.

---

## Residual Risk Summary

| Risk Area | Current Status | Recommended Action |
|-----------|---------------|-------------------|
| Prompt injection | Mitigated by human-in-the-loop | Consider Bedrock Guardrails for additional filtering |
| Data leakage | Mitigated by code design | Add input sanitization to detect credential patterns |
| Hallucination | Mitigated by user warnings | Keep knowledge base current, add response validation |
| Knowledge base poisoning | Mitigated by read-only design | Add integrity checks for knowledge base files |
| API abuse | Partially mitigated | Implement application-level rate limiting |
| Privilege escalation | Mitigated by human-in-the-loop | Add warnings when AI suggests IAM changes |

---

## References

- [Bedrock Security Guidelines](./BEDROCK_SECURITY_GUIDELINES.md)
- [GenAI Use Case Documentation](../ai/GENAI_USE_CASE.md)
- [Third-Party Components](../ai/THIRD_PARTY_COMPONENTS.md)
- [Amazon Bedrock Security](https://docs.aws.amazon.com/bedrock/latest/userguide/security.html)
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- Threat Model JSON export: `src/.threatmodel/ai_threat_model.json`
