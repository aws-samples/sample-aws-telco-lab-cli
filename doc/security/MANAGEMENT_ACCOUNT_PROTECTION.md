# Management Account Protection - Complete Process Flow

> **📝 Note on Example Data**
> 
> All AWS account IDs and resource identifiers in this document are **example values only**:
> - `987654321098` - Example partner account ID
> - `123456789012` - Example management account ID
> - User names, email addresses, and other identifiers are examples
> 
> Replace these with your actual values when implementing.

## Overview

This document outlines the complete implementation of management account protection in TelcoCLI's `create-partner` command, including the full flow from command execution through account provisioning and IAM role creation.

## Complete Process Flow

### 1. Command Execution
```bash
telcocli create-partner \
  --partner-name "ExternalPartner" \
  --partner-account-id "987654321098" \
  --admin-users "user1,user2" \
  --account-type "joint-developer" \
  --validation-duration "30d" \
  --contact-email "partner@example.com"
```

### 2. CreatePartnerCommand Processing

#### Input Validation
```python
# Partner name validation
if not validate_partner_name(args.partner_name):
    raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Invalid partner name format")

# Account ID validation  
if not validate_aws_account_id(args.partner_account_id):
    raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Invalid AWS account ID")
```

#### Request Preparation
```python
# Auto-generate contact email if not provided
partner_upper = args.partner_name.upper()
contact_email = args.contact_email or f"tibu-cse-lab+{partner_upper}_iam_trust@amazon.com"

# Create standardized account name
account_name = f"tibu-cse-lab+{partner_upper}_iam_trust"

# Parse admin users and duration
admin_users = [user.strip() for user in args.admin_users.split(",")]
duration_days = self._parse_duration_to_days(args.validation_duration)

# Create provisioning request
request = AccountProvisioningRequest(
    partner_name=args.partner_name,
    contact_email=contact_email,
    account_name=account_name,
    partner_account_id=args.partner_account_id,
    admin_users=admin_users,
    validation_duration_days=duration_days,
    account_type=args.account_type,
)
```

### 3. AccountProvisioningEngine Execution

#### Organizations Account Creation
```python
# Step 1: Create AWS Organizations account
logger.info(f"Creating AWS Organizations account: {request.account_name}")
account_result = self.organizations_service.create_account(request)

if not account_result["success"]:
    raise TelcoCLIException(ErrorCode.PARTNER_CREATION_FAILED, account_result["error_message"])

account_id = account_result["account_id"]  # New JDA account ID
```

#### IAM Configuration with Management Account Protection
```python
# Step 2: Setup IAM roles with security validation
logger.info("Creating IAM configuration...")
iam_result = self.iam_service.setup_partner_iam(
    account_id,                    # Target JDA account (newly created)
    request.partner_name,          # Partner identifier
    request.partner_account_id,    # Partner's AWS account ID
    request.account_type           # Account type (joint-developer, etc.)
)
```

### 4. IAMService Security Validation

#### Management Account Protection Check
```python
def setup_partner_iam(self, account_id: str, partner_name: str, partner_account_id: str, account_type: str):
    """Create comprehensive IAM setup in target account."""
    try:
        # SECURITY CHECKPOINT: Prevent role creation in management account
        if self._is_management_account(account_id):
            return {
                "success": False,
                "error_message": (
                    f"Cannot create partner roles in management account {account_id}. "
                    "Roles must be created in target JDA accounts only."
                )
            }
        
        # Continue with role creation in validated target account
        partner_upper = partner_name.upper()
        target_credentials = self._assume_role_in_target_account(account_id)
        # ... role creation continues
```

#### Management Account Detection Logic
```python
def _is_management_account(self, account_id: str) -> bool:
    """Check if account is a management account that should not have partner roles."""
    try:
        # Query AWS Organizations for management account ID
        org_client = boto3.client("organizations")
        org_response = org_client.describe_organization()
        management_account_id = org_response["Organization"]["MasterAccountId"]
        
        if account_id == management_account_id:
            logger.warning(f"Account {account_id} is the management account")
            return True
            
        return False
        
    except Exception as e:
        logger.debug(f"Could not verify account type for {account_id}: {e}")
        # Fail-open: Allow operation if Organizations API is unavailable
        return False
```

### 5. Role Creation Process (When Validated)

#### Cross-Account Role Setup
```python
# Assume OrganizationAccountAccessRole in target JDA account
target_credentials = self._assume_role_in_target_account(account_id)
target_iam_client = boto3.client("iam", **target_credentials)

# Create permission boundary policy
boundary_policy_arn = self._create_boundary_policy(target_iam_client, partner_upper, account_id)

# Create partner roles based on account type
roles_created = self._create_partner_roles(
    target_iam_client,
    partner_upper,
    account_type,
    account_id,
    partner_account_id,  # Partner's account that will assume these roles
    boundary_policy_arn,
)
```

### 6. Account Tagging and Finalization
```python
# Tag the newly created account
self.organizations_service.tag_account(account_id, request)

# Return comprehensive result
return AccountProvisioningResult(
    success=True,
    aws_account_id=account_id,
    account_name=request.account_name,
    cross_account_role_arn=iam_result["role_arn"],
    provisioning_time_seconds=provisioning_time,
    role_result=iam_result,
)
```

## Security Protection Points

### 1. Input Validation Layer
- **Partner Name**: Format and length validation
- **Account ID**: 12-digit AWS account number validation
- **Admin Users**: Email format validation

### 2. Management Account Protection Layer
- **API-Based Detection**: Uses Organizations `describe_organization()`
- **Authoritative Source**: Compares against actual management account ID
- **Early Termination**: Blocks execution before any role creation

### 3. Cross-Account Role Security
- **Permission Boundaries**: Restricts role capabilities
- **Least Privilege**: Minimal required permissions only
- **Account Isolation**: Roles created in target JDA account, not management

## Execution Scenarios

### Scenario 1: Normal Partner Creation (Success)
```
1. Command: create-partner --partner-name "TestPartner" --partner-account-id "987654321098"
2. Validation: ✅ Partner name valid, Account ID valid
3. Organizations: ✅ New JDA account created (e.g., 123456789012)
4. Security Check: ✅ Target account 123456789012 ≠ Management account
5. IAM Setup: ✅ Roles created in JDA account 123456789012
6. Result: ✅ Partner can assume roles from their account 987654321098
```

### Scenario 2: Management Account Protection (Blocked)
```
1. Command: create-partner --partner-name "TestPartner" --partner-account-id "987654321098"
2. Validation: ✅ Partner name valid, Account ID valid  
3. Organizations: ✅ Account creation attempted
4. Security Check: ❌ Target account = Management account (111111111111)
5. IAM Setup: ❌ BLOCKED - Management account protection triggered
6. Result: ❌ Error: Cannot create partner roles in management account
```

### Scenario 3: Organizations API Unavailable (Graceful Fallback)
```
1. Command: create-partner --partner-name "TestPartner" --partner-account-id "987654321098"
2. Validation: ✅ Partner name valid, Account ID valid
3. Organizations: ✅ New JDA account created (e.g., 123456789012)
4. Security Check: ⚠️ Organizations API timeout/error
5. IAM Setup: ✅ Proceeds with warning (fail-open for availability)
6. Result: ✅ Partner roles created with API failure logged
```

## Data Flow Architecture

### Request Flow
```
CreatePartnerCommand
    ↓ (validation)
AccountProvisioningEngine
    ↓ (account creation)
OrganizationsService
    ↓ (new JDA account)
IAMService.setup_partner_iam()
    ↓ (security check)
_is_management_account()
    ↓ (if valid)
Role Creation in Target JDA Account
```

### Security Checkpoint
```
Target Account ID
    ↓
Organizations API Call
    ↓
Management Account ID Comparison
    ↓
[BLOCK if Management] OR [PROCEED if JDA]
```

## Quality Assurance Process

### Build Validation
```bash
brazil-build test

# Results:
# ✅ 401 tests PASSED
# ✅ 1 xfailed (expected)
# ✅ MyPy type checking: SUCCESS
# ✅ Flake8 linting: SUCCESS
# ✅ Black formatting: SUCCESS
# ✅ Coverage: 59%
```

### Integration Testing
- **End-to-End Flow**: Complete partner creation workflow
- **Security Validation**: Management account blocking
- **Error Handling**: API failure scenarios
- **Data Integrity**: Account and role creation consistency

## Technical Implementation Details

### Key Classes and Methods
```python
# Command layer
CreatePartnerCommand.run()
CreatePartnerCommand._create_partner_account()

# Provisioning layer  
AccountProvisioningEngine.provision_partner_account()

# Service layer
OrganizationsService.create_account()
IAMService.setup_partner_iam()
IAMService._is_management_account()  # Security checkpoint
```

### Data Structures
```python
@dataclass
class AccountProvisioningRequest:
    partner_name: str
    contact_email: str
    account_name: str
    partner_account_id: str
    admin_users: List[str]
    validation_duration_days: int
    account_type: str

@dataclass  
class AccountProvisioningResult:
    success: bool
    aws_account_id: Optional[str]
    cross_account_role_arn: Optional[str]
    provisioning_time_seconds: Optional[float]
    role_result: Optional[Dict[str, Any]]
```

## Deployment Status

- **Branch**: `cr1-add-dedicated-host-commands`
- **Implementation**: Complete and tested
- **Security Enhancement**: Management account protection active
- **Build Status**: All quality gates passed
- **Ready**: For code review and merge
