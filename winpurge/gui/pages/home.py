"""
WinPurge Home Page
Dashboard with system info, quick stats, and one-click actions.
"""

import customtkinter as ctk
import threading
import logging
from typing import Callable, Dict, List, Optional, Tuple
from winpurge.gui.pages.backup import ConfirmDialog
from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import get_system_info, get_windows_version, t, get_relative_time
from winpurge.core.backup import backup_manager
from winpurge.core.bloatware import bloatware_manager
from winpurge.core.services import services_manager
from winpurge.core.telemetry import telemetry_manager

logger = logging.getLogger(__name__)


# ─── Stat Card ───────────────────────────────────────────────────────────────

COLOR_MAP = {
    "normal": lambda th: th.colors["text_primary"],
    "success": lambda th: th.colors["success"],
    "warning": lambda th: th.colors.get("warning", "#FFA500"),
    "danger": lambda th: th.colors["danger"],
    "accent": lambda th: th.colors["accent"],
}


class StatCard(ctk.CTkFrame):
    """Clickable stat card with icon, value, and label."""

    def __init__(
        self,
        master,
        icon: str,
        title: str,
        value: str = "...",
        color: str = "normal",
        on_click: Optional[Callable] = None,
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        self._on_click = on_click

        super().__init__(
            master,
            corner_radius=12,
            fg_color=self.theme.colors["bg_card"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            cursor="hand2" if on_click else "arrow",
            **kwargs,
        )

        self._build_ui(icon, title, value, color)
        self._bind_interactions()

    def _build_ui(self, icon: str, title: str, value: str, color: str) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=14)

        # Icon
        ctk.CTkLabel(
            container,
            text=icon,
            font=("Inter", 24),
        ).pack(anchor="w")

        # Value
        self.value_label = ctk.CTkLabel(
            container,
            text=value,
            font=self.theme.get_font("header", "bold"),
            text_color=self._resolve_color(color),
        )
        self.value_label.pack(anchor="w", pady=(6, 0))

        # Title
        self.title_label = ctk.CTkLabel(
            container,
            text=title,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.title_label.pack(anchor="w", pady=(2, 0))

    def _bind_interactions(self) -> None:
        normal = self.theme.colors["bg_card"]
        hover = self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"])

        def on_enter(_):
            self.configure(fg_color=hover)

        def on_leave(_):
            self.configure(fg_color=normal)

        if self._on_click:
            self.bind("<Button-1>", lambda _: self._on_click())
            self.bind("<Enter>", on_enter)
            self.bind("<Leave>", on_leave)

            # Propagate click to children
            for child in self.winfo_children():
                child.bind("<Button-1>", lambda _: self._on_click())

    def _resolve_color(self, color: str) -> str:
        resolver = COLOR_MAP.get(color)
        return resolver(self.theme) if resolver else self.theme.colors["text_primary"]

    def update_value(self, value: str, color: str = "normal") -> None:
        self.value_label.configure(
            text=value,
            text_color=self._resolve_color(color),
        )

    def update_title(self, title: str) -> None:
        self.title_label.configure(text=title)


# ─── System Info Table ───────────────────────────────────────────────────────

class SystemInfoCard(ctk.CTkFrame):
    """System information card with key-value rows."""

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

        self.info_labels: Dict[str, ctk.CTkLabel] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=16)

        info_items = [
            ("os", "🪟", t("home.os")),
            ("cpu", "🧠", t("home.cpu")),
            ("ram", "💾", t("home.ram")),
            ("disk", "💿", t("home.disk")),
            ("uptime", "⏱️", t("home.uptime")),
        ]

        for key, icon, label in info_items:
            row = ctk.CTkFrame(container, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row,
                text=f"{icon}  {label}:",
                font=self.theme.get_font("body"),
                text_color=self.theme.colors["text_secondary"],
                width=160,
                anchor="w",
            ).pack(side="left")

            value = ctk.CTkLabel(
                row,
                text="...",
                font=self.theme.get_font("body"),
                text_color=self.theme.colors["text_primary"],
                anchor="w",
            )
            value.pack(side="left", fill="x", expand=True)
            self.info_labels[key] = value

    def update_info(self, sys_info: Dict, win_ver: Dict) -> None:
        updates = {
            "os": win_ver.get("display", "Unknown"),
            "cpu": sys_info.get("cpu", "Unknown"),
            "ram": (
                f"{sys_info.get('ram_used', '?')} / {sys_info.get('ram_total', '?')} "
                f"({sys_info.get('ram_percent', 0)}%)"
            ),
            "disk": (
                f"{sys_info.get('disk_used', '?')} / {sys_info.get('disk_total', '?')} "
                f"({sys_info.get('disk_percent', 0)}%)"
            ),
            "uptime": sys_info.get("uptime", "Unknown"),
        }
        for key, text in updates.items():
            if key in self.info_labels:
                self.info_labels[key].configure(text=text)


# ─── Quick Action Card ──────────────────────────────────────────────────────

class QuickActionCard(ctk.CTkFrame):
    """Clickable action card with icon, title, description, and button."""

    def __init__(
        self,
        master,
        icon: str,
        title: str,
        description: str,
        button_text: str,
        button_color: str,
        button_hover: str,
        on_click: Callable,
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )
        self._build_ui(icon, title, description, button_text, button_color, button_hover, on_click)
        self._bind_hover()

    def _build_ui(
        self,
        icon: str,
        title: str,
        description: str,
        button_text: str,
        button_color: str,
        button_hover: str,
        on_click: Callable,
    ) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            container,
            text=f"{icon}  {title}",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            container,
            text=description,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
            wraplength=250,
        ).pack(anchor="w", pady=(4, 12))

        self.action_btn = ctk.CTkButton(
            container,
            text=button_text,
            height=34,
            fg_color=button_color,
            hover_color=button_hover,
            command=on_click,
        )
        self.action_btn.pack(anchor="w")

    def _bind_hover(self) -> None:
        normal = self.theme.colors["bg_card"]
        hover = self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"])

        self.bind("<Enter>", lambda _: self.configure(fg_color=hover))
        self.bind("<Leave>", lambda _: self.configure(fg_color=normal))


# ─── Main Home Page ─────────────────────────────────────────────────────────

class HomePage(ctk.CTkFrame):
    """Dashboard home page with system info, stats, and quick actions."""

    def __init__(self, master, on_navigate: Callable[[str], None], **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_navigate = on_navigate
        self._is_loading = False

        self._build_ui()
        self.refresh_data()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 0))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=t("home.title"),
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
            command=self.refresh_data,
        )
        self.refresh_btn.pack(side="right")

        ctk.CTkLabel(
            header,
            text=t("home.description"),
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

        self._build_system_info(content)
        self._build_quick_stats(content)
        self._build_quick_actions(content)

    # ── System Info ──────────────────────────────────────────────────────

    def _build_system_info(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"🖥️  {t('home.system_info')}")
        self.system_info_card = SystemInfoCard(parent)
        self.system_info_card.pack(fill="x", pady=(0, 20))

    # ── Quick Stats ──────────────────────────────────────────────────────

    def _build_quick_stats(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"📊  {t('home.quick_stats')}")

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 20))
        for i in range(4):
            grid.columnconfigure(i, weight=1)

        self.bloatware_card = StatCard(
            grid,
            icon="📦",
            title=t("home.bloatware_found", count="..."),
            on_click=lambda: self.on_navigate("bloatware"),
        )
        self.bloatware_card.grid(row=0, column=0, padx=(0, 6), pady=4, sticky="nsew")

        self.services_card = StatCard(
            grid,
            icon="🔍",
            title=t("home.tracking_services", count="..."),
            on_click=lambda: self.on_navigate("services"),
        )
        self.services_card.grid(row=0, column=1, padx=6, pady=4, sticky="nsew")

        self.telemetry_card = StatCard(
            grid,
            icon="📡",
            title=t("home.telemetry_status"),
            on_click=lambda: self.on_navigate("privacy"),
        )
        self.telemetry_card.grid(row=0, column=2, padx=6, pady=4, sticky="nsew")

        self.backup_card = StatCard(
            grid,
            icon="💾",
            title=t("home.last_backup"),
            on_click=lambda: self.on_navigate("backup"),
        )
        self.backup_card.grid(row=0, column=3, padx=(6, 0), pady=4, sticky="nsew")

    # ── Quick Actions ────────────────────────────────────────────────────

    def _build_quick_actions(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"⚡  {t('home.quick_actions')}")

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x")
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        QuickActionCard(
            grid,
            icon="🚀",
            title=t("home.apply_recommended"),
            description=t("home.apply_recommended_desc"),
            button_text=t("home.apply_recommended"),
            button_color=self.theme.colors["accent"],
            button_hover=self.theme.colors["accent_hover"],
            on_click=self._apply_recommended,
        ).grid(row=0, column=0, padx=(0, 6), pady=4, sticky="nsew")

        QuickActionCard(
            grid,
            icon="💾",
            title=t("home.create_backup"),
            description=t("home.create_backup_desc"),
            button_text=t("home.create_backup"),
            button_color=self.theme.colors["success"],
            button_hover="#00E676",
            on_click=self._create_backup,
        ).grid(row=0, column=1, padx=6, pady=4, sticky="nsew")

        QuickActionCard(
            grid,
            icon="🔄",
            title=t("home.restore_backup"),
            description=t("home.restore_backup_desc"),
            button_text=t("home.restore_backup"),
            button_color=self.theme.colors["bg_card"],
            button_hover=self.theme.colors["card_border"],
            on_click=self._restore_backup,
        ).grid(row=0, column=2, padx=(6, 0), pady=4, sticky="nsew")

    # ── Section Header Helper ────────────────────────────────────────────

    def _section_header(self, parent: ctk.CTkFrame, text: str) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 10))

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

    # ── Data Loading ─────────────────────────────────────────────────────

    def refresh_data(self) -> None:
        """Refresh all dashboard data asynchronously."""
        if self._is_loading:
            return

        self._is_loading = True
        self.refresh_btn.configure(state="disabled")

        def _worker():
            try:
                # System info
                sys_info = get_system_info()
                win_ver = get_windows_version()
                self.after(0, lambda: self.system_info_card.update_info(sys_info, win_ver))

                # Quick stats
                bloatware_count = bloatware_manager.get_bloatware_count()
                tracking_count = services_manager.get_tracking_services_count()
                telemetry_blocked = telemetry_manager.is_telemetry_blocked()
                last_backup = backup_manager.get_last_backup_time()

                self.after(0, lambda: self._update_stats(
                    bloatware_count, tracking_count, telemetry_blocked, last_backup
                ))

            except Exception as e:
                logger.exception("Failed to refresh dashboard data")
            finally:
                self.after(0, self._on_load_complete)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_load_complete(self) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")

    def _update_stats(
        self,
        bloatware_count: int,
        tracking_count: int,
        telemetry_blocked: bool,
        last_backup,
    ) -> None:
        # Bloatware
        self.bloatware_card.update_value(
            str(bloatware_count),
            "warning" if bloatware_count > 5 else ("success" if bloatware_count == 0 else "normal"),
        )
        self.bloatware_card.update_title(t("home.bloatware_found", count=bloatware_count))

        # Services
        self.services_card.update_value(
            str(tracking_count),
            "danger" if tracking_count > 0 else "success",
        )
        self.services_card.update_title(t("home.tracking_services", count=tracking_count))

        # Telemetry
        if telemetry_blocked:
            self.telemetry_card.update_value(t("home.telemetry_blocked"), "success")
        else:
            self.telemetry_card.update_value(t("home.telemetry_enabled"), "danger")

        # Backup
        if last_backup:
            self.backup_card.update_value(get_relative_time(last_backup), "success")
        else:
            self.backup_card.update_value(t("home.no_backup"), "warning")

    # ── Actions ──────────────────────────────────────────────────────────

    def _apply_recommended(self) -> None:
        """Apply recommended safe tweaks with progress tracking."""
        modal = ProgressModal(self.winfo_toplevel(), t("home.apply_recommended"))

        def _worker():
            try:
                from winpurge.core.privacy import privacy_manager

                # Backup first
                modal.log(f"💾  {t('backup.creating_backup')}")
                try:
                    backup_manager.create_backup("Before recommended optimizations")
                    modal.log(f"  ✓  {t('backup.backup_success')}", "success")
                except Exception as e:
                    modal.log(f"  ⚠  Backup skipped: {e}", "warning")

                steps: List[Tuple[str, Callable]] = [
                    (t("home.step_telemetry"), telemetry_manager.disable_telemetry),
                    (t("home.step_advertising"), telemetry_manager.disable_advertising_id),
                    (t("home.step_input_telemetry"), telemetry_manager.disable_input_telemetry),
                    (t("home.step_cortana"), privacy_manager.disable_cortana),
                    (t("home.step_copilot"), privacy_manager.disable_copilot),
                    (t("home.step_suggestions"), privacy_manager.disable_start_suggestions),
                    (t("home.step_lock_ads"), privacy_manager.disable_lock_screen_ads),
                ]

                total = len(steps)
                success_count = 0

                for i, (label, func) in enumerate(steps, 1):
                    if modal.cancelled:
                        modal.log(f"⏹  {t('common.cancelled')}", "warning")
                        break

                    modal.log(f"⚡  {label}")
                    modal.set_progress(i / total, f"{i}/{total}")

                    try:
                        success, _ = func()
                        if success:
                            success_count += 1
                            modal.log("  ✓  Done", "success")
                        else:
                            modal.log("  ✗  Failed", "error")
                    except Exception as e:
                        modal.log(f"  ✗  {e}", "error")

                if not modal.cancelled:
                    modal.complete(
                        success_count == total,
                        t("home.apply_complete",
                          success=success_count, total=total),
                    )

            except Exception as e:
                logger.exception("Apply recommended failed")
                modal.complete(False, f"{t('common.error')}: {e}")

            self.after(0, self.refresh_data)

        threading.Thread(target=_worker, daemon=True).start()

    def _create_backup(self) -> None:
        """Create a system backup."""
        modal = ProgressModal(self.winfo_toplevel(), t("home.create_backup"))

        def _worker():
            try:
                modal.log(f"💾  {t('backup.creating_backup')}")
                modal.set_progress(0.5)

                success, message, path = backup_manager.create_backup("Manual backup from dashboard")

                if success:
                    modal.log(f"  ✓  Saved to: {path}", "success")
                    modal.complete(True, t("backup.backup_success"))
                else:
                    modal.complete(False, t("backup.backup_failed", error=message))

            except Exception as e:
                logger.exception("Backup creation failed")
                modal.complete(False, str(e))

            self.after(0, self.refresh_data)

        threading.Thread(target=_worker, daemon=True).start()

    def _restore_backup(self) -> None:
        """Restore the most recent backup."""
        try:
            backups = backup_manager.get_backups()
        except Exception as e:
            logger.exception("Failed to list backups")
            return

        if not backups:
            from winpurge.gui.pages.backup import ConfirmDialog
            ConfirmDialog(
                self.winfo_toplevel(),
                title=t("common.warning"),
                message=t("backup.no_backups"),
                detail=t("backup.no_backups_hint"),
                confirm_text="OK",
                confirm_color=self.theme.colors["accent"],
                icon="📂",
            )
            return

        from winpurge.gui.pages.backup import ConfirmDialog

        latest = backups[0]
        dialog = ConfirmDialog(
            self.winfo_toplevel(),
            title=t("backup.confirm_restore_title"),
            message=t("backup.confirm_restore"),
            detail=f"📅  {latest.get('date', '?')}\n{latest.get('description', '')}",
            confirm_text=t("backup.restore"),
            confirm_color=self.theme.colors["accent"],
            icon="🔄",
        )

        if not dialog.result:
            return

        modal = ProgressModal(self.winfo_toplevel(), t("home.restore_backup"))

        def _worker():
            try:
                modal.log(f"🔄  {t('backup.restoring')}")
                modal.set_progress(0.5)

                success, message = backup_manager.restore_backup(latest["path"])

                if success:
                    modal.complete(True, t("backup.restore_success"))
                else:
                    modal.complete(False, t("backup.restore_failed", error=message))

            except Exception as e:
                logger.exception("Restore failed")
                modal.complete(False, str(e))

            self.after(0, self.refresh_data)

        threading.Thread(target=_worker, daemon=True).start()