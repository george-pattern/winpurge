"""
WinPurge Toggle Card Component
Reusable card with toggle switch or checkbox, risk badge, hover effects,
and disabled state support.
"""

import customtkinter as ctk
import logging
from typing import Callable, Optional

from winpurge.constants import CARD_RADIUS
from winpurge.gui.theme import get_theme
from winpurge.gui.components.tooltip import Tooltip
from winpurge.utils import t

logger = logging.getLogger(__name__)


# ─── Risk Badge ─────────────────────────────────────────────────────────────

class RiskBadge(ctk.CTkFrame):
    """Inline risk level badge with tooltip."""

    def __init__(
        self,
        master,
        risk_level: str = "safe",
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        self.risk_level = risk_level

        super().__init__(master, fg_color="transparent", **kwargs)

        risk_colors = self.theme.get_risk_colors(risk_level)

        self.label = ctk.CTkLabel(
            self,
            text=t(f"risk_levels.{risk_level}"),
            font=("Inter", 10, "bold"),
            fg_color=risk_colors["bg"],
            text_color=risk_colors["fg"],
            corner_radius=4,
            padx=8,
            pady=2,
            height=20,
        )
        self.label.pack()

        # Tooltip with risk description
        desc_key = f"risk_levels.{risk_level}_desc"
        Tooltip(self.label, t(desc_key))


# ─── Status Indicator ───────────────────────────────────────────────────────

class StatusIndicator(ctk.CTkFrame):
    """Small dot + text showing current applied status."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.dot = ctk.CTkFrame(
            self,
            width=6,
            height=6,
            corner_radius=3,
            fg_color=self.theme.colors.get("text_disabled", "#555"),
        )
        self.dot.pack(side="left", padx=(0, 4))
        self.dot.pack_propagate(False)

        self.label = ctk.CTkLabel(
            self,
            text="",
            font=("Inter", 9),
            text_color=self.theme.colors.get("text_disabled", "#555"),
        )
        self.label.pack(side="left")

        self.pack_forget()  # hidden by default

    def set_active(self) -> None:
        color = self.theme.colors["success"]
        self.dot.configure(fg_color=color)
        self.label.configure(
            text=t("toggle_card.active"),
            text_color=color,
        )
        self.pack(anchor="w", pady=(4, 0))

    def set_inactive(self) -> None:
        color = self.theme.colors.get("text_disabled", "#555")
        self.dot.configure(fg_color=color)
        self.label.configure(
            text=t("toggle_card.inactive"),
            text_color=color,
        )
        self.pack(anchor="w", pady=(4, 0))

    def hide(self) -> None:
        self.pack_forget()


# ─── Main Toggle Card ───────────────────────────────────────────────────────

class ToggleCard(ctk.CTkFrame):
    """
    Card component with:
    - Icon + title
    - Description
    - Risk level badge with tooltip
    - Toggle switch OR checkbox
    - Active/inactive status indicator
    - Hover highlight
    - Disabled state
    """

    def __init__(
        self,
        master,
        title: str,
        description: str,
        risk_level: str = "safe",
        initial_state: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
        icon: str = "",
        show_toggle: bool = True,
        show_checkbox: bool = False,
        show_status: bool = True,
        **kwargs,
    ) -> None:
        self.theme = get_theme()

        super().__init__(
            master,
            corner_radius=CARD_RADIUS,
            fg_color=self.theme.colors["bg_card"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )

        self._title = title
        self._description = description
        self._risk_level = risk_level
        self._on_toggle = on_toggle
        self._state = initial_state
        self._enabled = True
        self._show_status = show_status

        self._build_ui(icon, show_toggle, show_checkbox)
        self._bind_hover()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(
        self,
        icon: str,
        show_toggle: bool,
        show_checkbox: bool,
    ) -> None:
        self.grid_columnconfigure(0, weight=1)

        # ── Left: info ──
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=12)

        # Title row
        title_row = ctk.CTkFrame(info, fg_color="transparent")
        title_row.pack(fill="x")

        if icon:
            ctk.CTkLabel(
                title_row,
                text=icon,
                font=("Inter", 16),
                width=24,
            ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            title_row,
            text=self._title,
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Risk badge (inline with title)
        RiskBadge(title_row, risk_level=self._risk_level).pack(
            side="left", padx=(8, 0),
        )

        # Description
        if self._description:
            ctk.CTkLabel(
                info,
                text=self._description,
                font=self.theme.get_font("small"),
                text_color=self.theme.colors["text_secondary"],
                anchor="w",
                wraplength=420,
                justify="left",
            ).pack(fill="x", anchor="w", pady=(4, 0))

        # Status indicator
        if self._show_status:
            self.status_indicator = StatusIndicator(info)
            self._update_status_indicator()

        # ── Right: toggle/checkbox ──
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, padx=(0, 16), pady=12, sticky="e")

        self._control_type: Optional[str] = None

        if show_toggle:
            self._control_type = "toggle"
            self.toggle = ctk.CTkSwitch(
                right,
                text="",
                width=50,
                height=26,
                switch_width=46,
                switch_height=24,
                progress_color=self.theme.colors["accent"],
                button_color="#FFFFFF",
                button_hover_color="#F0F0F0",
                fg_color=self.theme.colors["card_border"],
                command=self._handle_toggle,
            )
            self.toggle.pack(anchor="center")

            if self._state:
                self.toggle.select()

        elif show_checkbox:
            self._control_type = "checkbox"
            self.checkbox = ctk.CTkCheckBox(
                right,
                text="",
                width=24,
                height=24,
                checkbox_width=24,
                checkbox_height=24,
                corner_radius=4,
                fg_color=self.theme.colors["accent"],
                hover_color=self.theme.colors["accent_hover"],
                border_color=self.theme.colors["card_border"],
                command=self._handle_toggle,
            )
            self.checkbox.pack(anchor="center")

            if self._state:
                self.checkbox.select()

    def _bind_hover(self) -> None:
        normal_bg = self.theme.colors["bg_card"]
        hover_bg = self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"])

        def on_enter(_):
            if self._enabled:
                self.configure(fg_color=hover_bg)

        def on_leave(_):
            if self._enabled:
                self.configure(fg_color=normal_bg)

        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)

    # ── Toggle Handling ──────────────────────────────────────────────────

    def _handle_toggle(self) -> None:
        """Internal handler for toggle/checkbox state change."""
        old_state = self._state

        if self._control_type == "toggle":
            self._state = self.toggle.get() == 1
        elif self._control_type == "checkbox":
            self._state = self.checkbox.get() == 1

        self._update_status_indicator()
        self._update_border()

        if self._on_toggle and self._state != old_state:
            try:
                self._on_toggle(self._state)
            except Exception as e:
                logger.exception("Toggle callback error for '%s'", self._title)

    def _update_status_indicator(self) -> None:
        """Update the status dot/text based on current state."""
        if not self._show_status or not hasattr(self, "status_indicator"):
            return

        if self._state:
            self.status_indicator.set_active()
        else:
            self.status_indicator.set_inactive()

    def _update_border(self) -> None:
        """Subtly change border color when active."""
        if self._state:
            # Use a muted accent color for active border
            # (CustomTkinter doesn't support alpha hex like #6C5CE766)
            active_border = self.theme.colors.get(
                "card_border_active",
                self.theme.colors.get("accent_hover", self.theme.colors["accent"]),
            )
            self.configure(border_color=active_border)
        else:
            self.configure(border_color=self.theme.colors["card_border"])

    # ── Public API ───────────────────────────────────────────────────────

    @property
    def state(self) -> bool:
        """Get current toggle state."""
        return self._state

    @state.setter
    def state(self, value: bool) -> None:
        """Set toggle state programmatically (no callback fired)."""
        self._state = value

        if self._control_type == "toggle":
            if value:
                self.toggle.select()
            else:
                self.toggle.deselect()
        elif self._control_type == "checkbox":
            if value:
                self.checkbox.select()
            else:
                self.checkbox.deselect()

        self._update_status_indicator()
        self._update_border()

    def get(self) -> bool:
        """Get current state (alias)."""
        return self._state

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the card and its control."""
        self._enabled = enabled
        widget_state = "normal" if enabled else "disabled"

        if self._control_type == "toggle":
            self.toggle.configure(state=widget_state)
        elif self._control_type == "checkbox":
            self.checkbox.configure(state=widget_state)

        # Visual feedback
        if not enabled:
            self.configure(
                fg_color=self.theme.colors.get("bg_disabled", self.theme.colors["bg_card"]),
                border_color=self.theme.colors["card_border"],
            )
        else:
            self.configure(
                fg_color=self.theme.colors["bg_card"],
            )
            self._update_border()

    @property
    def risk_level(self) -> str:
        return self._risk_level

    @property
    def title(self) -> str:
        return self._title

    def set_loading(self, loading: bool) -> None:
        """Show loading state on the card."""
        if loading:
            self.set_enabled(False)
            if hasattr(self, "status_indicator"):
                self.status_indicator.label.configure(text="⏳")
                self.status_indicator.dot.configure(
                    fg_color=self.theme.colors["accent"],
                )
                self.status_indicator.pack(anchor="w", pady=(4, 0))
        else:
            self.set_enabled(True)
            self._update_status_indicator()