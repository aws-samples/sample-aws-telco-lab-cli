# IAM Least Privilege Implementation Guide

**Document Version:** 1.0  
**Last Updated:** 2025-01-27  
**Owner:** TelcoCLI Security Team

---

## Executive Summary

This document provides comprehensive guidance for implementing IAM least privilege principles in TelcoCLI. It addresses the systematic use of wildcard permissions and provides a framework for reviewing, scoping, and improving IAM policies.

---

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Least Privilege Principles](#least-privilege-principles)
3. [Policy Review Framework](#policy-review-framework)
4. [Scoping Strategies](#scoping-strategies)
5. [Implementation Roadmap](#implementation-roadmap)
6. [Testing and Validation](#testing-and-validation)
7. [Monitoring and Compliance](#monitoring-and-compliance)

---

## Current State Assessment

### Identified Issues

**⚠️ CRITICAL FINDINGS:**

1. **Wildcard Actions with Wildcard Resources** - 21+ instances
   - Pattern: `"Action": "service:*", "Resource": "*"`
   - Impact: Grants unlimited permissions within service
   - Risk: Violates least privilege principle

2. **Boundary Policy Wildcards** - 33 wildcard service permissions
   - File: `boundary_policies.py`
   - Services: ec2:*, eks:*, s3:*, logs:*, cloudwatch:*, etc.
   - Impact: Permission boundaries should restrict, not enable broad access

3. **Joint Development Admin Policy** - 19 wildcard permissions
   - File: `account_provisioning.py` (lines 650-714)
   - Services: ec2:*, eks:*, s3:*, kms:*, lambda:*, etc.
   - Impact: Admin policy grants excessive permissions

4. **Sandbox Policy** - 12 wildcard permissions
   - File: `account_provisioning.py` (lines 725-740)
   - Impact: Even sandbox environments should follow least privilege

### Risk Assessment

| Risk Level | Count | Impact |
|------------|-------|--------|
| CRITICAL | 21 | Full service access with no resource scoping |
| HIGH | 33 | Boundary policies don't effectively limit permissions |
| MEDIUM | 19 | Admin policies too broad for operational needs |
| LOW | 12 | Sandbox policies could be more restrictive |

---

## Least Privilege Principles

### Core Principles

#### 1. **Grant Minimum Required Permissions**
- Start with no permissions
- Add only what's needed for specific tasks
- Remove permissions that are no longer needed

#### 2. **Scope to Specific Resources**
- Use resource ARNs instead of "*"
- Use conditions to further restrict access
- Leverage tags for dynamic resource scoping

#### 3. **Use Conditions Effectively**
- Restrict by IP address, VPC, or time
- Require MFA for sensitive operations
- Limit to specific AWS services

#### 4. **Separate Duties**
- Different roles for different functions
- No single role should have all permissions
- Use permission boundaries to enforce limits

#### 5. **Regular Review and Cleanup**
- Review permissions quarterly
- Remove unused permissions
- Update policies as requirements change

### AWS Best Practices

✅ **DO:**
- Use managed policies for common patterns
- Scope actions to specific resources
- Use conditions to restrict access
- Implement permission boundaries
- Enable CloudTrail for audit
- Use IAM Access Analyzer

❌ **DON'T:**
- Use "*" for actions unless absolutely necessary
- Use "*" for resources without strong justification
- Grant AdministratorAccess policy
- Create overly permissive custom policies
- Ignore IAM Access Analyzer findings

---

## Policy Review Framework

### Step 1: Inventory Current Permissions

**For each IAM policy, document:**
1. Policy name and purpose
2. Roles/users attached to policy
3. Actions granted (list all wildcards)
4. Resources affected
5. Conditions applied
6. Business justification

**Example Inventory:**
```
Policy: JDA-Boundary-Policy
Purpose: Permission boundary for partner accounts
Attached to: Partner assume roles
Wildcards: ec2:*, eks:*, s3:*, logs:*, cloudwatch:*, outposts:*, lambda:*, etc. (33 total)
Resources: "*" (all resources)
Conditions: None
Justification: "Broad permissions needed for telco lab operations"
```

### Step 2: Analyze Usage Patterns

**Use AWS IAM Access Analyzer and CloudTrail to determine:**
1. Which actions are actually used
2. Which resources are accessed
3. Frequency of access
4. Users/roles making requests

**Tools:**
```bash
# Generate IAM credential report
aws iam generate-credential-report
aws iam get-credential-report

# Analyze CloudTrail logs for IAM actions
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::IAM::Role \
  --max-results 50

# Use IAM Access Analyzer
aws accessanalyzer create-analyzer \
  --analyzer-name telcocli-analyzer \
  --type ACCOUNT

# Get findings
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:region:account:analyzer/telcocli-analyzer
```

### Step 3: Identify Scoping Opportunities

**For each wildcard permission, ask:**
1. Can we scope to specific actions? (e.g., `ec2:Describe*` instead of `ec2:*`)
2. Can we scope to specific resources? (e.g., specific VPC, subnet, or instance)
3. Can we add conditions? (e.g., require specific tags, VPC, or region)
4. Is this permission still needed?

**Decision Matrix:**

| Current | Scoping Option | Risk Reduction |
|---------|---------------|----------------|
| `ec2:*` on `*` | `ec2:Describe*`, `ec2:RunInstances`, `ec2:TerminateInstances` on specific VPC | HIGH |
| `s3:*` on `*` | `s3:GetObject`, `s3:PutObject` on specific bucket | HIGH |
| `iam:*` on `*` | `iam:Get*`, `iam:List*` on `*` + `iam:PassRole` on specific roles | CRITICAL |
| `kms:*` on `*` | `kms:Decrypt`, `kms:Encrypt`, `kms:GenerateDataKey` on specific keys | HIGH |

### Step 4: Create Scoped Policies

**Transform wildcards into specific permissions:**

**Before:**
```json
{
  "Effect": "Allow",
  "Action": "ec2:*",
  "Resource": "*"
}
```

**After:**
```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:DescribeInstances",
    "ec2:DescribeImages",
    "ec2:DescribeSecurityGroups",
    "ec2:DescribeVpcs",
    "ec2:DescribeSubnets",
    "ec2:RunInstances",
    "ec2:TerminateInstances",
    "ec2:StartInstances",
    "ec2:StopInstances"
  ],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "ec2:Vpc": "arn:aws:ec2:region:account:vpc/vpc-12345678"
    }
  }
}
```

---

## Scoping Strategies

### Strategy 1: Action-Level Scoping

**Replace service wildcards with specific actions:**

```python
# Before: Overly permissive
{
    "Effect": "Allow",
    "Action": "eks:*",
    "Resource": "*"
}

# After: Specific actions only
{
    "Effect": "Allow",
    "Action": [
        "eks:CreateCluster",
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:UpdateClusterConfig",
        "eks:DeleteCluster",
        "eks:CreateNodegroup",
        "eks:DescribeNodegroup",
        "eks:ListNodegroups",
        "eks:UpdateNodegroupConfig",
        "eks:DeleteNodegroup"
    ],
    "Resource": "*"
}
```

### Strategy 2: Resource-Level Scoping

**Scope to specific resources using ARNs:**

```python
# Before: All S3 buckets
{
    "Effect": "Allow",
    "Action": "s3:*",
    "Resource": "*"
}

# After: Specific buckets only
{
    "Effect": "Allow",
    "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
    ],
    "Resource": [
        "arn:aws:s3:::telcocli-terraform-state",
        "arn:aws:s3:::telcocli-terraform-state/*",
        "arn:aws:s3:::telcocli-logs-bucket",
        "arn:aws:s3:::telcocli-logs-bucket/*"
    ]
}
```

### Strategy 3: Condition-Based Scoping

**Use conditions to restrict access:**

```python
# Require specific VPC
{
    "Effect": "Allow",
    "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances"
    ],
    "Resource": "arn:aws:ec2:*:*:instance/*",
    "Condition": {
        "StringEquals": {
            "ec2:Vpc": "arn:aws:ec2:region:account:vpc/vpc-12345678"
        }
    }
}

# Require specific tags
{
    "Effect": "Allow",
    "Action": "ec2:*",
    "Resource": "*",
    "Condition": {
        "StringEquals": {
            "aws:RequestedRegion": "us-east-1",
            "ec2:ResourceTag/Environment": "lab"
        }
    }
}

# Require MFA for sensitive operations
{
    "Effect": "Allow",
    "Action": [
        "ec2:TerminateInstances",
        "rds:DeleteDBInstance"
    ],
    "Resource": "*",
    "Condition": {
        "Bool": {
            "aws:MultiFactorAuthPresent": "true"
        }
    }
}
```

### Strategy 4: Tag-Based Access Control

**Use tags for dynamic resource scoping:**

```python
# Allow access only to resources with specific tags
{
    "Effect": "Allow",
    "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:RebootInstances"
    ],
    "Resource": "*",
    "Condition": {
        "StringEquals": {
            "ec2:ResourceTag/Project": "TelcoCLI",
            "ec2:ResourceTag/Owner": "${aws:username}"
        }
    }
}
```

### Strategy 5: Permission Boundaries

**Use boundaries to enforce maximum permissions:**

```python
# Permission boundary that limits what roles can do
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:Describe*",
                "ec2:Get*",
                "ec2:RunInstances",
                "ec2:TerminateInstances",
                "eks:Describe*",
                "eks:List*",
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Deny",
            "Action": [
                "iam:*",
                "organizations:*",
                "account:*"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## Implementation Roadmap

### Phase 1: Assessment and Planning (Week 1-2)

**Objectives:**
- Complete policy inventory
- Analyze CloudTrail logs for usage patterns
- Run IAM Access Analyzer
- Identify quick wins

**Deliverables:**
- Policy inventory spreadsheet
- Usage analysis report
- Prioritized list of policies to update
- Risk assessment

**Actions:**
1. Export all IAM policies
2. Run IAM Access Analyzer
3. Analyze 90 days of CloudTrail logs
4. Document actual permissions used
5. Identify unused permissions

### Phase 2: High-Risk Policy Updates (Week 3-4)

**Priority:** 🔴 CRITICAL

**Focus Areas:**
1. Remove `iam:*` wildcards
2. Scope `kms:*` to specific keys
3. Restrict `organizations:*` access
4. Limit `s3:*` to specific buckets

**Example Updates:**

**Policy: JDA Boundary Policy**
- Current: 33 wildcard permissions
- Target: 0 wildcard permissions
- Approach: Replace with specific actions based on usage analysis

**Policy: Joint Development Admin**
- Current: 19 wildcard permissions
- Target: <5 wildcard permissions (only for read-only operations)
- Approach: Scope to specific resources and add conditions

### Phase 3: Medium-Risk Policy Updates (Week 5-6)

**Priority:** 🟡 HIGH

**Focus Areas:**
1. Scope EC2 permissions to specific VPCs
2. Scope EKS permissions to specific clusters
3. Add tag-based conditions
4. Implement resource-level scoping

### Phase 4: Testing and Validation (Week 7-8)

**Priority:** 🟢 MEDIUM

**Activities:**
1. Test updated policies in non-production
2. Monitor for access denied errors
3. Adjust policies based on feedback
4. Document changes and rationale

### Phase 5: Rollout and Monitoring (Week 9-10)

**Priority:** 🟢 MEDIUM

**Activities:**
1. Deploy updated policies to production
2. Monitor CloudTrail for access denied
3. Set up alerts for policy violations
4. Create runbook for policy updates

---

## Testing and Validation

### Pre-Deployment Testing

**1. Policy Simulator**
```bash
# Test policy before deployment
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::account:role/RoleName \
  --action-names ec2:RunInstances ec2:TerminateInstances \
  --resource-arns arn:aws:ec2:region:account:instance/*
```

**2. Dry Run Testing**
```python
# Test EC2 operations with dry run
import boto3

ec2 = boto3.client('ec2')

try:
    response = ec2.run_instances(
        ImageId='ami-12345678',
        InstanceType='t3.micro',
        MinCount=1,
        MaxCount=1,
        DryRun=True  # Test without actually creating
    )
except Exception as e:
    if 'DryRunOperation' in str(e):
        print("✅ Permission check passed")
    else:
        print(f"❌ Permission denied: {e}")
```

**3. CloudTrail Monitoring**
```bash
# Monitor for access denied errors after deployment
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AccessDenied \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --max-results 50
```

### Post-Deployment Validation

**1. Functional Testing**
- Test all critical workflows
- Verify no functionality is broken
- Document any access denied errors

**2. Security Testing**
- Verify wildcards are removed
- Confirm resource scoping works
- Test permission boundaries

**3. Performance Testing**
- Measure policy evaluation time
- Check for policy size limits
- Optimize complex conditions

---

## Monitoring and Compliance

### Continuous Monitoring

**1. IAM Access Analyzer**
```bash
# Create analyzer
aws accessanalyzer create-analyzer \
  --analyzer-name telcocli-continuous \
  --type ACCOUNT

# Schedule daily findings review
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:region:account:analyzer/telcocli-continuous \
  --filter '{"status":{"eq":["ACTIVE"]}}'
```

**2. CloudWatch Alarms**
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Alert on excessive IAM policy changes
cloudwatch.put_metric_alarm(
    AlarmName='TelcoCLI-IAM-Policy-Changes',
    ComparisonOperator='GreaterThanThreshold',
    EvaluationPeriods=1,
    MetricName='IAMPolicyChanges',
    Namespace='TelcoCLI/Security',
    Period=3600,
    Statistic='Sum',
    Threshold=5.0,
    ActionsEnabled=True,
    AlarmActions=['arn:aws:sns:region:account:security-alerts']
)
```

**3. Automated Policy Review**
```python
def check_policy_compliance(policy_document):
    """Check if policy follows least privilege principles."""
    violations = []
    
    for statement in policy_document.get('Statement', []):
        # Check for wildcard actions
        actions = statement.get('Action', [])
        if isinstance(actions, str):
            actions = [actions]
        
        for action in actions:
            if action.endswith(':*'):
                violations.append(f"Wildcard action: {action}")
        
        # Check for wildcard resources
        resources = statement.get('Resource', [])
        if isinstance(resources, str):
            resources = [resources]
        
        if '*' in resources and statement.get('Effect') == 'Allow':
            violations.append("Wildcard resource with Allow effect")
    
    return violations
```

### Compliance Reporting

**Monthly Reports:**
- Number of policies reviewed
- Wildcards removed
- Resource scoping improvements
- Access denied incidents
- Policy violations

**Quarterly Reviews:**
- Comprehensive policy audit
- Usage pattern analysis
- Permission cleanup
- Compliance gap assessment

---

## Policy Templates

### Template 1: Read-Only Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "ec2:Get*",
        "eks:Describe*",
        "eks:List*",
        "s3:GetObject",
        "s3:ListBucket",
        "logs:GetLogEvents",
        "logs:DescribeLogGroups",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

### Template 2: EKS Cluster Management

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:CreateCluster",
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:UpdateClusterConfig",
        "eks:DeleteCluster",
        "eks:CreateNodegroup",
        "eks:DescribeNodegroup",
        "eks:ListNodegroups",
        "eks:UpdateNodegroupConfig",
        "eks:DeleteNodegroup"
      ],
      "Resource": "arn:aws:eks:region:account:cluster/telcocli-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::account:role/TelcoCLI-EKS-*",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "eks.amazonaws.com"
        }
      }
    }
  ]
}
```

### Template 3: S3 Bucket Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::telcocli-*/*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::telcocli-*"
    }
  ]
}
```

### Template 4: S3 Bucket Policy with TLS Enforcement

**⚠️ SECURITY BEST PRACTICE:** Always enforce TLS for S3 bucket access to prevent data interception.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::telcocli-terraform-state",
        "arn:aws:s3:::telcocli-terraform-state/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    },
    {
      "Sid": "AllowSecureAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:role/TelcoCLI-Role"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::telcocli-terraform-state",
        "arn:aws:s3:::telcocli-terraform-state/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "true"
        }
      }
    }
  ]
}
```

**Key Points:**
- The `DenyInsecureTransport` statement blocks ALL non-HTTPS requests
- The `aws:SecureTransport` condition ensures TLS encryption in transit
- Apply this policy to ALL S3 buckets containing sensitive data (Terraform state, logs, configs)

---

## References

### AWS Documentation
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [IAM Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)
- [Permission Boundaries](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)
- [Policy Evaluation Logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)

### Security Standards
- AWS Well-Architected Framework - Security Pillar
- CIS AWS Foundations Benchmark
- NIST Cybersecurity Framework

### Internal Documentation
- [SECURITY.md](../../SECURITY.md) - Security guidelines
- [DATA_SECURITY_STRATEGY.md](DATA_SECURITY_STRATEGY.md) - Data security
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture

---

## Document Control

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-27 | TelcoCLI Security Team | Initial release |

**Review Schedule:**
- Quarterly review required
- Update after policy changes
- Update after security incidents

---

**⚠️ IMPORTANT NOTICE:**

This document provides guidance for implementing IAM least privilege. All policy changes MUST be tested in non-production environments before deployment. Monitor CloudTrail for access denied errors and adjust policies as needed.

**For questions or support, contact:**
- Security Team: security@telcocli.example.com
- IAM Team: iam@telcocli.example.com
