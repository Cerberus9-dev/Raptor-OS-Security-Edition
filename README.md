# Raptor OS Security Edition

<p align="center">
  <img src="https://raw.githubusercontent.com/Cerberus9-dev/Raptor-OS-Security-Edition/main/assets/raptor-logo.png" alt="Raptor OS Security Edition" width="200" />
</p>

**Raptor OS Security Edition** is a specialized, security-first Linux distribution built on **Debian 12 (Bookworm)**. Designed for cybersecurity professionals, penetration testers, network analysts, and privacy advocates, Raptor OS combines enterprise-grade auditing tools with an intuitive, dynamic system hardening architecture.

---

## Table of Contents
- [Base Architecture](#-base-architecture)
- [Key Features](#-key-features)
- [Raptor Security Modes](#-raptor-security-modes)
- [Control Center & CLI Utilities](#-control-center--cli-utilities)
- [Included Tooling Directory](#-included-tooling-directory)
- [System Requirements](#-system-requirements)
- [Building the ISO](#-building-the-iso)
- [Flashing & Live Booting](#-flashing--live-booting)
- [Security & Reversibility Design](#-security--reversibility-design)

---

## Base Architecture

Raptor OS Security Edition avoids bloat while providing broad hardware compatibility out of the box:

* **Base Distribution:** Debian 12 (Bookworm) `amd64`
* **Desktop Environment:** Lightweight, modular XFCE 4.18 with custom tactical GTK styling
* **Init System:** `systemd` (with anti-sysvinit package pinning enforced)
* **Boot Compatibility:** Hybrid ISO supporting legacy BIOS (ISOLINUX) and UEFI (GRUB2) with Secure Boot compatibility
* **Firewall Backend:** Modern `nftables` architecture replacing legacy `iptables`
* **Installer:** Calamares graphical installer for permanent disk installation

---

## Key Features

* **Raptor Control Center:** Native GTK dashboard providing one-click control over security modes, firewall behavior, and emergency network state.
* **Triple Security Profiles:** Switch operational posture dynamically between `SECURE`, `HARDENED`, and `LOCKDOWN`.
* **Hardware-Level Network Killswitch:** Cut all physical and virtual interfaces instantly with zero configuration drift.
* **Categorized Menu Structure:** Fully compliant XDG menu schema organizing security tools by operational phase (Recon, Analysis, Web, Exploitation, Forensics).
* **Live USB Ready:** Full live boot support with options for persistent storage overlays.

---

## Raptor Security Modes

Raptor OS provides three strict operational modes configured via `/usr/local/bin/raptor-security`:

| Mode | Inbound Network | Outbound Network | Kernel / Memory Hardening |
| :--- | :--- | :--- | :--- |
| **SECURE** | Drop all unsolicited traffic | Allow standard outbound connections | Standard Debian security defaults |
| **HARDENED** | Drop all unsolicited traffic | Restrict to HTTP, HTTPS, & DNS (Ports 53, 80, 443) | Restrict kernel pointer visibility (`kptr_restrict=2`), enable strict reverse-path filtering (`rp_filter=1`) |
| **LOCKDOWN** | Drop all traffic | Drop all traffic (Loopback `lo` allowed only) | Maximum memory & system restrictions enabled |

---

## 🎛️ Control Center & CLI Utilities

### Graphical Interface
Launch the dashboard via the application menu under **System → Raptor Security Control Center** or run:
```bash
raptor-control-center
