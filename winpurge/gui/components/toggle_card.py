"""
WinPurge GUI Toggle Card Component
Reusable toggle card widget for options.
"""

from typing import Callable, Optional
import customtkinter as ctk

from winpurge.gui.theme import get_theme_manager
from winpurge.constants import BORDER_RADIUS, FONT_SIZE_BODY, FONT_SIZE_SMALL

RISK_COLORS = {
    "safe": "#00D26A",
    "moderate": "#FFB347",
    "advanced": "#FF6B6B"
}


class ToggleCard(ctk.CTkFrame):
    """A toggle card widget for application options."""
    
    def __init__(
        self,
        parent,
        title: str,
        description: str = "",
        icon: str = "⚙️",
        risk_level: str = "safe",
        on_toggle: Optional[Callable[[bool], None]] = None,
        enabled: bool = False,
        **kwargs
    ):
        """
        Initialize a toggle card.
        
        Args:
            parent: Parent widget.
            title: Card title.
            description: Card description.
            icon: Icon emoji.
            risk_level: Risk level (safe, moderate, advanced).
            on_toggle: Callback when toggled.
            enabled: Initial toggle state.
        """
        super().__init__(parent, **kwargs)
        
        self.title = title
        self.description = description
        self.icon = icon
        self.risk_level = risk_level
        self.on_toggle = on_toggle
        self.is_enabled = enabled
        self.theme = get_theme_manager()
        
        # Configure frame
        self.configure(
            fg_color=self.theme.get_color("BG_TERTIARY"),
            border_width=1,
            border_color=self.theme.get_color("BORDER_COLOR"),
            corner_radius=BORDER_RADIUS
        )
        
        # Create content
        self._create_content()
        
        # Set height
        self.configure(height=80)
    
    def _create_content(self) -> None:
        """Create card content."""
        # Main horizontal container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=12)
        
        # Left section (icon, title, description)
        left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True)
        
        # Icon + Title
        header_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=0, pady=(0, 5))
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text=self.icon,
            font=("Arial", 16),
            fg_color="transparent",
            text_color=self.theme.get_color("TEXT_PRIMARY")
        )
        icon_label.pack(side="left", padx=(0, 8))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=self.title,
            font=("Arial", FONT_SIZE_BODY, "bold"),
            fg_color="transparent",
            text_color=self.theme.get_color("TEXT_PRIMARY")
        )
        title_label.pack(side="left")
        
        # Description and risk label
        desc_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        desc_frame.pack(fill="x", padx=24, pady=(0, 5))
        
        if self.description:
            desc_label = ctk.CTkLabel(
                desc_frame,
                text=self.description,
                font=("Arial", FONT_SIZE_SMALL),
                fg_color="transparent",
                text_color=self.theme.get_color("TEXT_SECONDARY")
            )
            desc_label.pack(anchor="w")
        
        # Risk badge
        risk_color = RISK_COLORS.get(self.risk_level, "#FFB347")
        risk_label = ctk.CTkLabel(
            desc_frame,
            text=f"● {self.risk_level.capitalize()}",
            font=("Arial", FONT_SIZE_SMALL, "bold"),
            fg_color="transparent",
            text_color=risk_color
        )
        risk_label.pack(anchor="w", pady=(3, 0))
        
        # Right section (toggle switch)
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.pack(side="right", padx=(15, 0))
        
        # Toggle switch
        self.switch = ctk.CTkSwitch(
            right_frame,
            text="",
            onvalue=True,
            offvalue=False,
            command=self._on_toggle,
            button_color=self.theme.get_color("ACCENT_PRIMARY"),
            progress_color=self.theme.get_color("ACCENT_PRIMARY")
        )
        self.switch.pack()
        
        # Set initial state
        if self.is_enabled:
            self.switch.select()
    
    def _on_toggle(self) -> None:
        """Handle toggle switch action."""
        self.is_enabled = self.switch.get()
        if self.on_toggle:
            self.on_toggle(self.is_enabled)
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Set toggle state programmatically.
        
        Args:
            enabled: New state.
        """
        self.is_enabled = enabled
        if enabled:
            self.switch.select()
        else:
            self.switch.deselect()
    
    def get_enabled(self) -> bool:
        """Get current toggle state."""
        return self.switch.get()
