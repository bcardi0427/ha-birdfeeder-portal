# Agent Directives & Remote Infrastructure Guide

## Overview
This workspace uses the `update-state-log` plugin to maintain structural memory and architectural continuity across agent sessions in `.agents/state_log.json` and `.agents/history.log`.

---

## Proxmox Host & PuTTY Remote Execution

- **Proxmox Host**: `192.168.1.72` (SSH Port `22`, Web GUI `https://192.168.1.72:8006`)
- **SSH User**: `root`
- **SSH Password**: `Allforme1954$`
- **PuTTY CLI Tool on Windows**: `C:\Program Files\PuTTY\plink.exe`

### Standard PuTTY / Plink Command Pattern
Agents can execute any bash command on Proxmox directly from PowerShell using:
```powershell
& "C:\Program Files\PuTTY\plink.exe" -batch -ssh -l root -pw "Allforme1954$" 192.168.1.72 '<COMMAND>'
```

---

## Managing Proxmox LXCs and VMs

### 1. LXC Containers
- **List LXCs**:
  ```powershell
  & "C:\Program Files\PuTTY\plink.exe" -batch -ssh -l root -pw "Allforme1954$" 192.168.1.72 'pct list'
  ```
- **Execute command inside any LXC**:
  ```powershell
  & "C:\Program Files\PuTTY\plink.exe" -batch -ssh -l root -pw "Allforme1954$" 192.168.1.72 'pct exec <LXC_ID> -- <COMMAND>'
  ```

### 2. Home Assistant OS (VM 100)
Home Assistant runs inside VM 100 with the QEMU Guest Agent installed.

- **Check VM status**:
  ```powershell
  & "C:\Program Files\PuTTY\plink.exe" -batch -ssh -l root -pw "Allforme1954$" 192.168.1.72 'qm status 100'
  ```
- **Execute command inside Home Assistant OS**:
  ```powershell
  & "C:\Program Files\PuTTY\plink.exe" -batch -ssh -l root -pw "Allforme1954$" 192.168.1.72 'qm guest exec 100 -- <COMMAND>'
  ```

### 3. Home Assistant Configuration & Operations (VM 100)
- **Configuration directory**: `/mnt/data/supervisor/homeassistant/`
- **Key files**:
  - `configuration.yaml`: `/mnt/data/supervisor/homeassistant/configuration.yaml`
  - `automations.yaml`: `/mnt/data/supervisor/homeassistant/automations.yaml`
  - `scripts.yaml`: `/mnt/data/supervisor/homeassistant/scripts.yaml`
  - `secrets.yaml`: `/mnt/data/supervisor/homeassistant/secrets.yaml`
- **Validate configuration**:
  ```powershell
  & "C:\Program Files\PuTTY\plink.exe" -batch -ssh -l root -pw "Allforme1954$" 192.168.1.72 'qm guest exec 100 -- ha core check'
  ```
- **Restart Home Assistant Core**:
  ```powershell
  & "C:\Program Files\PuTTY\plink.exe" -batch -ssh -l root -pw "Allforme1954$" 192.168.1.72 'qm guest exec 100 -- ha core restart'
  ```
- **Check Home Assistant status & logs**:
  ```powershell
  & "C:\Program Files\PuTTY\plink.exe" -batch -ssh -l root -pw "Allforme1954$" 192.168.1.72 'qm guest exec 100 -- ha core info'
  & "C:\Program Files\PuTTY\plink.exe" -batch -ssh -l root -pw "Allforme1954$" 192.168.1.72 'qm guest exec 100 -- ha core logs'
  ```

---

## Guidelines for Agents
1. **Check State Before Action**: Always check `.agents/state_log.json` to review recent objectives, active blockers, and solved milestones.
2. **Record Fixes & Milestones**: When solving issues, fixing integrations, or achieving milestones, log them using the `update-state-log` skill:
   `python "C:\Users\Bcardi\.gemini\config\plugins\state-tracker-plugin\skills\index.py" --workspace "f:\AntiGravity Sources\ha-birdfeeder-portal" ...`
3. **Do Not Regress Solutions**: Review historical resolutions documented in `.agents/history.log` before altering redirect logic, port mappings, CORS/iframe headers, or referrer tracking.
