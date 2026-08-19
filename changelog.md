# Changelog

All notable changes to Raptor OS Security Edition will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2026-08-19

### Added
- **Raptor Control Center:** Introduced a native graphical GUI dashboard for real-time monitoring of firewall rules and quick access to security toggles.
- **Dynamic Posture Engine:** Added the ability to hot-swap between Secure, Hardened, and Lockdown modes without dropping local sessions.
- **Hardware Killswitch:** Implemented `raptor-killswitch` for immediate emergency termination of all physical network hardware.

### Changed
- **Script Infrastructure:** Completed a massive, system-wide overhaul of all underlying bash scripts to improve execution speed, code readability, and stability under heavy loads.
- **Firewall Backend:** Migrated from legacy `iptables` to the modern `nftables` architecture for atomic ruleset flushing.
- **Menu Hierarchy:** Reorganized the XDG application menus to group security tools by operational phase (Reconnaissance, Web Security, Forensics, etc.) rather than alphabetical lists.

### Removed
- Removed legacy systemd-sysv dependencies to enforce modern init system architecture.
- Stripped out unnecessary background daemons that were exposing unneeded local ports.
