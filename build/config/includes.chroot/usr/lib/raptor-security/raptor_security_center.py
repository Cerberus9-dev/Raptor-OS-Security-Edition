#!/usr/bin/env python3
"""
Raptor Security Center — spec section 4/5/24.

This is a *view* over Mode Manager's state. It never touches nftables,
sysctl, or systemd directly, and it never renders a status it hasn't just
fetched from GetStatus() — see the module docstring in
raptor_mode_managerd.py for why that split exists.

This first slice covers the mode selector + a subset of the dashboard
(firewall, kill switch, VPN, Tor, persistence) — the fields Mode Manager
currently implements. Extending the dashboard to the rest of spec section
5 (System/Privacy panels, open ports, security events, etc.) means adding
the corresponding check to Mode Manager's build_status() first, THEN
wiring a tile here — never invent a tile that isn't backed by a real
check, per section 26.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib
from pydbus import SystemBus

BUS_NAME = "org.raptor.ModeManager"
OBJECT_PATH = "/org/raptor/ModeManager"

SHUTDOWN_BUS_NAME = "org.raptor.EmergencyShutdown"
SHUTDOWN_OBJECT_PATH = "/org/raptor/EmergencyShutdown"

MODES = ["secure", "hardened", "lockdown"]
MODE_LABELS = {"secure": "Secure", "hardened": "Hardened", "lockdown": "Lockdown"}

STATUS_FIELD_LABELS = {
    "firewall_active": "Firewall",
    "kill_switch_armed": "Kill Switch",
    "vpn_state": "VPN",
    "tor_state": "Tor",
    "mac_randomization": "MAC Randomization",
    "persistence": "Persistence",
}

# Values that should render as a "good/expected" state per field.
# Everything else (including "unknown" / "unverified") renders neutral —
# never green, per section 26: an unverifiable state must never look like
# a confirmed-good one.
GOOD_VALUES = {
    "firewall_active": {"active"},
    "kill_switch_armed": {"armed", "not_armed"},  # not_armed is correct in Secure mode
    "vpn_state": {"connected"},
    "tor_state": {"active"},
    "mac_randomization": {"enabled"},
    "persistence": {"encrypted_active", "none"},  # "none" is correct for amnesic sessions
}


class SecurityCenterWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Raptor Security Center")
        self.set_default_size(760, 560)

        try:
            self.bus = SystemBus()
            self.manager = self.bus.get(BUS_NAME, OBJECT_PATH)
            self.dbus_available = True
        except Exception as e:
            self.manager = None
            self.dbus_available = False
            self._dbus_error = str(e)

        try:
            self.shutdown_manager = self.bus.get(SHUTDOWN_BUS_NAME, SHUTDOWN_OBJECT_PATH)
            self.shutdown_available = True
        except Exception as e:
            self.shutdown_manager = None
            self.shutdown_available = False
            self._shutdown_dbus_error = str(e)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        root.set_margin_top(24)
        root.set_margin_bottom(24)
        root.set_margin_start(24)
        root.set_margin_end(24)

        header = Adw.HeaderBar()
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)
        toolbar_view.set_content(root)
        self.set_content(toolbar_view)

        if not self.dbus_available:
            banner = Adw.Banner(
                title=f"Cannot reach Mode Manager: {self._dbus_error}. "
                      f"Status shown is unavailable, not fake-good.",
                revealed=True,
            )
            root.append(banner)

        self.mode_label = Gtk.Label(label="Current mode: unknown")
        self.mode_label.add_css_class("title-2")
        root.append(self.mode_label)

        mode_switcher = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                                 homogeneous=True)
        self.mode_buttons = {}
        for mode in MODES:
            btn = Gtk.ToggleButton(label=MODE_LABELS[mode])
            btn.connect("clicked", self._on_mode_button_clicked, mode)
            mode_switcher.append(btn)
            self.mode_buttons[mode] = btn
        root.append(mode_switcher)

        self.lockdown_notice = Gtk.Label(
            label="Lockdown blocks all outbound traffic except through an "
                  "active VPN or Tor tunnel. Ordinary apps that need direct "
                  "internet access will stop working until you leave Lockdown.",
            wrap=True,
        )
        self.lockdown_notice.add_css_class("dim-label")
        self.lockdown_notice.set_visible(False)
        root.append(self.lockdown_notice)

        root.append(Gtk.Separator())

        self.status_grid = Gtk.Grid(row_spacing=8, column_spacing=16)
        root.append(self.status_grid)
        self.status_value_labels = {}
        for i, field in enumerate(STATUS_FIELD_LABELS):
            key_label = Gtk.Label(label=STATUS_FIELD_LABELS[field], xalign=0)
            value_label = Gtk.Label(label="—", xalign=0)
            self.status_grid.attach(key_label, 0, i, 1, 1)
            self.status_grid.attach(value_label, 1, i, 1, 1)
            self.status_value_labels[field] = value_label

        self.refresh_status()
        GLib.timeout_add_seconds(5, self._on_timer_tick)

        root.append(Gtk.Separator())

        emergency_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        emergency_btn = Gtk.Button(label="Emergency Shutdown & Clear Session")
        emergency_btn.add_css_class("destructive-action")
        emergency_btn.connect("clicked", self._on_emergency_shutdown_clicked)
        emergency_box.append(emergency_btn)
        root.append(emergency_box)

    # -- D-Bus interaction -------------------------------------------

    def _on_mode_button_clicked(self, button, mode):
        if not self.dbus_available:
            return
        success = self.manager.SetMode(mode)
        if not success:
            button.set_active(False)
            self._show_toast(f"Failed to switch to {MODE_LABELS[mode]} — "
                              f"check permissions and mode-manager logs")
        self.refresh_status()

    def _on_timer_tick(self):
        self.refresh_status()
        return True  # keep the timer running

    def refresh_status(self):
        if not self.dbus_available:
            return

        current_mode = self.manager.GetMode()
        self.mode_label.set_label(f"Current mode: {MODE_LABELS.get(current_mode, current_mode)}")
        for mode, btn in self.mode_buttons.items():
            btn.set_active(mode == current_mode)
        self.lockdown_notice.set_visible(current_mode == "lockdown")

        status = self.manager.GetStatus()
        for field, label_widget in self.status_value_labels.items():
            value = status.get(field, "unknown")
            label_widget.set_label(value.replace("_", " "))
            label_widget.remove_css_class("status-good")
            label_widget.remove_css_class("status-neutral")
            if value in GOOD_VALUES.get(field, set()):
                label_widget.add_css_class("status-good")
            else:
                label_widget.add_css_class("status-neutral")

    def _show_toast(self, message):
        # Minimal fallback — a proper Adw.ToastOverlay wiring is a small
        # follow-up, not blocking this slice.
        print(f"[security-center] {message}")

    # -- Emergency Shutdown --------------------------------------------
    # Spec section 10: must NOT happen automatically, requires deliberate
    # confirmation, must explain exactly what's being cleared. This dialog
    # is the entire confirmation step — TriggerEmergencyShutdown() on the
    # daemon side trusts that this dialog, specifically, is what stood
    # between the button and the D-Bus call.

    def _on_emergency_shutdown_clicked(self, button):
        if not self.shutdown_available:
            self._show_toast(f"Cannot reach Emergency Shutdown Manager: "
                              f"{self._shutdown_dbus_error}")
            return

        info = self.shutdown_manager.GetPersistenceInfo()
        persistence_active = info.get("persistence_active", False)
        swap_active = info.get("swap_active", False)

        body_lines = [
            "This will terminate the current session and clear temporary "
            "session data where supported.",
        ]
        if persistence_active:
            body_lines.append("Encrypted persistence is mounted and will remain untouched.")
        else:
            body_lines.append("No persistence volume is mounted — this session is fully amnesic already.")
        if swap_active:
            body_lines.append(
                "\u26a0 Swap is currently active. Deactivating it does not "
                "erase data already written to swap on disk — this session "
                "cannot guarantee no trace remains if swap was used."
            )

        dialog = Adw.AlertDialog(
            heading="\u26a0 Emergency Shutdown",
            body="\n\n".join(body_lines),
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("shutdown", "Shut Down & Clear Session")
        dialog.set_response_appearance("shutdown", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_emergency_dialog_response)
        dialog.present(self)

    def _on_emergency_dialog_response(self, dialog, response):
        if response != "shutdown":
            return
        live_user = GLib.get_user_name() or "raptor"
        accepted = self.shutdown_manager.TriggerEmergencyShutdown(live_user, True)
        if not accepted:
            self._show_toast("Emergency Shutdown was refused — check permissions/logs")


class SecurityCenterApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.raptor.SecurityCenter")

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = SecurityCenterWindow(self)
        win.present()


if __name__ == "__main__":
    import sys
    app = SecurityCenterApp()
    sys.exit(app.run(sys.argv))
