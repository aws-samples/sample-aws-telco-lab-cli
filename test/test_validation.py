"""Tests for validation utilities."""

from telco_cli.utils.validation import (
    sanitize_input,
    validate_aws_account_id,
    validate_duration,
    validate_email,
    validate_host_id,
    validate_outpost_id,
    validate_partner_name,
)


class TestValidateAwsAccountId:
    """Test cases for AWS account ID validation."""

    def test_valid_account_id(self):
        """Test validation of valid AWS account ID."""
        result = validate_aws_account_id("123456789012")
        assert result is True

    def test_valid_account_id_with_spaces(self):
        """Test validation removes spaces from account ID."""
        result = validate_aws_account_id("123 456 789 012")
        assert result is True

    def test_valid_account_id_with_dashes(self):
        """Test validation removes dashes from account ID."""
        result = validate_aws_account_id("123-456-789-012")
        assert result is True

    def test_valid_account_id_mixed_formatting(self):
        """Test validation handles mixed formatting."""
        result = validate_aws_account_id("123-456 789.012")
        assert result is True

    def test_empty_account_id(self):
        """Test validation returns False for empty account ID."""
        result = validate_aws_account_id("")
        assert result is False

    def test_none_account_id(self):
        """Test validation returns False for None account ID."""
        result = validate_aws_account_id(None)
        assert result is False

    def test_short_account_id(self):
        """Test validation returns False for short account ID."""
        result = validate_aws_account_id("12345")
        assert result is False

    def test_long_account_id(self):
        """Test validation returns False for long account ID."""
        result = validate_aws_account_id("1234567890123")
        assert result is False

    def test_non_numeric_account_id(self):
        """Test validation handles non-numeric characters."""
        # Should return False because after removing non-digits, length is wrong
        result = validate_aws_account_id("123abc456def")  # Only "123456" digits remain (6 digits)
        assert result is False

        # Should also return False for no digits
        result = validate_aws_account_id("abcdefghijkl")  # No digits
        assert result is False


class TestValidatePartnerName:
    """Test cases for partner name validation."""

    def test_valid_partner_name(self):
        """Test validation of valid partner names."""
        result = validate_partner_name("TestPartner")
        assert result is True

    def test_valid_partner_name_with_numbers(self):
        """Test validation allows numbers in partner name."""
        result = validate_partner_name("Partner123")
        assert result is True

    def test_valid_partner_name_with_hyphens(self):
        """Test validation allows hyphens in partner name."""
        result = validate_partner_name("Test-Partner")
        assert result is True

    def test_valid_partner_name_with_underscores(self):
        """Test validation allows underscores in partner name."""
        result = validate_partner_name("Test_Partner")
        assert result is True

    def test_empty_partner_name(self):
        """Test validation rejects empty partner name."""
        result = validate_partner_name("")
        assert result is False

    def test_none_partner_name(self):
        """Test validation rejects None partner name."""
        result = validate_partner_name(None)
        assert result is False

    def test_short_partner_name(self):
        """Test validation rejects partner name that's too short."""
        result = validate_partner_name("A")
        assert result is False

    def test_long_partner_name(self):
        """Test validation rejects partner name that's too long."""
        long_name = "A" * 65  # 65 characters (over 64 limit)
        result = validate_partner_name(long_name)
        assert result is False

    def test_partner_name_starting_with_number(self):
        """Test validation rejects partner name starting with number."""
        result = validate_partner_name("123Partner")
        assert result is False

    def test_partner_name_with_special_characters(self):
        """Test validation rejects partner name with invalid special characters."""
        result = validate_partner_name("Test@Partner")
        assert result is False


class TestValidateEmail:
    """Test cases for email validation."""

    def test_valid_email(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com",
        ]

        for email in valid_emails:
            valid, message = validate_email(email)
            assert valid is True, f"Email {email} should be valid"
            assert message == ""

    def test_empty_email(self):
        """Test validation rejects empty email."""
        valid, message = validate_email("")
        assert valid is False
        assert "Email address is required" in message

    def test_none_email(self):
        """Test validation rejects None email."""
        valid, message = validate_email(None)
        assert valid is False
        assert "Email address is required" in message

    def test_invalid_email_formats(self):
        """Test validation rejects invalid email formats."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "test@",
            "test.example.com",
            "test@example",
            "test@.com",
        ]

        for email in invalid_emails:
            valid, message = validate_email(email)
            assert valid is False, f"Email {email} should be invalid"
            assert "Invalid email address format" in message


class TestValidateDuration:
    """Test cases for duration validation."""

    def test_valid_durations(self):
        """Test validation of valid duration formats."""
        valid_durations = [
            ("30d", True),
            ("24h", True),
            ("60m", True),
            ("1d", True),
            ("365d", True),
            ("1h", True),
            ("8760h", True),
            ("1m", True),
            ("525600m", True),
        ]

        for duration, expected in valid_durations:
            valid, message = validate_duration(duration)
            assert valid is expected, f"Duration {duration} validation failed"
            if expected:
                assert message == ""

    def test_empty_duration(self):
        """Test validation rejects empty duration."""
        valid, message = validate_duration("")
        assert valid is False
        assert "Duration is required" in message

    def test_none_duration(self):
        """Test validation rejects None duration."""
        valid, message = validate_duration(None)
        assert valid is False
        assert "Duration is required" in message

    def test_invalid_duration_formats(self):
        """Test validation rejects invalid duration formats."""
        invalid_durations = [
            "30",
            "30days",
            "24hours",
            "60minutes",
            "30x",
            "d30",
            "h24",
        ]

        for duration in invalid_durations:
            valid, message = validate_duration(duration)
            assert valid is False, f"Duration {duration} should be invalid"
            assert "Duration must be in format like" in message

    def test_duration_boundary_values(self):
        """Test validation of duration boundary values."""
        # Days boundaries
        valid, _ = validate_duration("0d")
        assert valid is False

        valid, _ = validate_duration("366d")
        assert valid is False

        # Hours boundaries
        valid, _ = validate_duration("0h")
        assert valid is False

        valid, _ = validate_duration("8761h")
        assert valid is False

        # Minutes boundaries
        valid, _ = validate_duration("0m")
        assert valid is False

        valid, _ = validate_duration("525601m")
        assert valid is False

    def test_case_insensitive_duration(self):
        """Test validation is case insensitive."""
        valid, message = validate_duration("30D")
        assert valid is True
        assert message == ""


class TestSanitizeInput:
    """Test cases for input sanitization."""

    def test_normal_input(self):
        """Test sanitization of normal input."""
        result = sanitize_input("Hello World")
        assert result == "Hello World"

    def test_empty_input(self):
        """Test sanitization of empty input."""
        result = sanitize_input("")
        assert result == ""

    def test_none_input(self):
        """Test sanitization of None input."""
        result = sanitize_input(None)
        assert result == ""

    def test_input_with_control_characters(self):
        """Test sanitization removes control characters."""
        result = sanitize_input("Hello\x00\x1f\x7f\x9fWorld")
        assert result == "HelloWorld"

    def test_input_length_limiting(self):
        """Test sanitization limits input length."""
        long_input = "A" * 300
        result = sanitize_input(long_input)
        assert len(result) == 256  # Default max length

    def test_custom_max_length(self):
        """Test sanitization with custom max length."""
        long_input = "A" * 100
        result = sanitize_input(long_input, max_length=50)
        assert len(result) == 50

    def test_input_with_whitespace(self):
        """Test sanitization trims whitespace."""
        result = sanitize_input("  Hello World  ")
        assert result == "Hello World"


class TestValidateOutpostId:
    """Test cases for Outpost ID validation."""

    def test_valid_outpost_id(self):
        """Test validation of valid Outpost ID."""
        valid, message = validate_outpost_id("op-1234567890abcdef0")
        assert valid is True
        assert message == ""

    def test_empty_outpost_id(self):
        """Test validation rejects empty Outpost ID."""
        valid, message = validate_outpost_id("")
        assert valid is False
        assert "Outpost ID is required" in message

    def test_invalid_outpost_id_format(self):
        """Test validation rejects invalid Outpost ID format."""
        invalid_ids = [
            "op-123",
            "op-1234567890abcdef",
            "op-1234567890abcdef01",
            "h-1234567890abcdef0",
            "1234567890abcdef0",
        ]

        for outpost_id in invalid_ids:
            valid, message = validate_outpost_id(outpost_id)
            assert valid is False, f"Outpost ID {outpost_id} should be invalid"
            assert "Invalid Outpost ID format" in message


class TestValidateHostId:
    """Test cases for Host ID validation."""

    def test_valid_host_id(self):
        """Test validation of valid Host ID."""
        valid, message = validate_host_id("h-1234567890abcdef0")
        assert valid is True
        assert message == ""

    def test_empty_host_id(self):
        """Test validation rejects empty Host ID."""
        valid, message = validate_host_id("")
        assert valid is False
        assert "Host ID is required" in message

    def test_invalid_host_id_format(self):
        """Test validation rejects invalid Host ID format."""
        invalid_ids = [
            "h-123",
            "h-1234567890abcdef",
            "h-1234567890abcdef01",
            "op-1234567890abcdef0",
            "1234567890abcdef0",
        ]

        for host_id in invalid_ids:
            valid, message = validate_host_id(host_id)
            assert valid is False, f"Host ID {host_id} should be invalid"
            assert "Invalid Host ID format" in message
