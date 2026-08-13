# Changelog

## [Unreleased]

V1.0
### Changed
- Simplified repo structure: removed the separate `files/` source tree
  and `sync-files.sh` sync script (previously mirroring home edition's
  `files/scripts`/`files/system_files` convention). Everything now lives
  directly under `build/config/includes.chroot/` at its real destination
  path — one tree instead of two kept in sync by hand. live-build has no
  equivalent to BlueBuild's declarative `recipe.yml` source/destination
  mapping, so maintaining a mirrored source tree added a step without a
  real benefit at this project's size.
- Removed `raptor-crypto.list.chroot` (5 packages didn't justify a
  dedicated file; `seahorse` was also a GNOME app on a KDE Plasma
  system). Folded `hashid`/`openssl`/`kleopatra` into
  `raptor-pentest.list.chroot`.
- Deduplicated `exiftool` (forensics + osint) and `gdb` (development +
  reverse-engineering) across package lists.

### Added
- Repo scaffold: `live-build` skeleton (`build/`), `files/scripts/` +
  `files/system_files/` source layout, `sync-files.sh` mapping script
- Mode Manager — Secure/Hardened/Lockdown via real nftables rulesets,
  sysctl overrides, and systemd service posture per mode; `GetStatus()`
  re-verifies live system state on every call
- Security Center — GTK4/libadwaita dashboard, mode switcher, Emergency
  Shutdown confirmation dialog
- Emergency Shutdown Manager — session teardown + poweroff, honest about
  swap-erasure limitations
- Persistence Manager — status checks + `CreatePersistence` (LUKS + ext4
  on a user-selected removable device)
- VPN Manager — NetworkManager wrapper for OpenVPN/WireGuard
- Tor Manager — start/stop, SOCKS-liveness check, `NewIdentity()` via
  raw control-port client
- Network Protection Manager — interfaces, IP, DNS, IPv6 state, MAC
  randomization, open-port enumeration
- Best-effort install hook for tools absent from Debian's repos
  (Burp Suite, Metasploit, WPScan, NetExec)

### Known issues
- No component has been build-tested (`lb build` never run) or booted on
  real hardware — see `docs/ARCHITECTURE.md`'s pre-build checklist
- D-Bus authorization is a `raptor-admin` group check everywhere, not
  polkit
- Software Center, guided workflows, and several spec-listed managers
  (Firewall as distinct from Mode Manager, Privacy, Security Monitoring,
  Tool Launcher) not started

Full detail on all of the above: `docs/ARCHITECTURE.md`.
