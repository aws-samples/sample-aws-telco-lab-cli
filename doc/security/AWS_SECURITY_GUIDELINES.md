# AWS Security Guidelines for TelcoCLI

**Version:** 1.0  
**Last Updated:** 2025-01-26  
**Audience:** Developers, Operators, Security Engineers

---

## Table of Contents

1. [Overview](#overview)
2. [AWS Organizations Security](#aws-organizations-security)
3. [IAM Security](#iam-security)
4. [EC2 and VPC Security](#ec2-and-vpc-security)
5. [EKS Security](#eks-security)
6. [S3 Security](#s3-security)
7. [Systems Manager (SSM) Security](#systems-manager-ssm-security)
8. [Secrets Manager Security](#secrets-manager-security)
9. [CloudTrail and Monitoring](#cloudtrail-and-monitoring)
10. [Cross-Account Access Security](#cross-account-access-security)

---

## Overview

This document provides security guidelines for AWS services used by TelcoCLI. Follow these guidelines to maintain a secure infrastructure and comply with AWS security best practices.

### Security Principles

1. **Least Privilege:** Grant minimum permissions required
2. **Defense in Depth:** Multiple layers of security controls
3. **Encryption Everywhere:** Encrypt data at rest and in transit
4. **Audit Everything:** Enable comprehensive logging
5. **Automate Security:** Use automated security tools and checks

---

## AWS Organizations Security

### Overview

AWS Organizations manages multiple AWS accounts in a hierarchical structure. TelcoCLI uses Organizations to create and manage partner accounts.

### Security Best Practices

#### 1. Protect the Management Account

**Risk:** Compromise of management account affects entire organization

**Controls:**
- ✅ Enable MFA for all management account users
- ✅ Restrict management account access to minimum users
- ✅ Use separate accounts for workloads (never deploy in management account)
- ✅ Enable CloudTrail in management account
- ✅ Set up billing alerts

**TelcoCLI Implementation:**
```python
# Always validate management account before operations
if not is_management_account():
    raise TelcoCLIException("This operation requires management account access")
```

#### 2. Use Service Control Policies (SCPs)

**Risk:** Accounts can perform unauthorized actions

**Controls:**
- ✅ Apply SCPs to restrict account capabilities
- ✅ Deny access to sensitive services in development accounts
- ✅ Prevent disabling of CloudTrail
- ✅ Enforce encryption requirements

**Example SCP - Deny CloudTrail Deletion:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 3. Organizational Unit (OU) Structure

**Best Practice:** Organize accounts by environment and purpose

**Recommended Structure:**
```
Root
├── Security OU
│   ├── Log Archive Account
│   └── Security Tooling Account
├── Infrastructure OU
│   ├── Network Account
│   └── Shared Services Account
├── Development OU
│   └── Dev Accounts
├── Production OU
│   └── Prod Accounts
└── Partner OU
    └── Partner Accounts (created by TelcoCLI)
```

---

## IAM Security

### Overview

IAM controls access to AWS resources. TelcoCLI creates IAM roles for cross-account access and service operations.

### Security Best Practices

#### 1. Least Privilege Policies

**Risk:** Overly permissive policies enable privilege escalation

**Controls:**
- ✅ Start with minimum permissions
- ✅ Use IAM Access Analyzer to identify unused permissions
- ✅ Regularly review and tighten policies
- ✅ Avoid wildcard (*) permissions

**TelcoCLI Implementation:**
```python
# Example: Scoped EC2 permissions
policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "ec2:DescribeInstances",
            "ec2:DescribeDedicatedHosts"
        ],
        "Resource": "*",  # Describe actions require *
        "Condition": {
            "StringEquals": {
                "aws:RequestedRegion": ["us-west-2", "us-east-1"]
            }
        }
    }]
}
```

#### 2. Permission Boundaries

**Risk:** Created roles can escalate privileges

**Controls:**
- ✅ Apply permission boundaries to all created roles
- ✅ Prevent boundary removal
- ✅ Limit maximum permissions

**TelcoCLI Implementation:**
```python
# Always attach permission boundary when creating roles
iam_client.create_role(
    RoleName=role_name,
    AssumeRolePolicyDocument=trust_policy,
    PermissionsBoundary=f"arn:aws:iam::{account_id}:policy/TelcoCLIBoundary"
)
```

#### 3. Cross-Account Role Trust Policies

**Risk:** Unauthorized accounts can assume roles

**Controls:**
- ✅ Use external ID for additional security
- ✅ Restrict to specific principal ARNs
- ✅ Add condition keys for MFA
- ✅ Limit session duration

**Secure Trust Policy Example:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::123456789012:root"
    },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "unique-external-id-12345"
      },
      "Bool": {
        "aws:MultiFactorAuthPresent": "true"
      }
    }
  }]
}
```

#### 4. IAM Access Analyzer

**Risk:** Unintended resource sharing

**Controls:**
- ✅ Enable IAM Access Analyzer in all accounts
- ✅ Review findings regularly
- ✅ Archive resolved findings
- ✅ Automate remediation

---

## EC2 and VPC Security

### Overview

EC2 provides compute resources. TelcoCLI manages Dedicated Hosts and instances for telecommunications workloads.

### Security Best Practices

#### 1. Network Isolation

**Risk:** Unauthorized network access

**Controls:**
- ✅ Deploy resources in private subnets
- ✅ Use VPC endpoints for AWS service access
- ✅ Implement network segmentation
- ✅ Enable VPC Flow Logs

**VPC Architecture:**
```
VPC (10.0.0.0/16)
├── Public Subnets (10.0.1.0/24, 10.0.2.0/24)
│   └── NAT Gateways, Load Balancers
├── Private Subnets (10.0.10.0/24, 10.0.11.0/24)
│   └── EC2 Instances, EKS Nodes
└── Isolated Subnets (10.0.20.0/24, 10.0.21.0/24)
    └── Databases, Sensitive Workloads
```

#### 2. Security Groups

**Risk:** Overly permissive ingress rules

**Controls:**
- ✅ Default deny all inbound traffic
- ✅ Allow only required ports
- ✅ Use security group references instead of CIDR blocks
- ✅ Never use 0.0.0.0/0 for SSH/RDP

**Secure Security Group Example:**
```python
# Good: Restricted SSH access
security_group.authorize_ingress(
    IpProtocol='tcp',
    FromPort=22,
    ToPort=22,
    SourceSecurityGroupId='sg-management-bastion'  # Reference, not CIDR
)

# Bad: Open SSH to internet
# security_group.authorize_ingress(
#     IpProtocol='tcp',
#     FromPort=22,
#     ToPort=22,
#     CidrIp='0.0.0.0/0'  # NEVER DO THIS
# )
```

#### 3. EC2 Instance Security

**Risk:** Instance compromise

**Controls:**
- ✅ Use Systems Manager Session Manager (no SSH keys)
- ✅ Enable IMDSv2 (metadata service v2)
- ✅ Encrypt EBS volumes
- ✅ Use latest AMIs with security patches
- ✅ Implement host-based firewalls

**TelcoCLI Implementation:**
```python
# Launch instance with security best practices
instance = ec2_client.run_instances(
    ImageId=ami_id,
    InstanceType='m5.large',
    MetadataOptions={
        'HttpTokens': 'required',  # IMDSv2
        'HttpPutResponseHopLimit': 1
    },
    BlockDeviceMappings=[{
        'DeviceName': '/dev/xvda',
        'Ebs': {
            'Encrypted': True,  # Encrypt root volume
            'KmsKeyId': kms_key_id
        }
    }],
    IamInstanceProfile={'Name': 'TelcoCLI-Instance-Profile'}
)
```

---

## EKS Security

### Overview

Amazon EKS provides managed Kubernetes clusters. TelcoCLI deploys and configures EKS clusters for containerized workloads.

### Security Best Practices

#### 1. Cluster Access Control

**Risk:** Unauthorized cluster access

**Controls:**
- ✅ Enable cluster endpoint private access
- ✅ Restrict public endpoint access by CIDR
- ✅ Use IAM Roles for Service Accounts (IRSA)
- ✅ Enable EKS audit logging

**Secure Cluster Configuration:**
```python
cluster = eks_client.create_cluster(
    name='telco-cluster',
    resourcesVpcConfig={
        'subnetIds': private_subnet_ids,
        'endpointPrivateAccess': True,
        'endpointPublicAccess': True,  # If needed
        'publicAccessCidrs': ['10.0.0.0/8']  # Restrict to corporate network
    },
    logging={
        'clusterLogging': [{
            'types': ['api', 'audit', 'authenticator', 'controllerManager', 'scheduler'],
            'enabled': True
        }]
    },
    encryptionConfig=[{
        'resources': ['secrets'],
        'provider': {'keyArn': kms_key_arn}
    }]
)
```

#### 2. Pod Security

**Risk:** Container escape, privilege escalation

**Controls:**
- ✅ Use Pod Security Standards (restricted profile)
- ✅ Implement network policies
- ✅ Scan container images for vulnerabilities
- ✅ Use read-only root filesystems
- ✅ Drop unnecessary capabilities

**Pod Security Policy Example:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: app:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```

#### 3. IRSA (IAM Roles for Service Accounts)

**Risk:** Pods have excessive AWS permissions

**Controls:**
- ✅ Use IRSA instead of node IAM roles
- ✅ Scope permissions per service account
- ✅ Use separate service accounts per application

**IRSA Configuration:**
```python
# Create OIDC provider for cluster
oidc_provider = eks_client.describe_cluster(name=cluster_name)['cluster']['identity']['oidc']['issuer']

# Create IAM role with trust policy for service account
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Federated": f"arn:aws:iam::{account_id}:oidc-provider/{oidc_provider}"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
            "StringEquals": {
                f"{oidc_provider}:sub": "system:serviceaccount:default:my-service-account"
            }
        }
    }]
}
```

---

## S3 Security

### Overview

S3 provides object storage. TelcoCLI may use S3 for configuration storage and artifacts.

### Security Best Practices

#### 1. Block Public Access

**Risk:** Data exposure via public buckets

**Controls:**
- ✅ Enable S3 Block Public Access at account level
- ✅ Enable Block Public Access per bucket
- ✅ Use bucket policies to enforce encryption
- ✅ Enable versioning for data protection

**Secure Bucket Configuration:**
```python
# Create bucket with security best practices
s3_client.create_bucket(
    Bucket=bucket_name,
    CreateBucketConfiguration={'LocationConstraint': region}
)

# Block public access
s3_client.put_public_access_block(
    Bucket=bucket_name,
    PublicAccessBlockConfiguration={
        'BlockPublicAcls': True,
        'IgnorePublicAcls': True,
        'BlockPublicPolicy': True,
        'RestrictPublicBuckets': True
    }
)

# Enable versioning
s3_client.put_bucket_versioning(
    Bucket=bucket_name,
    VersioningConfiguration={'Status': 'Enabled'}
)

# Enable encryption
s3_client.put_bucket_encryption(
    Bucket=bucket_name,
    ServerSideEncryptionConfiguration={
        'Rules': [{
            'ApplyServerSideEncryptionByDefault': {
                'SSEAlgorithm': 'aws:kms',
                'KMSMasterKeyID': kms_key_id
            },
            'BucketKeyEnabled': True
        }]
    }
)
```

#### 2. Bucket Policies

**Risk:** Unauthorized access to bucket contents

**Controls:**
- ✅ Use least privilege bucket policies
- ✅ Enforce encryption in transit (TLS)
- ✅ Restrict access by VPC endpoint
- ✅ Enable MFA delete for versioned buckets

**Secure Bucket Policy:**
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
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    },
    {
      "Sid": "DenyUnencryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

---

## Systems Manager (SSM) Security

### Overview

AWS Systems Manager provides remote management capabilities. TelcoCLI uses SSM for secure instance access.

### Security Best Practices

#### 1. Session Manager

**Risk:** Unauthorized remote access

**Controls:**
- ✅ Use Session Manager instead of SSH
- ✅ Enable session logging to S3/CloudWatch
- ✅ Restrict session duration
- ✅ Require MFA for sessions

**Session Manager Configuration:**
```python
# Start session with logging
ssm_client.start_session(
    Target=instance_id,
    DocumentName='AWS-StartInteractiveCommand',
    Parameters={
        'command': ['bash'],
        'logStreamName': [f'session-{instance_id}-{timestamp}']
    }
)
```

#### 2. Parameter Store

**Risk:** Sensitive data exposure

**Controls:**
- ✅ Use SecureString parameters for secrets
- ✅ Encrypt with KMS
- ✅ Use IAM policies to restrict access
- ✅ Enable parameter versioning

**Secure Parameter Storage:**
```python
# Store secret securely
ssm_client.put_parameter(
    Name='/telcocli/database/password',
    Value=password,
    Type='SecureString',
    KeyId=kms_key_id,
    Tier='Advanced',  # For larger values and policies
    Overwrite=False
)
```

---

## Secrets Manager Security

### Overview

AWS Secrets Manager stores and rotates credentials. TelcoCLI should use Secrets Manager for all sensitive credentials.

### Security Best Practices

#### 1. Secret Storage

**Risk:** Credential exposure

**Controls:**
- ✅ Store all credentials in Secrets Manager
- ✅ Enable automatic rotation
- ✅ Use resource-based policies
- ✅ Enable encryption with KMS

**Secure Secret Storage:**
```python
# Create secret with rotation
secrets_client.create_secret(
    Name='telcocli/partner/credentials',
    Description='Partner account credentials',
    KmsKeyId=kms_key_id,
    SecretString=json.dumps({
        'username': username,
        'password': password
    }),
    Tags=[
        {'Key': 'Application', 'Value': 'TelcoCLI'},
        {'Key': 'Environment', 'Value': 'Production'}
    ]
)

# Enable rotation
secrets_client.rotate_secret(
    SecretId='telcocli/partner/credentials',
    RotationLambdaARN=rotation_lambda_arn,
    RotationRules={'AutomaticallyAfterDays': 30}
)
```

---

## CloudTrail and Monitoring

### Overview

CloudTrail provides audit logging for AWS API calls. Enable CloudTrail in all accounts.

### Security Best Practices

#### 1. CloudTrail Configuration

**Risk:** Insufficient audit trail

**Controls:**
- ✅ Enable CloudTrail in all regions
- ✅ Enable log file validation
- ✅ Store logs in centralized S3 bucket
- ✅ Enable S3 Object Lock for immutability
- ✅ Forward logs to CloudWatch Logs

**Secure CloudTrail Setup:**
```python
# Create trail with security best practices
cloudtrail_client.create_trail(
    Name='telcocli-audit-trail',
    S3BucketName=audit_bucket,
    IncludeGlobalServiceEvents=True,
    IsMultiRegionTrail=True,
    EnableLogFileValidation=True,
    KmsKeyId=kms_key_id,
    IsOrganizationTrail=True  # For Organizations
)

# Start logging
cloudtrail_client.start_logging(Name='telcocli-audit-trail')
```

#### 2. CloudWatch Alarms

**Risk:** Security incidents not detected

**Controls:**
- ✅ Create alarms for security events
- ✅ Monitor failed authentication attempts
- ✅ Alert on IAM policy changes
- ✅ Detect unusual API activity

**Example Metric Filter:**
```python
# Create metric filter for unauthorized API calls
logs_client.put_metric_filter(
    logGroupName='/aws/cloudtrail/logs',
    filterName='UnauthorizedAPICalls',
    filterPattern='{ ($.errorCode = "*UnauthorizedOperation") || ($.errorCode = "AccessDenied*") }',
    metricTransformations=[{
        'metricName': 'UnauthorizedAPICalls',
        'metricNamespace': 'CloudTrailMetrics',
        'metricValue': '1'
    }]
)

# Create alarm
cloudwatch_client.put_metric_alarm(
    AlarmName='UnauthorizedAPICallsAlarm',
    MetricName='UnauthorizedAPICalls',
    Namespace='CloudTrailMetrics',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=1,
    Threshold=1,
    ComparisonOperator='GreaterThanOrEqualToThreshold',
    AlarmActions=[sns_topic_arn]
)
```

---

## Cross-Account Access Security

### Overview

TelcoCLI creates cross-account roles for partner access. Secure these roles carefully.

### Security Best Practices

#### 1. External ID

**Risk:** Confused deputy problem

**Controls:**
- ✅ Always use external ID for cross-account roles
- ✅ Generate unique external ID per partner
- ✅ Store external ID securely
- ✅ Validate external ID on assume role

**Secure Cross-Account Role:**
```python
# Create role with external ID
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "AWS": f"arn:aws:iam::{partner_account_id}:root"
        },
        "Action": "sts:AssumeRole",
        "Condition": {
            "StringEquals": {
                "sts:ExternalId": generate_unique_external_id()
            }
        }
    }]
}
```

#### 2. Session Duration

**Risk:** Long-lived sessions increase exposure

**Controls:**
- ✅ Set minimum session duration required
- ✅ Default to 1 hour for interactive sessions
- ✅ Use shorter durations for automated processes

**Assume Role with Session Duration:**
```python
# Assume role with limited session
credentials = sts_client.assume_role(
    RoleArn=role_arn,
    RoleSessionName='telcocli-session',
    DurationSeconds=3600,  # 1 hour
    ExternalId=external_id
)
```

---

## Security Checklist

Use this checklist when deploying TelcoCLI infrastructure:

### AWS Organizations
- [ ] MFA enabled on management account
- [ ] CloudTrail enabled in management account
- [ ] SCPs applied to restrict account capabilities
- [ ] Organizational units properly structured

### IAM
- [ ] Least privilege policies applied
- [ ] Permission boundaries on all created roles
- [ ] IAM Access Analyzer enabled
- [ ] No wildcard permissions in production

### EC2/VPC
- [ ] Resources in private subnets
- [ ] Security groups restrict access
- [ ] VPC Flow Logs enabled
- [ ] IMDSv2 enabled on instances

### EKS
- [ ] Cluster endpoint access restricted
- [ ] EKS audit logging enabled
- [ ] IRSA configured for pods
- [ ] Pod Security Standards enforced

### S3
- [ ] Block Public Access enabled
- [ ] Bucket encryption enabled
- [ ] Versioning enabled
- [ ] Bucket policies enforce TLS

### Monitoring
- [ ] CloudTrail enabled in all regions
- [ ] CloudWatch alarms configured
- [ ] Security Hub enabled
- [ ] GuardDuty enabled

---

## References

- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)
- [AWS Security Hub Controls](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls.html)

---

**Document Control:**
- **Version:** 1.0
- **Last Updated:** 2025-01-26
- **Next Review:** 2025-04-26
- **Owner:** TelcoCLI Security Team
