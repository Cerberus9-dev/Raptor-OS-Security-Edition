# Changelog

All notable changes to Raptor OS Security Edition will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2026-08-19

### Added
- **Raptor Control Center:** Introduced a Kodachi-inspired graphical dashboard. All core security features are now fully integrated into a one-click GUI, eliminating the need for terminal commands.
- **One-Click Posture Engine:** Added dashboard widgets to hot-swap between Secure, Hardened, and Lockdown modes seamlessly.
- **GUI Panic Button:** Implemented a visual Emergency Killswitch within the dashboard for immediate termination of all network hardware.

### Changed
- **Backend Infrastructure:** Overhauled all core system bash scripts to act as a silent, high-speed backend for the new Control Center.
- **Firewall Architecture:** Migrated from legacy `iptables` to `nftables` to support instant, atomic ruleset switching when users click a new profile in the dashboard.
- **Menu Hierarchy:** Reorganized the application menus to logically group security tools by operational phase (Reconnaissance, Web Security, Forensics) for faster navigation.

### Removed
- Deprecated end-user CLI requirements for security modes; all features are now GUI-driven.
- Removed legacy systemd-sysv dependencies to enforce a modern, faster init system.
- Stripped out unnecessary background daemons that exposed unneeded local ports.
