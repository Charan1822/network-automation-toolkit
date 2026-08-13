"""
Shared helpers for loading device inventory and fetching configs,
either from real devices (Netmiko) or mock_data/ (for --mock runs).
"""
import os
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MOCK_DATA_DIR = REPO_ROOT / "mock_data"


def load_inventory(inventory_path: str) -> list[dict]:
    with open(inventory_path) as f:
        data = yaml.safe_load(f)
    return data["devices"]


def get_mock_config(device_name: str) -> str:
    """Read a device's config from mock_data/<name>_running.cfg."""
    mock_file = MOCK_DATA_DIR / f"{device_name}_running.cfg"
    if not mock_file.exists():
        raise FileNotFoundError(
            f"No mock config found for '{device_name}' at {mock_file}"
        )
    return mock_file.read_text()


def get_live_config(device: dict) -> str:
    """
    Pull the running config from a real device over SSH using Netmiko.
    Requires NET_USER / NET_PASS environment variables.
    """
    from netmiko import ConnectHandler  # imported lazily so --mock needs no deps

    username = os.environ.get("NET_USER")
    password = os.environ.get("NET_PASS")
    if not username or not password:
        raise EnvironmentError(
            "Set NET_USER and NET_PASS environment variables for live device access."
        )

    conn_params = {
        "device_type": device["device_type"],
        "host": device["host"],
        "username": username,
        "password": password,
    }

    with ConnectHandler(**conn_params) as conn:
        if device["device_type"] == "mikrotik_routeros":
            return conn.send_command("/export")
        return conn.send_command("show running-config")


def get_config(device: dict, mock: bool) -> str:
    return get_mock_config(device["name"]) if mock else get_live_config(device)
