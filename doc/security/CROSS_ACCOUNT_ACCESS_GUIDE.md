# Cross-Account Access Controls Guide

**Document Version:** 1.0
**Last Updated:** 2025-02-10
**Owner:** TelcoCLI Security Team

---

## Overview

TelcoCLI manages cross-account access for partner onboarding, dedicated host sharing, and infrastructure management. This guide documents the cross-account role assumption patterns, security controls, and operational checklists used throughout the tool.

> **WARNING:** This is sample/demo code. Cross-account access patterns shown here are for demonstration purposes. Review and adapt all IAM policies, trust relationships, and access controls to meet your organization's security requirements before production use.

---

## Table of Contents

1. [Cross-Account Access Patterns](#cross-account-access-patterns)
2. [Trust Policy Configuration](#trust-policy-configuration)
3. [Role Assumption Flow](#role-assumption-flow)
4. [RAM Resource Sharing](#ram-resource-sharing)
5. [Security Controls](#security-controls)
6. [Operational Checklist](#operational-checklist)
7. [Troubleshooting](#troubleshooting)

---

## Cross-Account Access Patterns

TelcoCLI uses three cross-account access patterns:

### Pattern 1: Partner Role Assumption (create-partner)

The management account creates IAM roles in newly provisioned partner accounts. These roles allow the partner's own AWS account to assume a role in the provisioned account.

```
┌─────────────────────┐     sts:AssumeRole      ┌─────────────────────┐
│  Management Account │ ──────────────────────►  │  Partner Account    │
│  (runs TelcoCLI)    │                          │  (newly created)    │
│                     │                          │                     │
│  OrganizationAdmin  │                          │  Partner-Admin role │
└─────────────────────┘                          └─────────────────────┘
                                                          ▲
                                                          │ sts:AssumeRole
                                                          │ (with ExternalId)
                                                 ┌────────┴──────────┐
                                                 │  Partner's Own    │
                                                 │  AWS Account      │
                                                 │  (trusted)        │
                                                 └───────────────────┘
```

**Files involved:**
- `src/telco_cli/services/account_provisioning.py` — provisions accounts and creates roles
- `src/telco_cli/utils/aws_utils.py` — `create_cross_account_role()`

### Pattern 2: Dedicated Host Sharing (assign-dedicated-host)

Dedicated hosts are shared with partner accounts via AWS Resource Access Manager (RAM).

```
┌─────────────────────┐     RAM Share            ┌─────────────────────┐
│  Host Owner Account │ ──────────────────────►  │  Partner Account    │
│  (Outpost owner)    │                          │  (receives access)  │
│                     │                          │                     │
│  EC2 Dedicated Host │                          │  Can launch EC2     │
│  h-xxxxxxxxx        │                          │  on shared host     │
└─────────────────────┘                          └─────────────────────┘
```

**Files involved:**
- `src/telco_cli/commands/assign_dedicated_host.py` — `_create_ram_share()`
- `src/telco_cli/commands/release_dedicated_host.py` — `_deallocate_host_from_account()`

### Pattern 3: Admin Role Assumption (JDA Admin)

Admin accounts are granted assume-role access to partner accounts for management and support operations.

```
┌─────────────────────┐     sts:AssumeRole      ┌─────────────────────┐
│  Admin Account(s)   │ ──────────────────────►  │  Partner Account    │
│  (support/ops)      │                          │                     │
│                     │                          │  JDA-Admin role     │
└─────────────────────┘                          └─────────────────────┘
```

**Files involved:**
- `src/telco_cli/services/account_provisioning.py` — `_setup_iam_roles()`

---

## Trust Policy Configuration

### Partner Trust Policy

When creating cross-account roles, TelcoCLI generates trust policies with the following structure:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::PARTNER_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "telco-PARTNER_ACCOUNT_ID"
        }
      }
    }
  ]
}
```

**Security controls in this policy:**
- Principal is scoped to a specific account (not `*`)
- ExternalId prevents confused deputy attacks
- Only `sts:AssumeRole` is allowed (not `sts:*`)

### Admin Trust Policy

Admin roles trust multiple admin account IDs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::ADMIN_ACCOUNT_1:root",
          "arn:aws:iam::ADMIN_ACCOUNT_2:root"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

> **WARNING:** Admin trust policies do not currently use ExternalId conditions. Consider adding ExternalId for production deployments to prevent confused deputy attacks.

---

## Role Assumption Flow

### Step-by-Step: Partner Account Provisioning

1. **Management account** calls `create-partner` with partner details
2. TelcoCLI creates a new AWS account via Organizations API
3. Management account assumes `OrganizationAccountAccessRole` in the new account
4. TelcoCLI creates IAM roles in the new account:
   - **Partner-Admin role** — trusted by the partner's own AWS account
   - **JDA-Admin role** — trusted by specified admin accounts
5. Permission boundaries are attached to limit maximum permissions
6. Role ARNs and switch-role URLs are returned to the operator

### Session Duration and Limits

- Default `MaxSessionDuration`: 3600 seconds (1 hour)
- Role assumption uses temporary credentials (STS)
- Credentials are not cached or stored to disk

---

## RAM Resource Sharing

### Creating a RAM Share

When `--enable-ram-sharing` is used with `assign-dedicated-host`:

1. TelcoCLI constructs the dedicated host ARN
2. Creates a RAM resource share named `dedicated-host-share-{account}-{host}`
3. Adds the target account as a principal
4. The target account can then launch EC2 instances on the shared host

### Removing a RAM Share

When `--deallocate` is used with `release-dedicated-host`:

1. TelcoCLI lists all RAM resource shares owned by the current account
2. Finds shares matching the host ID pattern
3. Deletes matching resource shares
4. Removes assignment tags from the host

### RAM Security Considerations

- RAM shares grant access to specific resources, not entire accounts
- Shares can be revoked at any time by the resource owner
- RAM does not grant IAM permissions — the target account still needs appropriate EC2 permissions
- Monitor RAM shares via AWS CloudTrail

---

## Security Controls

### Required Controls

| Control | Description | Status |
|---------|-------------|--------|
| ExternalId on partner roles | Prevents confused deputy attacks | ✅ Implemented |
| Scoped principals | Trust policies specify exact account IDs | ✅ Implemented |
| Temporary credentials | STS provides time-limited access | ✅ Implemented |
| MaxSessionDuration | Limits role session to 1 hour | ✅ Implemented |
| Permission boundaries | Limits maximum permissions for created roles | ⚠️ Partial (see Task 1.4) |
| CloudTrail logging | Audit all cross-account activity | 📋 Customer responsibility |
| MFA on role assumption | Require MFA for sensitive operations | 📋 Recommended |

### Recommended Additional Controls

1. **Add ExternalId to admin trust policies** — Currently only partner roles use ExternalId
2. **Implement session tags** — Pass context (partner name, operation type) via session tags
3. **Add IP restrictions** — Use `aws:SourceIp` conditions to limit where roles can be assumed from
4. **Enable AWS Organizations SCPs** — Use Service Control Policies to set guardrails across all accounts
5. **Implement role session naming** — Use `sts:RoleSessionName` to identify who assumed the role

### What TelcoCLI Does NOT Do

- Does not store or cache cross-account credentials
- Does not create long-lived access keys for cross-account access
- Does not grant `sts:*` — only `sts:AssumeRole`
- Does not use wildcard (`*`) principals in trust policies

---

## Operational Checklist

### Before Creating Cross-Account Access

- [ ] Verify the partner account ID is correct (12-digit number)
- [ ] Confirm admin account IDs are authorized for access
- [ ] Review the permissions that will be granted to the role
- [ ] Ensure CloudTrail is enabled in both accounts
- [ ] Document the business justification for cross-account access

### After Creating Cross-Account Access

- [ ] Verify the role was created with correct trust policy
- [ ] Test role assumption from the trusted account
- [ ] Confirm ExternalId is required for partner roles
- [ ] Review attached policies for least privilege
- [ ] Record the role ARN and creation date

### Periodic Review

- [ ] Audit all cross-account roles quarterly
- [ ] Remove roles for decommissioned partners
- [ ] Review and tighten permissions based on actual usage
- [ ] Check for unused roles (no assumption in 90+ days)
- [ ] Verify ExternalId values are still correct

### Before Removing Cross-Account Access

- [ ] Confirm no active workloads depend on the role
- [ ] Notify the partner/admin team of the planned revocation
- [ ] Remove RAM resource shares first (if applicable)
- [ ] Delete the IAM role
- [ ] Verify access is fully revoked

---

## Troubleshooting

### "Access Denied" on Role Assumption

1. Verify the trust policy includes the correct principal account ID
2. Check that ExternalId matches (for partner roles)
3. Ensure the assuming entity has `sts:AssumeRole` permission
4. Check for SCPs that may block cross-account access
5. Verify the role exists and is not in a deleted state

### "RAM Share Not Working"

1. Verify the RAM share was created successfully
2. Check that the target account accepted the share (if required)
3. Ensure the target account has EC2 permissions for the resource type
4. Verify the resource ARN is correct

### "Partner Cannot Access Resources"

1. Verify the partner is assuming the correct role
2. Check the role's permission policies (not just the trust policy)
3. Review permission boundaries for overly restrictive limits
4. Check CloudTrail for denied API calls to identify the missing permission

---

## References

- [AWS Cross-Account Access Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html)
- [AWS RAM User Guide](https://docs.aws.amazon.com/ram/latest/userguide/what-is.html)
- [Confused Deputy Prevention](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html)
- [IAM Least Privilege Guide](./IAM_LEAST_PRIVILEGE_GUIDE.md)
- [Data Security Strategy](./DATA_SECURITY_STRATEGY.md)
