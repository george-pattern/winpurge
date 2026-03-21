"""
WinPurge Network Page
DNS configuration, hosts file editor, and network optimizations.
"""

import customtkinter as ctk
import threading
import logging
from typing import Dict, List, Optional

from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.network import network_manager
from winpurge.constants import DNS_PRESETS

logger = logging.getLogger(__name__)


# ─── DNS Preset Card ────────────────────────────────────────────────────────

class DNSPresetCard(ctk.CTkFrame):
    """Selectable DNS preset card with provider info."""

    def __init__(
        self,
        master,
        preset_id: str,
        name: str,
        description: str,
        icon: str,
        on_select: callable,
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        self.preset_id = preset_id
        self._on_select = on_select
        self._is_selected = False

        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=10,
            border_width=2,
            border_color=self.theme.colors["card_border"],
            cursor="hand2",
            **kwargs,
        )

        self._build_ui(icon, name, description)
        self._bind_events()

    def _build_ui(self, icon: str, name: str, description: str) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(
            container,
            text=icon,
            font=("Inter", 22),
        ).pack(anchor="w")

        ctk.CTkLabel(
            container,
            text=name,
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            container,
            text=description,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
            anchor="w",
            wraplength=160,
        ).pack(anchor="w", pady=(2, 0))

        # IPs
        preset = DNS_PRESETS.get(self.preset_id, {})
        primary = preset.get("primary", "")
        secondary = preset.get("secondary", "")
        if primary:
            ctk.CTkLabel(
                container,
                text=f"{primary}" + (f", {secondary}" if secondary else ""),
                font=("Consolas", 9),
                text_color=self.theme.colors["text_disabled"],
                anchor="w",
            ).pack(anchor="w", pady=(4, 0))

    def _bind_events(self) -> None:
        normal_border = self.theme.colors["card_border"]
        hover_border = self.theme.colors.get("text_disabled", "#555")

        def on_enter(_):
            if not self._is_selected:
                self.configure(border_color=hover_border)

        def on_leave(_):
            if not self._is_selected:
                self.configure(border_color=normal_border)

        def on_click(_):
            self._on_select(self.preset_id)

        for widget in [self] + list(self.winfo_children()):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        if selected:
            self.configure(
                border_color=self.theme.colors["accent"],
                fg_color=self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"]),
            )
        else:
            self.configure(
                border_color=self.theme.colors["card_border"],
                fg_color=self.theme.colors["bg_card"],
            )


# ─── Hosts File Editor ──────────────────────────────────────────────────────

class HostsEditor(ctk.CTkFrame):
    """Hosts file viewer/editor with line count and save."""

    def __init__(self, master, on_save: callable, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )
        self._on_save = on_save
        self._original_content = ""
        self._build_ui()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # Header row
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        self.entries_label = ctk.CTkLabel(
            header,
            text=t("network.hosts_entries", count="..."),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.entries_label.pack(side="left")

        self.modified_badge = ctk.CTkLabel(
            header,
            text="● Modified",
            font=self.theme.get_font("small", "bold"),
            text_color=self.theme.colors.get("warning", "#FFA500"),
        )
        # Not packed initially — shown on edit

        # Text editor
        self.text = ctk.CTkTextbox(
            container,
            height=220,
            font=("Consolas", 11),
            fg_color=self.theme.colors.get("bg_main", "#1A1A2E"),
            text_color=self.theme.colors["text_primary"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            corner_radius=8,
        )
        self.text.pack(fill="x", pady=(0, 12))
        self.text.bind("<KeyRelease>", self._on_text_change)

        # Actions
        actions = ctk.CTkFrame(container, fg_color="transparent")
        actions.pack(fill="x")

        self.save_btn = ctk.CTkButton(
            actions,
            text=f"💾  {t('network.save_hosts')}",
            height=34,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._handle_save,
            state="disabled",
        )
        self.save_btn.pack(side="left")

        ctk.CTkButton(
            actions,
            text=f"↩️  {t('network.revert_hosts')}",
            height=34,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            command=self._revert,
        ).pack(side="left", padx=(8, 0))

    def set_content(self, content: str, entry_count: int) -> None:
        self._original_content = content
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.entries_label.configure(text=t("network.hosts_entries", count=entry_count))
        self.modified_badge.pack_forget()
        self.save_btn.configure(state="disabled")

    def _on_text_change(self, _event=None) -> None:
        current = self.text.get("1.0", "end-1c")
        is_modified = current != self._original_content

        if is_modified:
            self.modified_badge.pack(side="left", padx=(8, 0))
            self.save_btn.configure(state="normal")
        else:
            self.modified_badge.pack_forget()
            self.save_btn.configure(state="disabled")

    def _handle_save(self) -> None:
        content = self.text.get("1.0", "end-1c")
        self._on_save(content)

    def _revert(self) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", self._original_content)
        self._on_text_change()


# ─── Network Optimization Card ──────────────────────────────────────────────

class NetworkOptCard(ctk.CTkFrame):
    """Single network optimization with description and apply button."""

    def __init__(
        self,
        master,
        icon: str,
        title: str,
        description: str,
        risk_level: str = "safe",
        on_apply: callable = None,
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )
        self._build_ui(icon, title, description, risk_level, on_apply)
        self._bind_hover()

    def _build_ui(self, icon, title, description, risk_level, on_apply) -> None:
        self.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=12)

        # Title + risk badge
        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=f"{icon}  {title}",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")

        if risk_level != "safe":
            risk_colors = self.theme.get_risk_colors(risk_level)
            ctk.CTkLabel(
                title_row,
                text=t(f"risk_levels.{risk_level}"),
                font=("Inter", 10, "bold"),
                fg_color=risk_colors["bg"],
                text_color=risk_colors["fg"],
                corner_radius=4,
                padx=6,
                pady=1,
            ).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            left,
            text=description,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
            wraplength=500,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        if on_apply:
            self.apply_btn = ctk.CTkButton(
                self,
                text=f"⚡  {t('common.apply')}",
                width=90,
                height=32,
                fg_color=self.theme.colors["accent"],
                hover_color=self.theme.colors["accent_hover"],
                command=on_apply,
            )
            self.apply_btn.grid(row=0, column=1, padx=(0, 16), pady=12, sticky="e")

    def _bind_hover(self) -> None:
        normal = self.theme.colors["bg_card"]
        hover = self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"])
        self.bind("<Enter>", lambda _: self.configure(fg_color=hover))
        self.bind("<Leave>", lambda _: self.configure(fg_color=normal))


# ─── Main Network Page ──────────────────────────────────────────────────────

class NetworkPage(ctk.CTkFrame):
    """Network configuration page with DNS, hosts editor, and optimizations."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.selected_dns: Optional[str] = None
        self.dns_cards: Dict[str, DNSPresetCard] = {}
        self._is_loading = False

        self._build_ui()
        self.refresh_status()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 0))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=t("network.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            title_row,
            text=f"🔄  {t('common.refresh')}",
            width=120,
            height=32,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.refresh_status,
        )
        self.refresh_btn.pack(side="right")

        ctk.CTkLabel(
            header,
            text=t("network.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 0))

        # ── Scrollable content ──
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        content.pack(fill="both", expand=True, padx=32, pady=(12, 24))

        self._build_dns_section(content)
        self._build_hosts_section(content)
        self._build_optimization_section(content)

    # ── DNS Section ──────────────────────────────────────────────────────

    def _build_dns_section(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"🌐  {t('network.dns_settings')}")

        # Current DNS info
        status_frame = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        status_frame.pack(fill="x", pady=(0, 12))

        status_inner = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            status_inner,
            text=f"📡  {t('network.current_dns')}:",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(side="left")

        self.current_dns_label = ctk.CTkLabel(
            status_inner,
            text="...",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        self.current_dns_label.pack(side="left", padx=(8, 0))

        # DNS preset cards grid
        ctk.CTkLabel(
            parent,
            text=t("network.select_dns_provider"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(0, 8))

        preset_grid = ctk.CTkFrame(parent, fg_color="transparent")
        preset_grid.pack(fill="x", pady=(0, 12))
        for i in range(4):
            preset_grid.columnconfigure(i, weight=1)

        dns_presets_ui = [
            ("cloudflare", "☁️", t("network.dns_cloudflare"), "Fast & private DNS"),
            ("google", "🔍", t("network.dns_google"), "Reliable public DNS"),
            ("adguard", "🛡️", t("network.dns_adguard"), "Ad-blocking DNS"),
            ("quad9", "🔒", t("network.dns_quad9"), "Security-focused DNS"),
        ]

        for i, (pid, icon, name, desc) in enumerate(dns_presets_ui):
            card = DNSPresetCard(
                preset_grid,
                preset_id=pid,
                name=name,
                description=desc,
                icon=icon,
                on_select=self._select_dns,
            )
            card.grid(row=0, column=i, padx=(0 if i == 0 else 4, 0 if i == 3 else 4), pady=4, sticky="nsew")
            self.dns_cards[pid] = card

        # Custom DNS
        custom_frame = ctk.CTkFrame(parent, fg_color="transparent")
        custom_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            custom_frame,
            text=f"⌨️  {t('network.dns_custom')}:",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(side="left")

        self.custom_dns_entry = ctk.CTkEntry(
            custom_frame,
            width=220,
            height=34,
            placeholder_text="e.g., 1.1.1.1",
            fg_color=self.theme.colors.get("input_bg", self.theme.colors["bg_card"]),
            border_color=self.theme.colors.get("input_border", self.theme.colors["card_border"]),
            corner_radius=8,
        )
        self.custom_dns_entry.pack(side="left", padx=(8, 0))

        # DNS action buttons
        dns_actions = ctk.CTkFrame(parent, fg_color="transparent")
        dns_actions.pack(fill="x", pady=(0, 16))

        self.apply_dns_btn = ctk.CTkButton(
            dns_actions,
            text=f"⚡  {t('network.apply_dns')}",
            height=36,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._apply_dns,
        )
        self.apply_dns_btn.pack(side="left")

        ctk.CTkButton(
            dns_actions,
            text=f"↩️  {t('network.reset_dns')}",
            height=36,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            command=self._reset_dns,
        ).pack(side="left", padx=(8, 0))

    # ── Hosts Section ────────────────────────────────────────────────────

    def _build_hosts_section(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"📝  {t('network.hosts_file')}")

        self.hosts_editor = HostsEditor(parent, on_save=self._save_hosts)
        self.hosts_editor.pack(fill="x", pady=(0, 16))

    # ── Optimization Section ─────────────────────────────────────────────

    def _build_optimization_section(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"⚡  {t('network.network_optimization')}")

        optimizations = [
            {
                "icon": "📦",
                "title": t("network.disable_lso"),
                "description": t("network.disable_lso_desc"),
                "risk_level": "moderate",
                "on_apply": self._disable_lso,
            },
            {
                "icon": "📡",
                "title": t("network.enable_rss"),
                "description": t("network.enable_rss_desc"),
                "risk_level": "safe",
                "on_apply": self._enable_rss,
            },
        ]

        for opt in optimizations:
            NetworkOptCard(parent, **opt).pack(fill="x", pady=3)

    # ── Section Header Helper ────────────────────────────────────────────

    def _section_header(self, parent: ctk.CTkFrame, text: str) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(16, 10))

        ctk.CTkLabel(
            frame,
            text=text,
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")

        ctk.CTkFrame(
            frame,
            fg_color=self.theme.colors["card_border"],
            height=1,
        ).pack(side="left", fill="x", expand=True, padx=(12, 0), pady=1)

    # ── DNS Selection ────────────────────────────────────────────────────

    def _select_dns(self, preset_id: str) -> None:
        self.selected_dns = preset_id
        for pid, card in self.dns_cards.items():
            card.set_selected(pid == preset_id)
        self.custom_dns_entry.delete(0, "end")

    # ── Data Loading ─────────────────────────────────────────────────────

    def refresh_status(self) -> None:
        if self._is_loading:
            return

        self._is_loading = True
        self.refresh_btn.configure(state="disabled")

        def _load():
            try:
                dns_config = network_manager.get_current_dns()
                hosts_content = network_manager.get_hosts_file_content()
                hosts_count = network_manager.get_hosts_entry_count()
                self.after(0, lambda: self._on_status_loaded(dns_config, hosts_content, hosts_count))
            except Exception as e:
                logger.exception("Failed to load network status")
                self.after(0, lambda: self._on_load_error(str(e)))

        threading.Thread(target=_load, daemon=True).start()

    def _on_status_loaded(self, dns_config: Dict, hosts_content: str, hosts_count: int) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")

        # DNS display
        if dns_config:
            first_value = next(iter(dns_config.values()), "Unknown")
            self.current_dns_label.configure(text=str(first_value))
        else:
            self.current_dns_label.configure(text="Automatic (DHCP)")

        # Hosts editor
        self.hosts_editor.set_content(hosts_content, hosts_count)

    def _on_load_error(self, error: str) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self.current_dns_label.configure(text=f"❌ Error: {error}")

    # ── DNS Actions ──────────────────────────────────────────────────────

    def _apply_dns(self) -> None:
        custom_dns = self.custom_dns_entry.get().strip()

        if custom_dns:
            self._apply_custom_dns(custom_dns)
        elif self.selected_dns:
            self._apply_preset_dns(self.selected_dns)
        else:
            logger.info("No DNS selection made")

    def _apply_custom_dns(self, dns: str) -> None:
        modal = ProgressModal(self.winfo_toplevel(), t("network.applying_dns"))

        def _worker():
            try:
                modal.log(f"🌐  Setting DNS to {dns}")
                interfaces = network_manager.get_network_interfaces()
                success_count = 0

                for i, iface in enumerate(interfaces):
                    modal.set_progress((i + 1) / max(len(interfaces), 1))
                    success, message = network_manager.set_dns(iface, dns)
                    if success:
                        success_count += 1
                        modal.log(f"  ✓  {iface}: {message}", "success")
                    else:
                        modal.log(f"  ✗  {iface}: {message}", "error")

                modal.complete(
                    success_count > 0,
                    t("network.dns_applied", count=success_count),
                )
            except Exception as e:
                logger.exception("Custom DNS apply failed")
                modal.complete(False, str(e))

            self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_preset_dns(self, preset_id: str) -> None:
        preset = DNS_PRESETS.get(preset_id, {})
        name = preset.get("name", preset_id)

        modal = ProgressModal(self.winfo_toplevel(), f"{t('network.applying_dns')}: {name}")

        def _worker():
            try:
                modal.log(f"🌐  Applying {name} DNS...")
                modal.set_progress(0.5)

                success, message = network_manager.set_dns_preset(preset_id)

                if success:
                    modal.complete(True, message)
                else:
                    modal.complete(False, message)

            except Exception as e:
                logger.exception("Preset DNS apply failed")
                modal.complete(False, str(e))

            self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()

    def _reset_dns(self) -> None:
        modal = ProgressModal(self.winfo_toplevel(), t("network.resetting_dns"))

        def _worker():
            try:
                modal.log(f"↩️  {t('network.resetting_dns')}")
                modal.set_progress(0.5)

                success, message = network_manager.reset_dns()

                if success:
                    modal.complete(True, message)
                else:
                    modal.complete(False, message)

            except Exception as e:
                logger.exception("DNS reset failed")
                modal.complete(False, str(e))

            # Deselect all preset cards
            self.selected_dns = None
            self.after(0, lambda: [c.set_selected(False) for c in self.dns_cards.values()])
            self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()

    # ── Hosts Actions ────────────────────────────────────────────────────

    def _save_hosts(self, content: str) -> None:
        modal = ProgressModal(self.winfo_toplevel(), t("network.saving_hosts"))

        def _worker():
            try:
                modal.log(f"💾  {t('network.saving_hosts')}")
                modal.set_progress(0.5)

                success, message = network_manager.save_hosts_file(content)

                if success:
                    modal.complete(True, message)
                else:
                    modal.complete(False, message)

            except Exception as e:
                logger.exception("Hosts save failed")
                modal.complete(False, str(e))

            self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()

    # ── Network Optimization Actions ─────────────────────────────────────

    def _run_network_action(self, title: str, func: callable) -> None:
        """Generic wrapper for network optimization actions."""
        modal = ProgressModal(self.winfo_toplevel(), title)

        def _worker():
            try:
                modal.log(f"⚡  {title}")
                modal.set_progress(0.5)

                success, message = func()

                if success:
                    modal.complete(True, message)
                else:
                    modal.complete(False, message)

            except Exception as e:
                logger.exception("Network action '%s' failed", title)
                modal.complete(False, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _disable_lso(self) -> None:
        self._run_network_action(
            t("network.disable_lso"),
            network_manager.disable_large_send_offload,
        )

    def _enable_rss(self) -> None:
        self._run_network_action(
            t("network.enable_rss"),
            network_manager.enable_receive_side_scaling,
        )