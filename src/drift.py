#!/usr/bin/env python3
"""
drift.py — Compare each device's latest backup against its role's golden
config baseline and report exactly what changed.

Usage:
    python src/drift.py --mock
    python src/drift.py --inventory inventory.yaml
"""
import argparse
import difflib
from pathlib import Path

from devices import load_inventory, get_config
from rich.console import Console

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO_ROOT / "golden_configs"

console = Console()

# Maps a device 'role' (from inventory.yaml) to its golden config filename
ROLE_TO_GOLDEN = {
    "core_switch": "core_switch_golden.cfg",
    "access_switch": "access_switch_golden.cfg",
    "edge_router": "edge_router_golden.cfg",
}


def load_golden(role: str) -> str | None:
    filename = ROLE_TO_GOLDEN.get(role)
    if not filename:
        return None
    golden_path = GOLDEN_DIR / filename
    if not golden_path.exists():
        return None
    return golden_path.read_text()


def diff_configs(golden: str, current: str, device_name: str) -> list[str]:
    diff = difflib.unified_diff(
        golden.splitlines(),
        current.splitlines(),
        fromfile=f"golden/{device_name}",
        tofile=f"current/{device_name}",
        lineterm="",
    )
    return list(diff)


def main():
    parser = argparse.ArgumentParser(description="Detect config drift vs golden baseline.")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--inventory", default=str(REPO_ROOT / "inventory.yaml"))
    args = parser.parse_args()

    devices = load_inventory(args.inventory)
    any_drift = False

    for device in devices:
        golden = load_golden(device["role"])
        if golden is None:
            console.print(f"[yellow]No golden config defined for role '{device['role']}' ({device['name']}) — skipping[/yellow]")
            continue

        current = get_config(device, mock=args.mock)
        diff_lines = diff_configs(golden, current, device["name"])

        if not diff_lines:
            console.print(f"[green]✔ {device['name']}: no drift detected[/green]")
            continue

        any_drift = True
        console.print(f"[red]✘ {device['name']}: DRIFT DETECTED[/red]")
        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                console.print(f"  [green]{line}[/green]")
            elif line.startswith("-") and not line.startswith("---"):
                console.print(f"  [red]{line}[/red]")
            else:
                console.print(f"  [dim]{line}[/dim]")

    if any_drift:
        console.print("\n[bold red]Drift found on one or more devices.[/bold red]")
    else:
        console.print("\n[bold green]All devices match their golden baseline.[/bold green]")


if __name__ == "__main__":
    main()
