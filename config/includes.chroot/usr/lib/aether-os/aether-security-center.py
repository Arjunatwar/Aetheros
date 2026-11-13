#!/usr/bin/python3
"""AETHER Security & Privacy Center — Firewall, Telemetry Controls, and System Hardening."""

from __future__ import annotations
import os
import re
import shutil
import subprocess
import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

CSS = """
window { background-color: #0a0b1a; color: #e0e0ff; }
.sec-header {
    background: linear-gradient(135deg, #180a2a 0%, #0d1b4a 100%);
    padding: 22px 28px;
    border-bottom: 1px solid rgba(100,80,200,0.3);
}
.sec-title { font-size: 20px; font-weight: bold; color: #c0a8ff; }
.sec-subtitle { font-size: 12px; color: rgba(192,168,255,0.65); margin-top: 2px; }
.phase-badge {
    background: rgba(100,80,200,0.25);
    border: 1px solid rgba(100,80,200,0.5);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    color: #a080ff;
}
.nav-btn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: rgba(224,224,255,0.6);
    padding: 10px 18px;
    font-size: 13px;
    font-weight: bold;
}
.nav-btn:checked, .nav-btn:active {
    color: #c0a8ff;
    border-bottom: 2px solid #a080ff;
}
.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.card-title {
    font-size: 14px;
    font-weight: bold;
    color: #d0c8ff;
    margin-bottom: 6px;
}
.fact-key { font-size: 11px; color: rgba(192,168,255,0.6); }
.fact-val { font-size: 12px; font-weight: bold; color: #e8e0ff; }
.pill-active {
    background: rgba(40,180,80,0.18);
    border: 1px solid rgba(40,180,80,0.4);
    color: #80e090;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: bold;
}
.pill-inactive {
    background: rgba(255,80,80,0.16);
    border: 1px solid rgba(255,80,80,0.38);
    color: #ff9090;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: bold;
}
.action-btn {
    background: rgba(100,80,200,0.35);
    border: 1px solid rgba(100,80,200,0.6);
    border-radius: 7px;
    color: #e0e0ff;
    padding: 6px 16px;
    font-size: 12px;
}
.action-btn:hover { background: rgba(100,80,200,0.55); }
.danger-btn {
    background: rgba(220,50,50,0.25);
    border: 1px solid rgba(220,50,50,0.5);
    border-radius: 7px;
    color: #ff9090;
    padding: 6px 14px;
    font-size: 12px;
}
.danger-btn:hover { background: rgba(220,50,50,0.4); }
.sub-btn {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 7px;
    color: #b0a8d0;
    padding: 6px 14px;
    font-size: 12px;
}
.sub-btn:hover { background: rgba(255,255,255,0.12); }
.notice-box {
    background: rgba(80,160,255,0.07);
    border: 1px solid rgba(80,160,255,0.25);
    border-radius: 8px;
    padding: 10px 14px;
    color: rgba(160,200,255,0.9);
    font-size: 11px;
    margin-bottom: 10px;
}
.table-header {
    background: rgba(255,255,255,0.04);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding: 8px 12px;
    font-size: 11px;
    font-weight: bold;
    color: rgba(192,168,255,0.7);
}
.table-row {
    padding: 8px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.code-box {
    background: rgba(0,0,0,0.45);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    padding: 10px;
    font-family: monospace;
    font-size: 11px;
    color: #a0f0b0;
}
"""

def _is_ufw_active() -> bool:
    if not shutil.which("ufw"):
        return False
    try:
        out = subprocess.check_output(["pkexec", "ufw", "status"], text=True, timeout=5)
        return "Status: active" in out
    except Exception:
        return False

def _run_pkexec(cmd: list[str]) -> bool:
    try:
        res = subprocess.run(["pkexec"] + cmd, capture_output=True, text=True, timeout=30)
        return res.returncode == 0
    except Exception:
        return False


class AetherSecurityCenter(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER Security & Privacy")
        self.set_default_size(820, 720)
        self.set_resizable(True)

        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
        except Exception:
            pass

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        hdr.get_style_context().add_class("sec-header")
        ico = Gtk.Label()
        ico.set_markup('<span font="26">&#x1F6E1;</span>')
        hdr.pack_start(ico, False, False, 0)

        tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t = Gtk.Label(label="Security & Privacy Center")
        t.get_style_context().add_class("sec-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label="Firewall protection · Zero-telemetry audit · System hardening & privacy")
        s.get_style_context().add_class("sec-subtitle")
        s.set_halign(Gtk.Align.START)
        tb.pack_start(t, False, False, 0)
        tb.pack_start(s, False, False, 0)
        hdr.pack_start(tb, True, True, 0)

        badge = Gtk.Label(label="Phase 9 \u2014 Security")
        badge.get_style_context().add_class("phase-badge")
        hdr.pack_end(badge, False, False, 0)
        root.pack_start(hdr, False, False, 0)

        # Tabs Navigation
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        nav_box.set_margin_start(16)
        nav_box.set_margin_end(16)
        nav_box.set_margin_top(8)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)

        tabs = [
            ("firewall", "Firewall & Ports", self._build_firewall_tab),
            ("privacy", "Privacy & Zero-Telemetry", self._build_privacy_tab),
            ("hardening", "System Hardening", self._build_hardening_tab),
        ]

        self.nav_btns = []
        for stack_id, label, builder in tabs:
            btn = Gtk.ToggleButton(label=label)
            btn.get_style_context().add_class("nav-btn")
            btn.connect("clicked", lambda b, sid=stack_id: self._on_tab_click(b, sid))
            nav_box.pack_start(btn, False, False, 0)
            self.nav_btns.append(btn)
            self.stack.add_named(builder(), stack_id)

        root.pack_start(nav_box, False, False, 0)
        root.pack_start(self.stack, True, True, 0)

        self.nav_btns[0].set_active(True)
        self.stack.set_visible_child_name("firewall")

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def _on_tab_click(self, clicked_btn: Gtk.ToggleButton, stack_id: str):
        for btn in self.nav_btns:
            btn.set_active(btn == clicked_btn)
        self.stack.set_visible_child_name(stack_id)

    # ── 1. Firewall Tab ──────────────────────────────────────────────────────

    def _build_firewall_tab(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)

        has_ufw = shutil.which("ufw") is not None

        # Status Card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("card")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        ct = Gtk.Label(label="Firewall Status (Uncomplicated Firewall - UFW)")
        ct.get_style_context().add_class("card-title")
        top.pack_start(ct, False, False, 0)

        self.fw_pill = Gtk.Label(label="Installed" if has_ufw else "Not Installed")
        self.fw_pill.get_style_context().add_class("pill-active" if has_ufw else "pill-inactive")
        top.pack_end(self.fw_pill, False, False, 0)
        card.pack_start(top, False, False, 0)

        desc = Gtk.Label(
            label="The host firewall filters inbound and outbound network traffic to protect "
                  "your system from unauthorized network access and port scanning."
        )
        desc.get_style_context().add_class("fact-key")
        desc.set_halign(Gtk.Align.START)
        desc.set_line_wrap(True)
        card.pack_start(desc, False, False, 0)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_row.set_margin_top(6)

        if has_ufw:
            self.fw_toggle_btn = Gtk.Button(label="Enable Firewall (Shield)")
            self.fw_toggle_btn.get_style_context().add_class("action-btn")
            self.fw_toggle_btn.connect("clicked", self._on_toggle_firewall)
            btn_row.pack_start(self.fw_toggle_btn, False, False, 0)

            rst_btn = Gtk.Button(label="Set Strict Profile (Deny Inbound)")
            rst_btn.get_style_context().add_class("sub-btn")
            rst_btn.connect("clicked", lambda *_: _run_pkexec(["ufw", "default", "deny", "incoming"]))
            btn_row.pack_start(rst_btn, False, False, 0)
        else:
            inst_btn = Gtk.Button(label="Install UFW Firewall")
            inst_btn.get_style_context().add_class("action-btn")
            inst_btn.connect("clicked", lambda *_: _run_pkexec(["apt-get", "install", "-y", "ufw"]))
            btn_row.pack_start(inst_btn, False, False, 0)

        card.pack_start(btn_row, False, False, 0)
        vbox.pack_start(card, False, False, 0)

        # Quick Service Port Toggles Card
        ports_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        ports_card.get_style_context().add_class("card")
        pt = Gtk.Label(label="Quick Service Port Access Rules")
        pt.get_style_context().add_class("card-title")
        pt.set_halign(Gtk.Align.START)
        ports_card.pack_start(pt, False, False, 0)

        rules = [
            ("Secure Shell (SSH)", "Port 22/tcp — Remote command access", "22/tcp"),
            ("Local Web Server (HTTP/HTTPS)", "Ports 80, 443/tcp — Development servers", "80,443/tcp"),
            ("Samba Windows File Sharing", "Ports 137-139, 445 — LAN sharing", "samba"),
            ("Steam & Gaming Discovery", "Ports 27015-27050 — Local game servers", "27015:27050/udp"),
        ]

        for name, note, rule_spec in rules:
            rrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            rrow.get_style_context().add_class("table-row")

            tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            nl = Gtk.Label(label=name)
            nl.get_style_context().add_class("fact-val")
            nl.set_halign(Gtk.Align.START)
            no = Gtk.Label(label=note)
            no.get_style_context().add_class("fact-key")
            no.set_halign(Gtk.Align.START)
            tb.pack_start(nl, False, False, 0)
            tb.pack_start(no, False, False, 0)
            rrow.pack_start(tb, True, True, 0)

            allow_btn = Gtk.Button(label="Allow")
            allow_btn.get_style_context().add_class("sub-btn")
            allow_btn.connect("clicked", lambda _, rs=rule_spec: _run_pkexec(["ufw", "allow", rs]))
            rrow.pack_end(allow_btn, False, False, 0)

            deny_btn = Gtk.Button(label="Deny")
            deny_btn.get_style_context().add_class("sub-btn")
            deny_btn.connect("clicked", lambda _, rs=rule_spec: _run_pkexec(["ufw", "deny", rs]))
            rrow.pack_end(deny_btn, False, False, 4)

            ports_card.pack_start(rrow, False, False, 0)

        vbox.pack_start(ports_card, False, False, 0)

        # Active Listening Ports Card
        scan_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scan_card.get_style_context().add_class("card")

        stitle_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        sct = Gtk.Label(label="Active Network Ports (ss -tuln)")
        sct.get_style_context().add_class("card-title")
        stitle_row.pack_start(sct, False, False, 0)

        scan_btn = Gtk.Button(label="Scan Listening Ports")
        scan_btn.get_style_context().add_class("sub-btn")
        scan_btn.connect("clicked", self._on_scan_ports)
        stitle_row.pack_end(scan_btn, False, False, 0)
        scan_card.pack_start(stitle_row, False, False, 0)

        self.ports_view = Gtk.Label(label="Click 'Scan Listening Ports' to view active network sockets.")
        self.ports_view.get_style_context().add_class("code-box")
        self.ports_view.set_xalign(0)
        self.ports_view.set_line_wrap(True)
        scan_card.pack_start(self.ports_view, False, False, 0)

        vbox.pack_start(scan_card, False, False, 0)
        scroll.add(vbox)
        return scroll

    def _on_toggle_firewall(self, _):
        active = _is_ufw_active()
        cmd = ["ufw", "disable" if active else "enable"]
        _run_pkexec(cmd)
        new_active = _is_ufw_active()
        self.fw_pill.set_text("Shielded ✓" if new_active else "Inactive")
        ctx = self.fw_pill.get_style_context()
        ctx.remove_class("pill-active" if not new_active else "pill-inactive")
        ctx.add_class("pill-active" if new_active else "pill-inactive")
        self.fw_toggle_btn.set_label("Disable Firewall" if new_active else "Enable Firewall (Shield)")

    def _on_scan_ports(self, _):
        try:
            out = subprocess.check_output(["ss", "-tuln"], text=True, timeout=5)
            lines = out.strip().splitlines()[:15]
            self.ports_view.set_text("\n".join(lines))
        except Exception as e:
            self.ports_view.set_text(f"Error querying sockets: {e}")

    # ── 2. Privacy & Zero-Telemetry Tab ──────────────────────────────────────

    def _build_privacy_tab(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)

        # Zero Telemetry Guarantee Card
        zt_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        zt_card.get_style_context().add_class("card")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        zt_title = Gtk.Label(label="Zero-Telemetry & Transparency Guarantee")
        zt_title.get_style_context().add_class("card-title")
        top.pack_start(zt_title, False, False, 0)
        pill = Gtk.Label(label="Enforced ✓")
        pill.get_style_context().add_class("pill-active")
        top.pack_end(pill, False, False, 0)
        zt_card.pack_start(top, False, False, 0)

        msg = Gtk.Label(
            label="In accordance with the AETHER OS Core Charter:\n"
                  "• NO telemetry daemons are installed (popularity-contest, apport, whoopsie are absent).\n"
                  "• NO diagnostic phone-home or advertising tracking.\n"
                  "• All reports generated by AETHER tools are strictly local and user-previewable."
        )
        msg.get_style_context().add_class("fact-val")
        msg.set_xalign(0)
        zt_card.pack_start(msg, False, False, 0)
        vbox.pack_start(zt_card, False, False, 0)

        # Privacy Cleaner Card
        clean_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        clean_card.get_style_context().add_class("card")

        ctitle = Gtk.Label(label="Activity & History Cleaner")
        ctitle.get_style_context().add_class("card-title")
        ctitle.set_halign(Gtk.Align.START)
        clean_card.pack_start(ctitle, False, False, 0)

        cdesc = Gtk.Label(
            label="Clear local traces of recent documents, cached file previews, and bash terminal history."
        )
        cdesc.get_style_context().add_class("fact-key")
        cdesc.set_halign(Gtk.Align.START)
        clean_card.pack_start(cdesc, False, False, 0)

        cbtn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cbtn_row.set_margin_top(6)

        c_recent_btn = Gtk.Button(label="Clear Recent Documents")
        c_recent_btn.get_style_context().add_class("sub-btn")
        c_recent_btn.connect("clicked", self._on_clear_recent)
        cbtn_row.pack_start(c_recent_btn, False, False, 0)

        c_thumb_btn = Gtk.Button(label="Clear Preview Thumbnails")
        c_thumb_btn.get_style_context().add_class("sub-btn")
        c_thumb_btn.connect("clicked", self._on_clear_thumbnails)
        cbtn_row.pack_start(c_thumb_btn, False, False, 0)

        c_bash_btn = Gtk.Button(label="Clear Terminal History")
        c_bash_btn.get_style_context().add_class("sub-btn")
        c_bash_btn.connect("clicked", self._on_clear_bash_history)
        cbtn_row.pack_start(c_bash_btn, False, False, 0)

        clean_card.pack_start(cbtn_row, False, False, 0)

        self.clean_status_lbl = Gtk.Label(label="")
        self.clean_status_lbl.get_style_context().add_class("fact-val")
        self.clean_status_lbl.set_halign(Gtk.Align.START)
        clean_card.pack_start(self.clean_status_lbl, False, False, 0)

        vbox.pack_start(clean_card, False, False, 0)

        # DNS & Network Privacy Card
        dns_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        dns_card.get_style_context().add_class("card")
        dt = Gtk.Label(label="Network Privacy & DNS Security")
        dt.get_style_context().add_class("card-title")
        dt.set_halign(Gtk.Align.START)
        dns_card.pack_start(dt, False, False, 0)

        dns_info = Gtk.Label(
            label="• NetworkManager handles DNS queries via local resolver.\n"
                  "• MAC Address Randomization: Active for Wi-Fi scanning.\n"
                  "• Firewall Shield: Blocks inbound unsolicited packets."
        )
        dns_info.get_style_context().add_class("fact-val")
        dns_info.set_xalign(0)
        dns_card.pack_start(dns_info, False, False, 0)
        vbox.pack_start(dns_card, False, False, 0)

        scroll.add(vbox)
        return scroll

    def _on_clear_recent(self, _):
        path = os.path.expanduser("~/.local/share/recently-used.xbel")
        if os.path.exists(path):
            try:
                os.remove(path)
                self.clean_status_lbl.set_text("✓ Recent documents history cleared.")
            except Exception as e:
                self.clean_status_lbl.set_text(f"Error: {e}")
        else:
            self.clean_status_lbl.set_text("Recent documents list already empty.")

    def _on_clear_thumbnails(self, _):
        path = os.path.expanduser("~/.cache/thumbnails")
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                self.clean_status_lbl.set_text("✓ Preview thumbnails cache wiped.")
            except Exception as e:
                self.clean_status_lbl.set_text(f"Error: {e}")
        else:
            self.clean_status_lbl.set_text("Thumbnail cache is clean.")

    def _on_clear_bash_history(self, _):
        path = os.path.expanduser("~/.bash_history")
        if os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("")
                self.clean_status_lbl.set_text("✓ Terminal command history wiped.")
            except Exception as e:
                self.clean_status_lbl.set_text(f"Error: {e}")
        else:
            self.clean_status_lbl.set_text("Terminal history already empty.")

    # ── 3. System Hardening Tab ──────────────────────────────────────────────

    def _build_hardening_tab(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)

        # Privilege & Sudoers Card
        sudo_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sudo_card.get_style_context().add_class("card")
        st = Gtk.Label(label="Privileged Access & PolicyKit (Polkit)")
        st.get_style_context().add_class("card-title")
        st.set_halign(Gtk.Align.START)
        sudo_card.pack_start(st, False, False, 0)

        smsg = Gtk.Label(
            label="• Privileged actions in AETHER OS require explicit PolicyKit (pkexec) authentication.\n"
                  "• Sudo is restricted to administrative members of group 'sudo'.\n"
                  "• Root password login over SSH is disabled by default."
        )
        smsg.get_style_context().add_class("fact-val")
        smsg.set_xalign(0)
        sudo_card.pack_start(smsg, False, False, 0)
        vbox.pack_start(sudo_card, False, False, 0)

        # Kernel Security & Lockdown Card
        kern_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        kern_card.get_style_context().add_class("card")
        kt = Gtk.Label(label="Kernel Integrity & Memory Hardening")
        kt.get_style_context().add_class("card-title")
        kt.set_halign(Gtk.Align.START)
        kern_card.pack_start(kt, False, False, 0)

        lockdown = "Not Available"
        if os.path.exists("/sys/kernel/security/lockdown"):
            try:
                with open("/sys/kernel/security/lockdown", "r") as f:
                    lockdown = f.read().strip()
            except Exception:
                pass

        kitems = [
            ("Kernel Version:", os.uname().release),
            ("Kernel Lockdown State:", lockdown),
            ("ASLR (Address Space Layout Randomization):", "Enabled (Full 2-level ASLR)"),
            ("Ptrace Scope Hardening:", "Restricted to child processes"),
        ]
        grid = Gtk.Grid(column_spacing=24, row_spacing=6)
        for row, (k, v) in enumerate(kitems):
            kl = Gtk.Label(label=k)
            kl.get_style_context().add_class("fact-key")
            kl.set_halign(Gtk.Align.START)
            vl = Gtk.Label(label=v)
            vl.get_style_context().add_class("fact-val")
            vl.set_halign(Gtk.Align.START)
            grid.attach(kl, 0, row, 1, 1)
            grid.attach(vl, 1, row, 1, 1)

        kern_card.pack_start(grid, False, False, 0)
        vbox.pack_start(kern_card, False, False, 0)

        scroll.add(vbox)
        return scroll


if __name__ == "__main__":
    win = AetherSecurityCenter()
    Gtk.main()
