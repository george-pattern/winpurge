"""
WinPurge Privacy Page
Privacy and telemetry settings with data-driven toggles, status tracking,
and batch operations.
"""

import customtkinter as ctk
import threading
import logging
from typing import Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass, field
from winpurge.gui.pages.backup import ConfirmDialog
from winpurge.gui.theme import get_theme
from winpurge.gui.components.toggle_card import ToggleCard
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.privacy import privacy_manager
from winpurge.core.telemetry import telemetry_manager
from winpurge.core.backup import backup_manager

logger = logging.getLogger(__name__)


# ─── Optimization Definitions ────────────────────────────────────────────────

@dataclass(frozen=True)
class PrivacyToggleDef:
    """Declarative definition of a privacy toggle."""
    id: str
    title_key: str
    desc_key: str
    risk_level: str
    section: str
    status_key: str
    manager: str           # "privacy" or "telemetry"
    apply_func_name: str
    invert_status: bool = True  # True → status=True means enabled, toggle shows disabled


SECTIONS = {
    "telemetry": {
        "title_key": "privacy.category_telemetry",
        "icon": "📡",
        "order": 0,
    },
    "ai": {
        "title_key": "privacy.category_ai",
        "icon": "🤖",
        "order": 1,
    },
    "ads": {
        "title_key": "privacy.category_ads",
        "icon": "📢",
        "order": 2,
    },
    "history": {
        "title_key": "privacy.category_history",
        "icon": "📜",
        "order": 3,
    },
}

TOGGLES: List[PrivacyToggleDef] = [
    # ── Telemetry ──
    PrivacyToggleDef(
        id="telemetry",
        title_key="privacy.disable_telemetry",
        desc_key="privacy.disable_telemetry_desc",
        risk_level="safe",
        section="telemetry",
        status_key="telemetry_enabled",
        manager="telemetry",
        apply_func_name="disable_telemetry",
    ),
    PrivacyToggleDef(
        id="advertising_id",
        title_key="privacy.disable_advertising_id",
        desc_key="privacy.disable_advertising_id_desc",
        risk_level="safe",
        section="telemetry",
        status_key="advertising_id_enabled",
        manager="telemetry",
        apply_func_name="disable_advertising_id",
    ),
    PrivacyToggleDef(
        id="input_telemetry",
        title_key="privacy.disable_input_telemetry",
        desc_key="privacy.disable_input_telemetry_desc",
        risk_level="safe",
        section="telemetry",
        status_key="input_telemetry_enabled",
        manager="telemetry",
        apply_func_name="disable_input_telemetry",
    ),
    PrivacyToggleDef(
        id="telemetry_hosts",
        title_key="privacy.block_telemetry_hosts",
        desc_key="privacy.block_telemetry_hosts_desc",
        risk_level="moderate",
        section="telemetry",
        status_key="hosts_blocking_active",
        manager="telemetry",
        apply_func_name="block_telemetry_hosts",
        invert_status=False,  # status=True means already blocked = toggle ON
    ),
    # ── AI & Assistants ──
    PrivacyToggleDef(
        id="cortana",
        title_key="privacy.disable_cortana",
        desc_key="privacy.disable_cortana_desc",
        risk_level="safe",
        section="ai",
        status_key="cortana_enabled",
        manager="privacy",
        apply_func_name="disable_cortana",
    ),
    PrivacyToggleDef(
        id="copilot",
        title_key="privacy.disable_copilot",
        desc_key="privacy.disable_copilot_desc",
        risk_level="safe",
        section="ai",
        status_key="copilot_enabled",
        manager="privacy",
        apply_func_name="disable_copilot",
    ),
    PrivacyToggleDef(
        id="recall",
        title_key="privacy.disable_recall",
        desc_key="privacy.disable_recall_desc",
        risk_level="safe",
        section="ai",
        status_key="recall_enabled",
        manager="privacy",
        apply_func_name="disable_recall",
    ),
    # ── Ads ──
    PrivacyToggleDef(
        id="start_suggestions",
        title_key="privacy.disable_start_suggestions",
        desc_key="privacy.disable_start_suggestions_desc",
        risk_level="safe",
        section="ads",
        status_key="start_suggestions_enabled",
        manager="privacy",
        apply_func_name="disable_start_suggestions",
    ),
    PrivacyToggleDef(
        id="lock_screen_ads",
        title_key="privacy.disable_lock_screen_ads",
        desc_key="privacy.disable_lock_screen_ads_desc",
        risk_level="safe",
        section="ads",
        status_key="lock_screen_ads_enabled",
        manager="privacy",
        apply_func_name="disable_lock_screen_ads",
    ),
    # ── History ──
    PrivacyToggleDef(
        id="activity_history",
        title_key="privacy.disable_activity_history",
        desc_key="privacy.disable_activity_history_desc",
        risk_level="safe",
        section="history",
        status_key="activity_history_enabled",
        manager="privacy",
        apply_func_name="disable_activity_history",
    ),
    PrivacyToggleDef(
        id="clipboard_sync",
        title_key="privacy.disable_clipboard_sync",
        desc_key="privacy.disable_clipboard_sync_desc",
        risk_level="safe",
        section="history",
        status_key="clipboard_sync_enabled",
        manager="privacy",
        apply_func_name="disable_clipboard_sync",
    ),
]


# ─── Privacy Score Card ──────────────────────────────────────────────────────

class PrivacyScoreCard(ctk.CTkFrame):
    """Shows privacy protection score as a percentage with visual indicator."""

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
        container.pack(fill="x", padx=20, pady=16)

        # Left
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.pack(side="left", fill="y")

        self.title_label = ctk.CTkLabel(
            left,
            text="🔒  Checking privacy status...",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        self.title_label.pack(anchor="w")

        self.detail_label = ctk.CTkLabel(
            left,
            text="",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.detail_label.pack(anchor="w", pady=(2, 0))

        # Progress bar
        self.bar = ctk.CTkProgressBar(
            left,
            width=300,
            height=8,
            progress_color=self.theme.colors["accent"],
            fg_color=self.theme.colors.get("bg_main", "#1A1A2E"),
            corner_radius=4,
        )
        self.bar.pack(anchor="w", pady=(8, 0))
        self.bar.set(0)

        # Right: score
        self.score_label = ctk.CTkLabel(
            container,
            text="—",
            font=("Inter", 32, "bold"),
            text_color=self.theme.colors["accent"],
        )
        self.score_label.pack(side="right")

    def update_score(self, protected: int, total: int) -> None:
        ratio = protected / total if total > 0 else 0
        pct = int(ratio * 100)

        # Color based on score
        if ratio >= 0.8:
            color = self.theme.colors["success"]
            emoji = "🛡️"
            status = t("privacy.score_excellent")
        elif ratio >= 0.5:
            color = self.theme.colors.get("warning", "#FFA500")
            emoji = "⚠️"
            status = t("privacy.score_moderate")
        else:
            color = self.theme.colors["danger"]
            emoji = "🚨"
            status = t("privacy.score_poor")

        self.title_label.configure(text=f"{emoji}  {status}")
        self.detail_label.configure(
            text=t("privacy.score_detail", protected=protected, total=total)
        )
        self.bar.set(ratio)
        self.bar.configure(progress_color=color)
        self.score_label.configure(text=f"{pct}%", text_color=color)


# ─── Main Privacy Page ──────────────────────────────────────────────────────

class PrivacyPage(ctk.CTkFrame):
    """Privacy and telemetry settings page with score, sections, batch apply."""

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
            text=t("privacy.title"),
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
            text=t("privacy.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 0))

        # ── Privacy score ──
        self.score_card = PrivacyScoreCard(self)
        self.score_card.pack(fill="x", padx=32, pady=(16, 0))

        # ── Action bar ──
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=32, pady=(12, 0))

        self.apply_all_btn = ctk.CTkButton(
            action_bar,
            text=f"🔒  {t('privacy.apply_all')}",
            height=38,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._apply_all,
        )
        self.apply_all_btn.pack(side="left")

        self.apply_safe_btn = ctk.CTkButton(
            action_bar,
            text=f"✅  {t('privacy.apply_safe_only')}",
            height=36,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._apply_safe_only,
        )
        self.apply_safe_btn.pack(side="left", padx=(8, 0))

        # ── Scrollable content ──
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        content.pack(fill="both", expand=True, padx=32, pady=(8, 24))

        self._build_toggle_sections(content)

    def _build_toggle_sections(self, parent: ctk.CTkFrame) -> None:
        """Build all toggle cards grouped by section."""
        by_section: Dict[str, List[PrivacyToggleDef]] = {}
        for tog in TOGGLES:
            by_section.setdefault(tog.section, []).append(tog)

        sorted_sections = sorted(
            SECTIONS.keys(),
            key=lambda s: SECTIONS[s]["order"],
        )

        for section_id in sorted_sections:
            toggles = by_section.get(section_id, [])
            if not toggles:
                continue

            info = SECTIONS[section_id]
            icon = info["icon"]
            title = t(info["title_key"])

            # Section header
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
            for tog in toggles:
                card = ToggleCard(
                    parent,
                    title=t(tog.title_key),
                    description=t(tog.desc_key),
                    risk_level=tog.risk_level,
                    initial_state=False,
                    on_toggle=lambda state, td=tog: self._handle_toggle(td, state),
                )
                card.pack(fill="x", pady=3)
                self.cards[tog.id] = card

    # ── Status Management ────────────────────────────────────────────────

    def refresh_status(self) -> None:
        """Refresh all toggle states from the system."""
        if self._is_loading:
            return

        self._is_loading = True
        self.refresh_btn.configure(state="disabled")

        def _worker():
            try:
                privacy_status = privacy_manager.get_privacy_status()
                telemetry_status = telemetry_manager.get_telemetry_status()
                self.after(0, lambda: self._on_status_loaded(privacy_status, telemetry_status))
            except Exception as e:
                logger.exception("Failed to load privacy status")
                self.after(0, self._on_load_complete)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_status_loaded(
        self, privacy_status: Dict, telemetry_status: Dict
    ) -> None:
        self._on_load_complete()

        # Merge both status dicts
        combined = {**telemetry_status, **privacy_status}

        protected = 0
        total = len(TOGGLES)

        for tog in TOGGLES:
            raw_value = combined.get(tog.status_key, None)

            if raw_value is None:
                state = False
            elif tog.invert_status:
                state = not raw_value  # enabled=True → toggle OFF, so invert
            else:
                state = bool(raw_value)

            if tog.id in self.cards:
                self.cards[tog.id].state = state

            if state:
                protected += 1

        self.score_card.update_score(protected, total)

    def _on_load_complete(self) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")

    # ── Toggle Handling ──────────────────────────────────────────────────

    def _get_manager(self, manager_name: str):
        """Get the appropriate manager instance."""
        if manager_name == "telemetry":
            return telemetry_manager
        return privacy_manager

    def _handle_toggle(self, tog: PrivacyToggleDef, state: bool) -> None:
        """Handle a single toggle change."""
        if not state:
            self.refresh_status()
            return

        mgr = self._get_manager(tog.manager)
        func = getattr(mgr, tog.apply_func_name, None)

        if func is None:
            logger.error("No function '%s' on %s", tog.apply_func_name, tog.manager)
            return

        action_name = t(tog.title_key)
        modal = ProgressModal(self.winfo_toplevel(), action_name)

        def _worker():
            try:
                # Backup
                modal.log(f"💾  {t('backup.creating_backup')}")
                try:
                    backup_manager.create_backup(f"Before: {action_name}")
                    modal.log(f"  ✓  {t('backup.backup_success')}", "success")
                except Exception as e:
                    modal.log(f"  ⚠  Backup skipped: {e}", "warning")

                modal.log(f"🔒  {action_name}")
                modal.set_progress(0.5)

                success, message = func()

                if success:
                    modal.complete(True, f"✅  {message}")
                else:
                    modal.complete(False, f"❌  {message}")

            except Exception as e:
                logger.exception("Failed to apply %s", tog.id)
                modal.complete(False, f"{t('common.error')}: {e}")

            self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()

    # ── Batch Operations ─────────────────────────────────────────────────

    def _apply_all(self) -> None:
        """Apply ALL privacy settings (including moderate risk)."""
        self._batch_apply(
            title=t("privacy.apply_all"),
            toggles=TOGGLES,
            icon="🔒",
        )

    def _apply_safe_only(self) -> None:
        """Apply only 'safe' risk level privacy settings."""
        safe_toggles = [t for t in TOGGLES if t.risk_level == "safe"]
        self._batch_apply(
            title=t("privacy.apply_safe_only"),
            toggles=safe_toggles,
            icon="✅",
        )

    def _batch_apply(
        self,
        title: str,
        toggles: List[PrivacyToggleDef],
        icon: str,
    ) -> None:
        """Apply a batch of privacy toggles with confirmation."""
        from winpurge.gui.pages.backup import ConfirmDialog

        risk_counts = {"safe": 0, "moderate": 0, "advanced": 0}
        for tog in toggles:
            risk_counts[tog.risk_level] = risk_counts.get(tog.risk_level, 0) + 1

        detail_parts = [f"⚡  {len(toggles)} settings to apply"]
        for level, count in risk_counts.items():
            if count > 0:
                detail_parts.append(f"  • {t(f'risk_levels.{level}')}: {count}")

        dialog = ConfirmDialog(
            self.winfo_toplevel(),
            title=title,
            message=t("privacy.confirm_apply_all"),
            detail="\n".join(detail_parts),
            confirm_text=f"{icon}  {title}",
            confirm_color=self.theme.colors["accent"],
            icon=icon,
        )

        if not dialog.result:
            return

        self.apply_all_btn.configure(state="disabled")
        self.apply_safe_btn.configure(state="disabled")

        modal = ProgressModal(self.winfo_toplevel(), title)

        def _worker():
            try:
                # Backup
                modal.log(f"💾  {t('backup.creating_backup')}")
                try:
                    backup_manager.create_backup(f"Before: {title}")
                    modal.log(f"  ✓  {t('backup.backup_success')}", "success")
                except Exception as e:
                    modal.log(f"  ⚠  Backup skipped: {e}", "warning")

                total = len(toggles)
                success_count = 0

                for i, tog in enumerate(toggles, 1):
                    if modal.cancelled:
                        modal.log(f"⏹  {t('common.cancelled')}", "warning")
                        break

                    mgr = self._get_manager(tog.manager)
                    func = getattr(mgr, tog.apply_func_name, None)

                    if func is None:
                        modal.log(f"  ⚠  Unknown: {tog.id}", "warning")
                        continue

                    name = t(tog.title_key)
                    modal.log(f"🔒  {name}")
                    modal.set_progress(i / total, f"{i}/{total}")

                    try:
                        success, msg = func()
                        if success:
                            success_count += 1
                            modal.log(f"  ✓  Done", "success")
                        else:
                            modal.log(f"  ✗  {msg}", "error")
                    except Exception as e:
                        modal.log(f"  ✗  {e}", "error")

                if not modal.cancelled:
                    modal.complete(
                        success_count == total,
                        t("privacy.apply_complete",
                          success=success_count, total=total),
                    )

            except Exception as e:
                logger.exception("Batch privacy apply failed")
                modal.complete(False, f"{t('common.error')}: {e}")
            finally:
                self.after(0, lambda: self.apply_all_btn.configure(state="normal"))
                self.after(0, lambda: self.apply_safe_btn.configure(state="normal"))
                self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()