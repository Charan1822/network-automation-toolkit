#!/usr/bin/env python3
"""
backup.py — Pull running configs from all devices in inventory.yaml and
save timestamped, version-controlled copies under backups/<device>/.

Usage:
    python src/backup.py --mock
    python src/backup.py --inventory inventory.yaml
"""
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

from devices import load_inventory, get_config
from rich.console import Console
from rich.table import Table

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKUPS_DIR = REPO_ROOT / "backups"

console = Console()


def backup_device(device: dict, mock: bool) -> Path:
    config_text = get_config(device, mock=mock)

    device_dir = BACKUPS_DIR / device["name"]
    device_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = device_dir / f"{timestamp}.cfg"
    out_path.write_text(config_text)

    # Also write/overwrite a 'latest.cfg' for easy diffing by drift.py
    latest_path = device_dir / "latest.cfg"
    latest_path.write_text(config_text)

    return out_path


def git_commit_backups(mock: bool):
    """Best-effort git commit of the backups/ directory. Safe to fail (e.g. no git repo yet)."""
    try:
        subprocess.run(["git", "add", "backups/"], cwd=REPO_ROOT, check=True, capture_output=True)
        msg = f"Backup run ({'mock' if mock else 'live'}) at {datetime.now().isoformat(timespec='seconds')}"
        subprocess.run(["git", "commit", "-m", msg], cwd=REPO_ROOT, check=True, capture_output=True)
        console.print(f"[green]Committed backups to git:[/green] {msg}")
    except subprocess.CalledProcessError:
        console.print("[yellow]Skipped git commit (no repo, no changes, or git not configured).[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="Back up device configs.")
    parser.add_argument("--mock", action="store_true", help="Use mock_data/ instead of real devices")
    parser.add_argument("--inventory", default=str(REPO_ROOT / "inventory.yaml"))
    parser.add_argument("--no-git", action="store_true", help="Skip git commit step")
    args = parser.parse_args()

    devices = load_inventory(args.inventory)

    table = Table(title="Config Backup Results")
    table.add_column("Device")
    table.add_column("Role")
    table.add_column("Status")
    table.add_column("Saved To")

    for device in devices:
        try:
            out_path = backup_device(device, mock=args.mock)
            table.add_row(device["name"], device["role"], "[green]OK[/green]", str(out_path.relative_to(REPO_ROOT)))
        except Exception as e:
            table.add_row(device["name"], device["role"], f"[red]FAILED[/red]", str(e))

    console.print(table)

    if not args.no_git:
        git_commit_backups(mock=args.mock)


if __name__ == "__main__":
    main()
