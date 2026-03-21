"""
WinPurge Gaming Page
Gaming optimizations with toggle cards, status tracking, and batch apply.
"""

import customtkinter as ctk
import subprocess
import threading
import logging
from typing import Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass
from winpurge.gui.pages.backup import ConfirmDialog
from winpurge.gui.theme import get_theme
from winpurge.gui.components.toggle_card import ToggleCard
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.gaming import gaming_manager
from winpurge.core.backup import backup_manager

logger = logging.getLogger(__name__)


# ─── Optimization Definitions ────────────────────────────────────────────────

@dataclass(frozen=True)
class OptimizationDef:
    """Definition of a single gaming optimization."""
    id: str
    title_key: str
    desc_key: str
    risk_level: str
    section: str
    status_key: str
    apply_func_name: str
    invert_status: bool = False  # True if status=True means "disabled"


SECTIONS = {
    "performance": {
        "title_key": "gaming.category_performance",
        "icon": "⚡",
    },
    "input": {
        "title_key": "gaming.category_input",
        "icon": "🖱️",
    },
    "network": {
        "title_key": "gaming.category_network",
        "icon": "🌐",
    },
}

OPTIMIZATIONS: List[OptimizationDef] = [
    # ── Performance ──
    OptimizationDef(
        id="game_mode",
        title_key="gaming.enable_game_mode",
        desc_key="gaming.enable_game_mode_desc",
        risk_level="safe",
        section="performance",
        status_key="game_mode_enabled",
        apply_func_name="enable_game_mode",
    ),
    OptimizationDef(
        id="game_bar",
        title_key="gaming.disable_game_bar",
        desc_key="gaming.disable_game_bar_desc",
        risk_level="safe",
        section="performance",
        status_key="game_bar_disabled",
        apply_func_name="disable_game_bar",
    ),
    OptimizationDef(
        id="game_dvr",
        title_key="gaming.disable_game_dvr",
        desc_key="gaming.disable_game_dvr_desc",
        risk_level="safe",
        section="performance",
        status_key="game_dvr_disabled",
        apply_func_name="disable_game_dvr",
    ),
    OptimizationDef(
        id="power_plan",
        title_key="gaming.high_performance_power",
        desc_key="gaming.high_performance_power_desc",
        risk_level="safe",
        section="performance",
        status_key="high_performance_power",
        apply_func_name="set_high_performance_power",
    ),
    OptimizationDef(
        id="fullscreen_opt",
        title_key="gaming.disable_fullscreen_opt",
        desc_key="gaming.disable_fullscreen_opt_desc",
        risk_level="safe",
        section="performance",
        status_key="fullscreen_optimizations_disabled",
        apply_func_name="disable_fullscreen_optimizations",
    ),
    # ── Input ──
    OptimizationDef(
        id="mouse_accel",
        title_key="gaming.disable_mouse_accel",
        desc_key="gaming.disable_mouse_accel_desc",
        risk_level="safe",
        section="input",
        status_key="mouse_acceleration_disabled",
        apply_func_name="disable_mouse_acceleration",
    ),
    # ── Network ──
    OptimizationDef(
        id="nagle",
        title_key="gaming.disable_nagle",
        desc_key="gaming.disable_nagle_desc",
        risk_level="moderate",
        section="network",
        status_key="nagle_disabled",
        apply_func_name="disable_nagle_algorithm",
    ),
]


# ─── Status Summary Bar ─────────────────────────────────────────────────────

class StatusSummary(ctk.CTkFrame):
    """Shows how many optimizations are active / inactive."""

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

        # Left: text
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.pack(side="left")

        self.summary_label = ctk.CTkLabel(
            left,
            text="🎮  Checking optimization status...",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        self.summary_label.pack(anchor="w")

        self.detail_label = ctk.CTkLabel(
            left,
            text="",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.detail_label.pack(anchor="w", pady=(2, 0))

        # Right: progress ring (simple text-based)
        self.progress_label = ctk.CTkLabel(
            container,
            text="—",
            font=("Inter", 24, "bold"),
            text_color=self.theme.colors["accent"],
        )
        self.progress_label.pack(side="right")

    def update_status(self, active: int, total: int) -> None:
        ratio = active / total if total > 0 else 0

        if ratio >= 0.8:
            color = self.theme.colors["success"]
            emoji = "✅"
        elif ratio >= 0.4:
            color = self.theme.colors.get("warning", "#FFA500")
            emoji = "⚠️"
        else:
            color = self.theme.colors["danger"]
            emoji = "❌"

        self.summary_label.configure(
            text=f"{emoji}  {active}/{total} optimizations active"
        )
        self.detail_label.configure(
            text=t("gaming.status_hint") if active < total else t("gaming.all_applied")
        )
        self.progress_label.configure(
            text=f"{int(ratio * 100)}%",
            text_color=color,
        )


# ─── Info Card ───────────────────────────────────────────────────────────────

class InfoCard(ctk.CTkFrame):
    """Informational card with icon, text, and optional action button."""

    def __init__(
        self,
        master,
        icon: str,
        title: str,
        description: str,
        button_text: Optional[str] = None,
        button_command: Optional[Callable] = None,
        **kwargs,
    ) -> None:
        theme = get_theme()
        super().__init__(
            master,
            fg_color=theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=theme.colors["card_border"],
            **kwargs,
        )

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=14)

        # Header
        ctk.CTkLabel(
            container,
            text=f"{icon}  {title}",
            font=theme.get_font("body", "bold"),
            text_color=theme.colors["text_primary"],
        ).pack(anchor="w")

        # Description
        ctk.CTkLabel(
            container,
            text=description,
            font=theme.get_font("small"),
            text_color=theme.colors["text_secondary"],
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        # Button
        if button_text and button_command:
            ctk.CTkButton(
                container,
                text=button_text,
                height=30,
                fg_color=theme.colors.get("bg_main", "#1A1A2E"),
                hover_color=theme.colors["card_border"],
                border_width=1,
                border_color=theme.colors["card_border"],
                text_color=theme.colors["text_primary"],
                command=button_command,
            ).pack(anchor="w", pady=(10, 0))


# ─── Main Gaming Page ────────────────────────────────────────────────────────

class GamingPage(ctk.CTkFrame):
    """Gaming optimization page with sections, status tracking, batch apply."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.cards: Dict[str, ToggleCard] = {}
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
            text=t("gaming.title"),
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
            text=t("gaming.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 0))

        # ── Status summary ──
        self.status_summary = StatusSummary(self)
        self.status_summary.pack(fill="x", padx=32, pady=(16, 0))

        # ── Apply all button ──
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=32, pady=(12, 0))

        self.apply_all_btn = ctk.CTkButton(
            action_bar,
            text=f"🎮  {t('gaming.apply_all')}",
            height=38,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._apply_all,
        )
        self.apply_all_btn.pack(side="left")

        self.reset_all_btn = ctk.CTkButton(
            action_bar,
            text=f"↩️  {t('gaming.reset_all')}",
            height=36,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._reset_all,
        )
        self.reset_all_btn.pack(side="left", padx=(8, 0))

        # ── Scrollable content ──
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        content.pack(fill="both", expand=True, padx=32, pady=(8, 24))

        # ── Build sections ──
        self._build_optimization_sections(content)

        # ── HAGS info card ──
        self._build_hags_card(content)

    def _build_optimization_sections(self, parent: ctk.CTkFrame) -> None:
        """Build all optimization toggle cards grouped by section."""
        # Group optimizations by section
        by_section: Dict[str, List[OptimizationDef]] = {}
        for opt in OPTIMIZATIONS:
            by_section.setdefault(opt.section, []).append(opt)

        for section_id in ["performance", "input", "network"]:
            opts = by_section.get(section_id, [])
            if not opts:
                continue

            section_info = SECTIONS[section_id]
            icon = section_info["icon"]
            title = t(section_info["title_key"])

            # Section header with separator
            header_frame = ctk.CTkFrame(parent, fg_color="transparent")
            header_frame.pack(fill="x", pady=(18, 8))

            ctk.CTkLabel(
                header_frame,
                text=f"{icon}  {title}",
                font=self.theme.get_font("header", "bold"),
                text_color=self.theme.colors["text_primary"],
            ).pack(side="left")

            ctk.CTkFrame(
                header_frame,
                fg_color=self.theme.colors["card_border"],
                height=1,
            ).pack(side="left", fill="x", expand=True, padx=(12, 0), pady=1)

            # Toggle cards
            for opt in opts:
                card = ToggleCard(
                    parent,
                    title=t(opt.title_key),
                    description=t(opt.desc_key),
                    risk_level=opt.risk_level,
                    initial_state=False,
                    on_toggle=lambda state, o=opt: self._handle_toggle(o, state),
                )
                card.pack(fill="x", pady=3)
                self.cards[opt.id] = card

    def _build_hags_card(self, parent: ctk.CTkFrame) -> None:
        """Build the Hardware-Accelerated GPU Scheduling info card."""
        # Section header
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(18, 8))

        ctk.CTkLabel(
            header_frame,
            text=f"🖥️  {t('gaming.category_visuals')}",
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")

        ctk.CTkFrame(
            header_frame,
            fg_color=self.theme.colors["card_border"],
            height=1,
        ).pack(side="left", fill="x", expand=True, padx=(12, 0), pady=1)

        InfoCard(
            parent,
            icon="ℹ️",
            title=t("gaming.hags_info"),
            description=t("gaming.hags_info_desc"),
            button_text=t("gaming.open_graphics_settings"),
            button_command=self._open_graphics_settings,
        ).pack(fill="x", pady=3)

    # ── Status Management ────────────────────────────────────────────────

    def refresh_status(self) -> None:
        """Refresh toggle states from system."""
        if self._is_loading:
            return

        self._is_loading = True
        self.refresh_btn.configure(state="disabled")

        def _load():
            try:
                status = gaming_manager.get_gaming_status()
                self.after(0, lambda: self._on_status_loaded(status))
            except Exception as e:
                logger.exception("Failed to load gaming status")
                self.after(0, lambda: self._on_status_error(str(e)))

        threading.Thread(target=_load, daemon=True).start()

    def _on_status_loaded(self, status: Dict) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self._update_toggles(status)

    def _on_status_error(self, error: str) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        logger.error("Gaming status error: %s", error)

    def _update_toggles(self, status: Dict) -> None:
        """Sync toggle states with system status."""
        active_count = 0
        total_count = len(OPTIMIZATIONS)

        for opt in OPTIMIZATIONS:
            state = status.get(opt.status_key, False)
            if opt.invert_status:
                state = not state

            if opt.id in self.cards:
                self.cards[opt.id].state = state
                if state:
                    active_count += 1

        self.status_summary.update_status(active_count, total_count)

    # ── Toggle Handling ──────────────────────────────────────────────────

    def _handle_toggle(self, opt: OptimizationDef, state: bool) -> None:
        """Handle a single toggle change."""
        action_name = t(opt.title_key)
        func = getattr(gaming_manager, opt.apply_func_name, None)

        if func is None:
            logger.error("No function '%s' on gaming_manager", opt.apply_func_name)
            return

        if not state:
            # Toggle turned off — just refresh to revert visual state
            self.refresh_status()
            return

        modal = ProgressModal(self.winfo_toplevel(), action_name)

        def _worker():
            try:
                modal.log(f"💾  {t('backup.creating_backup')}")
                try:
                    backup_manager.create_backup(f"Before: {action_name}")
                    modal.log(f"  ✓  {t('backup.backup_success')}", "success")
                except Exception as e:
                    modal.log(f"  ⚠  Backup skipped: {e}", "warning")
                    logger.warning("Backup failed before %s: %s", action_name, e)

                modal.log(f"⚡  Applying: {action_name}")
                modal.set_progress(0.5)

                success, message = func()

                if success:
                    modal.complete(True, f"✅  {message}")
                else:
                    modal.complete(False, f"❌  {message}")

            except Exception as e:
                logger.exception("Failed to apply %s", opt.id)
                modal.complete(False, f"{t('common.error')}: {e}")

            self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()

    # ── Batch Operations ─────────────────────────────────────────────────

    def _apply_all(self) -> None:
        """Apply all gaming optimizations at once."""
        from winpurge.gui.pages.backup import ConfirmDialog

        dialog = ConfirmDialog(
            self.winfo_toplevel(),
            title=t("gaming.confirm_apply_all_title"),
            message=t("gaming.confirm_apply_all"),
            detail=(
                f"⚡  {len(OPTIMIZATIONS)} optimizations\n"
                f"{t('gaming.confirm_apply_all_detail')}"
            ),
            confirm_text=f"🎮  {t('gaming.apply_all')}",
            confirm_color=self.theme.colors["accent"],
            icon="🎮",
        )

        if not dialog.result:
            return

        self.apply_all_btn.configure(state="disabled")
        modal = ProgressModal(self.winfo_toplevel(), t("gaming.apply_all"))

        def _worker():
            try:
                # Backup
                modal.log(f"💾  {t('backup.creating_backup')}")
                try:
                    backup_manager.create_backup("Before all gaming optimizations")
                    modal.log(f"  ✓  {t('backup.backup_success')}", "success")
                except Exception as e:
                    modal.log(f"  ⚠  Backup skipped: {e}", "warning")

                modal.log(f"🎮  Applying all optimizations...")
                modal.set_progress(0.3)

                total = len(OPTIMIZATIONS)
                success_count = 0

                for i, opt in enumerate(OPTIMIZATIONS, 1):
                    if modal.cancelled:
                        modal.log(f"⏹  {t('common.cancelled')}", "warning")
                        break

                    func = getattr(gaming_manager, opt.apply_func_name, None)
                    if func is None:
                        modal.log(f"  ⚠  Unknown: {opt.id}", "warning")
                        continue

                    name = t(opt.title_key)
                    modal.log(f"  ⚡  {name}")
                    modal.set_progress(i / total, f"{i}/{total}")

                    try:
                        success, msg = func()
                        if success:
                            success_count += 1
                            modal.log(f"    ✓  {msg}", "success")
                        else:
                            modal.log(f"    ✗  {msg}", "error")
                    except Exception as e:
                        modal.log(f"    ✗  {e}", "error")

                if not modal.cancelled:
                    modal.complete(
                        success_count == total,
                        t("gaming.apply_all_complete",
                          success=success_count, total=total),
                    )

            except Exception as e:
                logger.exception("Apply all failed")
                modal.complete(False, f"{t('common.error')}: {e}")
            finally:
                self.after(0, lambda: self.apply_all_btn.configure(state="normal"))
                self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()

    def _reset_all(self) -> None:
        """Reset all optimizations to defaults."""
        from winpurge.gui.pages.backup import ConfirmDialog

        dialog = ConfirmDialog(
            self.winfo_toplevel(),
            title=t("gaming.confirm_reset_title"),
            message=t("gaming.confirm_reset"),
            detail=t("gaming.confirm_reset_detail"),
            confirm_text=f"↩️  {t('gaming.reset_all')}",
            confirm_color=self.theme.colors.get("warning", "#FFA500"),
            icon="↩️",
        )

        if not dialog.result:
            return

        modal = ProgressModal(self.winfo_toplevel(), t("gaming.reset_all"))

        def _worker():
            try:
                modal.log(f"↩️  Resetting gaming optimizations...")
                modal.set_progress(0.5)

                if hasattr(gaming_manager, "reset_all_gaming_optimizations"):
                    success, message = gaming_manager.reset_all_gaming_optimizations()
                else:
                    success, message = True, "Reset complete (no dedicated reset function)"

                if success:
                    modal.complete(True, message)
                else:
                    modal.complete(False, message)

            except Exception as e:
                logger.exception("Reset all failed")
                modal.complete(False, str(e))

            self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()

    # ── External Launchers ───────────────────────────────────────────────

    @staticmethod
    def _open_graphics_settings() -> None:
        """Open Windows Advanced Graphics Settings."""
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "ms-settings:display-advancedgraphics"],
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            logger.error("Failed to open graphics settings: %s", e)