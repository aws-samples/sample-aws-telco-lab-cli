# TelcoCLI System Architecture

**Version:** 1.0  
**Last Updated:** 2025-01-26  
**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [System Context](#system-context)
3. [Architecture Principles](#architecture-principles)
4. [Component Architecture](#component-architecture)
5. [AWS Service Integration](#aws-service-integration)
6. [Security Architecture](#security-architecture)
7. [Data Flow](#data-flow)
8. [Deployment Architecture](#deployment-architecture)
9. [Technology Stack](#technology-stack)

---

## Overview

TelcoCLI is a Python-based command-line interface designed for telecommunications lab automation and AWS infrastructure management. The system provides a unified interface for managing complex AWS environments including Organizations, IAM, EC2 Dedicated Hosts, EKS clusters, VPN configurations, and Outposts.

### Key Characteristics

- **Architecture Style:** Modular CLI with service-oriented internal architecture
- **Deployment Model:** Local CLI tool with AWS cloud integration
- **Primary Users:** DevOps engineers, infrastructure administrators, telecommunications operators
- **Scale:** Manages multiple AWS accounts across organizations

---

## System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                         TelcoCLI System                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐ │
│  │   Commands   │───▶│   Services   │───▶│  AWS Services   │ │
│  │   (CLI UX)   │    │  (Business   │    │  (Cloud Infra)  │ │
│  │              │    │   Logic)     │    │                 │ │
│  └──────────────┘    └──────────────┘    └─────────────────┘ │
│         │                    │                     │           │
│         ▼                    ▼                     ▼           │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐ │
│  │    Utils     │    │  Exceptions  │    │  Configuration  │ │
│  │  (Helpers)   │    │   (Errors)   │    │    (Settings)   │ │
│  └──────────────┘    └──────────────┘    └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │           AWS Cloud Services                │
        │                                             │
        │  • Organizations  • IAM      • EC2          │
        │  • EKS           • VPC      • S3           │
        │  • RAM           • STS      • SSM          │
        │  • Outposts      • Secrets  • CloudWatch   │
        └─────────────────────────────────────────────┘
```

### External Actors

1. **DevOps Engineers** - Primary users managing infrastructure
2. **Infrastructure Administrators** - Configure and maintain AWS environments
3. **Telecommunications Operators** - Manage telco-specific resources
4. **AWS Services** - Cloud infrastructure being managed
5. **Partner Organizations** - External AWS accounts with cross-account access

---

## Architecture Principles

### 1. Modularity
- Commands are independent and focused on single responsibilities
- Services encapsulate AWS API interactions
- Utilities provide reusable functionality

### 2. Security by Design
- Least privilege IAM policies
- No hardcoded credentials
- Secure credential management via AWS credential chain
- Input validation on all user inputs
- Audit logging for sensitive operations

### 3. Fail-Safe Defaults
- Operations require explicit confirmation for destructive actions
- Default timeouts prevent hanging operations
- Comprehensive error handling with meaningful messages

### 4. Separation of Concerns
- CLI layer handles user interaction
- Service layer handles business logic
- AWS SDK layer handles cloud API calls

### 5. Testability
- Dependency injection for AWS clients
- Mockable interfaces for testing
- Comprehensive unit test coverage

---

## Component Architecture

### Layer 1: Command Layer (`telco_cli.commands`)

**Responsibility:** User interface and input validation

**Components:**
- `BaseCommand` - Abstract base class defining command contract
- Individual command implementations (30+ commands)
- Argument parsing and validation
- User feedback and output formatting

**Key Commands:**
- `create-partner` - Partner account provisioning
- `configure-eks-access` - EKS cluster access configuration
- `list-test-servers` - SSM-managed server inventory
- `deploy-eks-full` - Complete EKS deployment
- `health` - System health checks

### Layer 2: Service Layer (`telco_cli.services`)

**Responsibility:** Business logic and AWS service orchestration

**Components:**
- `AccountProvisioningEngine` - Multi-step account creation workflow
- `OrganizationsService` - AWS Organizations management
- `IAMService` - IAM role and policy management
- `EC2Service` - EC2 and Dedicated Host management
- `EKSDeploymentService` - EKS cluster lifecycle management
- `SSMService` - Systems Manager operations
- `InstanceService` - EC2 instance management

**Design Pattern:** Service-oriented architecture with dependency injection

### Layer 3: Utility Layer (`telco_cli.utils`)

**Responsibility:** Cross-cutting concerns and helpers

**Components:**
- `logging` - Structured logging configuration
- `formatters` - Output formatting (JSON, table, text)
- `validation` - Input validation functions
- `aws_utils` - AWS SDK helpers
- `constants` - Application-wide constants

### Layer 4: Type System (`telco_cli.types`)

**Responsibility:** Type definitions and data models

**Components:**
- `BaseCommand` - Command interface
- `NetworkInterface` - Network interface data model
- `OutpostData` - Outpost information model
- `Provisioning` - Account provisioning data structures

### Layer 5: Exception Handling (`telco_cli.exceptions`)

**Responsibility:** Structured error handling

**Components:**
- `TelcoCLIException` - Base exception class
- `ErrorCode` - Enumeration of error codes
- Specific exception types for different failure scenarios

---

## AWS Service Integration

### Service Integration Map

```
TelcoCLI
    │
    ├─▶ AWS Organizations
    │   └─ Account creation, OU management, SCP policies
    │
    ├─▶ AWS IAM
    │   └─ Role creation, policy management, trust relationships
    │
    ├─▶ Amazon EC2
    │   └─ Dedicated Hosts, instances, security groups, VPC
    │
    ├─▶ Amazon EKS
    │   └─ Cluster creation, node groups, access configuration
    │
    ├─▶ AWS Systems Manager (SSM)
    │   └─ Session management, command execution, parameter store
    │
    ├─▶ AWS Resource Access Manager (RAM)
    │   └─ Cross-account resource sharing
    │
    ├─▶ AWS STS
    │   └─ Temporary credentials, assume role operations
    │
    ├─▶ Amazon S3
    │   └─ Configuration storage, artifact management
    │
    ├─▶ AWS Secrets Manager
    │   └─ Credential storage and rotation
    │
    └─▶ AWS Outposts
        └─ On-premises infrastructure management
```

### Integration Patterns

#### 1. AWS Organizations Integration
- **Purpose:** Multi-account management
- **Operations:** Create accounts, manage OUs, apply SCPs
- **Security:** Management account credentials required
- **Error Handling:** Retry with exponential backoff

#### 2. IAM Integration
- **Purpose:** Access control and permissions
- **Operations:** Create roles, attach policies, manage trust relationships
- **Security:** Least privilege policies, permission boundaries
- **Error Handling:** Policy validation before application

#### 3. EC2 Integration
- **Purpose:** Compute resource management
- **Operations:** Dedicated Host allocation, instance management, VPC configuration
- **Security:** Security group restrictions, private subnets
- **Error Handling:** Resource state validation

#### 4. EKS Integration
- **Purpose:** Kubernetes cluster management
- **Operations:** Cluster creation, node group management, access configuration
- **Security:** IRSA (IAM Roles for Service Accounts), network policies
- **Error Handling:** Cluster state monitoring, rollback on failure

#### 5. SSM Integration
- **Purpose:** Remote management and automation
- **Operations:** Session management, command execution, parameter storage
- **Security:** Session encryption, audit logging
- **Error Handling:** Connection timeout handling

---

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                  Security Layer 1                       │
│              Authentication & Authorization             │
│  • AWS Credential Chain                                 │
│  • IAM Roles and Policies                              │
│  • MFA for Sensitive Operations                        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  Security Layer 2                       │
│                 Input Validation                        │
│  • Account ID validation                                │
│  • Parameter sanitization                               │
│  • Command injection prevention                         │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  Security Layer 3                       │
│              Network Security                           │
│  • VPC isolation                                        │
│  • Security group restrictions                          │
│  • Private subnet deployment                            │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  Security Layer 4                       │
│                Data Protection                          │
│  • Encryption at rest (AWS KMS)                        │
│  • Encryption in transit (TLS 1.2+)                    │
│  • Secrets Manager integration                          │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  Security Layer 5                       │
│              Audit & Monitoring                         │
│  • CloudTrail logging                                   │
│  • Application logging                                  │
│  • Security Hub integration                             │
└─────────────────────────────────────────────────────────┘
```

### Security Controls

#### Authentication
- **AWS Credential Chain:** Supports IAM roles, profiles, environment variables
- **MFA:** Required for sensitive operations in production
- **Session Management:** Temporary credentials via STS

#### Authorization
- **IAM Policies:** Least privilege principle
- **Permission Boundaries:** Limit maximum permissions
- **Service Control Policies:** Organization-level restrictions

#### Data Protection
- **Credentials:** Never stored in code, use AWS credential providers
- **Secrets:** Stored in AWS Secrets Manager
- **Encryption:** KMS for data at rest, TLS for data in transit

#### Network Security
- **VPC Isolation:** Resources deployed in private subnets
- **Security Groups:** Restrictive ingress/egress rules
- **VPC Endpoints:** Private AWS service access

#### Audit & Compliance
- **CloudTrail:** All API calls logged
- **Application Logs:** Structured logging with correlation IDs
- **Security Hub:** Centralized security findings

---

## Data Flow

### Partner Account Creation Flow

```
User Command
    │
    ▼
┌─────────────────────────────────────┐
│  create-partner Command             │
│  • Validate inputs                  │
│  • Parse parameters                 │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  AccountProvisioningEngine          │
│  • Orchestrate workflow             │
│  • Handle state transitions         │
└─────────────────────────────────────┘
    │
    ├─▶ Step 1: Create AWS Account
    │   └─ OrganizationsService.create_account()
    │
    ├─▶ Step 2: Wait for Account Ready
    │   └─ Poll account status
    │
    ├─▶ Step 3: Create IAM Roles
    │   └─ IAMService.create_cross_account_role()
    │
    ├─▶ Step 4: Apply Permission Boundaries
    │   └─ IAMService.attach_boundary_policy()
    │
    └─▶ Step 5: Configure Trust Relationships
        └─ IAMService.update_trust_policy()
    │
    ▼
┌─────────────────────────────────────┐
│  Return Result                      │
│  • Account ID                       │
│  • Role ARNs                        │
│  • Switch role URLs                 │
└─────────────────────────────────────┘
```

### EKS Deployment Flow

```
User Command
    │
    ▼
┌─────────────────────────────────────┐
│  deploy-eks-full Command            │
│  • Validate cluster config          │
│  • Check prerequisites              │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  EKSDeploymentService               │
│  • Orchestrate deployment           │
│  • Monitor progress                 │
└─────────────────────────────────────┘
    │
    ├─▶ Step 1: Create VPC
    │   └─ EC2Service.create_vpc()
    │
    ├─▶ Step 2: Create EKS Cluster
    │   └─ EKS API: create_cluster()
    │
    ├─▶ Step 3: Wait for Cluster Active
    │   └─ Poll cluster status
    │
    ├─▶ Step 4: Create Node Group
    │   └─ EKS API: create_nodegroup()
    │
    ├─▶ Step 5: Configure kubectl Access
    │   └─ Update kubeconfig
    │
    └─▶ Step 6: Apply Security Policies
        └─ Kubernetes API: apply manifests
    │
    ▼
┌─────────────────────────────────────┐
│  Return Result                      │
│  • Cluster endpoint                 │
│  • Node group status                │
│  • kubectl config                   │
└─────────────────────────────────────┘
```

---

## Deployment Architecture

### Local Deployment

```
┌─────────────────────────────────────────────────────┐
│              Developer Workstation                  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │           TelcoCLI Installation              │  │
│  │                                              │  │
│  │  • Python 3.9+ runtime                      │  │
│  │  • pip package manager                      │  │
│  │  • AWS CLI configured                       │  │
│  │  • kubectl (optional)                       │  │
│  └──────────────────────────────────────────────┘  │
│                      │                             │
│                      ▼                             │
│  ┌──────────────────────────────────────────────┐  │
│  │        AWS Credentials                       │  │
│  │                                              │  │
│  │  • ~/.aws/credentials                       │  │
│  │  • ~/.aws/config                            │  │
│  │  • Environment variables                    │  │
│  │  • IAM role (EC2/ECS)                      │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │      AWS Cloud              │
        │                             │
        │  • API Gateway              │
        │  • AWS Services             │
        │  • CloudTrail Logging       │
        └─────────────────────────────┘
```

### CI/CD Integration

```
┌─────────────────────────────────────────────────────┐
│              CI/CD Pipeline                         │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │         Build Stage                          │  │
│  │  • Install dependencies                      │  │
│  │  • Run unit tests                            │  │
│  │  • Code quality checks                       │  │
│  └──────────────────────────────────────────────┘  │
│                      │                             │
│                      ▼                             │
│  ┌──────────────────────────────────────────────┐  │
│  │         Security Scan Stage                  │  │
│  │  • SAST (Bandit, Semgrep)                   │  │
│  │  • Dependency scanning                       │  │
│  │  • Secret detection                          │  │
│  └──────────────────────────────────────────────┘  │
│                      │                             │
│                      ▼                             │
│  ┌──────────────────────────────────────────────┐  │
│  │         Package Stage                        │  │
│  │  • Build wheel                               │  │
│  │  • Generate documentation                    │  │
│  │  • Create release artifacts                  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.9+ | Core implementation |
| CLI Framework | argparse | stdlib | Command-line interface |
| AWS SDK | boto3 | 1.0+ | AWS service integration |
| Output Formatting | rich | 14.0+ | Enhanced console output |
| Testing | pytest | 8.0+ | Unit and integration tests |
| Code Quality | black, isort, flake8 | latest | Code formatting and linting |
| Type Checking | mypy | latest | Static type analysis |

### AWS Services

| Service | Purpose | Security Considerations |
|---------|---------|------------------------|
| Organizations | Multi-account management | Management account access required |
| IAM | Access control | Least privilege policies |
| EC2 | Compute resources | Security group restrictions |
| EKS | Kubernetes clusters | IRSA, network policies |
| VPC | Network isolation | Private subnets, VPC endpoints |
| SSM | Remote management | Session encryption |
| S3 | Storage | Encryption at rest, bucket policies |
| Secrets Manager | Credential storage | Automatic rotation |
| CloudTrail | Audit logging | Immutable logs |
| KMS | Encryption | Key rotation policies |

### Development Tools

| Tool | Purpose |
|------|---------|
| Brazil | Build system (Amazon internal) |
| Git | Version control |
| CRUX | Code review (Amazon internal) |
| pytest-cov | Code coverage |
| bandit | Security scanning |

---

## Architecture Decision Records

### ADR-001: Command Pattern for CLI

**Status:** Accepted

**Context:** Need extensible command structure for 30+ commands

**Decision:** Use command pattern with BaseCommand abstract class

**Consequences:**
- ✅ Easy to add new commands
- ✅ Consistent error handling
- ✅ Testable in isolation
- ❌ Slight overhead for simple commands

### ADR-002: Service Layer Abstraction

**Status:** Accepted

**Context:** Complex AWS service interactions need orchestration

**Decision:** Separate service layer for business logic

**Consequences:**
- ✅ Testable without AWS calls
- ✅ Reusable across commands
- ✅ Clear separation of concerns
- ❌ Additional abstraction layer

### ADR-003: AWS Credential Chain

**Status:** Accepted

**Context:** Need flexible credential management

**Decision:** Use boto3 default credential chain

**Consequences:**
- ✅ Supports multiple credential sources
- ✅ No credential storage in code
- ✅ Compatible with AWS best practices
- ❌ Requires user configuration

### ADR-004: Structured Error Handling

**Status:** Accepted

**Context:** Need consistent error reporting

**Decision:** Use ErrorCode enum with TelcoCLIException

**Consequences:**
- ✅ Consistent error codes
- ✅ Machine-readable errors
- ✅ Clear error messages
- ❌ Requires error code maintenance

---

## Future Architecture Considerations

### Planned Enhancements

1. **API Server Mode**
   - REST API for programmatic access
   - Authentication via API keys
   - Rate limiting and throttling

2. **Event-Driven Architecture**
   - CloudWatch Events integration
   - Automated remediation workflows
   - Notification system

3. **Multi-Region Support**
   - Region-aware operations
   - Cross-region replication
   - Disaster recovery

4. **Enhanced Monitoring**
   - Prometheus metrics export
   - Grafana dashboards
   - Custom CloudWatch metrics

5. **Plugin System**
   - Third-party command extensions
   - Custom service integrations
   - Hook system for automation

---

## References

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [Python CLI Best Practices](https://docs.python-guide.org/writing/structure/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

---

**Document Control:**
- **Version:** 1.0
- **Last Updated:** 2025-01-26
- **Next Review:** 2025-04-26
- **Owner:** TelcoCLI Development Team
