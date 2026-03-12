"""
WinPurge Tooltip Component
Hover tooltip for widgets.
"""

import customtkinter as ctk
from typing import Optional

from winpurge.constants import TOOLTIP_DELAY
from winpurge.gui.theme import get_theme


class Tooltip:
    """Tooltip that appears on hover."""
    
    def __init__(
        self,
        widget: ctk.CTkBaseClass,
        text: str,
        delay: int = TOOLTIP_DELAY,
    ) -> None:
        self.widget = widget
        self.text = text
        self.delay = delay
        self.theme = get_theme()
        
        self._tooltip_window: Optional[ctk.CTkToplevel] = None
        self._after_id: Optional[str] = None
        
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<Button>", self._on_leave)
    
    def _on_enter(self, event) -> None:
        """Handle mouse enter."""
        self._schedule_show()
    
    def _on_leave(self, event) -> None:
        """Handle mouse leave."""
        self._cancel_show()
        self._hide()
    
    def _schedule_show(self) -> None:
        """Schedule tooltip display."""
        self._cancel_show()
        self._after_id = self.widget.after(self.delay, self._show)
    
    def _cancel_show(self) -> None:
        """Cancel scheduled tooltip display."""
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
    
    def _show(self) -> None:
        """Display the tooltip."""
        if self._tooltip_window:
            return
        
        # Get position
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        
        # Create tooltip window
        self._tooltip_window = ctk.CTkToplevel(self.widget)
        self._tooltip_window.wm_overrideredirect(True)
        self._tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Make it stay on top
        self._tooltip_window.wm_attributes("-topmost", True)
        
        # Tooltip frame
        frame = ctk.CTkFrame(
            self._tooltip_window,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=6,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        frame.pack()
        
        # Tooltip text
        label = ctk.CTkLabel(
            frame,
            text=self.text,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_primary"],
            wraplength=300,
            justify="left",
        )
        label.pack(padx=10, pady=6)
    
    def _hide(self) -> None:
        """Hide the tooltip."""
        if self._tooltip_window:
            self._tooltip_window.destroy()
            self._tooltip_window = None
    
    def update_text(self, text: str) -> None:
        """Update tooltip text."""
        self.text = text