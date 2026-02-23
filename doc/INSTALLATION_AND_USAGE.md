# TelcoCLI Installation and Usage Guide

> **⚠️ Security Notice:** This is sample code for demonstration purposes only. It is not intended for production use without proper security hardening, testing, and validation. AWS service charges will apply when running commands. See [SECURITY.md](../SECURITY.md) for detailed security guidance.

> **📝 Note on Example Data**
> 
> All AWS account IDs, resource IDs, and other identifiers shown in examples are **example values only**:
> - Account IDs: `123456789012`, `987654321098`
> - Resource IDs: `i-1234567890abcdef0`, `h-1234567890abcdef0`
> - Email addresses: `user@example.com`
> 
> Replace these with your actual values when running commands.

## Overview

TelcoCLI is a command-line tool for managing AWS Telco operations including Outposts management, partner account provisioning, VPN certificate generation, and test server management.

## Installation

### Prerequisites

- **Python 3.9 or higher**
- **AWS CLI configured** with appropriate credentials
- **AWS Organizations enabled** (for account management features)
- **Appropriate IAM permissions** for the services you plan to use

### Install from Source

```bash
# Clone or navigate to the TelcoCLI directory
cd /path/to/TelcoCLI

# Install the package
pip install .

# Or install with test dependencies for development
pip install .[test]
```

### Verify Installation

```bash
telcocli --help
```

## AWS Configuration

### AWS Credentials Setup

TelcoCLI uses standard AWS credential configuration. Set up your credentials using one of these methods:

#### Method 1: AWS CLI Configuration
```bash
aws configure
```

#### Method 2: AWS Profiles
```bash
# Configure multiple profiles
aws configure --profile production
aws configure --profile development

# Use with TelcoCLI
telcocli --profile production list-outposts
```

#### Method 3: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2
```

### Required AWS Permissions

Your AWS credentials need appropriate permissions for the services you plan to use:

#### For Outposts Management:
- `outposts:ListOutposts`
- `outposts:GetOutpost`
- `outposts:ListAssets`
- `ec2:DescribeInstances`
- `ec2:DescribeDedicatedHosts`

#### For Organizations Management:
- `organizations:ListAccounts`
- `organizations:DescribeAccount`
- `organizations:CreateAccount`

#### For VPN Operations:
- `ec2:DescribeInstances`
- `ssm:SendCommand`
- `ssm:GetCommandInvocation`
- `ssm:DescribeInstanceInformation`

#### For SSM Operations:
- `ssm:DescribeInstanceInformation`
- `ssm:StartSession`

## Usage Examples

### Account Setup Scenarios

#### Scenario 1: Management Account with Organizations
```bash
# Configure AWS profile for management account
aws configure --profile telco-management
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region name: us-west-2
# Default output format: json

# List all accounts in the organization
telcocli --profile telco-management list-all-accounts

# List accounts by type
telcocli --profile telco-management list-all-accounts --account-type partner
```

#### Scenario 2: Outpost Account with EC2 Resources
```bash
# Configure profile for account with Outposts
aws configure --profile outpost-account

# List all Outposts
telcocli --profile outpost-account list-outposts

# Get detailed Outpost information
telcocli --profile outpost-account describe-outpost --outpost-id op-1234567890abcdef0

# Analyze dedicated hosts across regions
telcocli --profile outpost-account analyze-dedicated-hosts --all-regions
```

#### Scenario 3: VPN Server Account
```bash
# Configure profile for VPN management account
aws configure --profile vpn-management

# List VPN certificates
telcocli --profile vpn-management list-vpn-certificates

# Create VPN certificate for partner
telcocli --profile vpn-management create-vpn partner-name \
  --allowed-subnets "192.168.100.0/24,10.0.0.0/16" \
  --certificate-duration "30d" \
  --output-dir ./certificates
```

### Common Commands

#### Health Monitoring
```bash
# Run health checks
telcocli health --format table

# JSON output for monitoring systems
telcocli health --format json
```

#### Outpost Management
```bash
# List Outposts with filters
telcocli list-outposts --region-filter us-west-2 --status-filter ACTIVE

# Get Outpost utilization summary
telcocli get-outpost-utilization-summary --region-filter us-west-2

# Include capacity details
telcocli list-outposts --include-capacity --output table
```

#### Partner Management
```bash
# Create new partner account
telcocli create-partner \
  --partner-name "partner-name" \
  --partner-account-id "987654321098" \
  --admin-account-ids "111111111111,222222222222" \
  --contact-email "partner@example.com" \
  --validation-duration "90d"

# List partner accounts
telcocli list-partners --status ACTIVE

# Describe specific partner
telcocli describe-partner partner-name

# Delete partner account
telcocli delete-partner partner-name --force
```

#### Dedicated Host Management
```bash
# Analyze dedicated hosts
telcocli analyze-dedicated-hosts --region us-west-2

# Assign dedicated host to partner
telcocli assign-dedicated-host --host-id h-1234567890abcdef0 \
  --partner-name "partner-name"

# Release dedicated host
telcocli release-dedicated-host --host-id h-1234567890abcdef0
```

#### Test Server Management
```bash
# List all test servers
telcocli list-test-servers --output table

# Filter by status
telcocli list-test-servers --status-filter online

# Start SSM session to test server
telcocli start-ssm --instance-id i-1234567890abcdef0
```

#### VPN Certificate Management
```bash
# List VPN certificates with details
telcocli list-vpn-certificates --show-details

# Create VPN certificate
telcocli create-vpn partner-name \
  --allowed-subnets "192.168.100.0/24" \
  --certificate-duration "30d"

# Revoke VPN certificate
telcocli revoke-vpn-certificate partner-name
```

#### EKS Cluster Management
```bash
# Deploy full EKS cluster
telcocli deploy-eks-full \
  --cluster-name my-cluster \
  --key-pair my-keypair \
  --region us-east-1

# Deploy EKS on Outposts
telcocli deploy-eks-full \
  --cluster-name outpost-cluster \
  --key-pair my-keypair \
  --use-outposts \
  --outpost-id op-1234567890abcdef0

# Configure kubectl access
telcocli configure-eks-access \
  --cluster-name my-cluster \
  --profile-name my-profile \
  --region us-east-1
```

#### Credential Management
```bash
# Configure credential mappings
telcocli configure-credentials add \
  --account-id 123456789012 \
  --profiles "production,backup"

# List credential mappings
telcocli configure-credentials list

# Update credentials interactively
telcocli update-credentials --format bash
```

### Advanced Usage

#### Multi-Region Operations
```bash
# Analyze dedicated hosts across all regions
telcocli analyze-dedicated-hosts --all-regions

# List Outposts in specific region
telcocli list-outposts --region-filter eu-west-1
```

#### Output Formatting
```bash
# JSON output for automation
telcocli list-outposts --output json

# Table format for human reading
telcocli list-outposts --output table

# Summary format for overview
telcocli list-outposts --output summary
```

#### Logging and Debugging
```bash
# Verbose logging
telcocli --verbose list-outposts

# Quiet mode (errors only)
telcocli --quiet health

# Log to file
telcocli --log-file telco.log list-all-accounts
```

## Configuration Files

### AWS Profile Configuration Example
```ini
# ~/.aws/config
[profile telco-management]
region = us-west-2
output = json

[profile outpost-account]
region = us-west-2
output = json

[profile vpn-management]
region = us-east-1
output = json

# ~/.aws/credentials
[telco-management]
aws_access_key_id = AKIA...
aws_secret_access_key = ...

[outpost-account]
aws_access_key_id = AKIA...
aws_secret_access_key = ...

[vpn-management]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
```

## Troubleshooting

### Common Issues

#### Credential Problems
```bash
# Check current AWS identity
aws sts get-caller-identity --profile your-profile

# Verify profile configuration
aws configure list --profile your-profile
```

#### Permission Issues
```bash
# Test basic permissions
telcocli health --profile your-profile

# Check specific service access
aws outposts list-outposts --profile your-profile
```

#### Network Connectivity
```bash
# Test AWS connectivity
aws sts get-caller-identity

# Check SSM connectivity for VPN operations
telcocli list-test-servers --status-filter online
```

### Error Codes

- **Exit Code 0**: Success
- **Exit Code 2**: Validation error
- **Exit Code 3**: AWS connection error
- **Exit Code 4**: Server discovery error
- **Exit Code 5**: SSM connection error
- **Exit Code 6**: Command execution error
- **Exit Code 7**: File operation error
- **Exit Code 9**: Configuration error
- **Exit Code 80-81**: Certificate errors

## Best Practices

1. **Use AWS Profiles**: Separate profiles for different environments and accounts
2. **Least Privilege**: Grant only necessary permissions to each profile
3. **Region Awareness**: Specify regions explicitly when working with regional resources
4. **Logging**: Use `--verbose` for debugging and `--log-file` for audit trails
5. **Automation**: Use JSON output format for scripting and automation
6. **Security**: Regularly rotate AWS credentials and review permissions

## Built-in Help System

### `help` - AWS CLI Help Integration

**Purpose**: Display help information for AWS CLI commands through TelcoCLI.

**Usage:**
```bash
# Get help for AWS service
telcocli help ec2

# Get help for specific AWS command
telcocli help ec2 describe-instances

# Get help for S3 commands
telcocli help s3 ls
```

**Options:**
- `command_parts` (optional): AWS command parts to get help for (e.g., 'ec2 describe-instances')

This command proxies to the AWS CLI help system, providing seamless access to AWS documentation.

### General Help Commands
```bash
# General TelcoCLI help
telcocli --help

# Command-specific help
telcocli create-partner --help
telcocli list-outposts --help
telcocli assign-dedicated-host --help
```

## Support

For additional help:
- Use `telcocli --help` for general help
- Use `telcocli <command> --help` for command-specific help
- Use `telcocli help <aws-command>` for AWS CLI help integration
- Check the generated API documentation for detailed function references
- Review error messages and exit codes for troubleshooting guidance
