# Changelog

All notable changes to the Raptor OS project will be documented in this file.

> **Note:** No stable ISO releases currently exist. The project is under initial framework construction.

---

## [Unreleased] - Initial System Blueprint

### Added
* **Base Architecture:** Configured Debian 12 (Bookworm) x86_64 `live-build` environment with XFCE desktop environment.
* **Control Center GUI:** Integrated initial Python/GTK3 `raptor-control-center` dashboard and helper scripts in `/usr/local/bin/`.
* **Security Toolchain:** Configured package manifests for security auditing (`nmap`, `wireshark`, `hashcat`, `aircrack-ng`), privacy (`librewolf`, `tor`, `dnscrypt-proxy`), and memory wiping (`secure-delete`).
* **Third-Party Repositories:** Configured automated key retrieval and repository indexing for LibreWolf (`librewolf.list.chroot`).
* **CI/CD Build Pipeline:** Created `.github/workflows/build-iso.yml` to automate ISO generation, validation, error artifact logging, and direct raw binary release publishing.
