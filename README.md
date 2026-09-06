# Raptor OS

Raptor OS is a specialized, privacy-focused Linux security distribution based on Debian 12 (Bookworm) and built around the XFCE desktop environment. Designed in the spirit of Kodachi, Raptor OS integrates routed anonymity, strict memory protection, and dynamic operational profiles directly into a lightweight live environment.

> **Development Status:** Raptor OS is currently in active pre-release development. Official raw `.iso` images are generated automatically via GitHub Actions pipelines and will be made available under [Releases](../../releases) upon initial tagged release (`v1.0.0`).

---

## Core Security Architecture

* **Raptor Security Center:** Custom GTK4/libadwaita (`python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`) Kodachi-style dashboard with live system (CPU/RAM/disk/uptime), network (interfaces/DNS/public-IP-through-Tor), and security status, plus profile toggles.
* **Routed Anonymity & DNS:** Pre-configured `tor` SOCKS5 routing for `librewolf`, paired with `stubby` (DNS-over-TLS via `dnsstub0`) for encrypted DNS lookup protection.
* **Firewall & Network Lockdown:** Centralized `nftables` policies with quick-toggle `rfkill` hardware/software killswitch scripts.
* **Anti-Forensics & Hardening:** Automated RAM wiping routines via `secure-delete` (`sdmem`) and non-persistent session memory configurations.
* **Auditing & Pentest Toolchain:** Lean, verified Debian bookworm-safe toolset spanning recon, scanning, web, password, wireless, and forensics (`nmap`, `masscan`, `gobuster`, `sqlmap`, `hashcat`, `aircrack-ng`, `sleuthkit`, and more). Tools not packaged in Debian (Burp, Metasploit, WPScan, NetExec, radare2, theHarvester) are best-effort installed at build time by `0300 raptor thirdparty tools.hook.chroot`.

---

## Operational Profiles

Raptor OS features three built-in operational modes managed by the Raptor Security Center:

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
