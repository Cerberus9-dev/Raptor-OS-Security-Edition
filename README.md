# Raptor Security

A portable Debian Live-based security, penetration-testing, networking,
privacy, and development workstation this is the security-focused edition of
the Raptor OS family. Separate build/pipeline from
[Raptor-OS](https://github.com/Cerberus9-dev/Raptor-OS) (Bazzite-based);
see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for why and for current
project status.

**Status:** seven D-Bus daemons (Mode Manager, Security Center, Emergency
Shutdown, Persistence, VPN, Tor, Network Protection Managers) implemented
and wired into a live-build skeleton. Zero real builds run yet — see
`docs/ARCHITECTURE.md`'s pre-build checklist before treating any of it as
verified beyond syntax-valid Python/shell and well-formed D-Bus policy
XML. Most of the full spec (Software Center, guided workflows,
Privacy/Security Monitoring managers, forensics/RE/OSINT tool
integration beyond package lists) is not built yet.

## Repo layout

Everything lives directly under `build/config/`, at the paths live-build
requires — no separate source tree, no sync/generation step. Edit files
in place.

- `build/auto/config` — the `lb config` invocation (architecture,
  distribution, bootloader, ISO metadata).
- `build/config/package-lists/*.list.chroot` — one file per tool
  category (base, desktop, pentest, networking, forensics,
  reverse-engineering, osint, development, sysadmin).
- `build/config/hooks/live/*.hook.chroot` — scripts that run inside the
  chroot during the build: installing the D-Bus daemons as real system
  services (`0200-...`), and a best-effort installer for tools not in
  Debian's repos (`0300-...`).
- `build/config/includes.chroot/` — the actual files that end up in the
  built image, at their real destination paths (e.g.
  `usr/lib/raptor-security/raptor_mode_managerd.py` becomes
  `/usr/lib/raptor-security/raptor_mode_managerd.py` on the live system).
  This is where every daemon's source, every systemd unit, every D-Bus
  policy, and the per-mode firewall/sysctl/service configs actually live.
- `docs/ARCHITECTURE.md` — design decisions, D-Bus interface reference
  for all seven components, and the pre-build checklist.

**On an earlier version of this repo:** there was a separate top-level
`files/` directory (mirroring [Raptor-OS](https://github.com/Cerberus9-dev/Raptor-OS)
(home edition)'s `files/scripts` + `files/system_files` convention) plus
a `sync-files.sh` script to copy it into `includes.chroot/` before every
build. That's been removed — home edition's BlueBuild can point its
build system at an arbitrary `files/` directory via `recipe.yml`'s
declarative source/destination list; live-build has no equivalent, so
keeping two directories in sync by hand added a "don't forget to run the
sync script" step without a real benefit at this project's size. One
tree, at the paths live-build actually requires, is simpler.

## Building

```sh
cd build
sudo lb clean --purge
./auto/config
sudo lb build
```

Requires `live-build`, `debootstrap`, and enough disk (Debian Live builds
typically need 15-20+ GB free) and network to Debian's archive. Not yet
validated in CI or locally by a maintainer — see
`docs/ARCHITECTURE.md`'s pre-build checklist before your first attempt.
