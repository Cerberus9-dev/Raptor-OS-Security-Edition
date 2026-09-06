# Changelog

All notable changes to the Raptor OS project will be documented in this file.

> **Note:** No stable ISO releases currently exist. The project is under initial framework construction.

---

## [Unreleased] - `main`

### Changed
* **Security Center Dashboard:** Replaced the GTK3 control center with a GTK4/libadwaita Kodachi-style dashboard (`raptor-security-center`) showing live system (CPU/RAM/disk/uptime), network (interfaces/DNS/public-IP-through-Tor), and security status alongside the three operational profiles.
* **Mode Manager Status:** Extended `raptor_mode_managerd.GetStatus()` with live system/network checks (CPU %, memory, disk, uptime, interfaces, DNS, public IP via Tor SOCKS).
* **Package List:** Curated a lean, verified Debian bookworm-safe pentest toolset spanning recon, scanning, web, password, wireless, and forensics; replaced `dnscrypt-proxy` (not in bookworm) with `stubby` and added `cryptsetup`/`gnome-disk-utility` for disk encryption (VeraCrypt is not packaged in Debian). Removed `veracrypt` and `burpsuite` from the apt list (handled via the third-party build hook).
* **Mode Config Files:** Added missing `secure/hardened/lockdown.{nft,sysctl.conf,services}` under `/etc/raptor-security/modes/` required by Mode Manager.
* **Daemon Wiring:** Fixed systemd `ExecStart` paths to run the actual Python daemons and enabled all Raptor D-Bus daemons + first-boot setup at build time; created the `raptor-admin` group.

---

## [Unreleased] - Initial System Blueprint

### Added
* **Base Architecture:** Configured Debian 12 (Bookworm) x86_64 `live-build` environment with XFCE desktop environment.
* **Control Center GUI:** Integrated initial Python/GTK3 `raptor-control-center` dashboard and helper scripts in `/usr/local/bin/`.
* **Security Toolchain:** Configured package manifests for security auditing (`nmap`, `wireshark`, `hashcat`, `aircrack-ng`), privacy (`librewolf`, `tor`, `dnscrypt-proxy`), and memory wiping (`secure-delete`).
* **Third-Party Repositories:** Configured automated key retrieval and repository indexing for LibreWolf (`librewolf.list.chroot`).
* **CI/CD Build Pipeline:** Created `.github/workflows/build-iso.yml` to automate ISO generation, validation, error artifact logging, and direct raw binary release publishing.
