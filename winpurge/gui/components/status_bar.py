"""
WinPurge Status Bar Component
Bottom status bar showing system info.
"""

import customtkinter as ctk
from typing import Optional

from winpurge.gui.theme import get_theme
from winpurge.utils import get_windows_version, t


class StatusBar(ctk.CTkFrame):
    """Bottom status bar component."""
    
    def __init__(self, master: any, **kwargs) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            height=32,
            corner_radius=0,
            fg_color=self.theme.colors["bg_sidebar"],
            **kwargs,
        )
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create status bar widgets."""
        # Left side: OS info
        self.os_label = ctk.CTkLabel(
            self,
            text=self._get_os_text(),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.os_label.pack(side="left", padx=16)
        
        # Separator
        sep = ctk.CTkFrame(
            self,
            width=1,
            height=16,
            fg_color=self.theme.colors["divider"],
        )
        sep.pack(side="left", padx=8)
        
        # Backup status
        self.backup_label = ctk.CTkLabel(
            self,
            text=t("status_bar.backup_status", status=t("home.no_backup")),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.backup_label.pack(side="left", padx=8)
        
        # Right side: status
        self.status_label = ctk.CTkLabel(
            self,
            text=t("status_bar.ready"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.status_label.pack(side="right", padx=16)
    
    def _get_os_text(self) -> str:
        """Get formatted OS version text."""
        version_info = get_windows_version()
        return t("status_bar.os_info", version=version_info.get("display", "Windows"))
    
    def set_status(self, text: str) -> None:
        """Set status text."""
        self.status_label.configure(text=text)
    
    def set_backup_status(self, text: str) -> None:
        """Set backup status text."""
        self.backup_label.configure(
            text=t("status_bar.backup_status", status=text)
        )
    
    def refresh(self) -> None:
        """Refresh status bar content."""
        self.os_label.configure(text=self._get_os_text())