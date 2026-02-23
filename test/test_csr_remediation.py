# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
CSR Remediation Security Regression Tests.

These tests scan the codebase to verify security fixes remain in place.
They act as regression guards for the CSR remediation work.
"""

import re
from pathlib import Path

import pytest

# Root paths
SRC_DIR = Path(__file__).parent.parent / "src" / "telco_cli"
TEMPLATE_DIR = SRC_DIR / "templates" / "terraform"


def _get_python_files() -> list:
    """Get all Python source files (excluding tests)."""
    return list(SRC_DIR.rglob("*.py"))


def _get_terraform_files() -> list:
    """Get all Terraform files."""
    return list(TEMPLATE_DIR.rglob("*.tf"))


def _read_file(path: Path) -> str:
    """Read file content safely."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


class TestNoUnlimitedIAMPermissions:
    """**Validates: Requirements 1.1**

    Property: No IAM policy in source code has both Action: '*' and Resource: '*'.
    """

    def test_no_action_star_resource_star(self):
        """No Python file should contain Action:'*' paired with Resource:'*'."""
        violations = []
        for py_file in _get_python_files():
            content = _read_file(py_file)
            # Look for Action: "*" or Action: "*" patterns
            has_action_star = bool(re.search(r"""['"]Action['"]\s*:\s*['"]\*['"]""", content))
            has_resource_star = bool(re.search(r"""['"]Resource['"]\s*:\s*['"]\*['"]""", content))
            if has_action_star and has_resource_star:
                violations.append(str(py_file.relative_to(SRC_DIR.parent.parent)))

        assert not violations, f"Files with Action:'*' + Resource:'*' (unlimited IAM): {violations}"


class TestNoIAMWildcardActions:
    """**Validates: Requirements 1.2**

    Property: No IAM policy contains 'iam:*' as an action.
    """

    def test_no_iam_wildcard(self):
        """No Python file should contain iam:* in an Allow IAM action."""
        violations = []
        for py_file in _get_python_files():
            content = _read_file(py_file)
            if not re.search(r"""['"]iam:\*['"]""", content):
                continue
            # Only flag iam:* in Allow contexts, not Deny (boundary policies)
            lines = content.splitlines()
            in_deny_block = False
            for line in lines:
                if '"Deny"' in line or "'Deny'" in line:
                    in_deny_block = True
                if '"Allow"' in line or "'Allow'" in line:
                    in_deny_block = False
                if re.search(r"""['"]iam:\*['"]""", line) and not in_deny_block:
                    violations.append(str(py_file.relative_to(SRC_DIR.parent.parent)))
                    break

        assert not violations, f"Files with 'iam:*' in Allow action: {violations}"


class TestNoHardcodedPasswordsInTerraform:
    """**Validates: Requirements 2.1**

    Property: No Terraform file contains 'CHANGE_ME' (hardcoded password).
    """

    def test_no_change_me_in_terraform(self):
        """No Terraform file should contain CHANGE_ME."""
        violations = []
        for tf_file in _get_terraform_files():
            content = _read_file(tf_file)
            if "CHANGE_ME" in content:
                violations.append(str(tf_file.relative_to(SRC_DIR.parent.parent)))

        assert not violations, f"Terraform files with hardcoded 'CHANGE_ME' password: {violations}"


class TestMIT0HeadersInSourceFiles:
    """**Validates: Requirements 3.1**

    Property: All Python source files have MIT-0 SPDX header.
    """

    def test_all_python_files_have_mit0_header(self):
        """All Python source files should have SPDX-License-Identifier: MIT-0."""
        violations = []
        for py_file in _get_python_files():
            if py_file.name == "__init__.py":
                continue  # Skip empty init files
            content = _read_file(py_file)
            if not content.strip():
                continue  # Skip empty files
            if "SPDX-License-Identifier: MIT-0" not in content:
                violations.append(str(py_file.relative_to(SRC_DIR.parent.parent)))

        assert not violations, f"Python files missing MIT-0 header: {violations}"


class TestNoInternalAmazonReferences:
    """**Validates: Requirements 7.1**

    Property: No source file contains @amazon.com or internal URLs.
    """

    INTERNAL_PATTERNS = [
        r"@amazon\.com",
        r"devcentral\.amazon",
        r"w\.amazon\.com",
        r"code\.amazon\.com",
        r"issues\.amazon\.com",
    ]

    def test_no_internal_references(self):
        """No Python source file should contain internal Amazon references."""
        violations = []
        for py_file in _get_python_files():
            content = _read_file(py_file)
            for pattern in self.INTERNAL_PATTERNS:
                if re.search(pattern, content):
                    violations.append(
                        f"{py_file.relative_to(SRC_DIR.parent.parent)}: matches {pattern}"
                    )
                    break  # One violation per file is enough

        assert not violations, f"Files with internal Amazon references: {violations}"


class TestVPNPrivateKeyPermissions:
    """**Validates: Requirements 5.1**

    Property: VPN code sets 0o600 permissions on private key files.
    """

    def test_vpn_sets_restrictive_permissions(self):
        """create_vpn.py should reference 0o600 permissions."""
        vpn_file = SRC_DIR / "commands" / "vpn" / "create_vpn.py"
        assert vpn_file.exists(), "create_vpn.py not found"
        content = _read_file(vpn_file)
        assert (
            "0o600" in content
        ), "create_vpn.py must set 0o600 permissions on VPN private key files"


class TestS3PolicyExamplesEnforceTLS:
    """**Validates: Requirements 6.1**

    Property: S3 bucket policy examples include aws:SecureTransport condition.
    """

    def test_s3_policies_enforce_tls(self):
        """Security docs with S3 policies should include SecureTransport."""
        doc_dir = Path(__file__).parent.parent / "doc" / "security"
        files_with_s3_policies = []
        files_missing_tls = []

        for doc_file in doc_dir.rglob("*.md"):
            content = _read_file(doc_file)
            if (
                "s3:" in content.lower()
                and "bucket" in content.lower()
                and "policy" in content.lower()
            ):
                files_with_s3_policies.append(doc_file.name)
                if "SecureTransport" not in content:
                    files_missing_tls.append(doc_file.name)

        assert (
            not files_missing_tls
        ), f"S3 policy docs missing SecureTransport enforcement: {files_missing_tls}"


class TestNoShellInjectionVulnerabilities:
    """**Validates: Requirements 2.3**

    Property: No subprocess call uses shell=True in production code.
    """

    def test_no_shell_true_in_source(self):
        """No Python source file should use shell=True in subprocess calls."""
        violations = []
        for py_file in _get_python_files():
            content = _read_file(py_file)
            # Find shell=True that isn't in a comment
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "shell=True" in stripped:
                    violations.append(f"{py_file.relative_to(SRC_DIR.parent.parent)}:{i}")

        assert not violations, f"Source files with shell=True: {violations}"


class TestInputValidationExists:
    """**Validates: Requirements 2.4**

    Property: Input validation module exists with required validators.
    """

    REQUIRED_VALIDATORS = [
        "validate_aws_account_id",
        "validate_partner_name",
        "validate_aws_arn",
        "validate_resource_name",
        "validate_input_length",
        "sanitize_for_logging",
        "validate_aws_region",
        "validate_s3_bucket_name",
        "validate_iam_role_name",
    ]

    def test_validation_module_exists(self):
        """validation.py should exist with all required validators."""
        validation_file = SRC_DIR / "utils" / "validation.py"
        assert validation_file.exists(), "validation.py not found"
        content = _read_file(validation_file)

        missing = [v for v in self.REQUIRED_VALIDATORS if f"def {v}" not in content]
        assert not missing, f"validation.py missing required validators: {missing}"


class TestBedrockCredentialIsolation:
    """**Validates: Requirements 4.4**

    Property: Bedrock credentials come from standard AWS credential chain,
    not hardcoded in source.
    """

    FORBIDDEN_PATTERNS = [
        r"api_key\s*=\s*['\"]",
        r"AKIA[A-Z0-9]{16}",  # AWS access key pattern
        r"bedrock_key\s*=",
        r"anthropic_key\s*=",
    ]

    def test_no_hardcoded_bedrock_credentials(self):
        """Agent code should not contain hardcoded Bedrock/API credentials."""
        agent_dir = SRC_DIR / "telcocli_agent"
        if not agent_dir.exists():
            pytest.skip("telcocli_agent directory not found")

        violations = []
        for py_file in agent_dir.rglob("*.py"):
            content = _read_file(py_file)
            for pattern in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, content):
                    violations.append(
                        f"{py_file.relative_to(SRC_DIR.parent.parent)}: matches {pattern}"
                    )
                    break

        assert not violations, f"Agent files with hardcoded credentials: {violations}"
