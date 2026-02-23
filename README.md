# TelcoCLI

[![License: MIT-0](https://img.shields.io/badge/License-MIT--0-yellow.svg)](https://opensource.org/licenses/MIT-0)

AWS Telco CLI - Command line tools for AWS Telco operations

Version set is CSECommandLineTools/development
Tests run in CSECommandLineToolsTests

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

### Requirements
- Python 3.9 or higher
- AWS credentials configured

### Install from source
```bash
pip install .
```


### Install with test dependencies
```bash
pip install .[test]
```

## Package Structure

The setup.py configuration includes:

### Data Files
- Configuration files from `configuration/` directory are bundled with the package
- Directory structure is preserved during installation
- Includes AWS configs, templates, and other non-Python resources

### Dependencies
- **Core**: boto3, botocore (AWS SDK)
- **Test**: pytest, pytest-cov, coverage

### CLI Entry Point
After installation, the `telcocli` command is available globally and runs `telco_cli.cli:main`

## Usage

```bash
telcocli
telcocli --help
```

## Documentation

Generated documentation for the latest released version can be accessed here:
https://devcentral.amazon.com/ac/brazil/package-master/package/go/documentation?name=TelcoCLI&interface=1.0&versionSet=live

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

### Security Documentation

- **[SECURITY.md](SECURITY.md)** - Security vulnerability reporting and operational security guidelines
- **[doc/DATA_SECURITY_STRATEGY.md](doc/DATA_SECURITY_STRATEGY.md)** - Comprehensive data security strategy including encryption, key management, and access controls
- **[doc/ENCRYPTION_IMPLEMENTATION_GUIDE.md](doc/ENCRYPTION_IMPLEMENTATION_GUIDE.md)** - Practical implementation guide for encrypting sensitive data
- **[doc/IAM_LEAST_PRIVILEGE_GUIDE.md](doc/IAM_LEAST_PRIVILEGE_GUIDE.md)** - IAM least privilege principles and policy scoping strategies
- **[doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)** - System architecture and security design
- **[doc/THREAT_MODEL.md](doc/THREAT_MODEL.md)** - Threat analysis and security controls

## Development

See instructions in DEVELOPMENT.md
