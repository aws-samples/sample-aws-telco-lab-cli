# TelcoCLI Workflows and Command Reference

> **📝 Note on Example Data**
> 
> All AWS account IDs, profile names, and resource identifiers in this document are **example values only**. Replace with your actual:
> - Account IDs (e.g., `123456789012` → your actual account ID)
> - Profile names (e.g., `management-account` → your actual profile name)
> - Resource IDs (e.g., `i-1234567890abcdef0` → your actual instance ID)

## Overview

This document provides a comprehensive reference for all TelcoCLI commands organized by functional categories. Each command includes all available options, parameters, and usage examples.

## Multi-Account Credential Management

TelcoCLI is designed to work across distributed AWS infrastructure spanning multiple accounts. Before executing any workflow, users must:

### **1. Account Identification**
Identify which AWS account contains the target resources:
- **Management Account** - For Organizations operations and partner account creation
- **Outpost Account** - For infrastructure management and dedicated host operations
- **Partner Accounts** - For VPN management and partner-specific resources
- **Workload Accounts** - For EKS deployments and application infrastructure

### **2. Credential Configuration**
Configure AWS CLI profiles for each account:
```bash
# Configure profiles for different accounts
aws configure --profile management-account
aws configure --profile outpost-account-us-west-2
aws configure --profile partner-account-production
aws configure --profile workload-account-development
```

### **3. Permission Verification**
Ensure your credentials have required permissions for the intended operations:
- **Infrastructure Management** - EC2, Outposts, Organizations read/write access
- **Partner Management** - Organizations, IAM, RAM permissions
- **VPN Operations** - EC2, SSM access to VPN servers
- **EKS Operations** - EKS, EC2, IAM permissions for cluster management

### **4. Profile Selection**
Use the `--profile` flag to target specific accounts:
```bash
# Work with Outposts in specific account
telcocli list-outposts --profile outpost-account-us-west-2

# Create partner in management account
telcocli create-partner --partner-name test --profile management-account

# Deploy EKS in workload account
telcocli deploy-eks-full --cluster-name prod --profile workload-account-production
```

### **5. Credential Management**
Use standard AWS credential management tools:
```bash
# AWS SSO (Recommended)
aws configure sso
aws sso login --profile your-profile

# AWS CLI Profiles
aws configure --profile your-profile

# Credential Management Tools
# aws-vault
aws-vault exec your-profile -- telcocli <command>

# granted
assume your-profile
telcocli <command>
```

### **6. Cross-Account Operations**
Some workflows span multiple accounts:
```bash
# 1. Create partner account (management account)
telcocli create-partner --partner-name acme --profile management-account

# 2. Assign dedicated host (outpost account)
telcocli assign-dedicated-host --host-id h-123 --partner-name acme --profile outpost-account

# 3. Generate VPN certificate (VPN server account)
telcocli create-vpn acme --allowed-subnets "10.0.0.0/16" --profile vpn-account
```

---

## 1. Infrastructure Management

### **Workflows Enabled:**
- **Daily Operations Monitoring** - Monitor Outpost health, capacity, and utilization across regions
- **Capacity Planning** - Analyze current usage and forecast future infrastructure needs
- **Resource Allocation** - Assign dedicated hosts to partners and manage cross-account access
- **Troubleshooting** - Investigate performance issues and infrastructure problems
- **Multi-Account Visibility** - View instances and resources across partner accounts on shared Outposts
- **Lifecycle Management** - Track host assignments, releases, and utilization over time

### `list-outposts`
**Purpose**: List all AWS Outposts and their status

**Usage:**
```bash
telcocli list-outposts [OPTIONS]
```

**Options:**
- `--region-filter` - Filter by region (e.g., us-west-2)
- `--status-filter` - Filter by Outpost status
  - Choices: `ACTIVE`, `PENDING`, `PROVISIONING`, `INACTIVE`, `DELETING`
- `--include-capacity` - Include detailed capacity information
- `--output` - Output format (default: json)
  - Choices: `json`, `table`, `summary`

**Examples:**
```bash
# List all outposts in table format
telcocli list-outposts --output table

# Filter by region and status
telcocli list-outposts --region-filter us-west-2 --status-filter ACTIVE

# Include capacity details
telcocli list-outposts --include-capacity --output table
```

---

### `describe-outpost`
**Purpose**: Get comprehensive details about a specific outpost

**Usage:**
```bash
telcocli describe-outpost --outpost-id OUTPOST_ID [OPTIONS]
```

**Options:**
- `--outpost-id` (required) - Outpost ID to describe
- `--include-hosts` - Include physical server information
- `--include-instances` - Include all running instances (cross-account)
- `--output` - Output format
  - Choices: `json`, `table`

**Examples:**
```bash
# Basic outpost information
telcocli describe-outpost --outpost-id op-1234567890abcdef0

# Complete view with hosts and instances
telcocli describe-outpost --outpost-id op-1234567890abcdef0 --include-hosts --include-instances --output table
```

---

### `get-outpost-utilization-summary`
**Purpose**: Analyze outpost capacity, utilization, and performance metrics

**Usage:**
```bash
telcocli get-outpost-utilization-summary [OPTIONS]
```

**Options:**
- `--region-filter` - Filter by specific region
- `--outpost-id` - Show enhanced rack view for specific outpost
- `--include-details` - Include detailed per-Outpost breakdown
- `--output` - Output format (default: json)
  - Choices: `json`, `table`, `summary`

**Examples:**
```bash
# Overall utilization summary
telcocli get-outpost-utilization-summary --outpost-id op-1234567890abcdef0

# Regional analysis with details
telcocli get-outpost-utilization-summary --region-filter us-west-2 --include-details
```

---

### `analyze-dedicated-hosts`
**Purpose**: Analyze dedicated hosts with assignment tracking and filtering

**Usage:**
```bash
telcocli analyze-dedicated-hosts [OPTIONS]
```

**Options:**
- `--region` - AWS region to analyze
- `--all-regions` - Analyze hosts across all regions
- `--partner` - Filter by partner name
- `--assigned-only` - Show only assigned hosts
- `--unassigned-only` - Show only unassigned hosts
- `--outpost-id` - Filter by specific Outpost ID
- `--instance-type` - Filter by instance type
- `--state` - Filter by host state
  - Choices: `available`, `under-assessment`, `permanent-failure`, `released`
- `--format` - Output format (default: table)
  - Choices: `table`, `json`, `csv`

**Examples:**
```bash
# Analyze all hosts in current region
telcocli analyze-dedicated-hosts --region us-west-2

# Show only unassigned hosts across all regions
telcocli analyze-dedicated-hosts --all-regions --unassigned-only

# Filter by outpost and partner
telcocli analyze-dedicated-hosts --outpost-id op-1234567890abcdef0 --partner partner-name
```

---

### `assign-dedicated-host`
**Purpose**: Assign a dedicated host to a partner or account

**Usage:**
```bash
telcocli assign-dedicated-host --host-id HOST_ID [OPTIONS]
```

**Options:**
- `--host-id` (required) - Dedicated host ID to assign
- `--partner-name` - Name of the partner to assign the host to
- `--account-id` - AWS account ID to assign the host to (alternative to partner-name)
- `--force` - Force assignment even if host is already assigned
- `--enable-ram-sharing` - Enable RAM sharing to grant access to target account

**Examples:**
```bash
# Assign host to partner
telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --partner-name partner-name

# Assign with RAM sharing enabled
telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --account-id 123456789012 --enable-ram-sharing

# Force assignment
telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --partner-name partner-name --force
```

---

### `release-dedicated-host`
**Purpose**: Safely release dedicated hosts after moving or terminating instances

**Usage:**
```bash
telcocli release-dedicated-host --host-id HOST_ID [OPTIONS]
```

**Options:**
- `--host-id` (required) - Dedicated host ID to release
- `--force` - Force release even if instances are running on the host
- `--deallocate` - Also remove RAM resource share (if exists)
- `--yes` - Skip confirmation prompt

**Examples:**
```bash
# Release host with validation
telcocli release-dedicated-host --host-id h-1234567890abcdef0

# Force release and remove RAM share
telcocli release-dedicated-host --host-id h-1234567890abcdef0 --force --deallocate --yes
```

---

## 2. Partner Account Management

### **Workflows Enabled:**
- **Partner Onboarding** - Create new partner accounts with proper IAM roles and cross-account trust
- **Account Lifecycle Management** - Track partner accounts from creation to deletion
- **Security Compliance** - Ensure proper permission boundaries and management account protection
- **Multi-Account Governance** - Manage partner access across AWS Organizations structure
- **Audit and Reporting** - Track partner account usage, status, and organizational structure
- **Access Control** - Configure cross-account roles with least-privilege permissions

### `create-partner`
**Purpose**: Create partner account with cross-account assume role configuration

**Usage:**
```bash
telcocli create-partner --partner-name NAME --partner-account-id ACCOUNT_ID --admin-account-ids ACCOUNTS [OPTIONS]
```

**Options:**
- `--partner-name` (required) - Unique identifier for the partner
- `--partner-account-id` (required) - Partner-owned AWS account ID (12-digit number)
- `--admin-account-ids` (required) - Comma-separated list of AWS account IDs for JDA admin role trust policy
- `--admin-users` - (Deprecated: use --admin-account-ids) Comma-separated list of AWS account IDs
- `--validation-duration` - Duration for validation environment (default: 30d)
- `--account-type` - Type of AWS account to create (default: joint-developer)
  - Choices: `joint-developer`, `sandbox`, `production`
- `--contact-email` - Partner contact email address (optional, auto-generated if not provided)

**Examples:**
```bash
# Create basic partner account
telcocli create-partner \
  --partner-name partner-name \
  --partner-account-id 987654321098 \
  --admin-account-ids 111111111111,222222222222

# Create with custom settings
telcocli create-partner \
  --partner-name partner-name \
  --partner-account-id 987654321098 \
  --admin-account-ids 111111111111 \
  --contact-email partner@example.com \
  --validation-duration 90d \
  --account-type production
```

---

### `list-partners`
**Purpose**: List all partner accounts with status and details

**Usage:**
```bash
telcocli list-partners [OPTIONS]
```

**Options:**
- `--status` - Filter partners by status (default: All)
  - Choices: `Active`, `Inactive`, `All`
- `--output` - Output format (default: table)
  - Choices: `json`, `table`

**Examples:**
```bash
# List all partners
telcocli list-partners

# Filter by status
telcocli list-partners --status Active --output json
```

---

### `describe-partner`
**Purpose**: Get detailed information about a specific partner account

**Usage:**
```bash
telcocli describe-partner --partner-name PARTNER_NAME
```

**Options:**
- `--partner-name` (required) - Name of the partner to describe

**Examples:**
```bash
telcocli describe-partner --partner-name partner-name
```

---

### `delete-partner`
**Purpose**: Delete a partner account and clean up associated resources

**Usage:**
```bash
telcocli delete-partner --partner-name PARTNER_NAME [OPTIONS]
```

**Options:**
- `--partner-name` (required) - Name of the partner to delete
- `--force` - Skip confirmation prompt
- `--account-id` - Specific account ID to delete

**Examples:**
```bash
# Delete with confirmation
telcocli delete-partner --partner-name partner-name

# Force delete without confirmation
telcocli delete-partner --partner-name partner-name --force
```

---

### `list-all-accounts`
**Purpose**: List all accounts in AWS Organizations with comprehensive Control Tower view

**Usage:**
```bash
telcocli list-all-accounts [OPTIONS]
```

**Options:**
- `--status` - Filter by AWS account status
  - Choices: `ACTIVE`, `SUSPENDED`, `PENDING_CLOSURE`
- `--account-type` - Filter by account type (default: all)
  - Choices: `joint-developer`, `sandbox`, `production`, `management`, `log-archive`, `audit`, `all`
- `--include-ou` - Include Organizational Unit information for each account
- `--output` - Output format (default: table)
  - Choices: `json`, `table`

**Examples:**
```bash
# List all accounts
telcocli list-all-accounts

# Filter by account type and include OU info
telcocli list-all-accounts --account-type production --include-ou --output json
```

---

## 3. VPN Certificate Management

### **Workflows Enabled:**
- **Secure Partner Access** - Generate VPN certificates for secure network access to AWS resources
- **Network Segmentation** - Configure routing rules to limit partner access to specific subnets
- **Certificate Lifecycle** - Manage certificate creation, renewal, and revocation processes
- **Access Auditing** - Track active VPN connections and certificate usage
- **Security Incident Response** - Quickly revoke compromised certificates and terminate connections
- **Compliance Management** - Maintain certificate inventory and expiration tracking

### `create-vpn`
**Purpose**: Generate VPN certificates for partner access with routing configuration

**Usage:**
```bash
telcocli create-vpn PARTNER_NAME --allowed-subnets SUBNETS [OPTIONS]
```

**Options:**
- `partner_name` (required) - Name of the partner to generate certificate for
- `--allowed-subnets` (required) - Comma-separated list of allowed subnets (e.g., "192.168.100.0/24,10.0.0.0/16")
- `--certificate-duration` - Certificate duration (default: 30d)
- `--output-dir` - Directory to save the .ovpn file (default: .)

**Examples:**
```bash
# Create VPN certificate for partner
telcocli create-vpn partner-name --allowed-subnets "192.168.100.0/24,10.0.0.0/16"

# Create with custom duration and output directory
telcocli create-vpn partner-name \
  --allowed-subnets "192.168.100.0/24" \
  --certificate-duration 60d \
  --output-dir ./certificates
```

---

### `list-vpn-certificates`
**Purpose**: List all active VPN certificates with optional detailed information

**Usage:**
```bash
telcocli list-vpn-certificates [OPTIONS]
```

**Options:**
- `--show-details` - Show detailed certificate information (validity dates, serial number)
- `--output` - Output format (default: table)
  - Choices: `json`, `table`

**Examples:**
```bash
# List all certificates
telcocli list-vpn-certificates

# Show detailed information in JSON format
telcocli list-vpn-certificates --show-details --output json
```

---

### `revoke-vpn-certificate`
**Purpose**: Revoke VPN certificates for a partner and clean up associated resources

**Usage:**
```bash
telcocli revoke-vpn-certificate PARTNER_NAME [OPTIONS]
```

**Options:**
- `partner_name` (required) - Name of the partner to revoke certificate for
- `--yes` - Skip confirmation prompt

**Examples:**
```bash
# Revoke certificate with confirmation
telcocli revoke-vpn-certificate partner-name

# Skip confirmation prompt
telcocli revoke-vpn-certificate partner-name --yes
```

---

## 4. EKS/Kubernetes Operations

### **Workflows Enabled:**
- **Cloud-Native Infrastructure Deployment** - Deploy complete EKS clusters with VPC, networking, and observability
- **Edge Computing Setup** - Deploy Kubernetes on AWS Outposts for edge workloads
- **Telco Workload Optimization** - Configure SR-IOV, dedicated hosts, and high-performance networking
- **Multi-Environment Management** - Deploy development, staging, and production Kubernetes environments
- **Infrastructure as Code** - Use Terraform modules for repeatable, version-controlled deployments
- **Observability Integration** - Set up Prometheus, Grafana, and CloudWatch monitoring for telco applications

### `deploy-eks-full`
**Purpose**: Deploy complete EKS infrastructure using Terraform modules

**Usage:**
```bash
telcocli deploy-eks-full --cluster-name CLUSTER_NAME [OPTIONS]
```

**Core Options:**
- `--cluster-name` (required) - EKS cluster name
- `--aws-region` - AWS region (default: us-east-1)
- `--aws-profile` - AWS profile to use (default: default)
- `--terraform-dir` - Terraform directory path (default: src/telco_cli/templates/terraform/eks)

**Infrastructure Control:**
- `--deploy-vpc` - Deploy new VPC
- `--deploy-eks` - Deploy new EKS cluster
- `--deploy-worker-nodes` - Deploy worker nodes
- `--deploy-observability` - Deploy observability stack (default: true)

**Existing Infrastructure:**
- `--existing-vpc-id` - Use existing VPC ID
- `--existing-key-pair-name` - Use existing key pair

**Cluster Configuration:**
- `--cluster-version` - EKS cluster version (default: 1.32)
- `--vpc-cidr` - VPC CIDR block (default: 100.77.0.0/16)
- `--edge-subnet-cidr` - Edge subnet CIDR (default: 100.77.4.0/24)

**Worker Configuration:**
- `--worker-instance-type` - Worker instance type (default: m5.2xlarge)
- `--outpost-instance-type` - Outpost instance type (default: bmn-sf2.metal-32xl)
- `--desired-capacity` - Desired worker nodes (default: 1)
- `--worker-node-volume-size` - Worker node EBS volume size (default: 100)

**Outposts Configuration:**
- `--use-outposts` - Deploy on AWS Outposts
- `--outpost-id` - Outpost ID (required if use-outposts)
- `--outpost-account-id` - Outpost account ID for RAM shared Outposts

**Dedicated Host Configuration:**
- `--use-dedicated-host` - Use dedicated host
- `--dedicated-host-id` - Dedicated host ID (required if use-dedicated-host)

**Security:**
- `--grafana-admin-password` - Grafana admin password (auto-generated if not provided)

**Advanced Options:**
- `--use-cilium` - Use Cilium CNI instead of VPC CNI
- `--install-observability-addons` - Install CloudWatch observability (default: true)
- `--install-prometheus-addons` - Install Prometheus monitoring (default: true)

**Operational Parameters:**
- `--dry-run` - Validate without deploying
- `--environment` - Environment name (default: test)

**Examples:**
```bash
# Basic EKS deployment (existing infrastructure)
telcocli deploy-eks-full \
  --cluster-name my-cluster \
  --existing-vpc-id vpc-12345 \
  --existing-key-pair-name my-keypair

# Full infrastructure deployment
telcocli deploy-eks-full \
  --cluster-name production-cluster \
  --deploy-vpc \
  --deploy-eks \
  --deploy-worker-nodes \
  --aws-region us-west-2 \
  --worker-instance-type m5.xlarge \
  --desired-capacity 3

# Deploy on Outposts
telcocli deploy-eks-full \
  --cluster-name outpost-cluster \
  --deploy-eks \
  --deploy-worker-nodes \
  --use-outposts \
  --outpost-id op-1234567890abcdef0

# Dry run validation
telcocli deploy-eks-full \
  --cluster-name test-cluster \
  --deploy-vpc \
  --deploy-eks \
  --dry-run
```

---

### `configure-eks-access`
**Purpose**: Configure kubectl access to EKS cluster

**Usage:**
```bash
telcocli configure-eks-access --cluster-name CLUSTER_NAME [OPTIONS]
```

**Options:**
- `--cluster-name` (required) - EKS cluster name
- `--profile-name` - AWS profile name
- `--region` - AWS region

**Examples:**
```bash
telcocli configure-eks-access \
  --cluster-name my-cluster \
  --profile-name my-profile \
  --region us-east-1
```

---

## 5. System Operations

### **Workflows Enabled:**
- **Health Monitoring** - Continuous system health checks for production environments
- **Incident Response** - Quick access to test servers and system diagnostics
- **Remote Administration** - Secure SSM-based access to instances without SSH keys
- **Service Discovery** - Locate and connect to test infrastructure and development resources
- **Operational Readiness** - Validate system connectivity and service availability
- **Maintenance Operations** - Perform routine checks and system maintenance tasks

### `health`
**Purpose**: Run health checks for production monitoring

**Usage:**
```bash
telcocli health [OPTIONS]
```

**Options:**
- `--format` - Output format (default: table)
  - Choices: `json`, `text`, `table`

**Examples:**
```bash
# Run health checks with table output
telcocli health --format table

# JSON output for monitoring systems
telcocli health --format json
```

---

### `list-test-servers`
**Purpose**: List all test servers with status information

**Usage:**
```bash
telcocli list-test-servers [OPTIONS]
```

**Options:**
- `--status-filter` - Filter by server status
- `--output` - Output format (default: table)
  - Choices: `json`, `table`

**Examples:**
```bash
# List all test servers
telcocli list-test-servers --output table

# Filter by status
telcocli list-test-servers --status-filter online
```

---

### `start-ssm`
**Purpose**: Start SSM session to instance

**Usage:**
```bash
telcocli start-ssm --instance-id INSTANCE_ID
```

**Options:**
- `--instance-id` (required) - Instance ID to connect to

**Examples:**
```bash
telcocli start-ssm --instance-id i-1234567890abcdef0
```

---

## 6. Configuration & Credentials

### **Workflows Enabled:**
- **Multi-Account Access Management** - Configure and manage AWS credentials across multiple accounts
- **Profile Management** - Set up AWS CLI profiles for different environments and roles
- **Credential Rotation** - Update and maintain AWS access keys and session tokens
- **Environment Setup** - Configure development and production environment access
- **Security Compliance** - Ensure proper credential management and access controls
- **Automation Support** - Prepare credential configurations for CI/CD and automation workflows

### `configure-credentials`
**Purpose**: Configure credential mappings for account access

**Usage:**
```bash
telcocli configure-credentials SUBCOMMAND [OPTIONS]
```

**Subcommands:**
- `add` - Add new credential mapping
- `list` - List existing credential mappings
- `remove` - Remove credential mapping

**Options for `add`:**
- `--account-id` (required) - AWS account ID
- `--profiles` (required) - Comma-separated list of AWS profiles

**Examples:**
```bash
# Add credential mapping
telcocli configure-credentials add \
  --account-id 123456789012 \
  --profiles "production,backup"

# List credential mappings
telcocli configure-credentials list
```

---

### `update-credentials`
**Purpose**: Update credential mappings interactively

**Usage:**
```bash
telcocli update-credentials [OPTIONS]
```

**Options:**
- `--format` - Output format for credential update script
  - Choices: `bash`, `json`

**Examples:**
```bash
# Update credentials interactively
telcocli update-credentials --format bash
```

---

## 7. Utility Commands

### **Workflows Enabled:**
- **User Experience Enhancement** - Provide integrated help and documentation access
- **Developer Productivity** - Enable shell autocompletion for faster command execution
- **AWS CLI Integration** - Seamless access to AWS documentation and help system
- **Onboarding Support** - Help new users discover and learn command functionality
- **Workflow Optimization** - Reduce context switching between tools and documentation
- **Command Discovery** - Explore available AWS services and operations through integrated help

### `help`
**Purpose**: Display help information for AWS CLI commands through TelcoCLI

**Usage:**
```bash
telcocli help [COMMAND_PARTS...]
```

**Options:**
- `command_parts` (optional) - AWS command parts to get help for

**Examples:**
```bash
# Get help for AWS service
telcocli help ec2

# Get help for specific AWS command
telcocli help ec2 describe-instances

# Get help for S3 commands
telcocli help s3 ls
```

---

### `install-completion`
**Purpose**: Install shell completion for TelcoCLI

**Usage:**
```bash
telcocli install-completion [OPTIONS]
```

**Options:**
- `--shell` - Target shell for completion
  - Choices: `bash`, `zsh`, `fish`

**Examples:**
```bash
# Install bash completion
telcocli install-completion --shell bash

# Install zsh completion
telcocli install-completion --shell zsh
```

---

## Global Options

All commands support these global options:

- `--profile` - AWS CLI profile to use for this command (optional)
- `--region` - AWS region to use for this command (optional)
- `--verbose`, `-v` - Enable verbose logging
- `--quiet`, `-q` - Enable quiet mode (errors only)
- `--log-file` - Log to specified file
- `--version` - Show version information
- `--help` - Show help message

**Examples:**
```bash
# Use specific AWS profile and region
telcocli list-outposts --profile production --region us-west-2

# Enable verbose logging
telcocli deploy-eks-full --cluster-name test --verbose

# Log to file
telcocli create-partner --partner-name test --log-file telco.log
```

---

## Exit Codes

- **0**: Success
- **1**: General error
- **2**: Validation error
- **3**: AWS connection error
- **4**: Server discovery error
- **5**: SSM connection error
- **6**: Command execution error
- **7**: File operation error
- **9**: Configuration error
- **80-81**: Certificate errors

---

## Notes

1. **AWS Credentials**: All commands (except help and install-completion) require valid AWS credentials
2. **Permissions**: Commands require appropriate IAM permissions for the AWS services they interact with
3. **Regions**: Some commands are region-specific, use `--region` to specify or set `AWS_DEFAULT_REGION`
4. **Profiles**: Use `--profile` to specify AWS CLI profiles or set `AWS_PROFILE` environment variable
5. **Validation**: Most commands include input validation and will show helpful error messages for invalid parameters

For detailed usage examples and scenarios, refer to the specific command guides in the documentation.