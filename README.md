# TelcoCLI

[![License: MIT-0](https://img.shields.io/badge/License-MIT--0-yellow.svg)](https://opensource.org/licenses/MIT-0)

AWS Telco CLI - Command line tools for AWS Telco operations

<!-- Branch: open-source -->

## ⚠️ Security and Legal Notices

**This is sample code for demonstration purposes only.** This code is not intended for production use without proper security hardening, testing, and validation. See [SECURITY.md](SECURITY.md) for detailed security considerations.

### Copyright and License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

SPDX-License-Identifier: MIT-0

This project is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file for details.

> **⚠️ Important Note on Example Data**
> 
> All AWS account IDs, resource IDs, and other identifiers shown in this documentation and code examples are **example values only**. Common example account IDs used throughout:
> - `123456789012` - Example management/primary account
> - `987654321098` - Example partner/secondary account
> - `111111111111`, `222222222222` - Additional example accounts
> 
> Replace these with your actual AWS account IDs when using the CLI.

## Installation

### Prerequisites

- Python 3.9 or higher
- AWS CLI installed and configured with valid credentials
- Git (to clone the repository)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/aws-samples/sample-aws-telco-lab-cli.git
cd sample-aws-telco-lab-cli

# Install the CLI
pip install .

# Verify installation
telcocli --help
```

### Install for Development

If you plan to modify the source code, install in editable mode:

```bash
pip install -e .
```

### Install with Test Dependencies

```bash
pip install ".[test]"
```

### Install from CI (wheel + sdist)

**Fully automated:** every push to `main` that passes CI updates the public prerelease **[`ci-build`](https://github.com/aws-samples/sample-aws-telco-lab-cli/releases/tag/ci-build)** with fresh wheel and sdist assets and **auto-generated release notes** (commits and merged PRs). You do not need to create a version tag for this install path.

Each run also uploads a **`telcocli-dist`** artifact (same files as **Assets** on `ci-build`).

- **Public download (no GitHub login):** open **[`ci-build`](https://github.com/aws-samples/sample-aws-telco-lab-cli/releases/tag/ci-build)** → **Assets** → download the wheel or sdist, then `pip install /path/to/telcocli-*.whl`.
- **From the Actions UI (requires sign-in):** open the run → **Artifacts** → download **`telcocli-dist`**. Artifacts are kept **90 days**.

For production use, prefer **PyPI** (after publish) or a **version tag** release over the `ci-build` snapshot.

### AWS Credentials Setup

TelcoCLI requires AWS credentials to interact with AWS services. Configure them using one of:

```bash
# Option 1: AWS CLI configuration
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

# Option 3: Use a named profile
telcocli --profile your-profile-name <command>
```

### Dependencies

- **Core**: boto3, botocore (AWS SDK), rich (console output); optional **MCP** via `pip install ".[mcp]"` (the `mcp` PyPI package requires **Python 3.10+**; on 3.9 the extra still installs `aiohttp` / `pydantic` for compatible code paths)
- **Test**: pytest, pytest-cov, coverage

## Usage

```bash
# Show all available commands
telcocli --help

# Run a specific command
telcocli health
telcocli list-outposts
telcocli list-all-accounts

# Use verbose mode for debugging
telcocli -v <command>

# Specify AWS profile and region
telcocli --profile my-profile --region us-west-2 <command>
```

### Available Commands

| Command | Description |
|---------|-------------|
| `analyze-dedicated-hosts` | Analyze dedicated hosts with assignment tracking |
| `ask` | Ask the TelcoCLI AI agent for help (interactive mode) |
| `assign-dedicated-host` | Assign a dedicated host to a partner or account |
| `configure-credentials` | Configure AWS account to profile mappings |
| `configure-eks-access` | Configure kubectl access to EKS cluster |
| `create-partner` | Create partner account with cross-account role |
| `create-vpn` | Generate VPN certificates for partner access |
| `delete-partner` | Delete a partner account |
| `deploy-eks-full` | Deploy complete EKS infrastructure via Terraform |
| `describe-outpost` | Get detailed info about a specific Outpost |
| `describe-partner` | Describe a specific partner account |
| `get-outpost-utilization-summary` | Get utilization summary across all Outposts |
| `health` | Run health checks for production monitoring |
| `install-completion` | Install shell completion for bash/zsh |
| `list-all-accounts` | List all accounts in AWS Organizations |
| `list-outposts` | List all AWS Outposts and their status |
| `list-partners` | List all partner accounts |
| `list-test-servers` | List all SSM managed test servers |
| `list-vpn-certificates` | List active VPN certificates |
| `release-dedicated-host` | Release a dedicated host assignment |
| `revoke-vpn-certificate` | Revoke VPN certificates for a partner |
| `start-ssm` | Start an SSM session to a managed instance |
| `update-credentials` | Update AWS credentials |

For detailed command guides, see:
- [EKS Commands Guide](doc/commands/EKS_COMMANDS_GUIDE.md)
- [Outposts Commands Guide](doc/commands/OUTPOSTS_COMMANDS_GUIDE.md)
- [VPN Commands Guide](doc/commands/VPN_COMMANDS_GUIDE.md)
- [Workflows Guide](doc/commands/telcocli-workflows.md)

## Documentation

### Security Documentation

- **[SECURITY.md](SECURITY.md)** - Security vulnerability reporting and operational security guidelines
- **[doc/DATA_SECURITY_STRATEGY.md](doc/DATA_SECURITY_STRATEGY.md)** - Comprehensive data security strategy including encryption, key management, and access controls
- **[doc/ENCRYPTION_IMPLEMENTATION_GUIDE.md](doc/ENCRYPTION_IMPLEMENTATION_GUIDE.md)** - Practical implementation guide for encrypting sensitive data
- **[doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)** - System architecture and security design
- **[doc/THREAT_MODEL.md](doc/THREAT_MODEL.md)** - Threat analysis and security controls

## Legal Disclaimers

### AWS Service Usage

This CLI tool interacts with multiple AWS services including:
- AWS Organizations
- AWS IAM
- Amazon EC2 (Dedicated Hosts)
- Amazon EKS
- Amazon S3
- AWS Resource Access Manager (RAM)

**Important:**
- Using this tool may incur AWS service charges
- Operations performed by this tool can affect your AWS infrastructure
- Always test in non-production environments first
- Review and understand all commands before execution
- Ensure you have appropriate IAM permissions
- Follow AWS security best practices

### Operational Risks

- **Data Loss**: Some operations may delete or modify AWS resources
- **Cost Impact**: EC2 Dedicated Hosts and EKS clusters incur significant costs
- **Security Impact**: Improper IAM policy configuration can create security vulnerabilities
- **Compliance**: Ensure operations comply with your organization's policies and regulatory requirements

### No Warranty

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

### Security

For security considerations and best practices, see [SECURITY.md](SECURITY.md).

To report security vulnerabilities, please see our [Security Policy](SECURITY.md#reporting-security-issues).

## Development

See instructions in [DEVELOPMENT.md](DEVELOPMENT.md).

## Open-Source Release Flow

Use this release sequence for `main` and tag releases:

1. Run local checks:
   ```bash
   pip install -e ".[test,dev]"
   python -m pip install 'setuptools>=78.1.1'
   black --check --target-version py39 src test
   isort --check-only --profile black src test
   flake8 src test --max-line-length=100 --ignore=E203,W503,E501
   mypy src --ignore-missing-imports --check-untyped-defs
   pytest test/ --cov=telco_cli --cov-report=xml --cov-report=term-missing -v
   python -m build
   twine check dist/*
   python -m venv .smoke-venv && . .smoke-venv/bin/activate && pip install dist/*.whl && telcocli --help
   ```
2. Open a PR into `main` and wait for required CI + security checks to pass.
3. Ensure `pyproject.toml` version matches the release tag (for example: `1.0.1` -> `v1.0.1`).
4. Create and push a version tag matching `pyproject.toml` (for example `v1.0.1`) from the `aws-samples/sample-aws-telco-lab-cli` repository.
5. Wait for **CI** to finish successfully on that tag; the **Release** workflow then runs automatically, opens/updates the GitHub Release (with **auto-generated release notes**: commits and merged PRs since the previous release), attaches the wheel and sdist, and uploads to PyPI.

Release artifacts are the source distribution (`.tar.gz`) and wheel (`.whl`) uploaded by GitHub Actions for **semver tags**. In addition, each push to `main` refreshes the public prerelease **[`ci-build`](https://github.com/aws-samples/sample-aws-telco-lab-cli/releases/tag/ci-build)** with the same wheel and sdist (convenience snapshot, not a supported release line).
