# Raptor OS — Security Edition
**Current version: v0.1.0 (pre-release)**

A Debian 12 (Bookworm) based privacy-focused **penetration testing + advanced cybersec live OS**, built in the spirit of Kodachi. Routed anonymity, encrypted DNS, a strict nftables firewall, and dynamic operational profiles all driven from a GTK4/libadwaita Kodachi-style Security Center dashboard — lean toolset, no bloat.

> **Heavy W.I.P — Feedback appreciated!** This is a **live** OS — boot it from a USB stick, nothing gets installed. By default every session is amnesic: RAM is wiped at shutdown and no data is written to the host drive. Optional encrypted persistence for configs and tool data.

---

## System Requirements

| | Minimum | Recommended |
|---|---|---|
| **CPU** | 64-bit x86_64, 1.6 GHz+ dual-core | Modern Intel/AMD multi-core |
| **RAM** | 4 GB (2 GB free after boot) | 8 GB+ for large scans + browser tabs |
| **Storage** | 4 GB USB stick (live) / 16 GB for encrypted persistence | 8 GB+ fast USB 3.0 stick |
| **GPU** | Any GPU with a Linux driver (basic 2D is all a live OS needs) | Anything with working open drivers (AMD/Intel best) |
| **Network** | Wired NIC for testing; wireless requires a chipset with monitor mode (see below) | USB adapter known-good with aircrack-ng |
| **Boot** | UEFI or BIOS with USB boot | UEFI with Secure Boot disabled |

---

## Installation

The ISO is built automatically by GitHub Actions from `main` and published on **Internet Archive** (like Raptor OS Home Edition — ISOs are too large for GitHub Releases). Download the latest Security Edition ISO from the Raptor OS collection on [Internet Archive](https://archive.org/), then flash it to a USB stick:

- **[Rufus](https://rufus.ie/en/)** — select **DD image mode** (not ISO copy mode)
- **[Ventoy](https://www.ventoy.net)** — copy the ISO to a Ventoy USB, boot and select it
- **[balenaEtcher](https://etcher.balena.io/)** — select the ISO and the stick, flash

Then boot your machine **from the USB**. Raptor OS runs entirely in RAM; nothing is installed to your hard drive and — with no persistence volume — no trace of the session survives a reboot (RAM is wiped on shutdown by `sdmem`).

### Optional: Encrypted Persistence

At boot, press <kbd>Tab</kbd> on the boot entry and append `persistence` to enable the optional encrypted persistence volume for `/home`:

- Create an LUKS volume labelled `raptor-home` (e.g. with **Disks** / `cryptsetup luksFormat`)
- On boot it unlocks, mounts `/home`, and the session is no longer fully amnesic — swap deactivation is offered on shutdown so you control what (if anything) leaks to disk

---

## First Boot

1. Automatic login to the `user` account launches **Raptor Security Center** as the dashboard.
2. The **first-boot service** wires the live user into `raptor-admin` (required for mode switches) and initialises `/etc/raptor-security`.
3. **Stubby** (DNS-over-TLS) is active out of the box on `dnsstub0`; **Tor** is pre-configured for LibreWolf via SOCKS5 `127.0.0.1:9050`.
4. The dashboard shows your current mode and live **System**, **Network**, and **Security** state — CPU, RAM, disk, uptime, interfaces, DNS servers, and your public IP *as seen through Tor* (never the clearnet IP).

---

## What's Included

### Pre-installed (always present)

| Category | Packages |
|---|---|
| **Desktop** | XFCE, LightDM autologin, htop |
| **Anonymity** | Tor + torsocks, LibreWolf with SOCKS5 proxy (third-party build hook), Stubby DNS-over-TLS, macchanger |
| **Firewall & Modes** | nftables with 3 bundled profiles (Secure / Hardened / Lockdown), iptables, rfkill killswitch |
| **Anti-Forensics** | secure-delete (`sdmem` RAM wipe at shutdown), BleachBit, MAT2 |
| **Encryption** | cryptsetup + Disks (LUKS persistence), KeePassXC |
| **VPN** | OpenVPN, WireGuard tools |
| **Sandboxing** | Firejail |

### Penetration Testing Toolset

| Category | Tools |
|---|---|
| **Recon & Scanning** | nmap, masscan, netdiscover, arp-scan, dnsrecon, dnsenum, recon-ng, bettercap, whois, traceroute, onesixtyone, smbclient, impacket |
| **Traffic & Pivoting** | tcpdump, wireshark + tshark, netcat, socat, proxychains4, dsniff |
| **Web App Security** | nikto, gobuster, wfuzz, ffuf, dirb, sqlmap, wapiti |
| **Password Auditing** | john, hashcat, hydra, medusa |
| **Wireless** | aircrack-ng, wifite (chipset must support monitor mode) |
| **Forensics & Stego** | binwalk, foremost, steghide, exiftool, testdisk, sleuthkit |
| **Cracking/Exploit Runtimes** | yara, ncat, whois, python3-impacket, librewolf dev tools |

> Tools not packaged in Debian — **Burp Suite**, **Metasploit Framework**, **WPScan**, **NetExec**, **radare2**, **theHarvester** — are installed best-effort at build time by the `0300 raptor thirdparty tools` hook, when the build environment allows.

---

## Operational Modes (Raptor Security Center)

| Profile | What it does |
|---|---|
| **Secure** | Default. Active nftables firewall, DNS-over-TLS, Tor-ready browser profile, base hardening (`sysctl`). |
| **Hardened** | Full Tor network isolation, randomized MAC addresses per interface, restrictive egress firewall (only listed traffic + Tor/VPN), tighter sysctl. |
| **Lockdown** | Cut it all: blocks all outbound except loopback/established (Tor/VPN tunnels still allowed), disables non-essential daemons, drops pending caches. |

Switching modes is immediate and is applied through the **Raptor Mode Manager** daemon (D-Bus) — the dashboard only requests a mode; the daemon applies the `nft`/`sysctl`/`services` configs and reports back its **verified** state. Any field the daemon cannot verify renders neutral — never fake-good.

---

## Security Architecture

- **D-Bus daemons** — Mode Manager, Tor Manager, VPN Manager, Network Protection Manager, Persistence Manager, Emergency Shutdown (all root-owned system services; the dashboard talks to them through system bus policies restricted to `raptor-admin` for privileged actions).
- **ntables** — per-mode generated rule sets under `/etc/raptor-security/modes/`.
- **`sdmem`** — RAM wipe on shutdown (three passes, so forensic recovery of the live session isn't feasible).
- **MAC randomization** and hardened `sysctl` applied on boot.
- **Public IP reporting always goes through the Tor SOCKS proxy** — the dashboard shows the exit-node IP, so connection identity is preserved even on the status page.

---

## Built With

- [Debian live-build](https://live-team.pages.debian.net/live-manual/) — `lb config / lb build` pipeline (`auto/`, hooks under `build/config/hooks/live/`, `includes.chroot` for the shipped `/etc`+`/usr` tree)
- [GitHub Actions](.github/workflows/build-iso.yml) — validated per-push build → ISO artifact (hosted on Internet Archive for releases)
- GTK4 + libadwaita dashboard, XFCE desktop, Tor, nftables

## Changelog
See [changelog.md](changelog.md) for the in-progress history.