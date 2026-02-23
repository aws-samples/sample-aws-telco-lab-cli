# AWS EKS Commands User Guide

> **⚠️ Security Notice:** This is sample code for demonstration purposes. Review all Terraform configurations, IAM policies, and security group rules before deploying to production. See [SECURITY.md](../../SECURITY.md) for detailed security guidance. AWS service charges will apply.

## Overview

This guide explains how to use TelcoCLI commands to deploy and manage Amazon EKS (Elastic Kubernetes Service) clusters using Terraform infrastructure-as-code.

## EKS Management Commands

### `deploy-eks-full` - Deploy Complete EKS Infrastructure

**Purpose**: Deploy complete EKS infrastructure using Terraform modules with flexible deployment control.

**Usage:**
```bash
# Basic EKS deployment (existing infrastructure)
telcocli deploy-eks-full \
  --cluster-name "my-cluster" \
  --existing-vpc-id "vpc-12345" \
  --existing-key-pair-name "my-keypair"

# Full infrastructure deployment
telcocli deploy-eks-full \
  --cluster-name "production-cluster" \
  --deploy-vpc \
  --deploy-eks \
  --deploy-worker-nodes \
  --aws-region "us-west-2" \
  --vpc-cidr "100.77.0.0/16" \
  --worker-instance-type "m5.xlarge" \
  --desired-capacity 3

# Deploy on Outposts
telcocli deploy-eks-full \
  --cluster-name "outpost-cluster" \
  --deploy-eks \
  --deploy-worker-nodes \
  --use-outposts \
  --outpost-id "op-1234567890abcdef0" \
  --outpost-instance-type "bmn-sf2.metal-32xl"

# Dry run validation
telcocli deploy-eks-full \
  --cluster-name "test-cluster" \
  --deploy-vpc \
  --deploy-eks \
  --dry-run
```

**Core Options:**
- `--cluster-name` (required): EKS cluster name
- `--aws-region` (optional, default: us-east-1): AWS region
- `--aws-profile` (optional, default: default): AWS CLI profile

**Infrastructure Control:**
- `--deploy-vpc`: Deploy new VPC infrastructure
- `--deploy-eks`: Deploy new EKS cluster
- `--deploy-worker-nodes`: Deploy worker nodes
- `--deploy-observability` (default: true): Deploy observability stack

**Existing Infrastructure:**
- `--existing-vpc-id`: Use existing VPC ID (required when deploy-vpc=false)
- `--existing-key-pair-name`: Use existing key pair

**Network Configuration:**
- `--vpc-cidr` (default: 100.77.0.0/16): VPC CIDR block
- `--edge-subnet-cidr` (default: 100.77.4.0/24): Edge subnet CIDR

**Worker Configuration:**
- `--worker-instance-type` (default: m5.2xlarge): Worker instance type
- `--outpost-instance-type` (default: bmn-sf2.metal-32xl): Outpost instance type
- `--desired-capacity` (default: 1): Desired worker nodes
- `--worker-node-volume-size` (default: 100): EBS volume size

**Outposts Configuration:**
- `--use-outposts`: Deploy on AWS Outposts
- `--outpost-id`: Outpost ID (required if use-outposts)
- `--outpost-account-id`: Outpost account ID for RAM shared Outposts

**Security:**
- `--grafana-admin-password`: Grafana admin password (auto-generated if not provided)

**Advanced Options:**
- `--use-cilium`: Use Cilium CNI instead of VPC CNI
- `--dry-run`: Validate without deploying
- `--environment` (default: test): Environment name

## Configuration File

Create `terraform.tfvars` from the example:

```bash
# Copy example configuration
cp src/telco_cli/templates/terraform/eks/terraform.tfvars.example terraform.tfvars

# Edit configuration
vim terraform.tfvars
```

**Example terraform.tfvars:**
```hcl
# AWS Configuration
aws_profile = "my-profile"
aws_region = "us-east-1"

# Existing Infrastructure
existing_vpc_id = "vpc-12345"
existing_key_pair_name = "my-keypair"

# Cluster Configuration
cluster_name = "my-cluster"
cluster_version = "1.32"

# Worker Configuration
worker_instance_type = "m5.2xlarge"
desired_capacity = 2

# Security
grafana_admin_password = "secure-password"
```

## Common Use Cases

### 1. **New Environment (Full Deployment)**
```bash
telcocli deploy-eks-full \
  --cluster-name "new-cluster" \
  --deploy-vpc \
  --deploy-eks \
  --deploy-worker-nodes \
  --worker-instance-type "m5.large" \
  --desired-capacity 2
```

### 2. **Existing VPC Deployment**
```bash
telcocli deploy-eks-full \
  --cluster-name "existing-vpc-cluster" \
  --existing-vpc-id "vpc-12345" \
  --deploy-eks \
  --deploy-worker-nodes \
  --existing-key-pair-name "my-keypair"
```

### 3. **Outposts Deployment**
```bash
telcocli deploy-eks-full \
  --cluster-name "outpost-cluster" \
  --deploy-eks \
  --deploy-worker-nodes \
  --use-outposts \
  --outpost-id "op-1234567890abcdef0" \
  --outpost-instance-type "bmn-sf2.metal-32xl"
```

### 4. **Observability Only**
```bash
telcocli deploy-eks-full \
  --cluster-name "existing-cluster" \
  --deploy-observability \
  --existing-vpc-id "vpc-12345"
```

## Terraform Infrastructure

### Architecture Components

**VPC Module** (when deploy-vpc=true):
- Custom VPC with configurable CIDR
- Public and private subnets across AZs
- Internet Gateway and NAT Gateway
- Route tables and security groups

**EKS Module** (when deploy-eks=true):
- Managed EKS control plane
- IAM roles and policies
- Security groups with restricted access
- Add-ons and networking configuration

**Worker Nodes Module** (when deploy-worker-nodes=true):
- Auto Scaling Groups or dedicated instances
- Launch templates with EKS-optimized AMIs
- gp3 encrypted EBS volumes
- Proper IAM instance profiles

**Observability Module** (when deploy-observability=true):
- Prometheus and Grafana stack
- CloudWatch integration
- SR-IOV monitoring (if enabled)
- Secure password generation

### Security Best Practices

- **Encrypted Storage**: gp3 volumes with encryption enabled
- **Restricted Security Groups**: Unprivileged ports only (1025-65535)
- **IAM Least Privilege**: Minimal required permissions
- **Secure Defaults**: Random password generation for Grafana

## Troubleshooting

### Validation Errors
```bash
# Check Terraform validation
terraform validate

# Check configuration
telcocli deploy-eks-full --dry-run --cluster-name "test"
```

### Common Issues

**"outpost_id required when use_outposts=true"**
- Provide --outpost-id when using --use-outposts

**"existing_vpc_id required when deploy_vpc=false"**
- Provide --existing-vpc-id or use --deploy-vpc

**"dedicated_host_id required when use_dedicated_host=true"**
- Provide --dedicated-host-id when using --use-dedicated-host

### Getting Help
```bash
telcocli deploy-eks-full --help
telcocli configure-eks-access --help
```

---

This guide covers the updated Terraform-based EKS deployment with flexible infrastructure control and security best practices.