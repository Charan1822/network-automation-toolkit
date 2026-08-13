
 **🔗 [Live demo](https://charan1822.github.io/network-automation-toolkit/)**
 
 # Network Automation & Compliance Toolkit

A Python + Ansible toolkit that automates the config backup, drift detection,
and compliance auditing tasks network engineers normally do by hand — the
same class of work I did manually across 250+ devices at Spectrum and BSNL,
now scripted and version-controlled.

## What it does

- **`backup.py`** — Connects to network devices (Cisco IOS / MikroTik) over
  SSH via [Netmiko](https://github.com/ktbyers/netmiko), pulls the running
  config, and commits a timestamped copy to Git so every change is versioned
  and recoverable.
- **`drift.py`** — Diffs the latest backup against a "golden config" baseline
  per device role and reports exactly what changed (added/removed/modified
  lines) — catches unauthorized or undocumented changes before they cause
  an incident.
- **`compliance.py`** — Runs a rule-based audit against configs (e.g. "no
  Telnet enabled," "SNMP community string isn't default," "VLAN 1 not used
  for user traffic") and outputs a pass/fail report per device.
- **`playbooks/vlan_automation.yml`** — Ansible playbook that pushes VLAN /
  interface changes to every device in the inventory at once, with a
  `--check` dry-run mode.

## Mock mode — run it with zero hardware

Every script supports `--mock`, which uses the sample configs in
`mock_data/` instead of connecting to real devices. This means anyone
(including you, right now) can clone this repo and see it work immediately,
without a lab.

```bash
git clone <this-repo>
cd network-automation-toolkit
pip install -r requirements.txt

python src/backup.py --mock
python src/drift.py --mock
python src/compliance.py --mock
```

## Running against real devices / a virtual lab

Point `inventory.yaml` at real device IPs (a [Containerlab](https://containerlab.dev/)
topology with Cisco IOL / MikroTik CHR images works well for this) and drop
`--mock`:

```bash
python src/backup.py --inventory inventory.yaml
```

Credentials are read from environment variables (`NET_USER`, `NET_PASS`) —
never hardcoded.

## Why I built this

At Spectrum I supported 150+ rack-connected devices and manually validated
config changes, VLAN mappings, and circuit turn-ups. This toolkit is that
same workflow — backup, diff, audit — turned into something repeatable,
version-controlled, and testable, which is how larger environments actually
scale that work.

## Roadmap

- [ ] NAPALM-based multi-vendor support (Juniper, Arista)
- [ ] GitHub Actions workflow to run compliance checks on every PR to `golden_configs/`
- [ ] Slack webhook alert on drift detection

      
