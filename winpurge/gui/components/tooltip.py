"""
WinPurge Tooltip Component
Themed hover tooltip with fade-in, auto-positioning, and multi-line support.
"""

import customtkinter as ctk
import logging
from typing import Optional

from winpurge.constants import TOOLTIP_DELAY
from winpurge.gui.theme import get_theme

logger = logging.getLogger(__name__)


# ─── Tooltip Window ─────────────────────────────────────────────────────────

class TooltipWindow(ctk.CTkToplevel):
    """
    Borderless themed tooltip window.
    Auto-positions near the widget and avoids going off-screen.
    """

    # Padding from widget edge
    OFFSET_Y = 6
    OFFSET_X = 0
    MAX_WIDTH = 320
    PADDING_X = 12
    PADDING_Y = 8

    def __init__(self, parent, text: str, x: int, y: int) -> None:
        super().__init__(parent)
        self.theme = get_theme()

        # Borderless
        self.wm_overrideredirect(True)
        self.wm_attributes("-topmost", True)

        # Transparent on some platforms
        try:
            self.wm_attributes("-alpha", 0.95)
        except Exception:
            pass

        self.configure(fg_color="transparent")

        self._build_ui(text)
        self._position(parent, x, y)

    def _build_ui(self, text: str) -> None:
        # Outer frame with shadow-like border
        outer = ctk.CTkFrame(
            self,
            fg_color=self.theme.colors.get("tooltip_bg", self.theme.colors["bg_card"]),
            corner_radius=8,
            border_width=1,
            border_color=self.theme.colors.get("tooltip_border", self.theme.colors["card_border"]),
        )
        outer.pack()

        # Text label
        self.label = ctk.CTkLabel(
            outer,
            text=text,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors.get("tooltip_text", self.theme.colors["text_primary"]),
            wraplength=self.MAX_WIDTH,
            justify="left",
            anchor="w",
        )
        self.label.pack(padx=self.PADDING_X, pady=self.PADDING_Y)

    def _position(self, parent, x: int, y: int) -> None:
        """Position tooltip, keeping it on-screen."""
        self.update_idletasks()

        tip_w = self.winfo_width()
        tip_h = self.winfo_height()

        # Screen dimensions
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # Default: below and to the right of cursor/widget
        final_x = x + self.OFFSET_X
        final_y = y + self.OFFSET_Y

        # Clamp to screen bounds
        if final_x + tip_w > screen_w - 8:
            final_x = screen_w - tip_w - 8

        if final_x < 8:
            final_x = 8

        if final_y + tip_h > screen_h - 8:
            # Show above the widget instead
            final_y = y - tip_h - self.OFFSET_Y

        if final_y < 8:
            final_y = 8

        self.wm_geometry(f"+{final_x}+{final_y}")


# ─── Main Tooltip Class ─────────────────────────────────────────────────────

class Tooltip:
    """
    Hover tooltip for any widget.

    Features:
    - Configurable delay before showing
    - Auto-hides on leave or click
    - Smart screen-edge positioning
    - Theme-aware styling
    - Thread-safe text updates

    Usage:
        tooltip = Tooltip(my_button, "This is a helpful tip")
        tooltip.update_text("Updated text")
    """

    def __init__(
        self,
        widget: ctk.CTkBaseClass,
        text: str,
        delay: int = TOOLTIP_DELAY,
        enabled: bool = True,
    ) -> None:
        self.widget = widget
        self._text = text
        self._delay = delay
        self._enabled = enabled

        self._tooltip_window: Optional[TooltipWindow] = None
        self._after_id: Optional[str] = None
        self._mouse_x = 0
        self._mouse_y = 0

        # Bind events
        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<Button>", self._on_leave, add="+")
        self.widget.bind("<Motion>", self._on_motion, add="+")
        self.widget.bind("<Destroy>", self._on_destroy, add="+")

    # ── Event Handlers ───────────────────────────────────────────────────

    def _on_enter(self, event) -> None:
        if not self._enabled or not self._text:
            return
        self._mouse_x = event.x_root
        self._mouse_y = event.y_root
        self._schedule_show()

    def _on_leave(self, event=None) -> None:
        self._cancel_show()
        self._hide()

    def _on_motion(self, event) -> None:
        """Track mouse position for better placement."""
        self._mouse_x = event.x_root
        self._mouse_y = event.y_root

    def _on_destroy(self, event=None) -> None:
        """Clean up when widget is destroyed."""
        self._cancel_show()
        self._hide()

    # ── Show / Hide ──────────────────────────────────────────────────────

    def _schedule_show(self) -> None:
        self._cancel_show()
        self._after_id = self.widget.after(self._delay, self._show)

    def _cancel_show(self) -> None:
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self) -> None:
        """Display the tooltip near the mouse cursor."""
        if self._tooltip_window is not None:
            return

        if not self._text or not self._enabled:
            return

        try:
            # Verify widget still exists
            self.widget.winfo_exists()
        except Exception:
            return

        # Position below the widget bottom edge
        try:
            widget_x = self.widget.winfo_rootx()
            widget_y = self.widget.winfo_rooty()
            widget_h = self.widget.winfo_height()

            x = widget_x
            y = widget_y + widget_h

            self._tooltip_window = TooltipWindow(self.widget, self._text, x, y)
        except Exception as e:
            logger.debug("Tooltip show failed: %s", e)
            self._tooltip_window = None

    def _hide(self) -> None:
        """Destroy the tooltip window."""
        if self._tooltip_window is not None:
            try:
                self._tooltip_window.destroy()
            except Exception:
                pass
            self._tooltip_window = None

    # ── Public API ───────────────────────────────────────────────────────

    def update_text(self, text: str) -> None:
        """Update tooltip text. If currently visible, updates live."""
        self._text = text

        if self._tooltip_window is not None:
            try:
                self._tooltip_window.label.configure(text=text)
            except Exception:
                pass

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self.update_text(value)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        if not value:
            self._on_leave()

    @property
    def delay(self) -> int:
        return self._delay

    @delay.setter
    def delay(self, value: int) -> None:
        self._delay = max(0, value)

    def destroy(self) -> None:
        """Clean up tooltip bindings and window."""
        self._cancel_show()
        self._hide()

        try:
            self.widget.unbind("<Enter>")
            self.widget.unbind("<Leave>")
            self.widget.unbind("<Button>")
            self.widget.unbind("<Motion>")
            self.widget.unbind("<Destroy>")
        except Exception:
            pass