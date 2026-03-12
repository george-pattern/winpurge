"""
WinPurge Sidebar Component
Navigation sidebar with icons and labels.
"""

import customtkinter as ctk
from typing import Callable, Dict, List, Optional

from winpurge.constants import SIDEBAR_WIDTH
from winpurge.gui.theme import get_theme
from winpurge.utils import t


class SidebarButton(ctk.CTkButton):
    """Custom sidebar navigation button."""
    
    def __init__(
        self,
        master: any,
        text: str,
        icon: str,
        command: Callable,
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            text=f"  {icon}  {text}",
            command=command,
            anchor="w",
            height=44,
            corner_radius=8,
            font=self.theme.get_font("body"),
            fg_color="transparent",
            text_color=self.theme.colors["text_secondary"],
            hover_color=self.theme.colors["bg_card"],
            **kwargs,
        )
        
        self._active = False
    
    def set_active(self, active: bool) -> None:
        """Set the active state of the button."""
        self._active = active
        
        if active:
            self.configure(
                fg_color=self.theme.colors["accent"],
                text_color="#FFFFFF",
                hover_color=self.theme.colors["accent_hover"],
            )
        else:
            self.configure(
                fg_color="transparent",
                text_color=self.theme.colors["text_secondary"],
                hover_color=self.theme.colors["bg_card"],
            )


class Sidebar(ctk.CTkFrame):
    """Navigation sidebar component."""
    
    ICONS: Dict[str, str] = {
        "home": "🏠",
        "bloatware": "📦",
        "privacy": "🔒",
        "services": "⚙️",
        "gaming": "🎮",
        "network": "🌐",
        "cleanup": "🧹",
        "backup": "💾",
        "settings": "⚡",
    }
    
    def __init__(
        self,
        master: any,
        on_navigate: Callable[[str], None],
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=self.theme.colors["bg_sidebar"],
            **kwargs,
        )
        
        self.on_navigate = on_navigate
        self.buttons: Dict[str, SidebarButton] = {}
        self.current_page = "home"
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create sidebar widgets."""
        # Logo section
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 10))
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="🛡️ WinPurge",
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        logo_label.pack(anchor="w")
        
        version_label = ctk.CTkLabel(
            logo_frame,
            text="v1.0.0",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        version_label.pack(anchor="w")
        
        # Divider
        divider = ctk.CTkFrame(
            self,
            height=1,
            fg_color=self.theme.colors["divider"],
        )
        divider.pack(fill="x", padx=16, pady=16)
        
        # Navigation buttons
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, padx=12)
        
        pages = [
            "home",
            "bloatware",
            "privacy",
            "services",
            "gaming",
            "network",
            "cleanup",
            "backup",
            "settings",
        ]
        
        for page in pages:
            btn = SidebarButton(
                nav_frame,
                text=t(f"sidebar.{page}"),
                icon=self.ICONS.get(page, "📄"),
                command=lambda p=page: self._handle_navigate(p),
            )
            btn.pack(fill="x", pady=2)
            self.buttons[page] = btn
        
        # Set initial active state
        self.buttons["home"].set_active(True)
    
    def _handle_navigate(self, page: str) -> None:
        """Handle navigation button click."""
        if page == self.current_page:
            return
        
        # Update button states
        if self.current_page in self.buttons:
            self.buttons[self.current_page].set_active(False)
        
        self.buttons[page].set_active(True)
        self.current_page = page
        
        # Call navigation callback
        self.on_navigate(page)
    
    def set_page(self, page: str) -> None:
        """Programmatically set the current page."""
        if page in self.buttons:
            self._handle_navigate(page)
    
    def refresh_labels(self) -> None:
        """Refresh button labels after language change."""
        for page, btn in self.buttons.items():
            icon = self.ICONS.get(page, "📄")
            btn.configure(text=f"  {icon}  {t(f'sidebar.{page}')}")