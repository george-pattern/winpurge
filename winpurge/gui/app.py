"""
WinPurge Main Application
Main application window with navigation and page management.
"""

import customtkinter as ctk
from typing import Dict, Optional

from winpurge.constants import (
    APP_NAME,
    APP_VERSION,
    MIN_HEIGHT,
    MIN_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from winpurge.gui.theme import get_theme
from winpurge.gui.components.sidebar import Sidebar
from winpurge.gui.components.status_bar import StatusBar
from winpurge.gui.pages.home import HomePage
from winpurge.gui.pages.bloatware import BloatwarePage
from winpurge.gui.pages.privacy import PrivacyPage
from winpurge.gui.pages.services import ServicesPage
from winpurge.gui.pages.gaming import GamingPage
from winpurge.gui.pages.network import NetworkPage
from winpurge.gui.pages.cleanup import CleanupPage
from winpurge.gui.pages.backup import BackupPage
from winpurge.gui.pages.settings import SettingsPage
from winpurge.utils import get_relative_time, load_config, t
from winpurge.backup import backup_manager


class WinPurgeApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self) -> None:
        super().__init__()
        
        self.theme = get_theme()
        self.config = load_config()
        
        # Apply saved theme
        self.theme.set_theme(self.config.get("theme", "dark"))
        
        # Configure window
        self._configure_window()
        
        # Create layout
        self._create_layout()
        
        # Initialize pages
        self.pages: Dict[str, ctk.CTkFrame] = {}
        self.current_page: Optional[str] = None
        
        # Load initial page
        self._navigate_to("home")
        
        # Update status bar
        self._update_backup_status()
    
    def _configure_window(self) -> None:
        """Configure the main window."""
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        
        # Center window on screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        
        # Set window colors
        self.configure(fg_color=self.theme.colors["bg_main"])
        
        # Set window icon (if available)
        try:
            from winpurge.utils import get_resource_path
            icon_path = get_resource_path("assets/icon.ico")
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_layout(self) -> None:
        """Create the main layout."""
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        # Configure grid
        self.main_container.columnconfigure(1, weight=1)
        self.main_container.rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = Sidebar(
            self.main_container,
            on_navigate=self._navigate_to,
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsw")
        
        # Content area
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # Status bar
        self.status_bar = StatusBar(self.main_container)
        self.status_bar.grid(row=1, column=1, sticky="sew")
    
    def _navigate_to(self, page_name: str) -> None:
        """
        Navigate to a page.
        
        Args:
            page_name: Name of the page to navigate to.
        """
        # Don't reload if already on this page
        if page_name == self.current_page:
            return
        
        # Hide current page
        if self.current_page and self.current_page in self.pages:
            self.pages[self.current_page].pack_forget()
        
        # Create page if it doesn't exist
        if page_name not in self.pages:
            self.pages[page_name] = self._create_page(page_name)
        
        # Show new page
        self.pages[page_name].pack(fill="both", expand=True)
        self.current_page = page_name
        
        # Update sidebar
        self.sidebar.set_page(page_name)
        
        # Update status bar
        self.status_bar.set_status(t("status_bar.ready"))
    
    def _create_page(self, page_name: str) -> ctk.CTkFrame:
        """
        Create a page instance.
        
        Args:
            page_name: Name of the page to create.
            
        Returns:
            Page frame instance.
        """
        page_classes = {
            "home": lambda: HomePage(
                self.content_frame,
                on_navigate=self._navigate_to,
            ),
            "bloatware": lambda: BloatwarePage(self.content_frame),
            "privacy": lambda: PrivacyPage(self.content_frame),
            "services": lambda: ServicesPage(self.content_frame),
            "gaming": lambda: GamingPage(self.content_frame),
            "network": lambda: NetworkPage(self.content_frame),
            "cleanup": lambda: CleanupPage(self.content_frame),
            "backup": lambda: BackupPage(self.content_frame),
            "settings": lambda: SettingsPage(
                self.content_frame,
                on_language_change=self._on_language_change,
            ),
        }
        
        if page_name in page_classes:
            return page_classes[page_name]()
        
        # Default fallback page
        return self._create_placeholder_page(page_name)
    
    def _create_placeholder_page(self, page_name: str) -> ctk.CTkFrame:
        """Create a placeholder page for unimplemented pages."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        ctk.CTkLabel(
            frame,
            text=f"Page: {page_name}",
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(pady=40)
        
        ctk.CTkLabel(
            frame,
            text="This page is under construction.",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack()
        
        return frame
    
    def _on_language_change(self, language: str) -> None:
        """
        Handle language change.
        
        Args:
            language: New language code.
        """
        # Refresh sidebar labels
        self.sidebar.refresh_labels()
        
        # Refresh status bar
        self.status_bar.refresh()
        
        # Clear and recreate current page
        if self.current_page:
            old_page = self.current_page
            
            # Remove old page
            if old_page in self.pages:
                self.pages[old_page].destroy()
                del self.pages[old_page]
            
            # Reset current page
            self.current_page = None
            
            # Navigate to recreate page
            self._navigate_to(old_page)
    
    def _update_backup_status(self) -> None:
        """Update backup status in status bar."""
        last_backup = backup_manager.get_last_backup_time()
        
        if last_backup:
            self.status_bar.set_backup_status(get_relative_time(last_backup))
        else:
            self.status_bar.set_backup_status(t("home.no_backup"))
    
    def _on_close(self) -> None:
        """Handle window close event."""
        self.destroy()
    
    def run(self) -> None:
        """Run the application main loop."""
        self.mainloop()