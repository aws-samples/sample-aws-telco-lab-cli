# Third Party Components

This document lists all third-party components used by TelcoCLI, their licenses, and approval status for AWS Samples publication.

---

## AI/ML Components

### Amazon Bedrock - Claude Models

| Attribute | Value |
|-----------|-------|
| **Component** | Amazon Bedrock Claude (Anthropic) |
| **Version** | Claude 3.5 Sonnet, Claude 3 Haiku |
| **License** | AWS Service (Commercial) |
| **Usage** | AI-powered CLI assistant (`ask-agent` command) |
| **Approval Status** | ✅ Approved - AWS managed service |
| **Data Handling** | User queries sent to Bedrock API; no data retention |

### Strands Agents SDK

| Attribute | Value |
|-----------|-------|
| **Component** | strands-agents |
| **Version** | Latest (pip install) |
| **License** | Apache 2.0 |
| **Source** | https://github.com/strands-agents/strands-agents |
| **Usage** | Agent orchestration framework for AI assistant |
| **Approval Status** | ✅ Approved - Apache 2.0 compatible |

### Model Context Protocol (MCP)

| Attribute | Value |
|-----------|-------|
| **Component** | MCP Server Integration |
| **Version** | 1.0 |
| **License** | MIT |
| **Usage** | Tool integration for AI agent |
| **Approval Status** | ✅ Approved - MIT compatible |

---

## Python Dependencies

### Core Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| boto3 | >=1.26.0 | Apache 2.0 | AWS SDK for Python |
| botocore | >=1.29.0 | Apache 2.0 | AWS SDK core |
| click | >=8.0.0 | BSD-3-Clause | CLI framework |
| rich | >=13.0.0 | MIT | Terminal formatting |
| pyyaml | >=6.0 | MIT | YAML parsing |
| requests | >=2.28.0 | Apache 2.0 | HTTP client |
| jinja2 | >=3.0.0 | BSD-3-Clause | Template engine |

### Development Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| pytest | >=7.0.0 | MIT | Testing framework |
| pytest-cov | >=4.0.0 | MIT | Coverage reporting |
| mypy | >=1.0.0 | MIT | Type checking |
| black | >=23.0.0 | MIT | Code formatting |
| flake8 | >=6.0.0 | MIT | Linting |
| isort | >=5.12.0 | MIT | Import sorting |
| bandit | >=1.7.0 | Apache 2.0 | Security scanning |

---

## Infrastructure Components

### Terraform Providers

| Provider | Version | License | Purpose |
|----------|---------|---------|---------|
| hashicorp/aws | >=5.0 | MPL 2.0 | AWS resource management |
| hashicorp/kubernetes | >=2.0 | MPL 2.0 | Kubernetes resources |
| hashicorp/helm | >=2.0 | MPL 2.0 | Helm chart deployment |
| hashicorp/random | >=3.0 | MPL 2.0 | Random value generation |
| hashicorp/tls | >=4.0 | MPL 2.0 | TLS certificate management |

### Kubernetes Components

| Component | Version | License | Purpose |
|-----------|---------|---------|---------|
| AWS Load Balancer Controller | v2.6+ | Apache 2.0 | ALB/NLB integration |
| Metrics Server | v0.6+ | Apache 2.0 | Resource metrics |
| Prometheus | v2.45+ | Apache 2.0 | Monitoring |
| Grafana | v10.0+ | AGPL 3.0 | Visualization |

---

## License Compatibility Matrix

| License | Compatible with MIT-0 | Notes |
|---------|----------------------|-------|
| Apache 2.0 | ✅ Yes | Most AWS SDKs |
| MIT | ✅ Yes | Many Python packages |
| BSD-3-Clause | ✅ Yes | Click, Jinja2 |
| MPL 2.0 | ✅ Yes | Terraform providers |
| AGPL 3.0 | ⚠️ Conditional | Grafana - deployed separately |

---

## Data Flow and Privacy

### AI Component Data Handling

1. **User Input**: CLI commands and queries
2. **Processing**: Sent to Amazon Bedrock API
3. **Response**: AI-generated responses displayed to user
4. **Storage**: No persistent storage of queries or responses
5. **Logging**: Debug logs only (no sensitive data)

### AWS Service Interactions

- All AWS API calls use standard AWS SDK authentication
- Credentials managed via AWS CLI configuration
- No credential storage in application code
- Session tokens handled by boto3/botocore

---

## Approval Documentation

### AWS Samples Requirements

- ✅ All dependencies have OSS-compatible licenses
- ✅ No GPL-licensed runtime dependencies
- ✅ AGPL components (Grafana) deployed separately
- ✅ AI/ML usage documented
- ✅ Data handling documented

### Third-Party Approval Status

| Category | Status | Notes |
|----------|--------|-------|
| Python packages | ✅ Approved | All Apache/MIT/BSD |
| Terraform providers | ✅ Approved | All MPL 2.0 |
| AI/ML services | ✅ Approved | AWS Bedrock |
| Kubernetes components | ✅ Approved | Apache 2.0 |

---

## Updates and Maintenance

This document should be updated when:

1. New dependencies are added
2. Dependency versions are updated
3. New AI/ML components are integrated
4. License terms change

**Last Updated:** 2026-02-03
**Maintainer:** TelcoCLI Team

---

## References

- [AWS Samples License Requirements](https://github.com/aws-samples/.github/blob/main/CONTRIBUTING.md)
- [SPDX License List](https://spdx.org/licenses/)
- [OSI Approved Licenses](https://opensource.org/licenses/)
