"""
WinPurge Main Application
Central application window and entry point.
"""

import customtkinter as ctk
import threading
from pathlib import Path
from typing import Optional

from winpurge.utils import get_logger, is_admin, request_admin, load_locale, setup_logging
from winpurge.gui.theme import Theme
from winpurge.gui.components.sidebar import Sidebar
from winpurge.gui.components.status_bar import StatusBar
from winpurge.constants import (
    APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_MIN_WIDTH,
    WINDOW_HEIGHT, WINDOW_MIN_HEIGHT
)

logger = get_logger(__name__)


class WinPurgeApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main application window."""
        super().__init__()
        
        # Setup
        setup_logging()
        
        # Check admin privileges
        if not is_admin():
            request_admin()
        
        # Initialize
        self.current_page = None
        self.theme = Theme(dark_mode=True)
        self.locale = load_locale("en")
        
        # Configure window
        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Configure appearance
        self.theme.set_dark_mode(True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create UI
        self._create_layout()
        
        logger.info(f"{APP_NAME} v{APP_VERSION} started")
    
    def _create_layout(self) -> None:
        """Create the main layout."""
        # Main container
        main_container = ctk.CTkFrame(
            self,
            fg_color=self.theme.bg_primary
        )
        main_container.pack(fill="both", expand=True)
        
        # Content container with sidebar
        content_container = ctk.CTkFrame(
            main_container,
            fg_color=self.theme.bg_primary
        )
        content_container.pack(fill="both", expand=True)
        
        # Sidebar
        self.sidebar = Sidebar(
            content_container,
            on_page_select=self._on_page_select,
            fg_color=self.theme.bg_secondary,
            corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=0, pady=0)
        
        # Main content area
        self.content_frame = ctk.CTkFrame(
            content_container,
            fg_color=self.theme.bg_primary,
            corner_radius=0
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        content_container.grid_rowconfigure(0, weight=1)
        content_container.grid_columnconfigure(1, weight=1)
        
        # Status bar
        self.status_bar = StatusBar(
            main_container,
            fg_color=self.theme.bg_secondary,
            corner_radius=0
        )
        self.status_bar.pack(fill="x", side="bottom")
        
        # Show home page by default
        self._on_page_select("home")
        self.sidebar.select_page("home")
    
    def _on_page_select(self, page_id: str) -> None:
        """
        Handle page selection.
        
        Args:
            page_id: ID of the selected page.
        """
        self.current_page = page_id
        
        # Clear current content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Create appropriate page
        if page_id == "home":
            from winpurge.gui.pages.home import HomePage
            page = HomePage(self.content_frame)
        elif page_id == "bloatware":
            from winpurge.gui.pages.bloatware import BloatwarePage
            page = BloatwarePage(self.content_frame)
        elif page_id == "privacy":
            from winpurge.gui.pages.privacy import PrivacyPage
            page = PrivacyPage(self.content_frame)
        elif page_id == "services":
            from winpurge.gui.pages.services import ServicesPage
            page = ServicesPage(self.content_frame)
        elif page_id == "gaming":
            from winpurge.gui.pages.gaming import GamingPage
            page = GamingPage(self.content_frame)
        elif page_id == "network":
            from winpurge.gui.pages.network import NetworkPage
            page = NetworkPage(self.content_frame)
        elif page_id == "cleanup":
            from winpurge.gui.pages.cleanup import CleanupPage
            page = CleanupPage(self.content_frame)
        elif page_id == "backup":
            from winpurge.gui.pages.backup import BackupPage
            page = BackupPage(self.content_frame)
        elif page_id == "settings":
            from winpurge.gui.pages.settings import SettingsPage
            page = SettingsPage(self.content_frame)
        else:
            return
        
        page.pack(fill="both", expand=True, padx=0, pady=0)


def main():
    """Main entry point."""
    app = WinPurgeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
