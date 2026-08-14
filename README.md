# Raptor Security
**Status: Pre-release — CI build pipeline in progress**

Custom OS based off Debian, designed to be a security and development workstation without being overly bloated or complicated. The Security Edition of the Raptor OS family — boots and runs entirely from USB, keeps the Live session amnesic by default, and treats persistence as something you opt into rather than something that just happens.

> **Heavy W.I.P — Feedback appreciated!**
> This **is** a Live USB OS — it boots and runs from the stick without touching your existing installation, and needs nothing installed to your internal drive unless you explicitly set up encrypted persistence. Seven core system daemons are implemented; no build has completed end-to-end yet.

---

## System Requirements

| | Minimum | Recommended |
|---|---|---|
| **CPU** | 64-bit x86_64, dual-core | Quad-core (e.g. Ryzen 3000 / Intel 8th gen or newer) — noticeably smoother if you're running VMs, containers, or compiling alongside your other tools |
| **RAM** | 4 GB (Live sessions keep filesystem writes in RAM by default, so this floor is a bit higher than an installed OS would need) | 8 GB (VMs/containers/hashcat-style workloads will want more) |
| **USB Drive** | 8 GB | 32 GB+ (room for encrypted persistence) |
| **Boot** | UEFI required | — |

---

## Installation

Build the ISO yourself (see **Building**, below), then flash it to a USB drive:

- **[Rufus](https://rufus.ie/en/)** — select **DD image mode** + **GPT** partition scheme
- **[Ventoy](https://www.ventoy.net)** — copy ISO to Ventoy USB, boot and select it
- **[balenaEtcher](https://etcher.balena.io/)** — straightforward drag-and-drop flashing

Boots directly into a Live KDE Plasma session. No installer, no first-boot setup wizard — the system is ready to use the moment it boots.

---

## Building

**Via GitHub Actions (recommended):** Actions tab → **Build Raptor OS Security ISO** → Run workflow. Builds on a GitHub-hosted runner and uploads the finished `.iso` plus its SHA-256 checksum as a downloadable artifact. No local setup required.

**Locally:**

```bash
cd build
sudo lb clean --purge
./auto/config
sudo lb build
```

Requires `live-build`, `debootstrap`, and enough disk (Debian Live builds typically need 15-20+ GB free) and network access to Debian's archive.

---

## What's Included

### Security & Networking

| Category | Tools |
|---|---|
| **Penetration Testing** | nmap, masscan, netdiscover, arp-scan, nikto, whatweb, sqlmap, gobuster, ffuf, hydra, john, hashcat, aircrack-ng |
| **Networking** | Wireshark, tshark, tcpdump, iperf3, macchanger, OpenVPN, WireGuard, Tor + torsocks, nyx |
| **Forensics** | Sleuth Kit, Autopsy, TestDisk, foremost, binwalk, exiftool, bulk-extractor, ddrescue, dc3dd |
| **Reverse Engineering** | radare2, gdb-multiarch, ltrace, strace, binutils, Bless (hex editor) |
| **OSINT** | whois, theHarvester, recon-ng |
| **Crypto / Password Auditing** | hashid, openssl, Kleopatra |

### Development

Git, build-essential, GCC/Clang/LLVM, CMake, Ninja, GDB/LLDB, Python 3, Node.js, Go, Rust, a JDK, Podman + Distrobox, virt-manager + QEMU.

### Desktop & System

Firefox ESR, Okular, LibreOffice, Kdenlive, Gwenview, Ark, VLC, Konsole, Dolphin, htop/btop, Timeshift, GParted, OpenSSH + FileZilla.

### Raptor Apps

| App | Purpose |
|---|---|
| **Raptor Security Center** | Dashboard GUI — live system/network/security status, one-click mode switching |
| **Mode Manager** | Backend daemon powering three modes: Secure, Hardened, Lockdown |
| **Emergency Shutdown** | Session teardown + poweroff, with a clear confirmation dialog before anything happens |
| **Persistence Manager** | Set up or check encrypted (LUKS) persistent storage on your USB drive |
| **VPN / Tor Managers** | Connect, disconnect, and monitor VPN or Tor state from the dashboard |
| **Network Protection Manager** | Interface, IP, DNS, IPv6, and MAC-randomization status and controls |

---

## Raptor Security Center — Mode Manager

GTK4/libadwaita dashboard with three modes — **Secure**, **Hardened**, **Lockdown** — each backed by a real nftables firewall ruleset, sysctl hardening profile, and systemd service posture, not just a UI label. Every dashboard indicator is re-verified against live system state on each check, never cached or assumed:

- **Secure** — baseline firewall, comfortable for everyday use
- **Hardened** — same tools and apps, output traffic restricted to an allowlist, aggressive logging
- **Lockdown** — real network kill switch: only VPN/Tor tunnel interfaces can originate outbound traffic

## Emergency Shutdown

A dedicated, separate daemon (not folded into Mode Manager) for ending a session fast: terminates the session, clears what a Live tmpfs session can actually clear, and powers off — honest in the confirmation dialog about what it can't guarantee (e.g. prior swap contents), rather than overclaiming forensic erasure.

## Persistence Manager

Distinguishes Live session data (gone at poweroff, by design) from encrypted persistent storage (LUKS + ext4, explicitly opt-in) — set up directly from the dashboard against a removable device you select.

---

## Built With
- [live-build](https://salsa.debian.org/live-team/live-build) — Debian's official Live image build system
- [Debian](https://www.debian.org/) (bookworm) — base distribution

## Changelog
See [changelog.md](changelog.md) for full version history.
