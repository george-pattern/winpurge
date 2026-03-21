"""
WinPurge Status Bar Component
Bottom status bar with OS info, backup status, operation status,
and real-time indicators.
"""

import customtkinter as ctk
import threading
import logging
import time
from typing import Optional, Callable
from enum import Enum

from winpurge.gui.theme import get_theme
from winpurge.utils import get_windows_version, t

logger = logging.getLogger(__name__)


# ─── Status Types ────────────────────────────────────────────────────────────

class StatusLevel(Enum):
    IDLE = "idle"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    WORKING = "working"


STATUS_CONFIG = {
    StatusLevel.IDLE:    {"icon": "●", "color_key": "text_disabled"},
    StatusLevel.INFO:    {"icon": "ℹ", "color_key": "accent"},
    StatusLevel.SUCCESS: {"icon": "✓", "color_key": "success"},
    StatusLevel.WARNING: {"icon": "⚠", "color_key": "warning"},
    StatusLevel.ERROR:   {"icon": "✗", "color_key": "danger"},
    StatusLevel.WORKING: {"icon": "⟳", "color_key": "accent"},
}


# ─── Status Indicator Dot ───────────────────────────────────────────────────

class StatusDot(ctk.CTkFrame):
    """Small colored dot indicating connection/status."""

    def __init__(self, master, color: str = "#4CAF50", size: int = 8, **kwargs) -> None:
        super().__init__(
            master,
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=color,
            **kwargs,
        )
        self.pack_propagate(False)

    def set_color(self, color: str) -> None:
        self.configure(fg_color=color)


# ─── Separator ───────────────────────────────────────────────────────────────

class BarSeparator(ctk.CTkFrame):
    """Vertical separator line for the status bar."""

    def __init__(self, master, **kwargs) -> None:
        theme = get_theme()
        super().__init__(
            master,
            width=1,
            height=14,
            fg_color=theme.colors["divider"],
            **kwargs,
        )


# ─── Main Status Bar ────────────────────────────────────────────────────────

class StatusBar(ctk.CTkFrame):
    """
    Bottom status bar with:
    - OS version info
    - Admin status indicator
    - Backup status
    - Operation status with auto-clear
    - Clock / uptime
    """

    # Auto-clear delay for transient status messages (ms)
    AUTO_CLEAR_DELAY = 5000

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()

        super().__init__(
            master,
            height=32,
            corner_radius=0,
            fg_color=self.theme.colors["bg_sidebar"],
            **kwargs,
        )
        self.pack_propagate(False)

        self._auto_clear_id: Optional[str] = None
        self._current_level = StatusLevel.IDLE

        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Left section ──
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(12, 0))

        # Admin indicator
        is_admin = self._check_admin()
        admin_color = self.theme.colors["success"] if is_admin else self.theme.colors.get("warning", "#FFA500")

        self.admin_dot = StatusDot(left, color=admin_color)
        self.admin_dot.pack(side="left", padx=(0, 6), pady=12)

        admin_text = t("status_bar.admin") if is_admin else t("status_bar.not_admin")
        ctk.CTkLabel(
            left,
            text=admin_text,
            font=("Inter", 10),
            text_color=admin_color,
        ).pack(side="left")

        BarSeparator(left).pack(side="left", padx=10, pady=9)

        # OS info
        self.os_label = ctk.CTkLabel(
            left,
            text=self._get_os_text(),
            font=("Inter", 10),
            text_color=self.theme.colors["text_disabled"],
        )
        self.os_label.pack(side="left")

        BarSeparator(left).pack(side="left", padx=10, pady=9)

        # Backup status
        self.backup_dot = StatusDot(left, color=self.theme.colors.get("warning", "#FFA500"))
        self.backup_dot.pack(side="left", padx=(0, 6), pady=12)

        self.backup_label = ctk.CTkLabel(
            left,
            text=t("status_bar.no_backup"),
            font=("Inter", 10),
            text_color=self.theme.colors["text_disabled"],
        )
        self.backup_label.pack(side="left")

        # ── Right section ──
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", fill="y", padx=(0, 12))

        # Status message
        self.status_dot = StatusDot(right, color=self.theme.colors.get("text_disabled", "#555"))
        self.status_dot.pack(side="left", padx=(0, 6), pady=12)

        self.status_label = ctk.CTkLabel(
            right,
            text=t("status_bar.ready"),
            font=("Inter", 10),
            text_color=self.theme.colors["text_disabled"],
        )
        self.status_label.pack(side="left")

    # ── Public API ───────────────────────────────────────────────────────

    def set_status(
        self,
        text: str,
        level: StatusLevel = StatusLevel.INFO,
        auto_clear: bool = True,
    ) -> None:
        """
        Set the status message with level indicator.

        Args:
            text: Status message text.
            level: StatusLevel enum for coloring.
            auto_clear: If True, revert to "Ready" after delay.
        """
        self._cancel_auto_clear()
        self._current_level = level

        config = STATUS_CONFIG.get(level, STATUS_CONFIG[StatusLevel.IDLE])
        color = self.theme.colors.get(config["color_key"], self.theme.colors["text_disabled"])

        self.status_label.configure(text=text, text_color=color)
        self.status_dot.set_color(color)

        if auto_clear and level not in (StatusLevel.WORKING, StatusLevel.IDLE):
            self._auto_clear_id = self.after(
                self.AUTO_CLEAR_DELAY,
                self._reset_status,
            )

    def set_working(self, text: str) -> None:
        """Set status to 'working' (won't auto-clear)."""
        self.set_status(text, StatusLevel.WORKING, auto_clear=False)

    def set_success(self, text: str) -> None:
        """Set status to 'success' (auto-clears)."""
        self.set_status(text, StatusLevel.SUCCESS)

    def set_error(self, text: str) -> None:
        """Set status to 'error' (auto-clears)."""
        self.set_status(text, StatusLevel.ERROR)

    def set_idle(self) -> None:
        """Reset to idle/ready state."""
        self._reset_status()

    def set_backup_status(
        self,
        text: str,
        has_backup: bool = True,
    ) -> None:
        """
        Update backup status display.

        Args:
            text: Status text (e.g. "2 hours ago").
            has_backup: Whether a backup exists.
        """
        color = self.theme.colors["success"] if has_backup else self.theme.colors.get("warning", "#FFA500")
        self.backup_dot.set_color(color)
        self.backup_label.configure(
            text=f"💾  {text}",
            text_color=self.theme.colors["text_disabled"] if has_backup else color,
        )

    def refresh(self) -> None:
        """Refresh status bar content (e.g. after language change)."""
        self.os_label.configure(text=self._get_os_text())

    # ── Internal ─────────────────────────────────────────────────────────

    def _reset_status(self) -> None:
        """Reset status to idle 'Ready' state."""
        self._current_level = StatusLevel.IDLE
        idle_color = self.theme.colors.get("text_disabled", "#555")
        self.status_label.configure(
            text=t("status_bar.ready"),
            text_color=idle_color,
        )
        self.status_dot.set_color(idle_color)

    def _cancel_auto_clear(self) -> None:
        if self._auto_clear_id:
            self.after_cancel(self._auto_clear_id)
            self._auto_clear_id = None

    @staticmethod
    def _get_os_text() -> str:
        try:
            info = get_windows_version()
            return info.get("display", "Windows")
        except Exception:
            return "Windows"

    @staticmethod
    def _check_admin() -> bool:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False