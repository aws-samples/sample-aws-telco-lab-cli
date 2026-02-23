# AWS Service Name Reference

Quick reference for AWS service names used in TelcoCLI.

| Abbreviation | Official Name | Used In |
|-------------|---------------|---------|
| EC2 | Amazon Elastic Compute Cloud | Outpost instances, bastion hosts, dedicated hosts |
| EKS | Amazon Elastic Kubernetes Service | Cluster deployment and management |
| S3 | Amazon Simple Storage Service | Terraform state, log storage |
| IAM | AWS Identity and Access Management | Role creation, policy management |
| SSM | AWS Systems Manager | VPN server access, command execution |
| KMS | AWS Key Management Service | Encryption key management |
| STS | AWS Security Token Service | Cross-account role assumption |
| RAM | AWS Resource Access Manager | Dedicated host sharing |
| VPC | Amazon Virtual Private Cloud | Network infrastructure |
| Organizations | AWS Organizations | Account management, SCPs |
| CloudTrail | AWS CloudTrail | API audit logging |
| CloudWatch | Amazon CloudWatch | Monitoring and alerting |
| Bedrock | Amazon Bedrock | AI assistant (Claude models) |

**Usage guidelines:**
- In code: use abbreviations (EC2, EKS, S3)
- In CLI output: use abbreviations
- In documentation headers: use full name on first reference, abbreviation thereafter
- In IAM policies: use service prefixes (ec2, eks, s3, iam, sts, ram, kms)
