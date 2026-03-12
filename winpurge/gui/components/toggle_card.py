"""
WinPurge Toggle Card Component
Reusable card with toggle switch for options.
"""

import customtkinter as ctk
from typing import Callable, Optional

from winpurge.constants import CARD_RADIUS
from winpurge.gui.theme import get_theme
from winpurge.gui.components.tooltip import Tooltip
from winpurge.utils import t


class ToggleCard(ctk.CTkFrame):
    """Card component with title, description, risk badge, and toggle."""
    
    def __init__(
        self,
        master: any,
        title: str,
        description: str,
        risk_level: str = "safe",
        initial_state: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
        icon: str = "",
        show_toggle: bool = True,
        show_checkbox: bool = False,
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
        
        self.title = title
        self.description = description
        self.risk_level = risk_level
        self.on_toggle = on_toggle
        self._state = initial_state
        
        self._create_widgets(icon, show_toggle, show_checkbox)
    
    def _create_widgets(
        self,
        icon: str,
        show_toggle: bool,
        show_checkbox: bool,
    ) -> None:
        """Create card widgets."""
        # Main container with padding
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=12)
        
        # Left side: icon, title, description
        left_frame = ctk.CTkFrame(container, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True)
        
        # Title row
        title_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        title_row.pack(fill="x", anchor="w")
        
        if icon:
            icon_label = ctk.CTkLabel(
                title_row,
                text=icon,
                font=self.theme.get_font("header"),
            )
            icon_label.pack(side="left", padx=(0, 8))
        
        title_label = ctk.CTkLabel(
            title_row,
            text=self.title,
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
            anchor="w",
        )
        title_label.pack(side="left", fill="x", expand=True)
        
        # Description
        desc_label = ctk.CTkLabel(
            left_frame,
            text=self.description,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
            anchor="w",
            wraplength=400,
            justify="left",
        )
        desc_label.pack(fill="x", anchor="w", pady=(4, 0))
        
        # Risk badge
        risk_colors = self.theme.get_risk_colors(self.risk_level)
        risk_badge = ctk.CTkLabel(
            left_frame,
            text=t(f"risk_levels.{self.risk_level}"),
            font=self.theme.get_font("small"),
            fg_color=risk_colors["bg"],
            text_color=risk_colors["fg"],
            corner_radius=4,
            padx=8,
            pady=2,
        )
        risk_badge.pack(anchor="w", pady=(8, 0))
        
        # Tooltip for risk badge
        Tooltip(risk_badge, t(f"risk_levels.{self.risk_level}_desc"))
        
        # Right side: toggle or checkbox
        right_frame = ctk.CTkFrame(container, fg_color="transparent")
        right_frame.pack(side="right", padx=(16, 0))
        
        if show_toggle:
            self.toggle = ctk.CTkSwitch(
                right_frame,
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
            self.checkbox = ctk.CTkCheckBox(
                right_frame,
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
    
    def _handle_toggle(self) -> None:
        """Handle toggle/checkbox state change."""
        if hasattr(self, "toggle"):
            self._state = self.toggle.get() == 1
        elif hasattr(self, "checkbox"):
            self._state = self.checkbox.get() == 1
        
        if self.on_toggle:
            self.on_toggle(self._state)
    
    @property
    def state(self) -> bool:
        """Get current toggle state."""
        return self._state
    
    @state.setter
    def state(self, value: bool) -> None:
        """Set toggle state."""
        self._state = value
        
        if hasattr(self, "toggle"):
            if value:
                self.toggle.select()
            else:
                self.toggle.deselect()
        elif hasattr(self, "checkbox"):
            if value:
                self.checkbox.select()
            else:
                self.checkbox.deselect()
    
    def get(self) -> bool:
        """Get current state (alias for state property)."""
        return self._state
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the card."""
        state = "normal" if enabled else "disabled"
        
        if hasattr(self, "toggle"):
            self.toggle.configure(state=state)
        elif hasattr(self, "checkbox"):
            self.checkbox.configure(state=state)