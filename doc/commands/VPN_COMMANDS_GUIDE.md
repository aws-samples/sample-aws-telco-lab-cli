# AWS VPN Commands User Guide

> **⚠️ Security Notice:** This is sample code for demonstration purposes. VPN operations involve private keys and certificates — handle them securely. Never share private keys or commit them to version control. See [SECURITY.md](../../SECURITY.md) for detailed security guidance.

## Overview

This guide explains how to use TelcoCLI commands to manage VPN certificates for partner access, including certificate generation, listing, and revocation.

## VPN Management Commands

### `create-vpn` - Generate VPN Certificate

**Purpose**: Generate VPN certificates for partner access with routing configuration.

**Usage:**
```bash
# Create VPN certificate for partner
telcocli create-vpn "partner-name" \
  --allowed-subnets "192.168.100.0/24,10.0.0.0/16"

# Create with custom duration and output directory
telcocli create-vpn "partner-name" \
  --allowed-subnets "192.168.100.0/24" \
  --certificate-duration "60d" \
  --output-dir "./certificates"
```

**Options:**
- `partner_name` (required): Name of the partner to generate certificate for
- `--allowed-subnets` (required): Comma-separated list of allowed subnets (e.g., "192.168.100.0/24,10.0.0.0/16")
- `--certificate-duration` (optional, default: 30d): Certificate duration (e.g., '30d')
- `--output-dir` (optional, default: .): Directory to save the .ovpn file

**Output:**
```json
{
  "Success": true,
  "Certificate": {
    "PartnerName": "partner-name",
    "CertificateFile": "./partner-name.ovpn",
    "AllowedSubnets": ["192.168.100.0/24", "10.0.0.0/16"],
    "ValidUntil": "2024-02-01T00:00:00Z"
  }
}
```

---

### `list-vpn-certificates` - List Active Certificates

**Purpose**: List all active VPN certificates with optional detailed information.

**Usage:**
```bash
# List all certificates
telcocli list-vpn-certificates

# Show detailed certificate information
telcocli list-vpn-certificates --show-details

# JSON output format
telcocli list-vpn-certificates --output json
```

**Options:**
- `--show-details` (optional): Show detailed certificate information (validity dates, serial number)
- `--output` (optional, default: table): Output format (json|table)

**Output:**
```json
{
  "Success": true,
  "Server": {
    "InstanceId": "i-1234567890abcdef0",
    "Name": "vpn-server",
    "Endpoint": "vpn.example.com:1194"
  },
  "Certificates": [
    {
      "Name": "partner-name",
      "RoutingEnabled": true,
      "AllowedSubnets": ["192.168.100.0/24"],
      "ValidFrom": "2024-01-01T00:00:00Z",
      "ValidUntil": "2024-02-01T00:00:00Z",
      "SerialNumber": "ABC123"
    }
  ]
}
```

---

### `revoke-vpn-certificate` - Revoke Certificate

**Purpose**: Revoke VPN certificates for a partner and clean up associated resources.

**Usage:**
```bash
# Revoke certificate with confirmation
telcocli revoke-vpn-certificate "partner-name"

# Skip confirmation prompt
telcocli revoke-vpn-certificate "partner-name" --yes
```

**Options:**
- `partner_name` (required): Name of the partner to revoke certificate for
- `--yes` (optional): Skip confirmation prompt

**Output:**
```json
{
  "Success": true,
  "Message": "Certificate for 'partner-name' revoked successfully",
  "Actions": [
    "Certificate revoked in Easy-RSA PKI",
    "Certificate Revocation List updated",
    "Client configuration files removed",
    "Existing VPN connections terminated"
  ]
}
```

---

## Common Use Cases

### 1. **Partner Onboarding**
```bash
# Generate VPN access for new partner
telcocli create-vpn "new-partner" \
  --allowed-subnets "192.168.100.0/24" \
  --certificate-duration "90d" \
  --output-dir "./partner-certificates"

# Verify certificate was created
telcocli list-vpn-certificates --show-details
```

### 2. **Certificate Management**
```bash
# List all active certificates
telcocli list-vpn-certificates --output table

# Check certificate details
telcocli list-vpn-certificates --show-details
```

### 3. **Partner Offboarding**
```bash
# Revoke partner access
telcocli revoke-vpn-certificate "old-partner" --yes

# Verify certificate was revoked
telcocli list-vpn-certificates
```

### 4. **Troubleshooting**
```bash
# Check VPN server status and certificates
telcocli list-vpn-certificates --show-details --output json

# Verify partner routing configuration
telcocli list-vpn-certificates --output table
```

---

## Security Considerations

### Certificate Validation
- Partner names must contain only alphanumeric characters, hyphens, and underscores
- Subnet validation ensures proper CIDR notation
- Certificate duration is limited to reasonable timeframes

### Network Security
- Allowed subnets are strictly enforced through routing configuration
- Client Configuration Directory (CCD) files control partner access
- Certificate Revocation List (CRL) is automatically updated

### Access Control
- VPN server discovery uses multiple security group filters
- SSM connectivity required for certificate operations
- All operations logged for audit purposes

---

## Troubleshooting

### Common Issues

**"VPN server not found"**
- Verify VPN server is running and tagged correctly
- Check SSM connectivity to the server
- Ensure proper security group configuration

**"Certificate generation failed"**
- Check Easy-RSA PKI configuration on server
- Verify sufficient disk space for certificate files
- Ensure OpenVPN service is running

**"Invalid subnet format"**
- Use proper CIDR notation (e.g., 192.168.1.0/24)
- Separate multiple subnets with commas
- Avoid overlapping subnet ranges

### Getting Help
```bash
# Command-specific help
telcocli create-vpn --help
telcocli list-vpn-certificates --help
telcocli revoke-vpn-certificate --help

# General help
telcocli --help
```

---

This guide provides comprehensive coverage of VPN certificate management for secure partner access to AWS resources.
