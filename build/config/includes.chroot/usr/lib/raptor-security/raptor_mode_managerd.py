#!/usr/bin/env python3
"""
raptor-mode-managerd — Raptor Security's Mode Manager daemon.

This is the ONLY component in Raptor Security allowed to change firewall,
hardening, or network-privacy state. Security Center and every other GUI
talks to this daemon over D-Bus and never touches nftables/sysctl/systemd
directly — that split is what makes spec section 26 ("security indicators
must be real") enforceable: there is exactly one place state changes can
happen, and exactly one place status is read from, and both go through the
same verification logic.

Runs as root via systemd (see raptor-mode-manager.service), exposes:

    Bus name:    org.raptor.ModeManager
    Object path: /org/raptor/ModeManager
    Interface:   org.raptor.ModeManager1

Methods:
    SetMode(s mode) -> b success           — "secure" | "hardened" | "lockdown"
    GetMode() -> s mode
    GetStatus() -> a{sv} status            — see build_status() below

Signals:
    ModeChanged(s mode)

Every value returned by GetStatus() is derived from an actual runtime
check (systemctl, nft, ip, etc.) at call time — nothing is cached from the
last SetMode() call and nothing is assumed. If a check itself fails, the
corresponding field is the string "unknown", never a guessed "ok" value.
"""

import subprocess
import logging
import sys
import json
from pathlib import Path

from pydbus import SystemBus
from pydbus.generic import signal
from gi.repository import GLib

MODES = ("secure", "hardened", "lockdown")
CONFIG_ROOT = Path("/etc/raptor-security/modes")
CURRENT_MODE_FILE = Path("/etc/raptor-security/current-mode")
RAPTOR_NFT_FAMILY = "inet"
RAPTOR_NFT_TABLE = "raptor_security"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s raptor-mode-managerd %(levelname)s: %(message)s",
)
log = logging.getLogger("raptor-mode-managerd")


def run(cmd, check=True, timeout=10):
    """Run a command, returning (returncode, stdout, stderr). Never raises
    on a non-zero exit unless check=True and the caller wants that."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if check and proc.returncode != 0:
            log.warning("command failed: %s -> rc=%s stderr=%s",
                        " ".join(cmd), proc.returncode, proc.stderr.strip())
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        log.error("command not found: %s", cmd[0])
        return 127, "", f"{cmd[0]}: not found"
    except subprocess.TimeoutExpired:
        log.error("command timed out: %s", " ".join(cmd))
        return 124, "", "timeout"


class ModeManager:
    """
    <node>
      <interface name='org.raptor.ModeManager1'>
        <method name='SetMode'>
          <arg type='s' name='mode' direction='in'/>
          <arg type='b' name='success' direction='out'/>
        </method>
        <method name='GetMode'>
          <arg type='s' name='mode' direction='out'/>
        </method>
        <method name='GetStatus'>
          <arg type='a{sv}' name='status' direction='out'/>
        </method>
        <signal name='ModeChanged'>
          <arg type='s' name='mode'/>
        </signal>
      </interface>
    </node>
    """

    ModeChanged = signal()

    def GetMode(self):
        if CURRENT_MODE_FILE.exists():
            mode = CURRENT_MODE_FILE.read_text().strip()
            if mode in MODES:
                return mode
        return "unknown"

    def SetMode(self, mode: str) -> bool:
        mode = mode.strip().lower()
        if mode not in MODES:
            log.error("rejected SetMode(%r): not a valid mode", mode)
            return False

        log.info("switching mode -> %s", mode)
        ok = True
        ok &= self._apply_firewall(mode)
        ok &= self._apply_sysctl(mode)
        ok &= self._apply_services(mode)

        if ok:
            CURRENT_MODE_FILE.write_text(mode + "\n")
            self.ModeChanged(mode)
            log.info("mode switch to %s completed", mode)
        else:
            log.error("mode switch to %s completed WITH ERRORS — "
                       "state may be inconsistent, check GetStatus()", mode)
        return ok

    def GetStatus(self):
        return self.build_status()

    # -- internal: applying state ------------------------------------

    def _apply_firewall(self, mode: str) -> bool:
        ruleset = CONFIG_ROOT / f"{mode}.nft"
        if not ruleset.exists():
            log.error("missing ruleset: %s", ruleset)
            return False
        rc, _, err = run(["nft", "-f", str(ruleset)])
        if rc != 0:
            log.error("nft load failed for %s: %s", mode, err.strip())
            return False
        return True

    def _apply_sysctl(self, mode: str) -> bool:
        sysctl_file = CONFIG_ROOT / f"{mode}.sysctl.conf"
        if not sysctl_file.exists():
            # Not every mode needs sysctl overrides; absence isn't an error.
            return True
        rc, _, err = run(["sysctl", "-p", str(sysctl_file)])
        if rc != 0:
            log.error("sysctl apply failed for %s: %s", mode, err.strip())
            return False
        return True

    def _apply_services(self, mode: str) -> bool:
        """
        Reads {mode}.services — one line per unit, prefixed with '+' to
        ensure-started or '-' to ensure-stopped. Lets each mode define its
        own service posture (e.g. lockdown stops non-essential network
        services) without hardcoding a service list in this daemon.
        """
        services_file = CONFIG_ROOT / f"{mode}.services"
        if not services_file.exists():
            return True

        ok = True
        for line in services_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            action, unit = line[0], line[1:].strip()
            if action == "+":
                rc, _, err = run(["systemctl", "start", unit], check=False)
            elif action == "-":
                rc, _, err = run(["systemctl", "stop", unit], check=False)
            else:
                log.warning("bad line in %s: %r", services_file, line)
                continue
            if rc != 0:
                log.warning("service action failed: %s %s (%s)",
                             action, unit, err.strip())
                ok = False
        return ok

    # -- internal: verifying state -------------------------------------
    # Every one of these checks live system state. None of them trust
    # what SetMode() *tried* to do — see module docstring.

    def build_status(self):
        status = {}

        status["mode"] = GLib.Variant("s", self.GetMode())
        status["firewall_active"] = GLib.Variant("s", self._check_firewall())
        status["kill_switch_armed"] = GLib.Variant("s", self._check_kill_switch())
        status["vpn_state"] = GLib.Variant("s", self._check_vpn())
        status["tor_state"] = GLib.Variant("s", self._check_tor())
        status["mac_randomization"] = GLib.Variant("s", self._check_mac_randomization())
        status["persistence"] = GLib.Variant("s", self._check_persistence())

        return status

    def _check_firewall(self) -> str:
        rc, out, _ = run(["systemctl", "is-active", "nftables"], check=False)
        if out.strip() != "active":
            return "inactive"
        # systemctl "active" only proves the unit ran, not that OUR
        # ruleset is what's loaded (someone could `nft flush ruleset`
        # after the fact) — actually check for our table.
        rc, out, _ = run(["nft", "list", "table", RAPTOR_NFT_FAMILY, RAPTOR_NFT_TABLE], check=False)
        return "active" if rc == 0 else "unverified"

    def _check_kill_switch(self) -> str:
        # Kill-switch is armed only if the raptor table's OUTPUT chain
        # specifically has policy drop. A naive substring check against
        # the whole table's text (checking for "policy drop" anywhere)
        # would false-positive on Secure/Hardened mode, since their
        # `forward` chain is also policy drop by design — only `output`
        # distinguishes Lockdown's real kill switch from the others.
        rc, out, _ = run(["nft", "-j", "list", "table", RAPTOR_NFT_FAMILY, RAPTOR_NFT_TABLE], check=False)
        if rc != 0:
            return "unknown"
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            return "unknown"

        for item in data.get("nftables", []):
            chain = item.get("chain")
            if chain and chain.get("hook") == "output" and chain.get("family") == "inet":
                return "armed" if chain.get("policy") == "drop" else "not_armed"
        return "unknown"

    def _check_vpn(self) -> str:
        rc, out, _ = run(
            ["nmcli", "-t", "-f", "TYPE,STATE", "connection", "show", "--active"],
            check=False,
        )
        if rc != 0:
            return "unknown"
        for line in out.splitlines():
            if line.startswith(("vpn:", "wireguard:")):
                return "connected"
        return "disconnected"

    def _check_tor(self) -> str:
        rc, out, _ = run(["systemctl", "is-active", "tor@default"], check=False)
        return "active" if out.strip() == "active" else "inactive"

    def _check_mac_randomization(self) -> str:
        rc, out, _ = run(
            ["nmcli", "-t", "-f", "802-11-wireless.cloned-mac-address",
             "connection", "show"],
            check=False,
        )
        if rc != 0:
            return "unknown"
        return "enabled" if "random" in out.lower() or "stable" in out.lower() else "disabled"

    def _check_persistence(self) -> str:
        rc, out, _ = run(["findmnt", "-n", "/lib/live/mount/persistence"], check=False)
        return "encrypted_active" if rc == 0 else "none"


def main():
    if CURRENT_MODE_FILE.parent.exists() is False:
        log.error("config root %s missing — is raptor-security package installed?",
                   CONFIG_ROOT)
        sys.exit(1)

    bus = SystemBus()
    manager = ModeManager()
    bus.publish("org.raptor.ModeManager", manager)

    # Apply the persisted mode's state on every daemon start (boot, and any
    # service restart). Without this, GetMode() would report a mode that
    # doesn't match GetStatus()'s live checks until a GUI SetMode() call
    # happened to occur — exactly the "fake indicator" spec section 26
    # forbids. This calls the same _apply_* methods SetMode() uses, not a
    # separate code path, so there's only one place mode-application logic
    # lives.
    startup_mode = manager.GetMode()
    if startup_mode == "unknown":
        log.warning("no current mode recorded, defaulting to secure")
        startup_mode = "secure"
    log.info("applying %s mode at startup", startup_mode)
    if not manager.SetMode(startup_mode):
        log.error("failed to fully apply %s mode at startup — "
                   "GetStatus() may show unverified/inconsistent state",
                   startup_mode)

    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
