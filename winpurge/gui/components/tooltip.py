"""
WinPurge GUI Tooltip Component
Hover tooltip for displaying additional information.
"""

import customtkinter as ctk
from typing import Optional

from winpurge.gui.theme import get_theme_manager
from winpurge.constants import FONT_SIZE_SMALL


class Tooltip:
    """Tooltip widget that appears on hover."""
    
    def __init__(
        self,
        widget,
        text: str,
        delay: int = 500
    ):
        """
        Initialize a tooltip.
        
        Args:
            widget: Widget to attach tooltip to.
            text: Tooltip text.
            delay: Delay before showing in milliseconds.
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.theme = get_theme_manager()
        self.tooltip = None
        self.timer_id = None
        
        # Bind events
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<Motion>", self._on_motion, add="+")
    
    def _on_enter(self, event) -> None:
        """Handle mouse enter event."""
        if not self.timer_id:
            self.timer_id = self.widget.after(
                self.delay,
                self._show_tooltip,
                event
            )
    
    def _on_leave(self, event) -> None:
        """Handle mouse leave event."""
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None
        self._hide_tooltip()
    
    def _on_motion(self, event) -> None:
        """Handle mouse motion event."""
        if self.tooltip:
            # Update tooltip position
            x = event.x_root + 10
            y = event.y_root + 10
            self.tooltip.geometry(f"+{x}+{y}")
    
    def _show_tooltip(self, event) -> None:
        """Show tooltip at mouse position."""
        if self.tooltip:
            return
        
        # Create tooltip window
        self.tooltip = ctk.CTkToplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.attributes("-topmost", True)
        
        # Configure appearance
        self.tooltip.configure(
            fg_color=self.theme.get_color("BG_TERTIARY")
        )
        
        # Add label
        label = ctk.CTkLabel(
            self.tooltip,
            text=self.text,
            font=("Arial", FONT_SIZE_SMALL),
            fg_color="transparent",
            text_color=self.theme.get_color("TEXT_PRIMARY"),
            wraplength=200,
            justify="left"
        )
        label.pack(padx=8, pady=6)
        
        # Position tooltip
        x = event.x_root + 10
        y = event.y_root + 10
        self.tooltip.geometry(f"+{x}+{y}")
    
    def _hide_tooltip(self) -> None:
        """Hide tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def destroy(self) -> None:
        """Destroy the tooltip and clean up."""
        self._hide_tooltip()
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
