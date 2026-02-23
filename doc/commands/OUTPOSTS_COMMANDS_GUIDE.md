# AWS Outposts Commands User Guide

> **⚠️ Security Notice:** This is sample code for demonstration purposes. Outpost operations involve cross-account access and dedicated host management — review IAM policies and RAM sharing configurations before use. See [SECURITY.md](../../SECURITY.md) for detailed security guidance.

> **📝 Note on Example Data**
> 
> All AWS account IDs, resource IDs, and ARNs shown in this guide are **example values only**:
> - Account IDs: `123456789012`, `987654321098`, `111122223333`, etc.
> - Resource IDs: `i-1234567890abcdef0`, `h-1234567890abcdef0`, etc.
> - ARNs: `arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789`
> 
> Replace these with your actual AWS resource identifiers when running commands.

## Overview

This guide explains how to use TelcoCLI commands to manage and monitor your AWS Outposts infrastructure, dedicated hosts, and running instances.

## Outpost Management Commands

### `list-outposts` - View All Your Outposts

**Purpose**: Get an overview of all outposts in your AWS account with status and utilization information.

**Basic Usage**:
```bash
# Simple list
telcocli list-outposts

# Professional table view with colors and status indicators
telcocli list-outposts --output table

# Summary with statistics
telcocli list-outposts --output summary
```

**What You'll See**:
- 🟢 **Available** outposts ready for use
- 🟡 **Pending** outposts being provisioned
- 🔴 **Deleting** outposts being removed
- Host counts and utilization per outpost
- Availability zones and capacity information

**Example Output**:
```
🏢 AWS Outposts Overview
┌────────────┬─────────────────────┬──────────────┬─────┬───────┐
│ Status     │ Outpost ID          │ Name         │ AZ  │ Hosts │
├────────────┼─────────────────────┼──────────────┼─────┼───────┤
│ 🟢 Available │ op-1234567890abcdef │ Production-1 │ us-west-2a │ 5 │
│ 🟡 Pending   │ op-2345678901bcdef0 │ Staging-2    │ us-west-2b │ 3 │
└────────────┴─────────────────────┴──────────────┴─────┴───────┘
```

---

### `describe-outpost` - Detailed Outpost Information

**Purpose**: Get comprehensive details about a specific outpost, including physical infrastructure and running instances.

**Basic Usage**:
```bash
# Basic outpost information
telcocli describe-outpost --outpost-id op-1234567890abcdef0

# Include physical server information
telcocli describe-outpost --outpost-id op-1234567890abcdef0 --include-hosts

# Include all running instances (across all accounts)
telcocli describe-outpost --outpost-id op-1234567890abcdef0 --include-instances

# Complete view with everything
telcocli describe-outpost --outpost-id op-1234567890abcdef0 --include-hosts --include-instances --output table
```

**What You'll See**:

**Basic Information**:
- Outpost name, ID, and status
- Availability zone and site information
- Capacity and utilization metrics

**With `--include-hosts`**:
- Physical server details with rack positions
- Server types and capabilities
- Hardware specifications
- Asset IDs for tracking

**With `--include-instances`**:
- All EC2 instances running on the outpost
- Instance types and states
- Which AWS account owns each instance
- Instance-to-server mapping

**Example Output with Physical Hosts**:
```
🏗️ Physical Infrastructure
┌─────────────────────┬───────────────┬─────────────┬─────────────────┐
│ Asset ID            │ Rack Position │ Server Type │ Instance Family │
├─────────────────────┼───────────────┼─────────────┼─────────────────┤
│ a-1234567890abcdef0 │ 13.0U        │ Server      │ bmn-cx2         │
│ a-2345678901bcdef01 │ 15.0U        │ Server      │ bmn-sf2         │
│ a-3456789012cdef012 │ 18.0U        │ Server      │ r7izde          │
└─────────────────────┴───────────────┴─────────────┴─────────────────┘
```

**Example Output with Instances**:
```
🖥️ Running Instances (Cross-Account View)
┌─────────────────────┬─────────────────────┬──────────────┬─────────────────┬─────────────┐
│ Instance ID         │ Asset ID            │ Account ID   │ Instance Type   │ State       │
├─────────────────────┼─────────────────────┼──────────────┼─────────────────┼─────────────┤
│ i-1234567890abcdef0 │ a-1234567890abcdef0 │ 111122223333 │ bmn-cx2.large   │ running     │
│ i-0987654321fedcba0 │ a-2345678901bcdef01 │ 444455556666 │ r7izde.xlarge   │ running     │
│ i-1111222233334444  │ a-3456789012cdef012 │ 777788889999 │ bmn-sf2.medium  │ stopped     │
└─────────────────────┴─────────────────────┴──────────────┴─────────────────┴─────────────┘
```

---

### `get-outpost-utilization-summary` - Capacity and Usage Analysis

**Purpose**: Analyze outpost capacity, utilization, and performance metrics for capacity planning and optimization.

**Usage:**
```bash
# Overall utilization summary
telcocli get-outpost-utilization-summary --outpost-id op-1234567890abcdef0

# Detailed rack-level analysis
telcocli get-outpost-utilization-summary --outpost-id op-1234567890abcdef0 --output table

# Include detailed per-Outpost breakdown
telcocli get-outpost-utilization-summary --region-filter us-west-2 --include-details
```

**Options:**
- `--region-filter` (optional): Filter by specific region (e.g., us-west-2)
- `--outpost-id` (optional): Show enhanced rack view for specific outpost
- `--include-details` (optional): Include detailed per-Outpost breakdown
- `--output` (optional, default: json): Output format (json|table|summary)

**What You'll See:**
- **Capacity Overview**: Total vs used resources
- **Rack Distribution**: Physical layout and utilization
- **Instance Distribution**: Types and families running
- **Performance Metrics**: CPU, memory, storage utilization
- **Recommendations**: Optimization suggestions

**Example Output**:
```
📊 Outpost Utilization Summary: op-1234567890abcdef0

Overall Capacity:
├── Total Servers: 11
├── Utilized Servers: 7 (64%)
├── Available Capacity: 4 servers
└── Instance Types: bmn-cx2, bmn-sf2, r7izde

Rack Distribution:
├── Rack Positions: 13.0U - 32.0U
├── Server Density: 11 servers across 20U
├── Power Utilization: 75%
└── Cooling Efficiency: Optimal

Recommendations:
├── 🟢 Capacity: 36% available for growth
├── 🟡 Optimization: Consider consolidating workloads
└── 🔵 Planning: Ready for 4 additional large instances
```

---

## Partner Management Commands

### `create-partner` - Create Partner Account

**Purpose**: Create partner account with cross-account assume role configuration.

**Usage:**
```bash
# Create basic partner account
telcocli create-partner \
  --partner-name "partner-name" \
  --partner-account-id "987654321098" \
  --admin-account-ids "111111111111,222222222222"

# Create with custom settings
telcocli create-partner \
  --partner-name "partner-name" \
  --partner-account-id "987654321098" \
  --admin-account-ids "111111111111" \
  --contact-email "partner@example.com" \
  --validation-duration "90d" \
  --account-type "production"
```

**Options:**
- `--partner-name` (required): Unique identifier for the partner
- `--partner-account-id` (required): Partner-owned AWS account ID (12-digit number)
- `--admin-account-ids` (required): Comma-separated list of AWS account IDs for JDA admin role trust policy
- `--validation-duration` (optional, default: 30d): Duration for validation environment
- `--account-type` (optional, default: joint-developer): Type of AWS account (joint-developer|sandbox|production)
- `--contact-email` (optional): Partner contact email address

**Output:**
```json
{
  "Success": true,
  "PartnerAccount": {
    "PartnerName": "partner-name",
    "AccountId": "123456789012",
    "Status": "ACTIVE"
  }
}
```

---

### `list-partners` - List Partner Accounts

**Purpose**: List all partner accounts with status and details.

**Usage:**
```bash
# List all partners
telcocli list-partners

# Filter by status
telcocli list-partners --status Active

# JSON output
telcocli list-partners --output json
```

**Options:**
- `--status` (optional, default: All): Filter partners by status (Active|Inactive|All)
- `--output` (optional, default: table): Output format (json|table)

**Output:**
```json
{
  "Success": true,
  "Partners": [
    {
      "Name": "PARTNER-NAME",
      "AccountId": "123456789012",
      "Status": "ACTIVE",
      "CreatedAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### `list-all-accounts` - List All AWS Accounts

**Purpose**: List all accounts in AWS Organizations with comprehensive Control Tower view and filtering options.

**Usage:**
```bash
# List all accounts
telcocli list-all-accounts

# Filter by account type
telcocli list-all-accounts --account-type joint-developer

# Filter by status
telcocli list-all-accounts --status ACTIVE

# Include Organizational Unit information
telcocli list-all-accounts --include-ou

# JSON output with filters
telcocli list-all-accounts --account-type production --output json
```

**Options:**
- `--status` (optional): Filter by AWS account status (ACTIVE|SUSPENDED|PENDING_CLOSURE)
- `--account-type` (optional, default: all): Filter by account type (joint-developer|sandbox|production|management|log-archive|audit|all)
- `--include-ou` (optional): Include Organizational Unit information for each account
- `--output` (optional, default: table): Output format (json|table)

**Output:**
```json
{
  "Success": true,
  "Accounts": [
    {
      "AccountId": "123456789012",
      "AccountName": "Partner-Production",
      "Email": "partner@example.com",
      "Status": "ACTIVE",
      "AccountType": "production",
      "JoinedMethod": "CREATED",
      "JoinedTimestamp": "2024-01-01T00:00:00Z",
      "Tags": {},
      "OrganizationalUnit": {
        "Id": "ou-xxxx-xxxxxxxx",
        "Name": "Production"
      }
    }
  ],
  "TotalCount": 1,
  "Summary": {
    "TotalAccounts": 1,
    "ByStatus": {
      "ACTIVE": 1
    },
    "ByType": {
      "production": 1
    }
  }
}
```

---

### `describe-partner` - Describe Partner Account

**Purpose**: Get detailed information about a specific partner account.

**Usage:**
```bash
# Describe partner by name
telcocli describe-partner --partner-name "partner-name"
```

**Options:**
- `--partner-name` (required): Name of the partner to describe

**Output:**
```json
{
  "Success": true,
  "Partner": {
    "Name": "PARTNER-NAME",
    "AccountId": "123456789012",
    "Status": "ACTIVE",
    "ContactEmail": "partner@example.com",
    "CreatedAt": "2024-01-01T00:00:00Z"
  }
}
```

---

### `delete-partner` - Delete Partner Account

**Purpose**: Delete a partner account and clean up associated resources.

**Usage:**
```bash
# Delete partner with confirmation
telcocli delete-partner --partner-name "partner-name"

# Force delete without confirmation
telcocli delete-partner --partner-name "partner-name" --force

# Delete by account ID
telcocli delete-partner --partner-name "partner-name" --account-id "123456789012"
```

**Options:**
- `--partner-name` (required): Name of the partner to delete
- `--force` (optional): Skip confirmation prompt
- `--account-id` (optional): Specific account ID to delete

**Output:**
```json
{
  "Success": true,
  "Message": "Partner 'partner-name' deleted successfully"
}
```

---

### `analyze-dedicated-hosts` - Host Analysis and Planning

**Purpose**: Analyze dedicated hosts with assignment tracking and filtering options.

**Usage:**
```bash
# Analyze all hosts in current region
telcocli analyze-dedicated-hosts --region us-west-2

# Analyze hosts across all regions
telcocli analyze-dedicated-hosts --all-regions

# Filter by specific outpost
telcocli analyze-dedicated-hosts --outpost-id op-1234567890abcdef0

# Filter by partner
telcocli analyze-dedicated-hosts --partner "partner-name"

# Show only assigned hosts
telcocli analyze-dedicated-hosts --assigned-only

# Show only unassigned hosts
telcocli analyze-dedicated-hosts --unassigned-only
```

**Options:**
- `--region` (optional): AWS region to analyze
- `--all-regions` (optional): Analyze hosts across all regions
- `--partner` (optional): Filter by partner name
- `--assigned-only` (optional): Show only assigned hosts
- `--unassigned-only` (optional): Show only unassigned hosts
- `--outpost-id` (optional): Filter by specific Outpost ID
- `--instance-type` (optional): Filter by instance type
- `--state` (optional): Filter by host state (available|under-assessment|permanent-failure|released)
- `--format` (optional, default: table): Output format (table|json|csv)

**What You'll See:**
- Host utilization percentages
- Available capacity per host
- Assignment status and partner information
- Instance type and state details
- Outpost association

---

### `assign-dedicated-host` - Smart Host Assignment

**Purpose**: Assign a dedicated host to a partner or account.

**Usage:**
```bash
# Assign host to partner
telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --partner-name "partner-name"

# Assign host to specific account
telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --account-id "123456789012"

# Assign with RAM sharing enabled
telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --partner-name "partner-name" --enable-ram-sharing

# Force assignment even if already assigned
telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --partner-name "partner-name" --force
```

**Options:**
- `--host-id` (required): Dedicated host ID to assign
- `--partner-name` (optional): Name of the partner to assign the host to
- `--account-id` (optional): AWS account ID to assign the host to (alternative to partner-name)
- `--force` (optional): Force assignment even if host is already assigned
- `--enable-ram-sharing` (optional): Enable RAM sharing to actually grant access to target account

**What It Does:**
- Assigns dedicated host to specified partner or account
- Tags the host with assignment information
- Optionally creates RAM resource share for cross-account access
- Validates host availability before assignment

---

### `release-dedicated-host` - Safe Host Release

**Purpose**: Safely release dedicated hosts after moving or terminating instances.

**Usage:**
```bash
# Release host after validation
telcocli release-dedicated-host --host-id h-1234567890abcdef0

# Force release even if instances are running
telcocli release-dedicated-host --host-id h-1234567890abcdef0 --force

# Also remove RAM resource share
telcocli release-dedicated-host --host-id h-1234567890abcdef0 --deallocate

# Skip confirmation prompt
telcocli release-dedicated-host --host-id h-1234567890abcdef0 --yes
```

**Options:**
- `--host-id` (required): Dedicated host ID to release
- `--force` (optional): Force release even if instances are running on the host
- `--deallocate` (optional): Also remove RAM resource share (if exists)
- `--yes` (optional): Skip confirmation prompt

**What It Does:**
- Validates no instances are running on the host
- Removes assignment tags and partner associations
- Optionally removes RAM resource shares
- Provides safety checks and confirmations

---

## Common Use Cases

### 1. **Daily Operations Monitoring**
```bash
# Quick health check of all outposts
telcocli list-outposts --output table

# Detailed view of production outpost
telcocli describe-outpost --outpost-id op-prod123 --include-instances --output table
```

### 2. **Capacity Planning**
```bash
# Analyze current utilization
telcocli get-outpost-utilization-summary --outpost-id op-prod123

# Check available dedicated host capacity
telcocli analyze-dedicated-hosts --outpost-id op-prod123
```

### 3. **Instance Management**
```bash
# See all instances across accounts
telcocli describe-outpost --outpost-id op-prod123 --include-instances

# Assign dedicated host to partner
telcocli assign-dedicated-host --host-id h-abc123 --partner-name "partner-name"
```

### 4. **Troubleshooting**
```bash
# Check physical infrastructure
telcocli describe-outpost --outpost-id op-prod123 --include-hosts

# Analyze performance issues
telcocli get-outpost-utilization-summary --outpost-id op-prod123 --include-details
```

### 5. **Cross-Account Visibility**
```bash
# See instances from all AWS accounts on the outpost
telcocli describe-outpost --outpost-id op-shared123 --include-instances

# Useful for shared outposts in enterprise environments
```

---

## Output Formats

### JSON Format (Default)
- Machine-readable output for automation
- Complete data structure with all fields
- Suitable for scripting and integration

### Table Format (`--output table`)
- Human-readable with colors and formatting
- Professional appearance for reports
- Status indicators and visual hierarchy

### Summary Format (`--output summary`)
- High-level overview with key metrics
- Perfect for dashboards and quick checks
- Condensed information for executives

---

## Tips for Effective Usage

### 1. **Use Table Output for Human Review**
```bash
telcocli list-outposts --output table  # Much easier to read
```

### 2. **Combine Flags for Complete Picture**
```bash
telcocli describe-outpost --outpost-id op-123 --include-hosts --include-instances --output table
```

### 3. **Use Proper Assignment Commands**
```bash
telcocli assign-dedicated-host --host-id h-123 --partner-name "partner-name"
```

### 4. **Regular Monitoring Commands**
```bash
# Daily health check
telcocli list-outposts --output summary

# Weekly capacity review
telcocli get-outpost-utilization-summary --outpost-id op-prod123
```

### 5. **Cross-Account Management**
```bash
# See all instances regardless of which account owns them
telcocli describe-outpost --outpost-id op-shared123 --include-instances
```

---

## Troubleshooting

### Common Issues

**"Outpost not found"**
- Verify the outpost ID is correct
- Check you're in the right AWS region
- Ensure you have proper permissions

**"No instances visible"**
- Use `--include-instances` flag
- Check cross-account permissions
- Verify instances are actually running

**"Physical data unavailable"**
- Use `--include-hosts` flag
- Ensure Outposts API permissions
- Check if outpost is fully provisioned

### Getting Help
```bash
# Command-specific help
telcocli describe-outpost --help
telcocli list-outposts --help

# General help
telcocli --help
```

---

This guide focuses on practical usage and what each command accomplishes for your day-to-day outpost management needs.
