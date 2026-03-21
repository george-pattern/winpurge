"""
WinPurge Main Application
Main application window with sidebar navigation, page management,
status bar, and theme/language support.
"""

import customtkinter as ctk
import logging
import threading
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
from winpurge.gui.components.status_bar import StatusBar, StatusLevel
from winpurge.utils import get_relative_time, load_config, t
from winpurge.core.backup import backup_manager

logger = logging.getLogger(__name__)


# ─── Page Registry ───────────────────────────────────────────────────────────
# Lazy imports to avoid circular dependencies and speed up startup.

PAGE_REGISTRY = {
    "home":      "winpurge.gui.pages.home.HomePage",
    "bloatware": "winpurge.gui.pages.bloatware.BloatwarePage",
    "privacy":   "winpurge.gui.pages.privacy.PrivacyPage",
    "services":  "winpurge.gui.pages.services.ServicesPage",
    "gaming":    "winpurge.gui.pages.gaming.GamingPage",
    "network":   "winpurge.gui.pages.network.NetworkPage",
    "cleanup":   "winpurge.gui.pages.cleanup.CleanupPage",
    "backup":    "winpurge.gui.pages.backup.BackupPage",
    "settings":  "winpurge.gui.pages.settings.SettingsPage",
}

# Pages that accept special kwargs
PAGE_KWARGS = {
    "home":     lambda app: {"on_navigate": app._navigate_to},
    "settings": lambda app: {"on_language_change": app._on_language_change},
}


def _import_page_class(dotted_path: str):
    """Dynamically import a page class from its dotted path."""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


# ─── Main Application ───────────────────────────────────────────────────────

class WinPurgeApp(ctk.CTk):
    """
    Main WinPurge application window.

    Manages:
    - Sidebar navigation
    - Lazy page loading and caching
    - Status bar updates
    - Theme and language switching
    - Graceful shutdown
    """

    def __init__(self) -> None:
        super().__init__()

        self.theme = get_theme()
        self.config_data = load_config()

        # Apply saved theme
        saved_theme = self.config_data.get("theme", "dark")
        self.theme.set_theme(saved_theme)

        # Register for theme changes
        self.theme.register_callback(self._on_theme_changed)

        # State
        self.pages: Dict[str, ctk.CTkFrame] = {}
        self.current_page: Optional[str] = None
        self._is_closing = False

        # Build UI
        self._configure_window()
        self._create_layout()

        # Navigate to home
        self._navigate_to("home")

        # Background initialization
        self._init_background_tasks()

    # ── Window Configuration ─────────────────────────────────────────────

    def _configure_window(self) -> None:
        """Configure the main window properties."""
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Center on screen
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - WINDOW_WIDTH) // 2
        y = (screen_h - WINDOW_HEIGHT) // 2
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        # Window colors
        self.configure(fg_color=self.theme.colors["bg_main"])

        # Window icon
        self._set_icon()

        # Close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_icon(self) -> None:
        """Set window icon if available."""
        try:
            from winpurge.utils import get_resource_path
            icon_path = get_resource_path("assets/icon.ico")
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass  # icon is optional

    # ── Layout ───────────────────────────────────────────────────────────

    def _create_layout(self) -> None:
        """Create the main three-panel layout: sidebar | content | statusbar."""
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        self.main_container.columnconfigure(1, weight=1)
        self.main_container.rowconfigure(0, weight=1)

        # ── Sidebar ──
        self.sidebar = Sidebar(
            self.main_container,
            on_navigate=self._navigate_to,
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsw")

        # ── Content area ──
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        # ── Status bar ──
        self.status_bar = StatusBar(self.main_container)
        self.status_bar.grid(row=1, column=1, sticky="sew")

    # ── Navigation ───────────────────────────────────────────────────────

    def _navigate_to(self, page_name: str) -> None:
        """
        Navigate to a page by name. Pages are lazily created and cached.

        Args:
            page_name: Page identifier (e.g. 'home', 'bloatware').
        """
        if page_name == self.current_page:
            return

        if page_name not in PAGE_REGISTRY:
            logger.warning("Unknown page: '%s'", page_name)
            return

        # Hide current page
        self._hide_current_page()

        # Create page if not cached
        if page_name not in self.pages:
            self.status_bar.set_working(f"Loading {page_name}...")

            try:
                page = self._create_page(page_name)
                self.pages[page_name] = page
            except Exception as e:
                logger.exception("Failed to create page '%s'", page_name)
                self.pages[page_name] = self._create_error_page(page_name, str(e))

        # Show page
        self.pages[page_name].pack(fill="both", expand=True)
        self.current_page = page_name

        # Update sidebar highlight
        self.sidebar.set_page(page_name)

        # Update status
        self.status_bar.set_status(t("status_bar.ready"), StatusLevel.IDLE)

        logger.debug("Navigated to '%s'", page_name)

    def _hide_current_page(self) -> None:
        """Hide the currently displayed page."""
        if self.current_page and self.current_page in self.pages:
            try:
                self.pages[self.current_page].pack_forget()
            except Exception:
                pass

    def _create_page(self, page_name: str) -> ctk.CTkFrame:
        """
        Dynamically create a page instance.

        Args:
            page_name: Page identifier.

        Returns:
            Instantiated page frame.
        """
        dotted_path = PAGE_REGISTRY[page_name]
        page_class = _import_page_class(dotted_path)

        # Determine kwargs
        kwargs_factory = PAGE_KWARGS.get(page_name)
        extra_kwargs = kwargs_factory(self) if kwargs_factory else {}

        return page_class(self.content_frame, **extra_kwargs)

    def _create_error_page(self, page_name: str, error: str) -> ctk.CTkFrame:
        """Create an error placeholder page."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")

        error_card = ctk.CTkFrame(
            frame,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["danger"],
        )
        error_card.pack(expand=True, padx=60, pady=60)

        inner = ctk.CTkFrame(error_card, fg_color="transparent")
        inner.pack(padx=32, pady=24)

        ctk.CTkLabel(
            inner,
            text="❌",
            font=("Inter", 48),
        ).pack()

        ctk.CTkLabel(
            inner,
            text=f"Failed to load: {page_name}",
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["danger"],
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            inner,
            text=error,
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
            wraplength=400,
        ).pack()

        ctk.CTkButton(
            inner,
            text=f"🔄  Retry",
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=lambda: self._retry_page(page_name),
        ).pack(pady=(16, 0))

        return frame

    def _retry_page(self, page_name: str) -> None:
        """Retry loading a failed page."""
        if page_name in self.pages:
            self.pages[page_name].destroy()
            del self.pages[page_name]
        self.current_page = None
        self._navigate_to(page_name)

    # ── Background Tasks ─────────────────────────────────────────────────

    def _init_background_tasks(self) -> None:
        """Run background initialization tasks."""

        def _worker():
            try:
                self._update_backup_status()
                self._update_sidebar_badges()
            except Exception as e:
                logger.debug("Background init error: %s", e)

        threading.Thread(target=_worker, daemon=True).start()

    def _update_backup_status(self) -> None:
        """Update backup status in status bar."""
        try:
            last_backup = backup_manager.get_last_backup_time()

            def _update():
                if last_backup:
                    self.status_bar.set_backup_status(
                        get_relative_time(last_backup),
                        has_backup=True,
                    )
                else:
                    self.status_bar.set_backup_status(
                        t("home.no_backup"),
                        has_backup=False,
                    )

            self.after(0, _update)
        except Exception as e:
            logger.debug("Failed to update backup status: %s", e)

    def _update_sidebar_badges(self) -> None:
        """Update notification badges on sidebar buttons."""
        try:
            from winpurge.core.bloatware import bloatware_manager
            count = bloatware_manager.get_bloatware_count()
            if count > 0:
                self.after(0, lambda: self.sidebar.set_badge("bloatware", count))
        except Exception as e:
            logger.debug("Failed to update sidebar badges: %s", e)

    # ── Theme Change ─────────────────────────────────────────────────────

    def _on_theme_changed(self, theme: str) -> None:
        """Handle theme change — update main window background."""
        try:
            self.configure(fg_color=self.theme.colors["bg_main"])
        except Exception as e:
            logger.debug("Theme change update error: %s", e)

    # ── Language Change ──────────────────────────────────────────────────

    def _on_language_change(self, language: str) -> None:
        """
        Handle language change — refresh UI elements.

        Args:
            language: New language code.
        """
        logger.info("Language changed to '%s'", language)

        # Refresh sidebar labels
        self.sidebar.refresh_labels()

        # Refresh status bar
        self.status_bar.refresh()

        # Destroy and recreate current page to apply new translations
        if self.current_page:
            old_page = self.current_page

            # Destroy the cached page
            if old_page in self.pages:
                try:
                    self.pages[old_page].destroy()
                except Exception:
                    pass
                del self.pages[old_page]

            # Reset and re-navigate
            self.current_page = None
            self._navigate_to(old_page)

        # Also clear other cached pages so they rebuild with new language
        pages_to_clear = [
            name for name in self.pages
            if name != self.current_page
        ]
        for name in pages_to_clear:
            try:
                self.pages[name].destroy()
            except Exception:
                pass
            del self.pages[name]

    # ── Shutdown ─────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        """Handle window close with cleanup."""
        if self._is_closing:
            return

        self._is_closing = True
        logger.info("Application closing...")

        # Unregister theme callback
        try:
            self.theme.unregister_callback(self._on_theme_changed)
        except Exception:
            pass

        # Destroy all pages
        for name, page in self.pages.items():
            try:
                page.destroy()
            except Exception:
                pass

        self.pages.clear()

        # Destroy main window
        try:
            self.destroy()
        except Exception:
            pass

    # ── Public API ───────────────────────────────────────────────────────

    def run(self) -> None:
        """Run the application main loop."""
        logger.info("Starting %s v%s", APP_NAME, APP_VERSION)
        self.mainloop()

    def navigate(self, page: str) -> None:
        """Public navigation method for external use."""
        self._navigate_to(page)

    def refresh_current_page(self) -> None:
        """Force refresh the current page by destroying and recreating it."""
        if self.current_page:
            page_name = self.current_page

            if page_name in self.pages:
                try:
                    self.pages[page_name].destroy()
                except Exception:
                    pass
                del self.pages[page_name]

            self.current_page = None
            self._navigate_to(page_name)