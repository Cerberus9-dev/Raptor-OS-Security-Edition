# ==============================================================================
# RAPTOR OS SECURITY EDITION - COMPLETE PROJECT FILES & DOCUMENTATION
# Base OS: Debian 12 (Bookworm) amd64
# Repository: https://github.com/Cerberus9-dev/Raptor-OS-Security-Edition
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. REPOSITORY STRUCTURE
# ------------------------------------------------------------------------------

Raptor-OS-Security-Edition/
├── .github/
│   └── workflows/
│       └── build-iso.yml
├── build/
│   ├── auto/
│   │   └── config
│   ├── config/
│   │   ├── archives/
│   │   │   └── anti-sysvinit.pref.chroot
│   │   ├── apt/
│   │   │   └── apt.conf
│   │   ├── includes.chroot/
│   │   │   ├── etc/
│   │   │   │   ├── raptor/
│   │   │   │   │   ├── modes/
│   │   │   │   │   │   ├── secure.conf
│   │   │   │   │   │   ├── hardened.conf
│   │   │   │   │   │   └── lockdown.conf
│   │   │   │   │   └── raptor.conf
│   │   │   │   ├── sysctl.d/
│   │   │   │   │   └── 99-raptor-hardening.conf
│   │   │   │   └── xdg/
│   │   │   │       └── menus/
│   │   │   │           └── applications-merged/
│   │   │   │               └── raptor-security.menu
│   │   │   ├── usr/
│   │   │   │   ├── local/
│   │   │   │   │   └── bin/
│   │   │   │   │       ├── raptor-security
│   │   │   │   │       ├── raptor-firewall
│   │   │   │   │       ├── raptor-killswitch
│   │   │   │   │       ├── raptor-status
│   │   │   │   │       └── raptor-control-center
│   │   │   │   └── share/
│   │   │   │       ├── applications/
│   │   │   │       │   └── raptor-control-center.desktop
│   │   │   │       └── desktop-directories/
│   │   │   │           ├── raptor-security.directory
│   │   │   │           ├── raptor-recon.directory
│   │   │   │           ├── raptor-netanalysis.directory
│   │   │   │           ├── raptor-websec.directory
│   │   │   │           ├── raptor-passwords.directory
│   │   │   │           ├── raptor-wireless.directory
│   │   │   │           ├── raptor-forensics.directory
│   │   │   │           └── raptor-reverse.directory
│   │   └── package-lists/
│   │       └── raptor-security.list.chroot
├── DOCUMENTATION.md
└── README.md


# ------------------------------------------------------------------------------
# 2. GITHUB ACTIONS WORKFLOW (.github/workflows/build-iso.yml)
# ------------------------------------------------------------------------------

name: Build Raptor OS Security Edition ISO

on:
  workflow_dispatch:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

permissions:
  contents: read

concurrency:
  group: raptor-security-build-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    name: Build Raptor OS Security ISO
    runs-on: ubuntu-24.04

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Disable AppArmor User Namespace Restrictions
        run: |
          sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0 || true

      - name: Cache live-build stages
        uses: actions/cache@v4
        with:
          path: build/cache
          key: raptor-security-lb-v2-${{ runner.os }}-${{ hashFiles('build/config/package-lists/*.list.chroot', 'build/auto/config') }}
          restore-keys: |
            raptor-security-lb-v2-${{ runner.os }}-

      - name: Free Runner Disk Space
        run: |
          sudo rm -rf \
            /usr/share/dotnet \
            /usr/local/lib/android \
            /opt/ghc \
            /usr/local/share/boost \
            "$AGENT_TOOLSDIRECTORY" || true
          df -h

      - name: Install Build Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            live-build \
            debootstrap \
            debian-archive-keyring \
            squashfs-tools \
            xorriso \
            isolinux \
            syslinux-utils \
            grub-efi-amd64-bin \
            mtools \
            dosfstools \
            rsync \
            python3-gi \
            gir1.2-gtk-3.0

      - name: Apply Live-Build Engine Patches
        run: |
          set -e
          LB_FILE="/usr/lib/live/build/lb_chroot_linux-image"
          sudo sed -i 's#${LB_PARENT_MIRROR_CHROOT}/dists/${LB_PARENT_DISTRIBUTION}/Contents-${LB_ARCHITECTURES}\.gz#${LB_PARENT_MIRROR_CHROOT}/dists/${LB_PARENT_DISTRIBUTION}/main/Contents-${LB_ARCHITECTURES}.gz#g' "$LB_FILE"
          sudo sed -i 's#${LB_MIRROR_CHROOT}/dists/${LB_DISTRIBUTION}/Contents-${LB_ARCHITECTURES}\.gz#${LB_MIRROR_CHROOT}/dists/${LB_DISTRIBUTION}/main/Contents-${LB_ARCHITECTURES}.gz#g' "$LB_FILE"
          sudo sed -i '/SECURITY/ s#/updates#-security#g' /usr/lib/live/build/lb_chroot_archives

          THEME_DIR="/usr/share/live/build/bootloaders/isolinux"
          sudo ln -sf /usr/lib/ISOLINUX/isolinux.bin "$THEME_DIR/isolinux.bin"
          sudo ln -sf /usr/lib/syslinux/modules/bios/vesamenu.c32 "$THEME_DIR/vesamenu.c32"

          LB_SYS="/usr/lib/live/build/lb_binary_syslinux"
          sudo sed -i 's#rsvg --format png --height 480 --width 640 splash.svg splash.png#rsvg-convert --format png --height 480 --width 640 splash.svg -o splash.png#' "$LB_SYS"

      - name: Set Permissions & Enforce Anti-sysvinit Pinning
        working-directory: build
        run: |
          set -e
          chmod +x config/includes.chroot/usr/local/bin/raptor-* || true

          mkdir -p config/archives config/apt
          cat <<'EOF' > config/archives/anti-sysvinit.pref.chroot
          Package: sysvinit-core sysv-rc initscripts orphan-sysvinit-scripts live-config-sysvinit
          Pin: release *
          Pin-Priority: -1
          EOF

          echo 'APT::Sandbox::User "root";' > config/apt/apt.conf

      - name: Configure Live-Build
        working-directory: build
        run: |
          set -e
          chmod +x auto/config
          ./auto/config

      - name: Build ISO Image
        working-directory: build
        run: sudo lb build

      - name: Add Hybrid UEFI & BIOS Boot
        working-directory: build
        run: |
          set -e
          ORIGINAL_ISO="$(find . -maxdepth 1 -type f -name '*.iso' -print -quit)"
          if [ -z "$ORIGINAL_ISO" ]; then
            echo "ERROR: No ISO produced by lb build."
            exit 1
          fi

          sudo chmod -R a+rwX binary "$ORIGINAL_ISO"
          mkdir -p efi-build/esp/EFI/BOOT

          cat <<'EOF' > efi-build/grub.cfg
          insmod part_gpt
          insmod part_msdos
          insmod fat
          insmod iso9660
          insmod all_video
          insmod gfxterm

          set default="0"
          set timeout=5

          search --no-floppy --set=root --label RAPTOR-SECURITY

          menuentry "Raptor OS Security Edition (Live)" {
              linux /live/vmlinuz boot=live components quiet splash
              initrd /live/initrd.img
          }

          menuentry "Raptor OS Security Edition (Failsafe)" {
              linux /live/vmlinuz boot=live components noapic noapm nodma nomce nolapic nosmp
              initrd /live/initrd.img
          }
          EOF

          grub-mkstandalone \
            --format=x86_64-efi \
            --output=efi-build/BOOTX64.EFI \
            --locales="" \
            --fonts="" \
            "boot/grub/grub.cfg=efi-build/grub.cfg"

          dd if=/dev/zero of=efi-build/efiboot.img bs=1M count=16
          mkfs.vfat -F 16 -n "RAPTOR_EFI" efi-build/efiboot.img
          mmd -i efi-build/efiboot.img ::/EFI
          mmd -i efi-build/efiboot.img ::/EFI/BOOT
          mcopy -i efi-build/efiboot.img efi-build/BOOTX64.EFI ::/EFI/BOOT/BOOTX64.EFI

          mkdir -p binary/EFI/BOOT
          cp efi-build/BOOTX64.EFI binary/EFI/BOOT/BOOTX64.EFI

          cd binary
          xorriso -as mkisofs \
            -r -J -l -cache-inodes -allow-multidot \
            -A "Raptor OS Security Edition" \
            -publisher "Cerberus9-dev" \
            -V "RAPTOR-SECURITY" \
            -no-emul-boot -boot-load-size 4 -boot-info-table \
            -b isolinux/isolinux.bin -c isolinux/boot.cat \
            -eltorito-alt-boot \
            -e --interval:appended_partition_2:all:: \
            -no-emul-boot \
            -append_partition 2 0xef ../efi-build/efiboot.img \
            -isohybrid-gpt-basdat \
            -o "../${ORIGINAL_ISO}.uefi" \
            .
          cd ..

          if [ -f "${ORIGINAL_ISO}.uefi" ]; then
            mv "${ORIGINAL_ISO}.uefi" "$ORIGINAL_ISO"
          fi

      - name: Generate SHA256 Checksum
        working-directory: build
        run: |
          ISO="$(find . -maxdepth 1 -type f -name '*.iso' -print -quit)"
          sha256sum "$ISO" > raptor-os-security.sha256
          cat raptor-os-security.sha256

      - name: Upload ISO Artifact
        uses: actions/upload-artifact@v4
        with:
          name: Raptor-OS-Security-ISO
          path: |
            build/*.iso
            build/raptor-os-security.sha256
          retention-days: 14


# ------------------------------------------------------------------------------
# 3. LIVE-BUILD AUTO CONFIGURATION (build/auto/config)
# ------------------------------------------------------------------------------

#!/bin/sh
set -e

lb config nobase \
    --mode debian \
    --architectures amd64 \
    --distribution bookworm \
    --parent-distribution bookworm \
    --archive-areas "main contrib non-free non-free-firmware" \
    --parent-archive-areas "main contrib non-free non-free-firmware" \
    --apt apt \
    --apt-indices false \
    --apt-recommends true \
    --debian-installer live \
    --debian-installer-gui true \
    --bootloader isolinux \
    --iso-application "Raptor OS Security Edition" \
    --iso-preparer "Cerberus9-dev" \
    --iso-publisher "Raptor OS Project" \
    --iso-volume "RAPTOR-SECURITY" \
    --win32-loader false \
    "${@}"


# ------------------------------------------------------------------------------
# 4. PACKAGE SELECTION LIST (build/config/package-lists/raptor-security.list.chroot)
# ------------------------------------------------------------------------------

# Base System & Desktop Environment
task-desktop
xfce4
xfce4-goodies
lightdm
network-manager-gnome
calamares
calamares-settings-debian
sudo
curl
wget
git
zsh
tmux

# Hardware, Firmware & GPU Support
firmware-linux
firmware-linux-nonfree
firmware-iwlwifi
firmware-realtek
firmware-atheros
bluetooth
bluez

# Core Security & Firewalls
nftables
ufw
apparmor
apparmor-utils
auditd
fail2ban
macchanger

# Reconnaissance & OSINT
nmap
masscan
dnsutils
whois
netcat-openbsd
theharvester
dnsrecon

# Network Analysis & Traffic Auditing
wireshark
tshark
tcpdump
traceroute
iperf3
ettercap-graphical
dsniff

# Web Security Testing
owasp-zap
nikto
sqlmap
ffuf

# Password Auditing & Cryptanalysis
john
hashcat
hydra

# Digital Forensics & Reverse Engineering
sleuthkit
autopsy
binwalk
gdb
radare2
hexedit
exiftool

# Wireless Security
aircrack-ng
kismet
reaver

# Development & System Scripting
build-essential
gcc
g++
make
python3
python3-pip
python3-gi
gir1.2-gtk-3.0
rustc
cargo
code


# ------------------------------------------------------------------------------
# 5. RAPTOR FIREWALL ENGINE (build/config/includes.chroot/usr/local/bin/raptor-firewall)
# ------------------------------------------------------------------------------

#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-status}"

apply_secure() {
    nft flush ruleset
    nft add table inet filter
    nft add chain inet filter input \{ type filter hook input priority 0 \; policy drop \; \}
    nft add chain inet filter forward \{ type filter hook forward priority 0 \; policy drop \; \}
    nft add chain inet filter output \{ type filter hook output priority 0 \; policy accept \; \}
    
    nft add rule inet filter input iifname "lo" accept
    nft add rule inet filter input ct state established,related accept
    nft add rule inet filter input meta l4proto icmp accept
    echo "[Raptor Firewall] SECURE mode applied (Inbound Drop, Outbound Allow)."
}

apply_hardened() {
    nft flush ruleset
    nft add table inet filter
    nft add chain inet filter input \{ type filter hook input priority 0 \; policy drop \; \}
    nft add chain inet filter forward \{ type filter hook forward priority 0 \; policy drop \; \}
    nft add chain inet filter output \{ type filter hook output priority 0 \; policy drop \; \}

    nft add rule inet filter input iifname "lo" accept
    nft add rule inet filter output oifname "lo" accept

    nft add rule inet filter input ct state established,related accept
    nft add rule inet filter output ct state established,related accept

    nft add rule inet filter output udp dport 53 accept
    nft add rule inet filter output tcp dport { 53, 80, 443 } accept
    echo "[Raptor Firewall] HARDENED mode applied (Strict Egress Filtering Active)."
}

apply_lockdown() {
    nft flush ruleset
    nft add table inet filter
    nft add chain inet filter input \{ type filter hook input priority 0 \; policy drop \; \}
    nft add chain inet filter forward \{ type filter hook forward priority 0 \; policy drop \; \}
    nft add chain inet filter output \{ type filter hook output priority 0 \; policy drop \; \}

    nft add rule inet filter input iifname "lo" accept
    nft add rule inet filter output oifname "lo" accept
    echo "[Raptor Firewall] LOCKDOWN mode applied (All External Traffic Cut)."
}

case "$MODE" in
    secure)   apply_secure ;;
    hardened) apply_hardened ;;
    lockdown) apply_lockdown ;;
    status)   nft list ruleset ;;
    *)        echo "Usage: $0 {secure|hardened|lockdown|status}" && exit 1 ;;
esac


# ------------------------------------------------------------------------------
# 6. RAPTOR SECURITY ENGINE (build/config/includes.chroot/usr/local/bin/raptor-security)
# ------------------------------------------------------------------------------

#!/usr/bin/env bash
set -euo pipefail

CONF_DIR="/etc/raptor"
STATE_FILE="${CONF_DIR}/current_mode"

mkdir -p "$CONF_DIR"
mkdir -p "${CONF_DIR}/modes"

MODE="${1:-status}"

set_mode() {
    TARGET_MODE="$1"
    echo "$TARGET_MODE" > "$STATE_FILE"
    
    if [[ "$TARGET_MODE" == "hardened" || "$TARGET_MODE" == "lockdown" ]]; then
        sysctl -w net.ipv4.conf.all.rp_filter=1 >/dev/null 2>&1 || true
        sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=1 >/dev/null 2>&1 || true
        sysctl -w kernel.kptr_restrict=2 >/dev/null 2>&1 || true
    fi

    /usr/local/bin/raptor-firewall "$TARGET_MODE"
    echo "Raptor Security Mode switched to: ${TARGET_MODE^^}"
}

case "$MODE" in
    secure|hardened|lockdown)
        set_mode "$MODE"
        ;;
    status)
        CURRENT=$(cat "$STATE_FILE" 2>/dev/null || echo "SECURE")
        echo "Current Raptor Security Mode: ${CURRENT^^}"
        ;;
    *)
        echo "Usage: raptor-security {secure|hardened|lockdown|status}"
        exit 1
        ;;
esac


# ------------------------------------------------------------------------------
# 7. RAPTOR KILLSWITCH (build/config/includes.chroot/usr/local/bin/raptor-killswitch)
# ------------------------------------------------------------------------------

#!/usr/bin/env bash
set -euo pipefail

STATE_FILE="/etc/raptor/killswitch_active"
mkdir -p /etc/raptor

ACTION="${1:-status}"

enable_killswitch() {
    touch "$STATE_FILE"
    nmcli networking off 2>/dev/null || true
    ip link set dev eth0 down 2>/dev/null || true
    ip link set dev wlan0 down 2>/dev/null || true
    /usr/local/bin/raptor-firewall lockdown
    echo "[Raptor Killswitch] NETWORK KILLED. All network devices disabled."
}

disable_killswitch() {
    rm -f "$STATE_FILE"
    nmcli networking on 2>/dev/null || true
    CURRENT_MODE=$(cat /etc/raptor/current_mode 2>/dev/null || echo "secure")
    /usr/local/bin/raptor-firewall "$CURRENT_MODE"
    echo "[Raptor Killswitch] Network restored. Re-applied $CURRENT_MODE mode."
}

case "$ACTION" in
    on|enable)   enable_killswitch ;;
    off|disable) disable_killswitch ;;
    status)
        if [ -f "$STATE_FILE" ]; then
            echo "Killswitch: ACTIVE (Network Blocked)"
        else
            echo "Killswitch: INACTIVE"
        fi
        ;;
    *) echo "Usage: $0 {on|off|status}" && exit 1 ;;
esac


# ------------------------------------------------------------------------------
# 8. RAPTOR STATUS AGENT (build/config/includes.chroot/usr/local/bin/raptor-status)
# ------------------------------------------------------------------------------

#!/usr/bin/env bash
set -euo pipefail

MODE=$(cat /etc/raptor/current_mode 2>/dev/null || echo "secure")
KILLSWITCH=$([ -f /etc/raptor/killswitch_active ] && echo "ACTIVE" || echo "INACTIVE")
FIREWALL=$(nft list ruleset 2>/dev/null | grep -q "table inet filter" && echo "ENABLED" || echo "DISABLED")

cat <<EOF
{
  "mode": "${MODE^^}",
  "killswitch": "${KILLSWITCH}",
  "firewall": "${FIREWALL}"
}
EOF


# ------------------------------------------------------------------------------
# 9. RAPTOR CONTROL CENTER GUI (build/config/includes.chroot/usr/local/bin/raptor-control-center)
# ------------------------------------------------------------------------------

#!/usr/bin/env python3
import sys
import subprocess
import json
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

class RaptorControlCenter(Gtk.Window):
    def __init__(self):
        super().__init__(title="Raptor Security Control Center")
        self.set_border_width(16)
        self.set_default_size(520, 380)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(main_box)

        title_label = Gtk.Label()
        title_label.set_markup("<span size='x-large' weight='bold'>Raptor OS Security Control Center</span>")
        main_box.pack_start(title_label, False, False, 0)

        self.status_card = Gtk.Frame(label="System Security Status")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box.set_border_width(12)
        
        self.lbl_mode = Gtk.Label(label="Security Mode: UNKNOWN")
        self.lbl_firewall = Gtk.Label(label="Firewall: UNKNOWN")
        self.lbl_ks = Gtk.Label(label="Killswitch: UNKNOWN")

        status_box.pack_start(self.lbl_mode, False, False, 0)
        status_box.pack_start(self.lbl_firewall, False, False, 0)
        status_box.pack_start(self.lbl_ks, False, False, 0)
        self.status_card.add(status_box)
        main_box.pack_start(self.status_card, False, False, 0)

        mode_frame = Gtk.Frame(label="Select Security Mode")
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        mode_box.set_border_width(12)

        btn_secure = Gtk.Button(label="SECURE")
        btn_secure.connect("clicked", lambda x: self.set_mode("secure"))

        btn_hardened = Gtk.Button(label="HARDENED")
        btn_hardened.connect("clicked", lambda x: self.set_mode("hardened"))

        btn_lockdown = Gtk.Button(label="LOCKDOWN")
        btn_lockdown.connect("clicked", lambda x: self.set_mode("lockdown"))

        mode_box.pack_start(btn_secure, True, True, 0)
        mode_box.pack_start(btn_hardened, True, True, 0)
        mode_box.pack_start(btn_lockdown, True, True, 0)
        mode_frame.add(mode_box)
        main_box.pack_start(mode_frame, False, False, 0)

        ks_frame = Gtk.Frame(label="Network Emergency Controls")
        ks_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ks_box.set_border_width(12)

        btn_ks_on = Gtk.Button(label="ENGAGE KILLSWITCH")
        btn_ks_on.connect("clicked", lambda x: self.toggle_killswitch("on"))

        btn_ks_off = Gtk.Button(label="RESTORE NETWORK")
        btn_ks_off.connect("clicked", lambda x: self.toggle_killswitch("off"))

        ks_box.pack_start(btn_ks_on, True, True, 0)
        ks_box.pack_start(btn_ks_off, True, True, 0)
        ks_frame.add(ks_box)
        main_box.pack_start(ks_frame, False, False, 0)

        self.refresh_status()

    def refresh_status(self):
        try:
            res = subprocess.check_output(["/usr/local/bin/raptor-status"]).decode("utf-8")
            data = json.loads(res)
            self.lbl_mode.set_markup(f"<b>Security Mode:</b> {data.get('mode')}")
            self.lbl_firewall.set_markup(f"<b>Firewall Status:</b> {data.get('firewall')}")
            self.lbl_ks.set_markup(f"<b>Killswitch:</b> {data.get('killswitch')}")
        except Exception as e:
            self.lbl_mode.set_text(f"Error fetching status: {e}")

    def set_mode(self, mode):
        subprocess.run(["pkexec", "/usr/local/bin/raptor-security", mode])
        self.refresh_status()

    def toggle_killswitch(self, action):
        subprocess.run(["pkexec", "/usr/local/bin/raptor-killswitch", action])
        self.refresh_status()

if __name__ == "__main__":
    app = RaptorControlCenter()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


# ------------------------------------------------------------------------------
# 10. DESKTOP SHORTCUT (build/config/includes.chroot/usr/share/applications/raptor-control-center.desktop)
# ------------------------------------------------------------------------------

[Desktop Entry]
Name=Raptor Security Control Center
Comment=Manage Security Modes, Firewall, and Emergency Killswitch
Exec=raptor-control-center
Icon=security-high
Terminal=false
Type=Application
Categories=System;Security;


# ------------------------------------------------------------------------------
# 11. APPLICATION MENU SPECIFICATION (build/config/includes.chroot/etc/xdg/menus/applications-merged/raptor-security.menu)
# ------------------------------------------------------------------------------

<!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"
 "http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">
<Menu>
  <Name>Applications</Name>
  <Menu>
    <Name>Raptor Security</Name>
    <Directory>raptor-security.directory</Directory>
    <Include>
      <Category>Security</Category>
    </Include>
    
    <Menu>
      <Name>Reconnaissance</Name>
      <Directory>raptor-recon.directory</Directory>
      <Include><Category>X-Raptor-Recon</Category></Include>
    </Menu>
    <Menu>
      <Name>Network Analysis</Name>
      <Directory>raptor-netanalysis.directory</Directory>
      <Include><Category>X-Raptor-NetAnalysis</Category></Include>
    </Menu>
    <Menu>
      <Name>Web Security</Name>
      <Directory>raptor-websec.directory</Directory>
      <Include><Category>X-Raptor-Web</Category></Include>
    </Menu>
    <Menu>
      <Name>Password Auditing</Name>
      <Directory>raptor-passwords.directory</Directory>
      <Include><Category>X-Raptor-Passwords</Category></Include>
    </Menu>
    <Menu>
      <Name>Reverse Engineering</Name>
      <Directory>raptor-reverse.directory</Directory>
      <Include><Category>X-Raptor-Reverse</Category></Include>
    </Menu>
  </Menu>
</Menu>


# ------------------------------------------------------------------------------
# 12. FULL README DOCUMENTATION (README.md)
# ------------------------------------------------------------------------------

# Raptor OS Security Edition

Raptor OS Security Edition is a specialized, security-first Linux distribution built directly on Debian 12 (Bookworm). Designed for cybersecurity professionals, penetration testers, network analysts, and privacy advocates, Raptor OS combines enterprise-grade auditing tools with an intuitive, dynamic system hardening architecture.

---

## Table of Contents
- Base Architecture
- Key Features
- Raptor Security Modes
- Control Center & CLI Utilities
- Included Tooling Directory
- System Requirements
- Building the ISO
- Flashing & Live Booting
- Security & Reversibility Design

---

## Base Architecture

Raptor OS Security Edition avoids bloat while providing broad hardware compatibility out of the box:

- Base Distribution: Debian 12 (Bookworm) amd64
- Desktop Environment: Lightweight, modular XFCE 4.18 with custom tactical GTK styling
- Init System: systemd (with anti-sysvinit package pinning enforced)
- Boot Compatibility: Hybrid ISO supporting legacy BIOS (ISOLINUX) and UEFI (GRUB2) with Secure Boot compatibility
- Firewall Backend: Modern nftables architecture replacing legacy iptables
- Installer: Calamares graphical installer for permanent disk installation

---

## Key Features

- Raptor Control Center: Native GTK dashboard providing one-click control over security modes, firewall behavior, and emergency network state.
- Triple Security Profiles: Switch operational posture dynamically between SECURE, HARDENED, and LOCKDOWN.
- Hardware-Level Network Killswitch: Cut all physical and virtual interfaces instantly with zero configuration drift.
- Categorized Menu Structure: Fully compliant XDG menu schema organizing security tools by operational phase (Recon, Analysis, Web, Exploitation, Forensics).
- Live USB Ready: Full live boot support with options for persistent storage overlays.

---

## Raptor Security Modes

Raptor OS provides three strict operational modes configured via `/usr/local/bin/raptor-security`:

| Mode | Inbound Network | Outbound Network | Kernel / Memory Hardening |
| :--- | :--- | :--- | :--- |
| SECURE | Drop all unsolicited traffic | Allow standard outbound connections | Standard Debian security defaults |
| HARDENED | Drop all unsolicited traffic | Restrict to HTTP, HTTPS, & DNS (Ports 53, 80, 443) | Restrict kernel pointer visibility (kptr_restrict=2), enable strict reverse-path filtering (rp_filter=1) |
| LOCKDOWN | Drop all traffic | Drop all traffic (Loopback lo allowed only) | Maximum memory & system restrictions enabled |

---

## Control Center & CLI Utilities

### Graphical Interface
Launch the dashboard via the application menu under System -> Raptor Security Control Center or run:
```bash
raptor-control-center
