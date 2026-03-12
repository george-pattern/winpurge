"""
WinPurge GUI Sidebar Component
Left navigation sidebar with page navigation.
"""

from typing import Callable, Optional
import customtkinter as ctk

from winpurge.utils import get_logger
from winpurge.gui.theme import get_theme_manager
from winpurge.constants import SIDEBAR_WIDTH, FONT_SIZE_BODY

logger = get_logger(__name__)


class Sidebar(ctk.CTkFrame):
    """Left sidebar with navigation buttons."""
    
    def __init__(
        self,
        parent,
        on_page_select: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """
        Initialize the sidebar.
        
        Args:
            parent: Parent widget.
            on_page_select: Callback when a page is selected.
        """
        super().__init__(parent, **kwargs)
        
        self.on_page_select = on_page_select
        self.theme = get_theme_manager()
        self.selected_page = ""
        self.buttons = {}
        
        # Configure sidebar appearance
        self.configure(
            fg_color=self.theme.get_color("BG_SECONDARY"),
            width=SIDEBAR_WIDTH,
            corner_radius=0
        )
        self.grid_propagate(False)
        
        # Create pages list
        self.pages = [
            ("home", "🏠 Dashboard"),
            ("bloatware", "📦 Bloatware"),
            ("privacy", "🔒 Privacy"),
            ("services", "⚙️ Services"),
            ("gaming", "🎮 Gaming"),
            ("network", "🌐 Network"),
            ("cleanup", "🧹 Cleanup"),
            ("backup", "💾 Backup"),
            ("settings", "⚙️ Settings")
        ]
        
        # Create navigation buttons
        self._create_nav_buttons()
    
    def _create_nav_buttons(self) -> None:
        """Create navigation buttons for each page."""
        for page_id, page_label in self.pages:
            btn = ctk.CTkButton(
                self,
                text=page_label,
                height=45,
                corner_radius=0,
                font=("Arial", FONT_SIZE_BODY),
                fg_color="transparent",
                hover_color=self.theme.get_color("ACCENT_PRIMARY"),
                text_color=self.theme.get_color("TEXT_PRIMARY"),
                command=lambda pid=page_id: self._select_page(pid)
            )
            btn.pack(fill="x", padx=0, pady=0)
            self.buttons[page_id] = btn
    
    def _select_page(self, page_id: str) -> None:
        """
        Select a page and update UI.
        
        Args:
            page_id: ID of the page to select.
        """
        # Update button colors
        if self.selected_page and self.selected_page in self.buttons:
            self.buttons[self.selected_page].configure(
                fg_color="transparent",
                text_color=self.theme.get_color("TEXT_PRIMARY")
            )
        
        # Set new selection
        self.selected_page = page_id
        self.buttons[page_id].configure(
            fg_color=self.theme.get_color("ACCENT_PRIMARY"),
            text_color=self.theme.get_color("TEXT_PRIMARY")
        )
        
        # Call callback
        if self.on_page_select:
            self.on_page_select(page_id)
    
    def select_page(self, page_id: str) -> None:
        """
        Programmatically select a page.
        
        Args:
            page_id: ID of the page to select.
        """
        self._select_page(page_id)
