# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""VPN-related commands for TelcoCLI."""

from telco_cli.commands.vpn.create_vpn import CreateVPNCommand
from telco_cli.commands.vpn.list_vpn_certificates import ListVPNCertificatesCommand
from telco_cli.commands.vpn.revoke_vpn_certificate import RevokeVPNCertificateCommand

__all__ = [
    "CreateVPNCommand",
    "ListVPNCertificatesCommand",
    "RevokeVPNCertificateCommand",
]
