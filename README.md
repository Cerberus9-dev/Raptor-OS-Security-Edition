# Raptor OS

Raptor OS is a specialized, privacy-focused Linux security distribution based on Debian 12 (Bookworm) and built around the XFCE desktop environment. Designed in the spirit of Kodachi, Raptor OS integrates routed anonymity, strict memory protection, and dynamic operational profiles directly into a lightweight live environment.

> **Development Status:** Raptor OS is currently in active pre-release development. Official raw `.iso` images are generated automatically via GitHub Actions pipelines and will be made available under [Releases](../../releases) upon initial tagged release (`v1.0.0`).

---

## Core Security Architecture

* **Raptor Control Center:** Custom GTK3 (`python3-gi`) management dashboard for real-time security posture monitoring, profile toggling, and anonymity controls.
* **Routed Anonymity & DNS:** Pre-configured `tor` SOCKS5 routing for `librewolf`, paired with `dnscrypt-proxy` and `resolvconf` for encrypted DNS lookup protection.
* **Firewall & Network Lockdown:** Centralized `nftables` policies with quick-toggle `rfkill` hardware/software killswitch scripts.
* **Anti-Forensics & Hardening:** Automated RAM wiping routines via `secure-delete` (`sdmem`) and non-persistent session memory configurations.
* **Auditing Toolchain:** Bundled with essential security, network analysis, and wireless auditing suites (`nmap`, `wireshark`, `aircrack-ng`, `hydra`, `john`, `hashcat`, `autopsy`).

---

## Operational Profiles

Raptor OS features three built-in operational modes managed by the Raptor Control Center:

| Profile | Description |
| :--- | :--- |
| **Security** | Standard mode with active firewall, encrypted DNS, and custom privacy browser profiles. |
| **Hardened** | Enforces full Tor network isolation, randomized MAC addresses, and strict packet filtering. |
| **Lockdown** | Immediate system isolation: cuts active network interfaces, purges volatile memory caches, and disables non-essential daemons. |

---

## Building the ISO

The ISO image is generated using Debian `live-build` within an isolated containerized environment.

### Automated CI/CD (GitHub Actions)
Building is fully automated via `.github/workflows/build-iso.yml`:
1. **Push/PR to `main`:** Triggers automatic code validation and builds a test ISO, uploaded as a pipeline artifact.
2. **Release Tag (`v*`):** Triggers a full build and uploads raw, uncompressed `.iso` and `.sha256` files directly to GitHub Releases.
