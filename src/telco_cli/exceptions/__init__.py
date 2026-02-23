# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Exception handling for the Telco CLI."""

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode

# Export only what's needed
__all__ = ["TelcoCLIException", "ErrorCode"]
