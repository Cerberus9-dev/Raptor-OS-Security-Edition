# Changelog

## [Unreleased]

Nothing has shipped as a numbered release yet — no build has completed end-to-end. Everything below describes the current state of `main`.

### Added
- `live-build` skeleton (`build/`) targeting Debian bookworm, producing a USB-bootable hybrid ISO.
- Mode Manager — Secure/Hardened/Lockdown via real nftables rulesets, sysctl overrides, and systemd service posture per mode; `GetStatus()` re-verifies live system state on every call rather than trusting the last mode switch.
- Security Center — GTK4/libadwaita dashboard, mode switcher, Emergency Shutdown confirmation dialog.
- Emergency Shutdown Manager — session teardown + poweroff, honest about swap-erasure limitations rather than overclaiming what a tmpfs-backed Live session can guarantee.
- Persistence Manager — status checks + `CreatePersistence` (LUKS + ext4 on a user-selected removable device).
- VPN Manager — NetworkManager wrapper for OpenVPN/WireGuard.
- Tor Manager — start/stop, SOCKS-liveness check, `NewIdentity()` via a raw control-port client.
- Network Protection Manager — interfaces, IP, DNS, IPv6 state, MAC randomization, open-port enumeration.
- Best-effort install hook (`0300-raptor-thirdparty-tools.hook.chroot`) for tools absent from Debian's repos: Burp Suite, Metasploit, WPScan, NetExec, theHarvester, radare2 (via a transiently-enabled bookworm-backports source).
- `.github/workflows/build-iso.yml` and `update.yml` — CI-driven ISO builds via GitHub Actions.

### Changed
- Simplified repo structure: removed an earlier separate `files/` source tree and its `sync-files.sh` sync script (which mirrored home edition's `files/scripts`/`files/system_files` convention). `live-build` has no equivalent to BlueBuild's declarative `recipe.yml` source/destination mapping, so keeping a second directory in sync by hand added a step without a real benefit at this project's size — everything now lives directly under `build/config/includes.chroot/`, at the paths `live-build` itself requires.
- Removed `raptor-crypto.list.chroot` (5 packages didn't justify a dedicated file; `seahorse` was also a GNOME app on a KDE Plasma system). Folded `hashid`/`openssl`/`kleopatra` into `raptor-pentest.list.chroot`.
- Deduplicated `exiftool` (forensics + osint) and `gdb` (development + reverse-engineering) across package lists.
- Removed `docs/ARCHITECTURE.md` (internal design notes; had no effect on the build itself).

### Fixed
- **CI: wrong Debian security-repo path.** live-build's `lb_chroot_archives` hardcodes the pre-2023 `<dist>/updates` suite name for its security mirror lines instead of the current `<dist>-security` — confirmed by reading the actual installed script and reproduced against a real failed CI run (`404 Not Found` on `debian-security bookworm/updates`). Both workflows now patch this via `sed`, scoped only to lines referencing the security mirror variables (verified the `VOLATILE` mirror lines, which already used the correct format, are untouched).
- **CI: stale `Contents-<arch>.gz` index path.** Same live-build version also references the pre-reorg path for the package Contents index (used for kernel-image package selection); both workflows patch this too.
- **CI: 7 wrong/missing package names**, found via a real failed build run and corrected against actual Debian bookworm package data: `spectacle` → `kde-spectacle`; `ddrescue` → `gddrescue` (the package that provides the `ddrescue` command; plain `ddrescue` is a different, unrelated tool); `journalctl` removed (never a real package — it ships with `systemd`, already present); `klipper` removed (no installable bookworm package exists — Plasma's built-in clipboard plasmoid already covers this); `theharvester` and `radare2` moved from plain package lists into the best-effort third-party hook, since neither is a plain-`apt`-installable Debian package (theHarvester needs a Python venv from source; radare2 is only in `bookworm-backports`, not plain bookworm).
- **File tree: missing daemon files.** `raptor-emergency-shutdown.sh`, `raptor-firstboot.sh`, `raptor_tor_managerd.py`, `raptor_vpn_managerd.py`, and the `raptor-vpn-manager.service` unit had gone missing from `build/config/includes.chroot/` during early CI debugging, leaving VPN/Tor Manager's D-Bus policies referencing daemons that no longer existed. Restored.
- **File tree: stray/misplaced files.** Removed a corrupted duplicate filename, a misplaced duplicate service file, and a stray junk file. Moved `raptor-torrc-addition.conf` back to `etc/raptor-security/` from `etc/raptor-security/modes/`, where it didn't belong.
- **File tree: 5 package lists uploaded to the wrong folder**, landing in `build/config/hooks/live/` (which also deleted the previously-restored `0300-raptor-thirdparty-tools.hook.chroot` in the same pass) instead of `build/config/package-lists/`, leaving the real `package-lists/` copies stale with the un-fixed package names above. Moved to the correct location; `0300` hook restored.
- Two rounds of dead `docs/ARCHITECTURE.md` links in this file and `README.md`, after that file was intentionally deleted.

### Known Issues
- No component has been build-tested end-to-end (`lb build` has not yet completed successfully) or booted on real hardware.
- D-Bus authorization is a `raptor-admin` group check everywhere, not polkit.
- Software Center, guided workflows, and several spec-listed managers (Firewall as distinct from Mode Manager, Privacy, Security Monitoring, Tool Launcher) not started.
- `bulk_extractor` (forensics) has no Debian package and is not covered by the best-effort hook either — it requires a nontrivial C++ source build, deliberately not automated without someone reviewing its actual build steps first.
