# Encryption Implementation Guide

**Document Version:** 1.0  
**Last Updated:** 2025-01-27

---

## Quick Start

This guide provides practical implementation examples for encrypting sensitive data in TelcoCLI.

---

## AWS Credentials Encryption

### Using AWS Systems Manager Parameter Store

```python
import boto3
from botocore.exceptions import ClientError

class SecureCredentialStore:
    """Secure storage for AWS credentials using Parameter Store."""
    
    def __init__(self, kms_key_id: str):
        self.ssm_client = boto3.client('ssm')
        self.kms_key_id = kms_key_id
    
    def store_credential(self, name: str, value: str) -> bool:
        """Store encrypted credential in Parameter Store."""
        try:
            self.ssm_client.put_parameter(
                Name=f'/telcocli/credentials/{name}',
                Value=value,
                Type='SecureString',
                KeyId=self.kms_key_id,
                Overwrite=True,
                Tags=[
                    {'Key': 'Application', 'Value': 'TelcoCLI'},
                    {'Key': 'Classification', 'Value': 'CRITICAL'}
                ]
            )
            return True
        except ClientError as e:
            print(f"Error storing credential: {e}")
            return False
    
    def retrieve_credential(self, name: str) -> str:
        """Retrieve and decrypt credential from Parameter Store."""
        try:
            response = self.ssm_client.get_parameter(
                Name=f'/telcocli/credentials/{name}',
                WithDecryption=True
            )
            return response['Parameter']['Value']
        except ClientError as e:
            print(f"Error retrieving credential: {e}")
            return None
```


### Using OS Keychain (Local Development)

```python
import keyring
from keyring.errors import KeyringError

class LocalCredentialStore:
    """Secure storage using OS keychain for local development."""
    
    SERVICE_NAME = 'TelcoCLI'
    
    @staticmethod
    def store_credential(key: str, value: str) -> bool:
        """Store credential in OS keychain."""
        try:
            keyring.set_password(
                LocalCredentialStore.SERVICE_NAME,
                key,
                value
            )
            return True
        except KeyringError as e:
            print(f"Error storing in keychain: {e}")
            return False
    
    @staticmethod
    def retrieve_credential(key: str) -> str:
        """Retrieve credential from OS keychain."""
        try:
            return keyring.get_password(
                LocalCredentialStore.SERVICE_NAME,
                key
            )
        except KeyringError as e:
            print(f"Error retrieving from keychain: {e}")
            return None
    
    @staticmethod
    def delete_credential(key: str) -> bool:
        """Delete credential from OS keychain."""
        try:
            keyring.delete_password(
                LocalCredentialStore.SERVICE_NAME,
                key
            )
            return True
        except KeyringError as e:
            print(f"Error deleting from keychain: {e}")
            return False
```

---

## VPN Certificate Encryption

### Encrypting Certificate Files

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class CertificateEncryption:
    """Encrypt and decrypt VPN certificates."""
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    @staticmethod
    def encrypt_certificate(cert_data: bytes, password: str) -> dict:
        """Encrypt certificate data."""
        salt = os.urandom(16)
        key = CertificateEncryption.derive_key(password, salt)
        f = Fernet(key)
        encrypted_data = f.encrypt(cert_data)
        
        return {
            'encrypted_data': encrypted_data,
            'salt': salt
        }
    
    @staticmethod
    def decrypt_certificate(encrypted_data: bytes, salt: bytes, password: str) -> bytes:
        """Decrypt certificate data."""
        key = CertificateEncryption.derive_key(password, salt)
        f = Fernet(key)
        return f.decrypt(encrypted_data)
```

---

## Session Data Encryption

### Encrypting Session Files

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import json
import os

class SessionEncryption:
    """Encrypt and decrypt session data."""
    
    def __init__(self, key: bytes = None):
        """Initialize with encryption key."""
        self.key = key or AESGCM.generate_key(bit_length=256)
        self.aesgcm = AESGCM(self.key)
    
    def encrypt_session(self, session_data: dict) -> dict:
        """Encrypt session data."""
        nonce = os.urandom(12)
        plaintext = json.dumps(session_data).encode()
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, None)
        
        return {
            'ciphertext': ciphertext,
            'nonce': nonce
        }
    
    def decrypt_session(self, ciphertext: bytes, nonce: bytes) -> dict:
        """Decrypt session data."""
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(plaintext.decode())
```

---

## Data Access Logging

### Implementing Audit Logging

```python
import logging
import json
from datetime import datetime
from typing import Optional

class DataAccessLogger:
    """Log data access for audit trail."""
    
    def __init__(self, log_file: str = 'data_access.log'):
        """Initialize logger."""
        self.logger = logging.getLogger('DataAccess')
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_access(
        self,
        user: str,
        action: str,
        resource: str,
        classification: str,
        result: str,
        details: Optional[dict] = None
    ):
        """Log data access event."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user': user,
            'action': action,
            'resource': resource,
            'classification': classification,
            'result': result,
            'details': details or {}
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_credential_access(self, user: str, credential_type: str):
        """Log credential access (CRITICAL classification)."""
        self.log_access(
            user=user,
            action='RETRIEVE_CREDENTIAL',
            resource=credential_type,
            classification='CRITICAL',
            result='SUCCESS'
        )
    
    def log_encryption_operation(
        self,
        operation: str,
        resource: str,
        success: bool
    ):
        """Log encryption/decryption operation."""
        self.log_access(
            user='SYSTEM',
            action=f'ENCRYPTION_{operation.upper()}',
            resource=resource,
            classification='CONFIDENTIAL',
            result='SUCCESS' if success else 'FAILURE'
        )
```

---

## AWS KMS Integration

### Using KMS for Envelope Encryption

```python
import boto3
from botocore.exceptions import ClientError

class KMSEncryption:
    """Envelope encryption using AWS KMS."""
    
    def __init__(self, kms_key_id: str):
        """Initialize with KMS key ID."""
        self.kms_client = boto3.client('kms')
        self.kms_key_id = kms_key_id
    
    def generate_data_key(self) -> dict:
        """Generate data encryption key."""
        try:
            response = self.kms_client.generate_data_key(
                KeyId=self.kms_key_id,
                KeySpec='AES_256'
            )
            return {
                'plaintext_key': response['Plaintext'],
                'encrypted_key': response['CiphertextBlob']
            }
        except ClientError as e:
            print(f"Error generating data key: {e}")
            return None
    
    def decrypt_data_key(self, encrypted_key: bytes) -> bytes:
        """Decrypt data encryption key."""
        try:
            response = self.kms_client.decrypt(
                CiphertextBlob=encrypted_key
            )
            return response['Plaintext']
        except ClientError as e:
            print(f"Error decrypting data key: {e}")
            return None
    
    def encrypt_data(self, plaintext: bytes) -> dict:
        """Encrypt data using envelope encryption."""
        # Generate data key
        data_key = self.generate_data_key()
        if not data_key:
            return None
        
        # Encrypt data with data key
        aesgcm = AESGCM(data_key['plaintext_key'])
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        return {
            'ciphertext': ciphertext,
            'nonce': nonce,
            'encrypted_data_key': data_key['encrypted_key']
        }
    
    def decrypt_data(
        self,
        ciphertext: bytes,
        nonce: bytes,
        encrypted_data_key: bytes
    ) -> bytes:
        """Decrypt data using envelope encryption."""
        # Decrypt data key
        plaintext_key = self.decrypt_data_key(encrypted_data_key)
        if not plaintext_key:
            return None
        
        # Decrypt data with data key
        aesgcm = AESGCM(plaintext_key)
        return aesgcm.decrypt(nonce, ciphertext, None)
```

---

## Usage Examples

### Example 1: Storing AWS Credentials Securely

```python
# Initialize credential store
kms_key_id = 'arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012'
cred_store = SecureCredentialStore(kms_key_id)

# Store credentials
cred_store.store_credential('aws_access_key_id', 'AKIAIOSFODNN7EXAMPLE')
cred_store.store_credential('aws_secret_access_key', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')

# Retrieve credentials
access_key = cred_store.retrieve_credential('aws_access_key_id')
secret_key = cred_store.retrieve_credential('aws_secret_access_key')
```

### Example 2: Encrypting VPN Certificates

```python
# Read certificate file
with open('vpn_cert.ovpn', 'rb') as f:
    cert_data = f.read()

# Encrypt certificate
password = input("Enter encryption password: ")
encrypted = CertificateEncryption.encrypt_certificate(cert_data, password)

# Save encrypted certificate
with open('vpn_cert.encrypted', 'wb') as f:
    f.write(encrypted['encrypted_data'])
with open('vpn_cert.salt', 'wb') as f:
    f.write(encrypted['salt'])

# Later: Decrypt certificate
with open('vpn_cert.encrypted', 'rb') as f:
    encrypted_data = f.read()
with open('vpn_cert.salt', 'rb') as f:
    salt = f.read()

password = input("Enter decryption password: ")
decrypted = CertificateEncryption.decrypt_certificate(encrypted_data, salt, password)
```

### Example 3: Logging Data Access

```python
# Initialize logger
logger = DataAccessLogger()

# Log credential access
logger.log_credential_access(
    user='john.doe',
    credential_type='AWS_ACCESS_KEY'
)

# Log encryption operation
logger.log_encryption_operation(
    operation='ENCRYPT',
    resource='session_data.json',
    success=True
)

# Log general data access
logger.log_access(
    user='jane.smith',
    action='READ',
    resource='vpc_configuration',
    classification='CONFIDENTIAL',
    result='SUCCESS',
    details={'vpc_id': 'vpc-12345678'}
)
```

---

## Security Best Practices

### 1. Key Management

✅ **DO:**
- Use AWS KMS for master keys
- Implement envelope encryption for data
- Rotate keys regularly (90 days for data keys)
- Store keys securely (never in code or config files)
- Use strong key derivation functions (PBKDF2 with 100,000+ iterations)

❌ **DON'T:**
- Hardcode encryption keys
- Use weak passwords for key derivation
- Reuse keys across different purposes
- Store keys in version control
- Share keys via insecure channels

### 2. Encryption Implementation

✅ **DO:**
- Use authenticated encryption (AES-GCM, ChaCha20-Poly1305)
- Generate unique nonces/IVs for each encryption
- Use cryptographically secure random number generators
- Validate decryption results
- Clear sensitive data from memory after use

❌ **DON'T:**
- Use deprecated algorithms (DES, RC4, MD5)
- Reuse nonces/IVs
- Implement custom cryptography
- Ignore encryption errors
- Store plaintext alongside ciphertext

### 3. Access Control

✅ **DO:**
- Implement least privilege access
- Log all access to sensitive data
- Use IAM roles instead of long-lived credentials
- Implement multi-factor authentication
- Review access logs regularly

❌ **DON'T:**
- Grant broad permissions
- Share credentials between users
- Use root credentials
- Disable logging
- Ignore access anomalies

---

## Testing Encryption

### Unit Tests

```python
import unittest

class TestEncryption(unittest.TestCase):
    """Test encryption implementations."""
    
    def test_certificate_encryption_roundtrip(self):
        """Test certificate encryption and decryption."""
        original_data = b"test certificate data"
        password = "test_password_123"
        
        # Encrypt
        encrypted = CertificateEncryption.encrypt_certificate(
            original_data,
            password
        )
        
        # Decrypt
        decrypted = CertificateEncryption.decrypt_certificate(
            encrypted['encrypted_data'],
            encrypted['salt'],
            password
        )
        
        self.assertEqual(original_data, decrypted)
    
    def test_session_encryption_roundtrip(self):
        """Test session data encryption and decryption."""
        session_enc = SessionEncryption()
        original_data = {'user': 'test', 'token': 'abc123'}
        
        # Encrypt
        encrypted = session_enc.encrypt_session(original_data)
        
        # Decrypt
        decrypted = session_enc.decrypt_session(
            encrypted['ciphertext'],
            encrypted['nonce']
        )
        
        self.assertEqual(original_data, decrypted)
```

---

## Troubleshooting

### Common Issues

**Issue:** "KMS key not found"
- **Solution:** Verify KMS key ID and region are correct
- **Solution:** Check IAM permissions for kms:GenerateDataKey

**Issue:** "Decryption failed"
- **Solution:** Verify password/key is correct
- **Solution:** Check that nonce/salt matches encryption
- **Solution:** Ensure data hasn't been corrupted

**Issue:** "Permission denied accessing keychain"
- **Solution:** Grant keychain access to application
- **Solution:** Use sudo for system keychain on Linux
- **Solution:** Check keyring backend is installed

---

## KMS Key Management

### Key Creation Requirements

When creating KMS keys for TelcoCLI operations, follow these guidelines:

**Symmetric Keys (Recommended for Data Encryption):**
```bash
# Create a symmetric KMS key for data encryption
aws kms create-key \
  --description "TelcoCLI data encryption key" \
  --key-usage ENCRYPT_DECRYPT \
  --origin AWS_KMS \
  --tags TagKey=Application,TagValue=TelcoCLI \
         TagKey=Environment,TagValue=production
```

**Key Alias (Required for Usability):**
```bash
# Create an alias for easy reference
aws kms create-alias \
  --alias-name alias/telcocli-data-key \
  --target-key-id <key-id>
```

### Key Rotation Policies

| Key Type | Rotation Period | Method |
|----------|----------------|--------|
| KMS symmetric keys | Annual (automatic) | Enable automatic rotation |
| KMS asymmetric keys | Manual | Create new key, re-encrypt data |
| Data encryption keys | Per-operation | Generated via `GenerateDataKey` |
| VPN certificates | 30-90 days | Regenerate via `create-vpn` |

**Enable Automatic Rotation:**
```bash
aws kms enable-key-rotation --key-id <key-id>

# Verify rotation is enabled
aws kms get-key-rotation-status --key-id <key-id>
```

### KMS IAM Permissions

Minimum permissions for TelcoCLI encryption operations:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowEncryptDecrypt",
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:GenerateDataKeyWithoutPlaintext",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:REGION:ACCOUNT:key/KEY-ID"
    }
  ]
}
```

Do NOT grant:
- `kms:*` — overly permissive
- `kms:ScheduleKeyDeletion` — prevents accidental key deletion
- `kms:DisableKey` — prevents accidental key disabling

### KMS Best Practices

1. **One key per purpose** — separate keys for data encryption, credential storage, and S3 encryption
2. **Enable automatic rotation** — for all symmetric keys
3. **Use key aliases** — never hardcode key IDs in application code
4. **Restrict key policies** — limit who can administer vs use the key
5. **Enable CloudTrail** — log all KMS API calls for audit
6. **Use envelope encryption** — generate data keys with `GenerateDataKey`, encrypt data locally
7. **Tag keys** — include Application, Environment, and Owner tags
8. **Monitor key usage** — set CloudWatch alarms for unusual KMS activity

---

## References

- [DATA_SECURITY_STRATEGY.md](DATA_SECURITY_STRATEGY.md) - Overall security strategy
- [AWS KMS Developer Guide](https://docs.aws.amazon.com/kms/latest/developerguide/)
- [AWS KMS Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html)
- [Python Cryptography Library](https://cryptography.io/)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)

---

**Document Version:** 1.1
**Last Updated:** 2025-02-10  
**Next Review:** 2025-04-27
