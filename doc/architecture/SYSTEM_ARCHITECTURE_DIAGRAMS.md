# TelcoCLI System Architecture Diagrams

This document contains comprehensive system architecture diagrams for TelcoCLI.

## Table of Contents
1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Component Architecture](#2-component-architecture)
3. [Command Execution Flow](#3-command-execution-flow)
4. [Account Provisioning Flow](#4-account-provisioning-flow)
5. [AI Agent Integration](#5-ai-agent-integration)
6. [Multi-Account Architecture](#6-multi-account-architecture)
7. [Data Flow Diagram](#7-data-flow-diagram)
8. [Deployment Architecture](#8-deployment-architecture)

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Entry Point<br/>cli.py]
        Agent[AI Agent<br/>Natural Language Interface]
    end
    
    subgraph "Command Layer"
        CMD1[Infrastructure Commands]
        CMD2[Partner Commands]
        CMD3[VPN Commands]
        CMD4[EKS Commands]
        CMD5[System Commands]
    end
    
    subgraph "Service Layer"
        SVC1[Account Provisioning<br/>Service]
        SVC2[EKS Deployment<br/>Service]
        SVC3[EC2 Service]
        SVC4[Organizations<br/>Service]
        SVC5[IAM Service]
        SVC6[SSM Service]
    end
    
    subgraph "Infrastructure Layer"
        AWS1[AWS Client Manager]
        AWS2[Organizations Helper]
        AWS3[IAM Helper]
        AWS4[EC2 Helper]
    end
    
    subgraph "External Systems"
        ORG[AWS Organizations]
        EC2[AWS EC2/Outposts]
        IAM[AWS IAM]
        EKS[AWS EKS]
        SSM[AWS SSM]
        BEDROCK[Amazon Bedrock]
        TF[Terraform]
    end
    
    CLI --> CMD1 & CMD2 & CMD3 & CMD4 & CMD5
    Agent --> CMD1 & CMD2 & CMD3 & CMD4 & CMD5
    
    CMD1 & CMD2 & CMD3 & CMD4 & CMD5 --> SVC1 & SVC2 & SVC3 & SVC4 & SVC5 & SVC6
    
    SVC1 & SVC2 & SVC3 & SVC4 & SVC5 & SVC6 --> AWS1 & AWS2 & AWS3 & AWS4
    
    AWS1 & AWS2 & AWS3 & AWS4 --> ORG & EC2 & IAM & EKS & SSM
    SVC2 --> TF
    Agent --> BEDROCK
    
    style CLI fill:#e1f5ff
    style Agent fill:#e1f5ff
    style SVC1 fill:#fff4e6
    style SVC2 fill:#fff4e6
    style AWS1 fill:#f3e5f5
    style ORG fill:#e8f5e9
    style BEDROCK fill:#e8f5e9
```

---

## 2. Component Architecture

```mermaid
graph LR
    subgraph "TelcoCLI Application"
        subgraph "Presentation"
            CLI[CLI Parser<br/>argparse]
            OUT[Output Formatters<br/>Rich/JSON/Table]
        end
        
        subgraph "Commands"
            BASE[BaseCommand<br/>Abstract Class]
            INFRA[Infrastructure<br/>Commands]
            PARTNER[Partner<br/>Commands]
            VPN[VPN<br/>Commands]
            K8S[EKS<br/>Commands]
        end
        
        subgraph "Services"
            PROV[Account<br/>Provisioning]
            DEPLOY[EKS<br/>Deployment]
            MONITOR[Monitoring<br/>Service]
        end
        
        subgraph "AI Integration"
            AGENT[TelcoCLI Agent]
            KB[Knowledge Base]
            MCP[MCP Server]
            TOOLS[Agent Tools]
        end
        
        subgraph "Utilities"
            AWSUTIL[AWS Utils]
            LOG[Logging]
            VALID[Validation]
            FMT[Formatters]
        end
        
        subgraph "Types & Exceptions"
            TYPES[Data Models]
            EXC[Exception Classes]
            CODES[Error Codes]
        end
    end
    
    CLI --> BASE
    BASE --> INFRA & PARTNER & VPN & K8S
    INFRA & PARTNER & VPN & K8S --> PROV & DEPLOY & MONITOR
    PROV & DEPLOY & MONITOR --> AWSUTIL
    
    AGENT --> TOOLS
    TOOLS --> INFRA & PARTNER & VPN & K8S
    AGENT --> KB
    AGENT --> MCP
    
    INFRA & PARTNER & VPN & K8S --> OUT
    PROV & DEPLOY & MONITOR --> LOG & VALID
    INFRA & PARTNER & VPN & K8S --> EXC
    EXC --> CODES
    
    style CLI fill:#4fc3f7
    style AGENT fill:#81c784
    style PROV fill:#ffb74d
    style AWSUTIL fill:#ba68c8
```

---

## 3. Command Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI Entry Point
    participant Parser as Argument Parser
    participant Discovery as Command Discovery
    participant Command as Command Instance
    participant Service as Service Layer
    participant AWS as AWS SDK
    participant Formatter as Output Formatter
    
    User->>CLI: telcocli list-outposts --output table
    CLI->>Parser: Parse arguments
    Parser->>Discovery: Discover commands
    Discovery->>Discovery: Scan commands/ directory
    Discovery->>Discovery: Import modules
    Discovery->>Discovery: Find BaseCommand subclasses
    Discovery-->>Parser: Return command list
    Parser->>Parser: Register subparsers
    Parser->>Command: Instantiate ListOutpostsCommand
    Command->>Command: register(parser)
    Parser-->>CLI: Parsed args
    CLI->>Command: run(args)
    Command->>Service: Get Outposts data
    Service->>AWS: boto3.client('outposts')
    AWS->>AWS: list_outposts()
    AWS-->>Service: Outpost data
    Service->>Service: Process & enrich data
    Service-->>Command: Processed results
    Command->>Formatter: Format as table
    Formatter-->>Command: Rich table
    Command-->>User: Display table
    
    Note over User,Formatter: Total execution time: 1-3 seconds
```

---

## 4. Account Provisioning Flow

```mermaid
sequenceDiagram
    participant User
    participant CMD as CreatePartnerCommand
    participant Engine as AccountProvisioningEngine
    participant OrgAPI as Organizations API
    participant STS as STS API
    participant IAM as IAM API (Target Account)
    
    User->>CMD: create-partner --partner-name acme
    CMD->>CMD: Validate inputs
    CMD->>Engine: provision_partner_account()
    
    Note over Engine,OrgAPI: Step 1: Create Account
    Engine->>OrgAPI: create_account()
    OrgAPI-->>Engine: CreateAccountStatus ID
    Engine->>OrgAPI: Poll describe_create_account_status()
    OrgAPI-->>Engine: Account ID (after ~30-60s)
    
    Note over Engine,STS: Step 2: Assume Role
    Engine->>Engine: Validate not same account
    Engine->>STS: assume_role(OrganizationAccountAccessRole)
    STS-->>Engine: Temporary credentials
    
    Note over Engine,IAM: Step 3: Create IAM Setup
    Engine->>IAM: Create permission boundary policy
    IAM-->>Engine: Boundary policy ARN
    
    Engine->>IAM: Create partner roles (Admin/ReadOnly/etc)
    IAM-->>Engine: Role ARNs
    
    Engine->>IAM: Create role policies
    IAM-->>Engine: Policy ARNs
    
    Engine->>IAM: Attach policies to roles
    IAM-->>Engine: Success
    
    Engine->>IAM: Create JDA admin role
    IAM-->>Engine: Admin role ARN
    
    Engine->>IAM: Attach AdministratorAccess
    IAM-->>Engine: Success
    
    Note over Engine,OrgAPI: Step 4: Tag Account
    Engine->>OrgAPI: tag_resource()
    OrgAPI-->>Engine: Success
    
    Engine-->>CMD: AccountProvisioningResult
    CMD-->>User: Display success with role URLs
    
    Note over User,IAM: Total time: 60-120 seconds
```

---

## 5. AI Agent Integration

```mermaid
graph TB
    subgraph "User Interaction"
        USER[User Query:<br/>"list outposts in us-west-2"]
    end
    
    subgraph "AI Agent Layer"
        AGENT[TelcoCLI Agent<br/>Strands Framework]
        SESSION[Session Manager<br/>Conversation Context]
        PROMPT[System Prompt<br/>Command Selection Logic]
    end
    
    subgraph "Tool Layer"
        SEARCH[search_commands_tool<br/>Knowledge Base Search]
        EXEC[execute_command_tool<br/>TelcoCLI Execution]
        BASH[enhanced_execute_bash_tool<br/>AWS CLI Fallback]
        DOCS[enhanced_search_aws_docs_tool<br/>Documentation]
    end
    
    subgraph "Knowledge Base"
        KB_CMD[commands.json<br/>21 Commands]
        KB_ERR[aws_errors.json<br/>Error Patterns]
        KB_CACHE[Pre-built Cache<br/>Fast Loading]
    end
    
    subgraph "Execution Layer"
        MCP[MCP Server<br/>Command Executor]
        CLI_EXEC[CLI Commands]
        AWS_CLI[AWS CLI]
    end
    
    subgraph "External Services"
        BEDROCK[Amazon Bedrock<br/>Claude 4]
        AWS_API[AWS APIs]
    end
    
    USER --> AGENT
    AGENT --> SESSION
    AGENT --> PROMPT
    AGENT --> BEDROCK
    
    PROMPT --> SEARCH
    SEARCH --> KB_CMD & KB_ERR & KB_CACHE
    
    SEARCH -->|Command Found| EXEC
    SEARCH -->|No Command| BASH
    
    EXEC --> MCP
    MCP --> CLI_EXEC
    CLI_EXEC --> AWS_API
    
    BASH --> AWS_CLI
    AWS_CLI --> AWS_API
    
    AGENT --> DOCS
    
    AWS_API -->|Response| AGENT
    AGENT -->|Formatted Answer| USER
    
    style USER fill:#e3f2fd
    style AGENT fill:#c8e6c9
    style BEDROCK fill:#fff9c4
    style KB_CMD fill:#f3e5f5
    style MCP fill:#ffe0b2
```

---

## 6. Multi-Account Architecture

```mermaid
graph TB
    subgraph "User Workstation"
        CLI[TelcoCLI]
        CREDS[AWS Credentials<br/>~/.aws/credentials]
        PROFILES[AWS Profiles<br/>~/.aws/config]
    end
    
    subgraph "Management Account"
        ORG[AWS Organizations]
        MGMT_IAM[IAM Roles]
    end
    
    subgraph "Outpost Account"
        OUTPOSTS[AWS Outposts]
        EC2[EC2 Instances]
        HOSTS[Dedicated Hosts]
        OUTPOST_IAM[IAM Roles]
    end
    
    subgraph "Partner Account 1"
        P1_IAM[Partner IAM Roles<br/>- Admin Role<br/>- ReadOnly Role<br/>- JDA Admin Role]
        P1_BOUNDARY[Permission Boundary]
        P1_RESOURCES[Partner Resources]
    end
    
    subgraph "Partner Account 2"
        P2_IAM[Partner IAM Roles]
        P2_BOUNDARY[Permission Boundary]
        P2_RESOURCES[Partner Resources]
    end
    
    subgraph "VPN Server Account"
        VPN[VPN Server<br/>EC2 Instance]
        CERTS[Certificate Store]
        VPN_SSM[SSM Agent]
    end
    
    subgraph "Workload Account"
        EKS[EKS Clusters]
        WORKERS[Worker Nodes]
        APPS[Applications]
    end
    
    CLI --> CREDS & PROFILES
    
    CLI -->|--profile mgmt| ORG
    CLI -->|--profile outpost| OUTPOSTS & EC2 & HOSTS
    CLI -->|--profile vpn| VPN
    CLI -->|--profile workload| EKS
    
    ORG -->|Create Account| P1_IAM & P2_IAM
    ORG -->|AssumeRole| P1_IAM & P2_IAM
    
    P1_IAM --> P1_BOUNDARY
    P1_BOUNDARY --> P1_RESOURCES
    
    P2_IAM --> P2_BOUNDARY
    P2_BOUNDARY --> P2_RESOURCES
    
    HOSTS -->|RAM Share| P1_RESOURCES & P2_RESOURCES
    
    CLI -->|SSM Commands| VPN_SSM
    VPN_SSM --> CERTS
    
    EKS --> WORKERS
    WORKERS -->|On Outposts| OUTPOSTS
    WORKERS -->|On Dedicated Hosts| HOSTS
    
    style CLI fill:#4fc3f7
    style ORG fill:#81c784
    style P1_BOUNDARY fill:#ef5350
    style P2_BOUNDARY fill:#ef5350
    style HOSTS fill:#ffb74d
```

---

## 7. Data Flow Diagram

```mermaid
flowchart TD
    START([User Command]) --> PARSE[Parse Arguments]
    PARSE --> VALIDATE{Validate<br/>Inputs}
    VALIDATE -->|Invalid| ERROR1[Display Error]
    VALIDATE -->|Valid| AUTH{AWS<br/>Credentials<br/>Valid?}
    
    AUTH -->|No| ERROR2[Credential Error]
    AUTH -->|Yes| DISCOVER[Discover Command]
    
    DISCOVER --> INSTANTIATE[Instantiate Command]
    INSTANTIATE --> EXECUTE[Execute Command.run]
    
    EXECUTE --> SERVICE[Call Service Layer]
    SERVICE --> CLIENT[Get AWS Client]
    CLIENT --> CACHE{Client<br/>Cached?}
    
    CACHE -->|Yes| REUSE[Reuse Client]
    CACHE -->|No| CREATE[Create New Client]
    CREATE --> STORE[Store in Cache]
    STORE --> REUSE
    
    REUSE --> API[Call AWS API]
    API --> PAGINATE{Paginated<br/>Response?}
    
    PAGINATE -->|Yes| LOOP[Iterate Pages]
    LOOP --> COLLECT[Collect Results]
    COLLECT --> PROCESS
    
    PAGINATE -->|No| PROCESS[Process Response]
    
    PROCESS --> ENRICH[Enrich Data]
    ENRICH --> FORMAT{Output<br/>Format?}
    
    FORMAT -->|JSON| JSON_OUT[JSON Formatter]
    FORMAT -->|Table| TABLE_OUT[Rich Table Formatter]
    FORMAT -->|Summary| SUMMARY_OUT[Summary Formatter]
    
    JSON_OUT --> DISPLAY[Display to User]
    TABLE_OUT --> DISPLAY
    SUMMARY_OUT --> DISPLAY
    
    DISPLAY --> LOG[Write to Log]
    LOG --> END([Complete])
    
    ERROR1 --> END
    ERROR2 --> END
    
    style START fill:#e1f5ff
    style END fill:#c8e6c9
    style ERROR1 fill:#ffcdd2
    style ERROR2 fill:#ffcdd2
    style API fill:#fff9c4
    style DISPLAY fill:#e1f5ff
```

---

## 8. Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV_WS[Developer Workstation]
        DEV_CLI[TelcoCLI<br/>pip install -e .]
        DEV_TEST[pytest<br/>Unit Tests]
    end
    
    subgraph "CI/CD Pipeline"
        GIT[Git Repository]
        BUILD[Brazil Build<br/>brazil-build release]
        TEST[Test Suite<br/>pytest --cov]
        LINT[Code Quality<br/>mypy, black, isort]
        PACKAGE[Package Build<br/>Python Wheel]
    end
    
    subgraph "Distribution"
        BRAZIL[Brazil Package<br/>Repository]
        PIP[pip install]
        S3[S3 Distribution<br/>Optional]
    end
    
    subgraph "User Environments"
        USER1[User Workstation 1<br/>telcocli installed]
        USER2[User Workstation 2<br/>telcocli installed]
        CICD[CI/CD Runner<br/>Automated Scripts]
    end
    
    subgraph "Runtime Dependencies"
        PYTHON[Python 3.9+]
        BOTO3[boto3/botocore]
        RICH[Rich Console]
        STRANDS[Strands Framework]
        TERRAFORM[Terraform Binary<br/>Optional for EKS]
    end
    
    subgraph "AWS Services"
        BEDROCK[Amazon Bedrock<br/>AI Agent]
        ORG_SVC[AWS Organizations]
        EC2_SVC[AWS EC2/Outposts]
        IAM_SVC[AWS IAM]
        EKS_SVC[AWS EKS]
    end
    
    DEV_WS --> DEV_CLI
    DEV_CLI --> DEV_TEST
    DEV_WS --> GIT
    
    GIT --> BUILD
    BUILD --> TEST
    TEST --> LINT
    LINT --> PACKAGE
    PACKAGE --> BRAZIL
    PACKAGE --> S3
    
    BRAZIL --> PIP
    S3 --> PIP
    
    PIP --> USER1 & USER2 & CICD
    
    USER1 & USER2 & CICD --> PYTHON & BOTO3 & RICH & STRANDS
    USER1 & USER2 --> TERRAFORM
    
    USER1 & USER2 & CICD --> BEDROCK & ORG_SVC & EC2_SVC & IAM_SVC & EKS_SVC
    
    style DEV_WS fill:#e3f2fd
    style PACKAGE fill:#c8e6c9
    style USER1 fill:#fff9c4
    style BEDROCK fill:#ffe0b2
```

---

## 9. Security Architecture

```mermaid
graph TB
    subgraph "Authentication Layer"
        CREDS[AWS Credentials<br/>Access Key + Secret]
        PROFILES[AWS Profiles<br/>Named Configurations]
        ENV[Environment Variables<br/>AWS_PROFILE, AWS_REGION]
    end
    
    subgraph "Authorization Layer"
        IAM_USER[IAM User/Role<br/>in Source Account]
        ASSUME[AssumeRole<br/>Cross-Account]
        BOUNDARY[Permission Boundary<br/>Maximum Permissions]
    end
    
    subgraph "Management Account"
        MGMT_ROLE[Management Role<br/>Organizations Admin]
        ORG_PERMS[Organizations Permissions<br/>- CreateAccount<br/>- TagResource<br/>- DescribeAccount]
    end
    
    subgraph "Target Partner Account"
        ORG_ACCESS[OrganizationAccountAccessRole<br/>Assumed by Management]
        PARTNER_ROLES[Partner Roles<br/>- Admin Role<br/>- ReadOnly Role]
        JDA_ROLE[JDA Admin Role<br/>Full Administrator]
        BOUNDARY_POLICY[Permission Boundary Policy<br/>Limits Max Permissions]
    end
    
    subgraph "Security Controls"
        SAME_ACCT[Same Account Check<br/>Prevents Self-Assumption]
        TRUST_POLICY[Trust Policy<br/>Defines Who Can Assume]
        DENY_RULES[Explicit Deny Rules<br/>IAM Restrictions]
        AUDIT[CloudTrail Logging<br/>All API Calls]
    end
    
    CREDS --> IAM_USER
    PROFILES --> IAM_USER
    ENV --> IAM_USER
    
    IAM_USER --> MGMT_ROLE
    MGMT_ROLE --> ORG_PERMS
    
    ORG_PERMS -->|Create Account| ORG_ACCESS
    MGMT_ROLE -->|AssumeRole| ASSUME
    ASSUME --> SAME_ACCT
    SAME_ACCT -->|Different Account| ORG_ACCESS
    
    ORG_ACCESS -->|Create| PARTNER_ROLES & JDA_ROLE
    ORG_ACCESS -->|Create| BOUNDARY_POLICY
    
    BOUNDARY_POLICY -->|Applied To| PARTNER_ROLES
    BOUNDARY_POLICY --> DENY_RULES
    
    PARTNER_ROLES --> TRUST_POLICY
    JDA_ROLE --> TRUST_POLICY
    
    TRUST_POLICY -->|Allows| IAM_USER
    
    IAM_USER & MGMT_ROLE & ORG_ACCESS & PARTNER_ROLES & JDA_ROLE --> AUDIT
    
    style SAME_ACCT fill:#ef5350
    style BOUNDARY_POLICY fill:#ef5350
    style DENY_RULES fill:#ef5350
    style AUDIT fill:#81c784
    style TRUST_POLICY fill:#ffb74d
```

---

## 10. EKS Deployment Architecture

```mermaid
graph TB
    subgraph "TelcoCLI"
        CMD[deploy-eks-full Command]
        SVC[EKS Deployment Service]
    end
    
    subgraph "Terraform Execution"
        TF_INIT[terraform init]
        TF_PLAN[terraform plan]
        TF_APPLY[terraform apply]
        TF_STATE[Terraform State]
    end
    
    subgraph "Terraform Modules"
        VPC_MOD[VPC Module<br/>- Subnets<br/>- Route Tables<br/>- NAT Gateway]
        EKS_MOD[EKS Module<br/>- Control Plane<br/>- Security Groups<br/>- IAM Roles]
        WORKER_MOD[Worker Node Module<br/>- Auto Scaling Group<br/>- Launch Template<br/>- IAM Instance Profile]
        OBS_MOD[Observability Module<br/>- Prometheus<br/>- Grafana<br/>- CloudWatch]
    end
    
    subgraph "AWS Infrastructure"
        VPC[VPC<br/>100.77.0.0/16]
        EKS_CP[EKS Control Plane<br/>Managed by AWS]
        WORKERS[Worker Nodes<br/>EC2 Instances]
        OUTPOST[AWS Outpost<br/>Optional]
        DH[Dedicated Host<br/>Optional]
    end
    
    subgraph "Kubernetes Resources"
        CNI[VPC CNI / Cilium<br/>Network Plugin]
        PROM[Prometheus<br/>Metrics Collection]
        GRAF[Grafana<br/>Visualization]
        CW[CloudWatch Agent<br/>Log Aggregation]
    end
    
    CMD --> SVC
    SVC --> TF_INIT
    TF_INIT --> TF_PLAN
    TF_PLAN --> TF_APPLY
    TF_APPLY --> TF_STATE
    
    TF_APPLY --> VPC_MOD & EKS_MOD & WORKER_MOD & OBS_MOD
    
    VPC_MOD --> VPC
    EKS_MOD --> EKS_CP
    WORKER_MOD --> WORKERS
    
    WORKERS -->|Optional| OUTPOST
    WORKERS -->|Optional| DH
    
    OBS_MOD --> CNI & PROM & GRAF & CW
    
    EKS_CP --> WORKERS
    WORKERS --> CNI
    CNI --> PROM
    PROM --> GRAF
    WORKERS --> CW
    
    style CMD fill:#4fc3f7
    style TF_APPLY fill:#81c784
    style EKS_CP fill:#ffb74d
    style OUTPOST fill:#ba68c8
    style DH fill:#ba68c8
```

---

## Diagram Usage Guide

### For System Design Interviews
- Start with **Diagram 1** (High-Level Architecture) for overview
- Use **Diagram 3** (Command Execution Flow) to explain request handling
- Reference **Diagram 6** (Multi-Account Architecture) for scalability discussion

### For Technical Documentation
- **Diagram 2** (Component Architecture) shows module organization
- **Diagram 7** (Data Flow) explains processing pipeline
- **Diagram 9** (Security Architecture) documents security controls

### For Onboarding New Developers
- Begin with **Diagram 1** for system overview
- Study **Diagram 2** for code organization
- Review **Diagram 3** for understanding execution flow

### For Operations Teams
- **Diagram 8** (Deployment Architecture) for installation
- **Diagram 6** (Multi-Account Architecture) for AWS setup
- **Diagram 10** (EKS Deployment) for Kubernetes operations

---

## Legend

```mermaid
graph LR
    A[Component] --> B[Component]
    C[External System]
    D[User Interface]
    E[Service Layer]
    F[Data Store]
    
    style A fill:#4fc3f7
    style C fill:#81c784
    style D fill:#e1f5ff
    style E fill:#ffb74d
    style F fill:#ba68c8
```

- **Blue** (#4fc3f7): Core application components
- **Green** (#81c784): External AWS services
- **Light Blue** (#e1f5ff): User-facing interfaces
- **Orange** (#ffb74d): Service layer components
- **Purple** (#ba68c8): Infrastructure/utilities
- **Red** (#ef5350): Security controls/boundaries

