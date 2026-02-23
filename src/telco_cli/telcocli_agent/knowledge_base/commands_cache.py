# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Pre-compiled knowledge base for faster access."""

# Auto-generated from commands.json - do not edit manually
# Run: python -m telco_cli.telcocli_agent.knowledge_base.cache_builder to regenerate

COMMANDS = {
    "commands": {
        "list-outposts": {
            "name": "list-outposts",
            "description": "List all AWS Outposts and their status",
            "usage": "telcocli list-outposts [OPTIONS]",
            "category": "infrastructure-management",
            "parameters": [
                {
                    "name": "--region-filter",
                    "description": "Filter by region (e.g., us-west-2)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--status-filter",
                    "description": "Filter by Outpost status",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--include-capacity",
                    "description": "Include detailed capacity information",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--output",
                    "description": "Output format (default: json)",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {"command": "telcocli list-outposts --output table", "description": ""},
                {
                    "command": "telcocli list-outposts --region-filter us-west-2 --status-filter ACTIVE",
                    "description": "",
                },
                {
                    "command": "telcocli list-outposts --include-capacity --output table",
                    "description": "",
                },
            ],
            "workflows": [
                "Daily Operations Monitoring: Monitor Outpost health, capacity, and utilization across regions",
                "Capacity Planning: Analyze current usage and forecast future infrastructure needs",
                "Resource Allocation: Assign dedicated hosts to partners and manage cross-account access",
                "Troubleshooting: Investigate performance issues and infrastructure problems",
                "Multi-Account Visibility: View instances and resources across partner accounts on shared Outposts",
                "Lifecycle Management: Track host assignments, releases, and utilization over time",
            ],
        },
        "describe-outpost": {
            "name": "describe-outpost",
            "description": "Get comprehensive details about a specific outpost",
            "usage": "telcocli describe-outpost --outpost-id OUTPOST_ID [OPTIONS]",
            "category": "infrastructure-management",
            "parameters": [
                {
                    "name": "--include-hosts",
                    "description": "Include physical server information",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--include-instances",
                    "description": "Include all running instances (cross-account)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--output",
                    "description": "Output format",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {
                    "command": "telcocli describe-outpost --outpost-id op-1234567890abcdef0",
                    "description": "",
                },
                {
                    "command": "telcocli describe-outpost --outpost-id op-1234567890abcdef0 --include-hosts --include-instances --output table",
                    "description": "",
                },
            ],
            "workflows": [
                "Daily Operations Monitoring: Monitor Outpost health, capacity, and utilization across regions",
                "Capacity Planning: Analyze current usage and forecast future infrastructure needs",
                "Resource Allocation: Assign dedicated hosts to partners and manage cross-account access",
                "Troubleshooting: Investigate performance issues and infrastructure problems",
                "Multi-Account Visibility: View instances and resources across partner accounts on shared Outposts",
                "Lifecycle Management: Track host assignments, releases, and utilization over time",
            ],
        },
        "get-outpost-utilization-summary": {
            "name": "get-outpost-utilization-summary",
            "description": "Analyze outpost capacity, utilization, and performance metrics",
            "usage": "telcocli get-outpost-utilization-summary [OPTIONS]",
            "category": "infrastructure-management",
            "parameters": [
                {
                    "name": "--region-filter",
                    "description": "Filter by specific region",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--outpost-id",
                    "description": "Show enhanced rack view for specific outpost",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--include-details",
                    "description": "Include detailed per-Outpost breakdown",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--output",
                    "description": "Output format (default: json)",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {
                    "command": "telcocli get-outpost-utilization-summary --outpost-id op-1234567890abcdef0",
                    "description": "",
                },
                {
                    "command": "telcocli get-outpost-utilization-summary --region-filter us-west-2 --include-details",
                    "description": "",
                },
            ],
            "workflows": [
                "Daily Operations Monitoring: Monitor Outpost health, capacity, and utilization across regions",
                "Capacity Planning: Analyze current usage and forecast future infrastructure needs",
                "Resource Allocation: Assign dedicated hosts to partners and manage cross-account access",
                "Troubleshooting: Investigate performance issues and infrastructure problems",
                "Multi-Account Visibility: View instances and resources across partner accounts on shared Outposts",
                "Lifecycle Management: Track host assignments, releases, and utilization over time",
            ],
        },
        "analyze-dedicated-hosts": {
            "name": "analyze-dedicated-hosts",
            "description": "Analyze dedicated hosts with assignment tracking and filtering",
            "usage": "telcocli analyze-dedicated-hosts [OPTIONS]",
            "category": "infrastructure-management",
            "parameters": [
                {
                    "name": "--region",
                    "description": "AWS region to analyze",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--all-regions",
                    "description": "Analyze hosts across all regions",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--partner",
                    "description": "Filter by partner name",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--assigned-only",
                    "description": "Show only assigned hosts",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--unassigned-only",
                    "description": "Show only unassigned hosts",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--outpost-id",
                    "description": "Filter by specific Outpost ID",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--instance-type",
                    "description": "Filter by instance type",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--state",
                    "description": "Filter by host state",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--format",
                    "description": "Output format (default: table)",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {
                    "command": "telcocli analyze-dedicated-hosts --region us-west-2",
                    "description": "",
                },
                {
                    "command": "telcocli analyze-dedicated-hosts --all-regions --unassigned-only",
                    "description": "",
                },
                {
                    "command": "telcocli analyze-dedicated-hosts --outpost-id op-1234567890abcdef0 --partner partner-name",
                    "description": "",
                },
            ],
            "workflows": [
                "Daily Operations Monitoring: Monitor Outpost health, capacity, and utilization across regions",
                "Capacity Planning: Analyze current usage and forecast future infrastructure needs",
                "Resource Allocation: Assign dedicated hosts to partners and manage cross-account access",
                "Troubleshooting: Investigate performance issues and infrastructure problems",
                "Multi-Account Visibility: View instances and resources across partner accounts on shared Outposts",
                "Lifecycle Management: Track host assignments, releases, and utilization over time",
            ],
        },
        "assign-dedicated-host": {
            "name": "assign-dedicated-host",
            "description": "Assign a dedicated host to a partner or account",
            "usage": "telcocli assign-dedicated-host --host-id HOST_ID [OPTIONS]",
            "category": "infrastructure-management",
            "parameters": [
                {
                    "name": "--partner-name",
                    "description": "Name of the partner to assign the host to",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--account-id",
                    "description": "AWS account ID to assign the host to (alternative to partner-name)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--force",
                    "description": "Force assignment even if host is already assigned",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--enable-ram-sharing",
                    "description": "Enable RAM sharing to grant access to target account",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {
                    "command": "telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --partner-name partner-name",
                    "description": "",
                },
                {
                    "command": "telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --account-id 123456789012 --enable-ram-sharing",
                    "description": "",
                },
                {
                    "command": "telcocli assign-dedicated-host --host-id h-1234567890abcdef0 --partner-name partner-name --force",
                    "description": "",
                },
            ],
            "workflows": [
                "Daily Operations Monitoring: Monitor Outpost health, capacity, and utilization across regions",
                "Capacity Planning: Analyze current usage and forecast future infrastructure needs",
                "Resource Allocation: Assign dedicated hosts to partners and manage cross-account access",
                "Troubleshooting: Investigate performance issues and infrastructure problems",
                "Multi-Account Visibility: View instances and resources across partner accounts on shared Outposts",
                "Lifecycle Management: Track host assignments, releases, and utilization over time",
            ],
        },
        "release-dedicated-host": {
            "name": "release-dedicated-host",
            "description": "Safely release dedicated hosts after moving or terminating instances",
            "usage": "telcocli release-dedicated-host --host-id HOST_ID [OPTIONS]",
            "category": "infrastructure-management",
            "parameters": [
                {
                    "name": "--force",
                    "description": "Force release even if instances are running on the host",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--deallocate",
                    "description": "Also remove RAM resource share (if exists)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--yes",
                    "description": "Skip confirmation prompt",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {
                    "command": "telcocli release-dedicated-host --host-id h-1234567890abcdef0",
                    "description": "",
                },
                {
                    "command": "telcocli release-dedicated-host --host-id h-1234567890abcdef0 --force --deallocate --yes",
                    "description": "",
                },
            ],
            "workflows": [
                "Daily Operations Monitoring: Monitor Outpost health, capacity, and utilization across regions",
                "Capacity Planning: Analyze current usage and forecast future infrastructure needs",
                "Resource Allocation: Assign dedicated hosts to partners and manage cross-account access",
                "Troubleshooting: Investigate performance issues and infrastructure problems",
                "Multi-Account Visibility: View instances and resources across partner accounts on shared Outposts",
                "Lifecycle Management: Track host assignments, releases, and utilization over time",
            ],
        },
        "create-partner": {
            "name": "create-partner",
            "description": "Create partner account with cross-account assume role configuration",
            "usage": "telcocli create-partner --partner-name NAME --partner-account-id ACCOUNT_ID --admin-account-ids ACCOUNTS [OPTIONS]",
            "category": "partner-account-management",
            "parameters": [
                {
                    "name": "--admin-users",
                    "description": "(Deprecated: use --admin-account-ids) Comma-separated list of AWS account IDs",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--validation-duration",
                    "description": "Duration for validation environment (default: 30d)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--account-type",
                    "description": "Type of AWS account to create (default: joint-developer)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--contact-email",
                    "description": "Partner contact email address (optional, auto-generated if not provided)",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {"command": "telcocli create-partner \\", "description": ""},
                {"command": "--partner-name partner-name \\", "description": ""},
                {"command": "--partner-account-id 987654321098 \\", "description": ""},
                {"command": "--admin-account-ids 111111111111,222222222222", "description": ""},
                {"command": "telcocli create-partner \\", "description": ""},
                {"command": "--partner-name partner-name \\", "description": ""},
                {"command": "--partner-account-id 987654321098 \\", "description": ""},
                {"command": "--admin-account-ids 111111111111 \\", "description": ""},
                {"command": "--contact-email partner@example.com \\", "description": ""},
                {"command": "--validation-duration 90d \\", "description": ""},
                {"command": "--account-type production", "description": ""},
            ],
            "workflows": [
                "Partner Onboarding: Create new partner accounts with proper IAM roles and cross-account trust",
                "Account Lifecycle Management: Track partner accounts from creation to deletion",
                "Security Compliance: Ensure proper permission boundaries and management account protection",
                "Multi-Account Governance: Manage partner access across AWS Organizations structure",
                "Audit and Reporting: Track partner account usage, status, and organizational structure",
                "Access Control: Configure cross-account roles with least-privilege permissions",
            ],
        },
        "list-partners": {
            "name": "list-partners",
            "description": "List all partner accounts with status and details",
            "usage": "telcocli list-partners [OPTIONS]",
            "category": "partner-account-management",
            "parameters": [
                {
                    "name": "--status",
                    "description": "Filter partners by status (default: All)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--output",
                    "description": "Output format (default: table)",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {"command": "telcocli list-partners", "description": ""},
                {
                    "command": "telcocli list-partners --status Active --output json",
                    "description": "",
                },
            ],
            "workflows": [
                "Partner Onboarding: Create new partner accounts with proper IAM roles and cross-account trust",
                "Account Lifecycle Management: Track partner accounts from creation to deletion",
                "Security Compliance: Ensure proper permission boundaries and management account protection",
                "Multi-Account Governance: Manage partner access across AWS Organizations structure",
                "Audit and Reporting: Track partner account usage, status, and organizational structure",
                "Access Control: Configure cross-account roles with least-privilege permissions",
            ],
        },
        "describe-partner": {
            "name": "describe-partner",
            "description": "Get detailed information about a specific partner account",
            "usage": "telcocli describe-partner --partner-name PARTNER_NAME",
            "category": "partner-account-management",
            "parameters": [],
            "examples": [
                {
                    "command": "telcocli describe-partner --partner-name partner-name",
                    "description": "",
                }
            ],
            "workflows": [
                "Partner Onboarding: Create new partner accounts with proper IAM roles and cross-account trust",
                "Account Lifecycle Management: Track partner accounts from creation to deletion",
                "Security Compliance: Ensure proper permission boundaries and management account protection",
                "Multi-Account Governance: Manage partner access across AWS Organizations structure",
                "Audit and Reporting: Track partner account usage, status, and organizational structure",
                "Access Control: Configure cross-account roles with least-privilege permissions",
            ],
        },
        "delete-partner": {
            "name": "delete-partner",
            "description": "Delete a partner account and clean up associated resources",
            "usage": "telcocli delete-partner --partner-name PARTNER_NAME [OPTIONS]",
            "category": "partner-account-management",
            "parameters": [
                {
                    "name": "--force",
                    "description": "Skip confirmation prompt",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--account-id",
                    "description": "Specific account ID to delete",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {
                    "command": "telcocli delete-partner --partner-name partner-name",
                    "description": "",
                },
                {
                    "command": "telcocli delete-partner --partner-name partner-name --force",
                    "description": "",
                },
            ],
            "workflows": [
                "Partner Onboarding: Create new partner accounts with proper IAM roles and cross-account trust",
                "Account Lifecycle Management: Track partner accounts from creation to deletion",
                "Security Compliance: Ensure proper permission boundaries and management account protection",
                "Multi-Account Governance: Manage partner access across AWS Organizations structure",
                "Audit and Reporting: Track partner account usage, status, and organizational structure",
                "Access Control: Configure cross-account roles with least-privilege permissions",
            ],
        },
        "list-all-accounts": {
            "name": "list-all-accounts",
            "description": "List all accounts in AWS Organizations with comprehensive Control Tower view",
            "usage": "telcocli list-all-accounts [OPTIONS]",
            "category": "partner-account-management",
            "parameters": [
                {
                    "name": "--status",
                    "description": "Filter by AWS account status",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--account-type",
                    "description": "Filter by account type (default: all)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--include-ou",
                    "description": "Include Organizational Unit information for each account",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--output",
                    "description": "Output format (default: table)",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {"command": "telcocli list-all-accounts", "description": ""},
                {
                    "command": "telcocli list-all-accounts --account-type production --include-ou --output json",
                    "description": "",
                },
            ],
            "workflows": [
                "Partner Onboarding: Create new partner accounts with proper IAM roles and cross-account trust",
                "Account Lifecycle Management: Track partner accounts from creation to deletion",
                "Security Compliance: Ensure proper permission boundaries and management account protection",
                "Multi-Account Governance: Manage partner access across AWS Organizations structure",
                "Audit and Reporting: Track partner account usage, status, and organizational structure",
                "Access Control: Configure cross-account roles with least-privilege permissions",
            ],
        },
        "create-vpn": {
            "name": "create-vpn",
            "description": "Generate VPN certificates for partner access with routing configuration",
            "usage": "telcocli create-vpn PARTNER_NAME --allowed-subnets SUBNETS [OPTIONS]",
            "category": "vpn-certificate-management",
            "parameters": [
                {
                    "name": "--certificate-duration",
                    "description": "Certificate duration (default: 30d)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--output-dir",
                    "description": "Directory to save the .ovpn file (default: .)",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {
                    "command": 'telcocli create-vpn partner-name --allowed-subnets "192.168.100.0/24,10.0.0.0/16"',
                    "description": "",
                },
                {"command": "telcocli create-vpn partner-name \\", "description": ""},
                {"command": '--allowed-subnets "192.168.100.0/24" \\', "description": ""},
                {"command": "--certificate-duration 60d \\", "description": ""},
                {"command": "--output-dir ./certificates", "description": ""},
            ],
            "workflows": [
                "Secure Partner Access: Generate VPN certificates for secure network access to AWS resources",
                "Network Segmentation: Configure routing rules to limit partner access to specific subnets",
                "Certificate Lifecycle: Manage certificate creation, renewal, and revocation processes",
                "Access Auditing: Track active VPN connections and certificate usage",
                "Security Incident Response: Quickly revoke compromised certificates and terminate connections",
                "Compliance Management: Maintain certificate inventory and expiration tracking",
            ],
        },
        "list-vpn-certificates": {
            "name": "list-vpn-certificates",
            "description": "List all active VPN certificates with optional detailed information",
            "usage": "telcocli list-vpn-certificates [OPTIONS]",
            "category": "vpn-certificate-management",
            "parameters": [
                {
                    "name": "--show-details",
                    "description": "Show detailed certificate information (validity dates, serial number)",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--output",
                    "description": "Output format (default: table)",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {"command": "telcocli list-vpn-certificates", "description": ""},
                {
                    "command": "telcocli list-vpn-certificates --show-details --output json",
                    "description": "",
                },
            ],
            "workflows": [
                "Secure Partner Access: Generate VPN certificates for secure network access to AWS resources",
                "Network Segmentation: Configure routing rules to limit partner access to specific subnets",
                "Certificate Lifecycle: Manage certificate creation, renewal, and revocation processes",
                "Access Auditing: Track active VPN connections and certificate usage",
                "Security Incident Response: Quickly revoke compromised certificates and terminate connections",
                "Compliance Management: Maintain certificate inventory and expiration tracking",
            ],
        },
        "revoke-vpn-certificate": {
            "name": "revoke-vpn-certificate",
            "description": "Revoke VPN certificates for a partner and clean up associated resources",
            "usage": "telcocli revoke-vpn-certificate PARTNER_NAME [OPTIONS]",
            "category": "vpn-certificate-management",
            "parameters": [
                {
                    "name": "--yes",
                    "description": "Skip confirmation prompt",
                    "required": False,
                    "choices": [],
                }
            ],
            "examples": [
                {"command": "telcocli revoke-vpn-certificate partner-name", "description": ""},
                {
                    "command": "telcocli revoke-vpn-certificate partner-name --yes",
                    "description": "",
                },
            ],
            "workflows": [
                "Secure Partner Access: Generate VPN certificates for secure network access to AWS resources",
                "Network Segmentation: Configure routing rules to limit partner access to specific subnets",
                "Certificate Lifecycle: Manage certificate creation, renewal, and revocation processes",
                "Access Auditing: Track active VPN connections and certificate usage",
                "Security Incident Response: Quickly revoke compromised certificates and terminate connections",
                "Compliance Management: Maintain certificate inventory and expiration tracking",
            ],
        },
        "configure-eks-access": {
            "name": "configure-eks-access",
            "description": "Configure kubectl access to EKS cluster",
            "usage": "telcocli configure-eks-access --cluster-name CLUSTER_NAME [OPTIONS]",
            "category": "eks-kubernetes-operations",
            "parameters": [
                {
                    "name": "--profile-name",
                    "description": "AWS profile name",
                    "required": False,
                    "choices": [],
                },
                {"name": "--region", "description": "AWS region", "required": False, "choices": []},
            ],
            "examples": [
                {"command": "telcocli configure-eks-access \\", "description": ""},
                {"command": "--cluster-name my-cluster \\", "description": ""},
                {"command": "--profile-name my-profile \\", "description": ""},
                {"command": "--region us-east-1", "description": ""},
            ],
            "workflows": [
                "Cloud-Native Infrastructure Deployment: Deploy complete EKS clusters with VPC, networking, and observability",
                "Edge Computing Setup: Deploy Kubernetes on AWS Outposts for edge workloads",
                "Telco Workload Optimization: Configure SR-IOV, dedicated hosts, and high-performance networking",
                "Multi-Environment Management: Deploy development, staging, and production Kubernetes environments",
                "Infrastructure as Code: Use Terraform modules for repeatable, version-controlled deployments",
                "Observability Integration: Set up Prometheus, Grafana, and CloudWatch monitoring for telco applications",
            ],
        },
        "health": {
            "name": "health",
            "description": "Run health checks for production monitoring",
            "usage": "telcocli health [OPTIONS]",
            "category": "system-operations",
            "parameters": [
                {
                    "name": "--format",
                    "description": "Output format (default: table)",
                    "required": False,
                    "choices": [],
                }
            ],
            "examples": [
                {"command": "telcocli health --format table", "description": ""},
                {"command": "telcocli health --format json", "description": ""},
            ],
            "workflows": [
                "Health Monitoring: Continuous system health checks for production environments",
                "Incident Response: Quick access to test servers and system diagnostics",
                "Remote Administration: Secure SSM-based access to instances without SSH keys",
                "Service Discovery: Locate and connect to test infrastructure and development resources",
                "Operational Readiness: Validate system connectivity and service availability",
                "Maintenance Operations: Perform routine checks and system maintenance tasks",
            ],
        },
        "list-test-servers": {
            "name": "list-test-servers",
            "description": "List all test servers with status information",
            "usage": "telcocli list-test-servers [OPTIONS]",
            "category": "system-operations",
            "parameters": [
                {
                    "name": "--status-filter",
                    "description": "Filter by server status",
                    "required": False,
                    "choices": [],
                },
                {
                    "name": "--output",
                    "description": "Output format (default: table)",
                    "required": False,
                    "choices": [],
                },
            ],
            "examples": [
                {"command": "telcocli list-test-servers --output table", "description": ""},
                {"command": "telcocli list-test-servers --status-filter online", "description": ""},
            ],
            "workflows": [
                "Health Monitoring: Continuous system health checks for production environments",
                "Incident Response: Quick access to test servers and system diagnostics",
                "Remote Administration: Secure SSM-based access to instances without SSH keys",
                "Service Discovery: Locate and connect to test infrastructure and development resources",
                "Operational Readiness: Validate system connectivity and service availability",
                "Maintenance Operations: Perform routine checks and system maintenance tasks",
            ],
        },
        "start-ssm": {
            "name": "start-ssm",
            "description": "Start SSM session to instance",
            "usage": "telcocli start-ssm --instance-id INSTANCE_ID",
            "category": "system-operations",
            "parameters": [],
            "examples": [
                {
                    "command": "telcocli start-ssm --instance-id i-1234567890abcdef0",
                    "description": "",
                }
            ],
            "workflows": [
                "Health Monitoring: Continuous system health checks for production environments",
                "Incident Response: Quick access to test servers and system diagnostics",
                "Remote Administration: Secure SSM-based access to instances without SSH keys",
                "Service Discovery: Locate and connect to test infrastructure and development resources",
                "Operational Readiness: Validate system connectivity and service availability",
                "Maintenance Operations: Perform routine checks and system maintenance tasks",
            ],
        },
        "update-credentials": {
            "name": "update-credentials",
            "description": "Update credential mappings interactively",
            "usage": "telcocli update-credentials [OPTIONS]",
            "category": "configuration-&-credentials",
            "parameters": [
                {
                    "name": "--format",
                    "description": "Output format for credential update script",
                    "required": False,
                    "choices": [],
                }
            ],
            "examples": [
                {"command": "telcocli update-credentials --format bash", "description": ""}
            ],
            "workflows": [
                "Multi-Account Access Management: Configure and manage AWS credentials across multiple accounts",
                "Profile Management: Set up AWS CLI profiles for different environments and roles",
                "Credential Rotation: Update and maintain AWS access keys and session tokens",
                "Environment Setup: Configure development and production environment access",
                "Security Compliance: Ensure proper credential management and access controls",
                "Automation Support: Prepare credential configurations for CI/CD and automation workflows",
            ],
        },
        "help": {
            "name": "help",
            "description": "Display help information for AWS CLI commands through TelcoCLI",
            "usage": "telcocli help [COMMAND_PARTS...]",
            "category": "utility-commands",
            "parameters": [],
            "examples": [
                {"command": "telcocli help ec2", "description": ""},
                {"command": "telcocli help ec2 describe-instances", "description": ""},
                {"command": "telcocli help s3 ls", "description": ""},
            ],
            "workflows": [
                "User Experience Enhancement: Provide integrated help and documentation access",
                "Developer Productivity: Enable shell autocompletion for faster command execution",
                "AWS CLI Integration: Seamless access to AWS documentation and help system",
                "Onboarding Support: Help new users discover and learn command functionality",
                "Workflow Optimization: Reduce context switching between tools and documentation",
                "Command Discovery: Explore available AWS services and operations through integrated help",
            ],
        },
        "install-completion": {
            "name": "install-completion",
            "description": "Install shell completion for TelcoCLI",
            "usage": "telcocli install-completion [OPTIONS]",
            "category": "utility-commands",
            "parameters": [
                {
                    "name": "--shell",
                    "description": "Target shell for completion",
                    "required": False,
                    "choices": [],
                }
            ],
            "examples": [
                {"command": "telcocli install-completion --shell bash", "description": ""},
                {"command": "telcocli install-completion --shell zsh", "description": ""},
            ],
            "workflows": [
                "User Experience Enhancement: Provide integrated help and documentation access",
                "Developer Productivity: Enable shell autocompletion for faster command execution",
                "AWS CLI Integration: Seamless access to AWS documentation and help system",
                "Onboarding Support: Help new users discover and learn command functionality",
                "Workflow Optimization: Reduce context switching between tools and documentation",
                "Command Discovery: Explore available AWS services and operations through integrated help",
            ],
        },
    },
    "categories": {
        "infrastructure-management": [
            "list-outposts",
            "describe-outpost",
            "get-outpost-utilization-summary",
            "analyze-dedicated-hosts",
            "assign-dedicated-host",
            "release-dedicated-host",
        ],
        "partner-account-management": [
            "create-partner",
            "list-partners",
            "describe-partner",
            "delete-partner",
            "list-all-accounts",
        ],
        "vpn-certificate-management": [
            "create-vpn",
            "list-vpn-certificates",
            "revoke-vpn-certificate",
        ],
        "eks-kubernetes-operations": ["configure-eks-access"],
        "system-operations": ["health", "list-test-servers", "start-ssm"],
        "configuration-&-credentials": ["update-credentials"],
        "utility-commands": ["help", "install-completion"],
    },
    "workflows": {
        "infrastructure-management": [
            "Daily Operations Monitoring: Monitor Outpost health, capacity, and utilization across regions",
            "Capacity Planning: Analyze current usage and forecast future infrastructure needs",
            "Resource Allocation: Assign dedicated hosts to partners and manage cross-account access",
            "Troubleshooting: Investigate performance issues and infrastructure problems",
            "Multi-Account Visibility: View instances and resources across partner accounts on shared Outposts",
            "Lifecycle Management: Track host assignments, releases, and utilization over time",
        ],
        "partner-account-management": [
            "Partner Onboarding: Create new partner accounts with proper IAM roles and cross-account trust",
            "Account Lifecycle Management: Track partner accounts from creation to deletion",
            "Security Compliance: Ensure proper permission boundaries and management account protection",
            "Multi-Account Governance: Manage partner access across AWS Organizations structure",
            "Audit and Reporting: Track partner account usage, status, and organizational structure",
            "Access Control: Configure cross-account roles with least-privilege permissions",
        ],
        "vpn-certificate-management": [
            "Secure Partner Access: Generate VPN certificates for secure network access to AWS resources",
            "Network Segmentation: Configure routing rules to limit partner access to specific subnets",
            "Certificate Lifecycle: Manage certificate creation, renewal, and revocation processes",
            "Access Auditing: Track active VPN connections and certificate usage",
            "Security Incident Response: Quickly revoke compromised certificates and terminate connections",
            "Compliance Management: Maintain certificate inventory and expiration tracking",
        ],
        "eks-kubernetes-operations": [
            "Cloud-Native Infrastructure Deployment: Deploy complete EKS clusters with VPC, networking, and observability",
            "Edge Computing Setup: Deploy Kubernetes on AWS Outposts for edge workloads",
            "Telco Workload Optimization: Configure SR-IOV, dedicated hosts, and high-performance networking",
            "Multi-Environment Management: Deploy development, staging, and production Kubernetes environments",
            "Infrastructure as Code: Use Terraform modules for repeatable, version-controlled deployments",
            "Observability Integration: Set up Prometheus, Grafana, and CloudWatch monitoring for telco applications",
        ],
        "system-operations": [
            "Health Monitoring: Continuous system health checks for production environments",
            "Incident Response: Quick access to test servers and system diagnostics",
            "Remote Administration: Secure SSM-based access to instances without SSH keys",
            "Service Discovery: Locate and connect to test infrastructure and development resources",
            "Operational Readiness: Validate system connectivity and service availability",
            "Maintenance Operations: Perform routine checks and system maintenance tasks",
        ],
        "configuration-&-credentials": [
            "Multi-Account Access Management: Configure and manage AWS credentials across multiple accounts",
            "Profile Management: Set up AWS CLI profiles for different environments and roles",
            "Credential Rotation: Update and maintain AWS access keys and session tokens",
            "Environment Setup: Configure development and production environment access",
            "Security Compliance: Ensure proper credential management and access controls",
            "Automation Support: Prepare credential configurations for CI/CD and automation workflows",
        ],
        "utility-commands": [
            "User Experience Enhancement: Provide integrated help and documentation access",
            "Developer Productivity: Enable shell autocompletion for faster command execution",
            "AWS CLI Integration: Seamless access to AWS documentation and help system",
            "Onboarding Support: Help new users discover and learn command functionality",
            "Workflow Optimization: Reduce context switching between tools and documentation",
            "Command Discovery: Explore available AWS services and operations through integrated help",
        ],
    },
    "metadata": {"version": "2.0", "source": "telcocli-workflows.md", "total_commands": 21},
}

AWS_ERRORS = {
    "AccessDenied": {
        "description": "IAM permissions issue - the credentials don't have required permissions",
        "common_causes": [
            "Missing IAM policy permissions",
            "Incorrect AWS profile selected",
            "Session token expired",
            "Resource-based policy blocking access",
        ],
        "solutions": [
            "Check IAM policies attached to your user/role",
            "Verify you're using the correct AWS profile with --profile",
            "Refresh your AWS credentials if using temporary credentials",
            "Check resource-based policies (e.g., S3 bucket policies)",
        ],
        "aws_docs": "https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html",
    },
    "InvalidParameterValue": {
        "description": "One or more parameters have invalid values",
        "common_causes": [
            "Incorrect parameter format",
            "Value out of acceptable range",
            "Incompatible parameter combination",
        ],
        "solutions": [
            "Check parameter format in command documentation",
            "Verify parameter values are within acceptable ranges",
            "Review parameter combinations for compatibility",
        ],
        "aws_docs": "https://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html",
    },
    "ResourceNotFound": {
        "description": "The specified resource doesn't exist",
        "common_causes": [
            "Resource ID is incorrect",
            "Resource was deleted",
            "Wrong region selected",
            "Resource in different account",
        ],
        "solutions": [
            "Verify the resource ID is correct",
            "Check if resource exists in the AWS Console",
            "Ensure you're in the correct region with --region",
            "Confirm you're using the correct AWS account",
        ],
        "aws_docs": "https://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html",
    },
    "ThrottlingException": {
        "description": "API rate limit exceeded",
        "common_causes": ["Too many API calls in short time", "Shared account limits reached"],
        "solutions": [
            "Implement exponential backoff and retry",
            "Reduce frequency of API calls",
            "Request service quota increase if needed",
        ],
        "aws_docs": "https://docs.aws.amazon.com/general/latest/gr/api-retries.html",
    },
}
