"""
WinPurge Services Page
Windows service management with search, filters, batch operations,
and status indicators.
"""

import customtkinter as ctk
import threading
import logging
from typing import Dict, List, Optional, Set
from enum import Enum
from winpurge.gui.pages.backup import ConfirmDialog
from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.services import services_manager
from winpurge.core.backup import backup_manager

logger = logging.getLogger(__name__)


# ─── Constants ────────────────────────────────────────────────────────────────

RISK_FILTERS = ["all", "safe", "moderate", "advanced"]

STATUS_CONFIG = {
    "Running": {"color_key": "success", "icon": "🟢"},
    "Stopped": {"color_key": "text_disabled", "icon": "🔴"},
    "Disabled": {"color_key": "text_disabled", "icon": "⚫"},
    "Unknown": {"color_key": "text_disabled", "icon": "⚪"},
}


# ─── Service Item Widget ────────────────────────────────────────────────────

class ServiceItem(ctk.CTkFrame):
    """Single service card with info, status, risk badge, and action button."""

    def __init__(
        self,
        master,
        service: Dict,
        on_action: callable,
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

        self.service = service
        self.on_action = on_action
        self._is_processing = False

        self._build_ui()
        self._bind_hover()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # ── Left: info ──
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=12)

        # Title row: name + badges
        title_row = ctk.CTkFrame(info, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=self.service.get("display_name", "Unknown"),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
            anchor="w",
        ).pack(side="left")

        # Risk badge
        risk_level = self.service.get("risk_level", "moderate")
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

        # Status badge
        status = self.service.get("status", "Unknown")
        status_cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["Unknown"])
        status_color = self.theme.colors.get(
            status_cfg["color_key"], self.theme.colors["text_disabled"]
        )

        self.status_badge = ctk.CTkLabel(
            title_row,
            text=f"{status_cfg['icon']}  {status}",
            font=("Inter", 10),
            fg_color=self.theme.colors.get("bg_main", "#1A1A2E"),
            text_color=status_color,
            corner_radius=4,
            padx=6,
            pady=1,
        )
        self.status_badge.pack(side="left", padx=(6, 0))

        # Description
        desc = self.service.get("description", "")
        if desc:
            ctk.CTkLabel(
                info,
                text=desc,
                font=self.theme.get_font("small"),
                text_color=self.theme.colors["text_secondary"],
                wraplength=480,
                anchor="w",
                justify="left",
            ).pack(anchor="w", pady=(4, 0))

        # Technical info
        svc_name = self.service.get("name", "")
        start_type = self.service.get("start_type", "Unknown")
        ctk.CTkLabel(
            info,
            text=f"{svc_name}  •  {start_type}",
            font=("Consolas", 10),
            text_color=self.theme.colors["text_disabled"],
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # ── Right: action button ──
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=0, column=1, padx=(0, 16), pady=12, sticky="e")

        is_disabled = start_type == "Disabled"

        self.action_btn = ctk.CTkButton(
            action_frame,
            text=f"{'✅  Enable' if is_disabled else '⛔  Disable'}",
            width=100,
            height=32,
            fg_color=self.theme.colors["success"] if is_disabled else self.theme.colors["danger"],
            hover_color="#00E676" if is_disabled else "#FF8080",
            command=self._handle_action,
        )
        self.action_btn.pack()

    def _bind_hover(self) -> None:
        normal = self.theme.colors["bg_card"]
        hover = self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"])

        def on_enter(_):
            if not self._is_processing:
                self.configure(fg_color=hover)

        def on_leave(_):
            if not self._is_processing:
                self.configure(fg_color=normal)

        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)

    def _handle_action(self) -> None:
        action = "enable" if self.service.get("start_type") == "Disabled" else "disable"
        self.on_action(self.service.get("name", ""), action, self)

    def set_processing(self, active: bool) -> None:
        self._is_processing = active
        if active:
            self.configure(
                fg_color=self.theme.colors.get("bg_warning", "#3A2A00"),
                border_color=self.theme.colors.get("warning", "#FFA500"),
            )
            self.action_btn.configure(state="disabled")
        else:
            self.configure(
                fg_color=self.theme.colors["bg_card"],
                border_color=self.theme.colors["card_border"],
            )
            self.action_btn.configure(state="normal")

    # ── Properties for filtering ──

    @property
    def risk_level(self) -> str:
        return self.service.get("risk_level", "moderate")

    @property
    def category(self) -> str:
        return self.service.get("category", "other")

    @property
    def service_name(self) -> str:
        return self.service.get("name", "")

    def matches_search(self, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        searchable = " ".join([
            self.service.get("name", ""),
            self.service.get("display_name", ""),
            self.service.get("description", ""),
        ]).lower()
        return q in searchable


# ─── Services Summary Card ──────────────────────────────────────────────────

class ServicesSummary(ctk.CTkFrame):
    """Summary card showing service stats."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=14)

        for i in range(4):
            container.columnconfigure(i, weight=1)

        self.stat_labels: Dict[str, Tuple[ctk.CTkLabel, ctk.CTkLabel]] = {}

        stats = [
            ("total", "📋", t("services.stat_total")),
            ("running", "🟢", t("services.stat_running")),
            ("disabled", "⛔", t("services.stat_disabled")),
            ("manageable", "🔧", t("services.stat_manageable")),
        ]

        for i, (key, icon, label) in enumerate(stats):
            frame = ctk.CTkFrame(container, fg_color="transparent")
            frame.grid(row=0, column=i, padx=4, sticky="nsew")

            val = ctk.CTkLabel(
                frame,
                text="...",
                font=self.theme.get_font("header", "bold"),
                text_color=self.theme.colors["text_primary"],
            )
            val.pack(anchor="w")

            desc = ctk.CTkLabel(
                frame,
                text=f"{icon}  {label}",
                font=self.theme.get_font("small"),
                text_color=self.theme.colors["text_secondary"],
            )
            desc.pack(anchor="w")

            self.stat_labels[key] = (val, desc)

    def update_stats(
        self,
        total: int,
        running: int,
        disabled: int,
        manageable: int,
    ) -> None:
        values = {
            "total": (str(total), "normal"),
            "running": (str(running), "success"),
            "disabled": (str(disabled), "text_disabled"),
            "manageable": (str(manageable), "accent"),
        }
        for key, (text, color_key) in values.items():
            if key in self.stat_labels:
                val_label, _ = self.stat_labels[key]
                color = self.theme.colors.get(color_key, self.theme.colors["text_primary"])
                val_label.configure(text=text, text_color=color)


# ─── Filter & Search Bar ────────────────────────────────────────────────────

class ServiceFilterBar(ctk.CTkFrame):
    """Search input and risk-level filter tabs."""

    def __init__(self, master, on_change: callable, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._active_filter = "all"

        self._build_ui()

    def _build_ui(self) -> None:
        # Search
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 8))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._emit())

        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text=f"🔍  {t('services.search_placeholder')}",
            height=36,
            corner_radius=8,
            fg_color=self.theme.colors["bg_card"],
            border_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
        )
        self.search_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            search_frame,
            text="✕",
            width=36,
            height=36,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_secondary"],
            command=lambda: self.search_var.set(""),
        ).pack(side="left", padx=(4, 0))

        # Filter tabs
        tabs = ctk.CTkFrame(self, fg_color="transparent")
        tabs.pack(fill="x")

        self.tab_btns: Dict[str, ctk.CTkButton] = {}

        filter_labels = {
            "all": f"📋  {t('services.filter_all')}",
            "safe": f"✅  {t('services.filter_safe')}",
            "moderate": f"⚠️  {t('services.filter_moderate')}",
            "advanced": f"🔴  {t('services.filter_advanced')}",
        }

        for fid, label in filter_labels.items():
            is_active = fid == self._active_filter
            btn = ctk.CTkButton(
                tabs,
                text=label,
                height=30,
                corner_radius=6,
                fg_color=self.theme.colors["accent"] if is_active else "transparent",
                hover_color=self.theme.colors["accent_hover"] if is_active else self.theme.colors["bg_card"],
                text_color="#FFFFFF" if is_active else self.theme.colors["text_secondary"],
                font=self.theme.get_font("small"),
                command=lambda f=fid: self._set_filter(f),
            )
            btn.pack(side="left", padx=(0, 4))
            self.tab_btns[fid] = btn

    def _set_filter(self, fid: str) -> None:
        self._active_filter = fid
        for f, btn in self.tab_btns.items():
            is_active = f == fid
            btn.configure(
                fg_color=self.theme.colors["accent"] if is_active else "transparent",
                text_color="#FFFFFF" if is_active else self.theme.colors["text_secondary"],
            )
        self._emit()

    def _emit(self) -> None:
        self._on_change(self.search_var.get(), self._active_filter)

    @property
    def query(self) -> str:
        return self.search_var.get()

    @property
    def active_filter(self) -> str:
        return self._active_filter


# ─── Main Services Page ─────────────────────────────────────────────────────

class ServicesPage(ctk.CTkFrame):
    """Windows service management page with search, filters, and batch ops."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.service_items: Dict[str, ServiceItem] = {}
        self.all_services: List[Dict] = []
        self._is_loading = False

        self._build_ui()
        self.refresh_list()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 0))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=t("services.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            title_row,
            text=f"🔄  {t('services.refresh')}",
            width=130,
            height=32,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.refresh_list,
        )
        self.refresh_btn.pack(side="right")

        ctk.CTkLabel(
            header,
            text=t("services.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 0))

        # ── Summary card ──
        self.summary = ServicesSummary(self)
        self.summary.pack(fill="x", padx=32, pady=(12, 0))

        # ── Filter bar ──
        self.filter_bar = ServiceFilterBar(self, on_change=self._apply_filters)
        self.filter_bar.pack(fill="x", padx=32, pady=(12, 0))

        # ── Services list ──
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        self.list_frame.pack(fill="both", expand=True, padx=32, pady=(8, 24))

        self.state_label = ctk.CTkLabel(
            self.list_frame,
            text="",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )

    # ── Data Loading ─────────────────────────────────────────────────────

    def refresh_list(self) -> None:
        if self._is_loading:
            return

        self._is_loading = True
        self.refresh_btn.configure(state="disabled")
        self._show_state(f"⏳  {t('common.loading')}")
        self._clear_items()

        def _worker():
            try:
                services = services_manager.get_services_list()
                self.after(0, lambda: self._on_loaded(services))
            except Exception as e:
                logger.exception("Failed to load services")
                self.after(0, lambda: self._on_load_error(str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_loaded(self, services: List[Dict]) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self._hide_state()

        self.all_services = services

        if not services:
            self._show_state(f"📋  {t('services.none_found')}")
            self.summary.update_stats(0, 0, 0, 0)
            return

        # Update summary
        total = len(services)
        running = sum(1 for s in services if s.get("status") == "Running")
        disabled = sum(1 for s in services if s.get("start_type") == "Disabled")
        manageable = sum(1 for s in services if s.get("risk_level") == "safe")
        self.summary.update_stats(total, running, disabled, manageable)

        # Populate with current filter
        self._apply_filters(
            self.filter_bar.query,
            self.filter_bar.active_filter,
        )

    def _on_load_error(self, error: str) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self._show_state(f"❌  {t('common.error')}: {error}")

    # ── List Management ──────────────────────────────────────────────────

    def _clear_items(self) -> None:
        for widget in self.list_frame.winfo_children():
            if widget is not self.state_label:
                widget.destroy()
        self.service_items.clear()

    def _apply_filters(self, query: str, risk_filter: str) -> None:
        """Rebuild the list based on search query and risk filter."""
        filtered = [
            svc for svc in self.all_services
            if (risk_filter == "all" or svc.get("risk_level") == risk_filter)
            and (not query or query.lower() in " ".join([
                svc.get("name", ""),
                svc.get("display_name", ""),
                svc.get("description", ""),
            ]).lower())
        ]

        self._hide_state()

        if not filtered:
            self._clear_items()
            self._show_state(f"🔍  {t('services.no_results')}")
            return

        self._populate_list(filtered)

    def _populate_list(self, services: List[Dict]) -> None:
        self._clear_items()

        # Group by category
        categories: Dict[str, List[Dict]] = {}
        for svc in services:
            cat = svc.get("category", "other")
            categories.setdefault(cat, []).append(svc)

        cat_meta = services_manager.get_categories() if hasattr(services_manager, "get_categories") else {}

        for cat, svcs in sorted(categories.items()):
            cat_display = cat_meta.get(cat, {}).get("display_name", cat.replace("_", " ").title())
            icon = cat_meta.get(cat, {}).get("icon", "📂")

            # Category header
            header_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            header_frame.pack(fill="x", pady=(14, 6))

            ctk.CTkLabel(
                header_frame,
                text=f"{icon}  {cat_display} ({len(svcs)})",
                font=self.theme.get_font("body", "bold"),
                text_color=self.theme.colors["text_secondary"],
            ).pack(side="left")

            ctk.CTkFrame(
                header_frame,
                fg_color=self.theme.colors["card_border"],
                height=1,
            ).pack(side="left", fill="x", expand=True, padx=(12, 0), pady=1)

            # Sort by display name
            for svc in sorted(svcs, key=lambda s: s.get("display_name", "")):
                item = ServiceItem(
                    self.list_frame,
                    svc,
                    on_action=self._handle_service_action,
                )
                item.pack(fill="x", pady=2)
                self.service_items[svc.get("name", "")] = item

    # ── Service Actions ──────────────────────────────────────────────────

    def _handle_service_action(
        self,
        service_name: str,
        action: str,
        item: Optional[ServiceItem] = None,
    ) -> None:
        """Handle enable/disable for a single service."""
        from winpurge.gui.pages.backup import ConfirmDialog

        display = service_name
        if item:
            display = item.service.get("display_name", service_name)

        is_disable = action == "disable"
        verb = t("services.disabling") if is_disable else t("services.enabling")

        dialog = ConfirmDialog(
            self.winfo_toplevel(),
            title=f"{verb} {display}",
            message=t("services.confirm_action", action=verb.lower(), name=display),
            detail=t("services.confirm_action_detail"),
            confirm_text=f"{'⛔' if is_disable else '✅'}  {verb}",
            confirm_color=self.theme.colors["danger"] if is_disable else self.theme.colors["success"],
            icon="⛔" if is_disable else "✅",
            is_danger=is_disable,
        )

        if not dialog.result:
            return

        if item:
            item.set_processing(True)

        modal = ProgressModal(self.winfo_toplevel(), f"{verb} {display}")

        def _worker():
            try:
                modal.log(f"💾  {t('backup.creating_backup')}")
                try:
                    backup_manager.create_backup(f"Before {action} {service_name}")
                    modal.log(f"  ✓  {t('backup.backup_success')}", "success")
                except Exception as e:
                    modal.log(f"  ⚠  Backup skipped: {e}", "warning")

                modal.log(f"{'⛔' if is_disable else '✅'}  {verb} {display}...")
                modal.set_progress(0.5)

                if is_disable:
                    success, message = services_manager.disable_service(service_name)
                else:
                    success, message = services_manager.enable_service(service_name)

                if success:
                    modal.complete(True, f"✅  {message}")
                else:
                    modal.complete(False, f"❌  {message}")

            except Exception as e:
                logger.exception("Service action failed: %s %s", action, service_name)
                modal.complete(False, f"{t('common.error')}: {e}")
            finally:
                if item:
                    self.after(0, lambda: item.set_processing(False))
                self.after(500, self.refresh_list)

        threading.Thread(target=_worker, daemon=True).start()

    # ── State Helpers ────────────────────────────────────────────────────

    def _show_state(self, text: str) -> None:
        self.state_label.configure(text=text)
        self.state_label.pack(pady=40)

    def _hide_state(self) -> None:
        self.state_label.pack_forget()