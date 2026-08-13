# Raptor Security — Architecture

## Pre-build checklist

16 gaps have accumulated in "Known gaps" below across seven components.
Rather than working through them in the order they were discovered,
here's the same list triaged by what actually stops a first build/boot
from working versus what's fine to leave for later. Check these in order.

### Tier 1 — will likely break `lb build` itself, fix first

**Resolved this session, via web search against packages.debian.org**
(no longer speculative — I don't have direct Debian mirror access from
this sandbox for `apt`, but the package tracker website itself was
reachable and gave a direct answer for each):

- [x] `python3-pydbus` — **confirmed present** in Debian bookworm
      (0.6.0-5, stable). All seven daemons depending on it are safe.
- [x] `burpsuite`, `metasploit-framework`, `wpscan`, `crackmapexec` —
      **confirmed absent** from Debian's repos (every install guide found
      uses a curl-pipe installer, gem install, or source build — not
      `apt install`). Removed from `raptor-pentest.list.chroot` so the
      build won't fail on these names. A best-effort install hook now
      exists for all four —
      `build/config/hooks/live/0300-raptor-thirdparty-tools.hook.chroot`
      — but none of its four installs have been executed even once; it's
      written from each tool's documented install method, not tested.
      That hook's own log output on a real build is the actual
      verification step, not this line.

Everything else that was Tier 1 is now handled. No open Tier 1 items.


### Tier 2 — build will likely succeed, but verify these on first real boot

Nothing here stops `lb build`, but each is an unverified assumption a
component's correctness depends on:

- [ ] Tor: does `/run/tor/control.authcookie` actually exist after the
      0200 hook's torrc append + `systemctl start tor@default`? Does
      `NewIdentity()` succeed against a real tor instance? (gap #13)
- [ ] Network Protection: does `resolvectl status` return anything on a
      stock NetworkManager setup, or does it silently fall through to the
      `/etc/resolv.conf` fallback every time? Either is fine, but confirm
      which path is actually live. (gap #15)
- [ ] Network Protection: does `ethtool -P <device>` output parse
      correctly for MAC randomization detection on real hardware/VM NICs?
- [ ] Firstboot: does live-config actually create a user named exactly
      `raptor` (matching `username=raptor` in `build/auto/config`'s
      `--bootappend-live`, and matching the hardcoded default in
      `raptor-firstboot.sh` and `raptor_security_center.py`'s emergency
      shutdown call)? If live-config's actual behavior differs, group
      membership and Emergency Shutdown both silently fail.
- [ ] Mode Manager: does `_check_kill_switch()`'s JSON-scoped output-chain
      check (fixed this session, see below) actually match the real
      `nft -j list table` schema on the installed nftables version? Fixed
      from memory of the schema, not validated against a real `nft`
      binary.
- [ ] `0300-raptor-thirdparty-tools.hook.chroot`: check `/var/log/raptor-
      thirdparty-install.log` after first boot — entirely unexecuted.
      Also: two of its four installs (`wpscan`, `netexec`) pull in
      `ruby`/`pipx` and build dependencies via `apt-get install` *inside
      the hook* rather than a package list, inconsistent with how every
      other package here is declared — works, but worth moving into
      `raptor-pentest.list.chroot` for consistency once confirmed working.

**Already fixed while writing this checklist** (not deferred — these were
real bugs, not accuracy nuances): `_check_firewall()` and
`_check_kill_switch()` in Mode Manager were passing `"inet raptor_security"`
as a single subprocess argv element instead of two separate tokens —
`subprocess.run` doesn't shell-split strings, so `nft` would have failed
to parse the table reference and both checks would have permanently
returned "unverified"/"unknown" regardless of actual firewall state.
Separately, `_check_kill_switch()`'s original substring check
(`"policy drop" in out`) would have reported Secure mode's kill switch as
"armed" — Secure's `forward` chain is also `policy drop` by design, so a
whole-table substring match couldn't distinguish it from Lockdown's real
`output`-chain kill switch. Fixed to a JSON-scoped check against the
output chain specifically. **This is exactly the class of bug this
checklist exists to catch before a build.** Re-audited every other
daemon's module-level constants for the same "space-containing string
later split as one argv element" pattern — none found (`RAPTOR_NFT_TABLE`
was the only one). That clears this specific pattern, not every possible
subprocess bug in every daemon.

### Tier 3 — safe to defer past a first working build

Real gaps, but none of them block getting a bootable, functionally
correct-enough image to test the Tier 1/2 items above:

- [ ] D-Bus authorization is a `raptor-admin` group check everywhere, not
      polkit (gap #2)
- [ ] `CreatePersistence`'s passphrase travels as a plain D-Bus argument
      (gap #8)
- [ ] VPN Manager's real interface name isn't pushed into Lockdown's
      kill-switch allowlist dynamically (gap #10)
- [ ] Network Protection's `SetIPv6Enabled` can silently fight Lockdown's
      IPv6 sysctl (gap #14)
- [ ] Hardened mode's `ptrace_scope=1` vs. the RE toolset — needs a
      product decision, not a bug fix (gap #4)
- [ ] Emergency Shutdown's swap-erasure limitation — needs a product
      decision (disable swap entirely?) not a script change (gap #7)
- [ ] No GUI wired to Persistence/VPN/Tor/Network Protection Managers yet
      (gaps #9, #11, #12, #16) — Security Center only surfaces Mode
      Manager's data right now
- [ ] Software Center, guided workflows (spec sections 21-22) — not
      started (gap #6)



Early scaffold. What's real and working end-to-end right now:

- `live-build` config skeleton (`build/`) — not yet build-tested (see
  "Known gaps" below).
- Mode Manager daemon (`build/config/includes.chroot/usr/lib/raptor-security/raptor_mode_managerd.py`) —
  a real root D-Bus service that loads actual nftables rulesets, applies
  sysctl overrides, and starts/stops systemd units per mode, and reports
  GetStatus() from live system checks, not cached/assumed state.
- Three real nftables rulesets (Secure / Hardened / Lockdown) implementing
  genuinely different postures, including a real kill-switch in Lockdown.
- Security Center (`build/config/includes.chroot/usr/lib/raptor-security/raptor_security_center.py`) — a
  GTK4/libadwaita app that reads Mode Manager over D-Bus and renders only
  what it's told; it has no privileged code path of its own. Now also
  hosts the Emergency Shutdown confirmation dialog.
- **Emergency Shutdown Manager** (under `build/config/includes.chroot/`) — a
  separate root D-Bus daemon (deliberately not folded into Mode Manager —
  see spec section 27's module list) that terminates the session and
  powers off after explicit GUI confirmation. Honest about its actual
  guarantees: the live session's tmpfs overlay disappears on poweroff by
  construction, but swap (if ever active) is only deactivated, not
  cryptographically erased — `GetPersistenceInfo()` surfaces that to the
  GUI so the confirmation dialog doesn't overclaim.
- **Persistence Manager** (under `build/config/includes.chroot/`) — owns the
  Live-session-vs-persistent-storage distinction spec section 23
  requires, plus the capability neither Mode Manager nor Emergency
  Shutdown have: actually creating an encrypted persistence volume
  (`CreatePersistence`, LUKS + ext4 on a user-selected removable device,
  never the boot device). Read-only status/device-listing methods are
  world-readable; the destructive create call is `raptor-admin`-gated
  like everything else pending real polkit.
- **VPN Manager** (under `build/config/includes.chroot/`) — thin wrapper around
  NetworkManager (`nmcli`) rather than a reimplementation; handles
  OpenVPN/WireGuard profile listing, connect/disconnect, and importing
  `.ovpn`/WireGuard `.conf` files.
- **Tor Manager** (under `build/config/includes.chroot/`) — start/stop `tor@default`,
  SOCKS-port liveness check, and `NewIdentity()` via a raw control-port
  client (cookie auth, no third-party control library dependency).
  `GetStatus()` deliberately reports `circuit_status: "unknown"` rather
  than inferring it from service-active + port-listening — verifying an
  actual circuit is built needs either log-scraping or a live network
  call through the proxy, neither of which belongs in a fast status
  check, and guessing would violate section 26.
- **Network Protection Manager** (under `build/config/includes.chroot/`) —
  owns the dashboard's Network panel: interfaces, active connection, IPv4
  address, DNS servers, IPv6 state, MAC randomization, and open-port
  enumeration (`ss -tulnp`). Overlaps with Mode Manager's Lockdown IPv6
  sysctl — see the module docstring's coupling-gap note, same unresolved
  pattern as VPN Manager vs. the kill switch.

Everything else in the full spec (Software Center, guided workflows,
Emergency Shutdown, VPN/Tor/Privacy managers as distinct components,
System/Privacy dashboard panels, forensics/OSINT/RE tool integration
beyond package lists) is **not built yet**.

## Why this is a separate project from RaptorOS

RaptorOS (`Cerberus9-dev/Raptor-OS`) is a Bazzite-based (Fedora Atomic /
rpm-ostree) image built with BlueBuild. This spec requires a Debian
Live-based portable/amnesic USB image. Those are different base OSes and
different build toolchains with no shared pipeline — see the conversation
history for the full reasoning. Branding/design language should still
feel related; the build systems can't be merged.

## The one rule that shapes everything else

**Mode Manager is the only component allowed to change security-relevant
system state. Every other component only reads.**

This exists specifically to satisfy spec section 26 ("security indicators
must be real"). If two components could both flip firewall rules, or if
Security Center cached its last-known status instead of querying live,
"the dashboard says X" and "the system actually does X" could drift apart
silently. Keeping exactly one writer and having every status check re-verify
against the running system (not a config file, not a last-known value)
is what makes that structurally hard to get wrong, rather than a discipline
someone has to remember to maintain by hand.

Concretely: Security Center never calls `nft`, `sysctl`, or `systemctl`
directly, and never renders a dashboard tile that isn't backed by a
corresponding check in `ModeManager.build_status()`.

## D-Bus interfaces

```
Bus name:    org.raptor.ModeManager   (system bus)
Object path: /org/raptor/ModeManager
Interface:   org.raptor.ModeManager1

SetMode(s mode) -> b success     — restricted to `raptor-admin` group (TODO: polkit)
GetMode() -> s mode              — world-readable
GetStatus() -> a{sv} status      — world-readable
ModeChanged(s mode)              — signal
```

```
Bus name:    org.raptor.EmergencyShutdown   (system bus)
Object path: /org/raptor/EmergencyShutdown
Interface:   org.raptor.EmergencyShutdown1

GetPersistenceInfo() -> a{sv} info               — world-readable
TriggerEmergencyShutdown(s live_user, b confirmed) -> b accepted
                                                  — restricted to `raptor-admin` (TODO: polkit)
                                                  — confirmed=True is a safety rail, NOT a
                                                    substitute for the GUI's confirmation dialog
```

```
Bus name:    org.raptor.PersistenceManager   (system bus)
Object path: /org/raptor/PersistenceManager
Interface:   org.raptor.PersistenceManager1

GetStatus() -> a{sv} status                      — world-readable
ListCandidateDevices() -> aa{sv} devices         — world-readable, read-only
CreatePersistence(s device_path, s passphrase) -> b success
                                                  — restricted to `raptor-admin` (TODO: polkit)
                                                  — DESTRUCTIVE: wipes device_path entirely
```

```
Bus name:    org.raptor.VPNManager   (system bus)
Object path: /org/raptor/VPNManager
Interface:   org.raptor.VPNManager1

GetStatus() -> a{sv} status                      — world-readable
ListProfiles() -> aa{sv} profiles                — world-readable, read-only
Connect(s profile_name) -> b success             — restricted to `raptor-admin` (TODO: polkit;
                                                    also worth reconsidering whether Connect/
                                                    Disconnect need admin-gating at all — see the
                                                    note in this daemon's own .conf file)
Disconnect() -> b success                        — restricted to `raptor-admin`
ImportProfile(s file_path) -> b success          — restricted to `raptor-admin`
```

```
Bus name:    org.raptor.TorManager   (system bus)
Object path: /org/raptor/TorManager
Interface:   org.raptor.TorManager1

GetStatus() -> a{sv} status                      — world-readable
Start() -> b success                             — restricted to `raptor-admin`
Stop() -> b success                              — restricted to `raptor-admin`
NewIdentity() -> b success                       — restricted to `raptor-admin`;
                                                    requires torrc's ControlPort/
                                                    CookieAuthentication (installed by
                                                    the 0200 hook) — untested, see gap #13
```

```
Bus name:    org.raptor.NetworkProtectionManager   (system bus)
Object path: /org/raptor/NetworkProtectionManager
Interface:   org.raptor.NetworkProtectionManager1

GetStatus() -> a{sv} status                      — world-readable
ListOpenPorts() -> aa{sv} ports                  — world-readable, read-only
SetMACRandomization(b enabled) -> b success      — restricted to `raptor-admin`
SetIPv6Enabled(b enabled) -> b success           — restricted to `raptor-admin`;
                                                    can silently fight Lockdown's
                                                    own IPv6 sysctl, see gap #14
```

**Note on the three managers all checking persistence independently:**
Mode Manager and Emergency Shutdown each do their own `findmnt
/lib/live/mount/persistence` rather than calling Persistence Manager's
`GetStatus()`. That's duplication I left in deliberately rather than
making three root daemons depend on each other's startup order for a
single filesystem check — if persistence detection logic ever needs to
get smarter than "is this mount point present," THAT's the trigger to
consolidate, not before.

## Known gaps / explicit TODOs (not silently deferred, deliberately listed)

1. **`lb build` has not been run.** This sandbox can't do a multi-hour
   Debian Live build against Debian mirrors (only Ubuntu mirrors are
   network-reachable here). Package availability in `raptor-pentest.list.chroot`
   and `raptor-development.list.chroot` in particular needs a real dry run —
   several packages (burpsuite, metasploit-framework, VS Code/VSCodium) are
   flagged inline as likely not in stock Debian repos.
2. **D-Bus authorization is a group check, not polkit.** Flagged in
   `org.raptor.ModeManager.conf`. Fine for a scaffold, not for a release.
3. **`kill_switch_armed` check is coarse** — it looks for `"policy drop"`
   anywhere in the raptor table's output, not specifically verifying the
   VPN/Tor interface allowlist is correct. Good enough to distinguish
   Secure from Lockdown right now; not rigorous enough to trust blindly.
4. **Hardened mode's `ptrace_scope=1` conflicts with the Reverse
   Engineering toolset this same OS ships** (gdb attach). Flagged inline
   in `hardened.sysctl.conf`; needs a decision, not resolved here.
5. **Persistence Manager, VPN Manager, Tor Manager, Privacy Manager,
   Firewall Manager-as-distinct-from-Mode-Manager**: spec section 27 lists
   these as separate modular components. Right now Mode Manager does
   firewall+sysctl+services directly rather than delegating to child
   managers. That's fine at this scale; if/when VPN and Tor state need to
   be *driven* (not just read) by this system, split them out rather than
   letting Mode Manager grow into a god-object.
6. **Software Center, guided workflows (spec sections 21–22)** — not
   started.
7. **Emergency Shutdown's swap caveat is real, not just a comment** — if
   you care about swap ever holding sensitive data in a way that survives
   this flow, the actual fix is disabling swap for Raptor Security
   entirely (or requiring swap to live only inside encrypted persistence),
   not a more aggressive wipe command in the shutdown script. Worth a
   deliberate decision rather than tightening the script further.
8. **Persistence Manager's `CreatePersistence` passes the passphrase as a
   plain D-Bus method argument.** Flagged in its own docstring — this is
   the single biggest thing I'd fix before trusting this with a real
   passphrase: move to a polkit-mediated secret agent or an out-of-band
   FD-passing mechanism instead of a D-Bus string argument.
9. **No GUI wired to Persistence Manager yet.** Security Center still
   only shows Mode Manager's coarse persistence check; there's no "Set Up
   Persistence" flow using `ListCandidateDevices`/`CreatePersistence` yet.
10. **VPN Manager and Lockdown's kill switch aren't actually coupled.**
    `lockdown.nft` hardcodes `tun0`/`wg0` as trusted tunnel interfaces;
    VPN Manager reports the REAL interface a connection came up on via
    `GetStatus()` but doesn't push that into Mode Manager's nftables set.
    If NetworkManager ever names a tunnel something else, Lockdown would
    silently block legitimate VPN traffic rather than allow it. Documented
    in `raptor_vpn_managerd.py`'s module docstring with two possible fixes
    — not resolved here.
11. **No GUI wired to VPN Manager yet** either — same pattern as
    Persistence Manager above.
12. **No GUI wired to Tor Manager yet** either.
13. **Tor control-cookie path is unverified.** `COOKIE_PATH` in
    `raptor_tor_managerd.py` assumes `/run/tor/control.authcookie`, which
    is the common Debian `tor` package location but has moved across tor
    releases before. The torrc append in the 0200 hook enabling
    `ControlPort`/`CookieAuthentication` has also never been tested
    against a real running tor instance. First `lb build` + boot should
    specifically check `NewIdentity()` actually works, not just that the
    service starts.
14. **Network Protection Manager's `SetIPv6Enabled` and Mode Manager's
    Lockdown hardening can silently fight each other** — see the
    coupling-gap note in `raptor_network_protection_managerd.py`'s module
    docstring. Same shape of problem as gap #10 (VPN interfaces vs. kill
    switch): a mode-owned hardening setting and a general-purpose manager
    can both legitimately want to control the same knob, and nothing yet
    arbitrates between them.
15. **`_dns_servers()`'s resolvectl path is unverified** against a stock
    Debian NetworkManager setup — flagged inline; the `/etc/resolv.conf`
    fallback is what will actually carry this on an unconfigured system.
16. **No GUI wired to Network Protection Manager yet.**
17. **No `cosign.pub` equivalent.** Home edition ships a cosign public
    key for verifying its signed OCI image. That's a container-signing
    mechanism specific to BlueBuild's OCI output — it doesn't apply to an
    ISO the same way. The Debian Live convention would be GPG-signed
    checksums (a `SHA256SUMS`/`SHA256SUMS.gpg` published alongside each
    release). Deliberately not adding a placeholder key file for a
    signing pipeline that doesn't exist yet — that would look like real
    infrastructure and wouldn't be.
