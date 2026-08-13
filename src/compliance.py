#!/usr/bin/env python3
"""
compliance.py — Run a set of security/best-practice rules against each
device's config and report pass/fail per rule.

Usage:
    python src/compliance.py --mock
    python src/compliance.py --inventory inventory.yaml
"""
import argparse
import re
from pathlib import Path

from devices import load_inventory, get_config
from rich.console import Console
from rich.table import Table

REPO_ROOT = Path(__file__).resolve().parent.parent
console = Console()


def rule_no_telnet(config: str) -> tuple[bool, str]:
    """Telnet should not be an allowed transport on VTY lines."""
    if re.search(r"transport input.*\btelnet\b", config, re.IGNORECASE):
        return False, "Telnet is enabled as a VTY transport input"
    if re.search(r"disabled=no", config) and "telnet" in config.lower():
        # crude RouterOS check: '/ip service' 'set telnet disabled=no'
        if re.search(r"set telnet disabled=no", config):
            return False, "Telnet service is enabled (RouterOS)"
    return True, "Telnet disabled"


def rule_no_default_snmp_community(config: str) -> tuple[bool, str]:
    """SNMP community string should not be the default 'public'/'private'."""
    match = re.search(r"snmp-server community (\S+)", config)
    if match and match.group(1) in ("public", "private"):
        return False, f"SNMP community string is default ('{match.group(1)}')"
    match_ros = re.search(r"set \[ find default=yes \] name=(\S+)", config)
    if match_ros and match_ros.group(1) in ("public", "private"):
        return False, f"SNMP community string is default ('{match_ros.group(1)}')"
    return True, "SNMP community string is not a known default"

def rule_password_encryption(config: str) -> tuple[bool, str]:
    """Cisco: 'service password-encryption' should be present (skip for RouterOS)."""
    if "hostname" not in config:
        return True, "N/A (non-IOS device)"
    if "service password-encryption" in config:
        return True, "Password encryption service enabled"
    return False, "'service password-encryption' missing"


RULES = [
    ("No Telnet", rule_no_telnet),
    ("Non-default SNMP community", rule_no_default_snmp_community),
    ("Password encryption enabled", rule_password_encryption),
]


def main():
    parser = argparse.ArgumentParser(description="Audit device configs against compliance rules.")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--inventory", default=str(REPO_ROOT / "inventory.yaml"))
    args = parser.parse_args()

    devices = load_inventory(args.inventory)

    table = Table(title="Compliance Audit Report")
    table.add_column("Device")
    table.add_column("Rule")
    table.add_column("Result")
    table.add_column("Detail")

    fail_count = 0
    for device in devices:
        config = get_config(device, mock=args.mock)
        for rule_name, rule_fn in RULES:
            passed, detail = rule_fn(config)
            result = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
            if not passed:
                fail_count += 1
            table.add_row(device["name"], rule_name, result, detail)

    console.print(table)
    console.print(
        f"\n[bold]{fail_count} failing check(s)[/bold] across {len(devices)} device(s)."
        if fail_count else "\n[bold green]All devices pass all compliance checks.[/bold green]"
    )


if __name__ == "__main__":
    main()
