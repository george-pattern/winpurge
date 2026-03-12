"""
WinPurge GUI Status Bar Component
Bottom status bar showing system information and backup status.
"""

import customtkinter as ctk
from datetime import datetime

from winpurge.gui.theme import get_theme_manager
from winpurge.constants import FONT_SIZE_SMALL


class StatusBar(ctk.CTkFrame):
    """Status bar showing OS info and backup status."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the status bar.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent, **kwargs)
        
        self.theme = get_theme_manager()
        
        # Configure frame
        self.configure(
            fg_color=self.theme.get_color("BG_SECONDARY"),
            height=40,
            corner_radius=0
        )
        self.grid_propagate(False)
        
        # Create content
        self._create_content()
    
    def _create_content(self) -> None:
        """Create status bar content."""
        # OS version
        self.os_label = ctk.CTkLabel(
            self,
            text="Windows 11 Pro | Build: 22621",
            font=("Arial", FONT_SIZE_SMALL),
            fg_color="transparent",
            text_color=self.theme.get_color("TEXT_SECONDARY")
        )
        self.os_label.pack(side="left", padx=15, pady=10)
        
        # Separator
        sep = ctk.CTkLabel(
            self,
            text="|",
            fg_color="transparent",
            text_color=self.theme.get_color("TEXT_SECONDARY")
        )
        sep.pack(side="left", padx=5)
        
        # Backup status
        self.backup_label = ctk.CTkLabel(
            self,
            text="Backup: No backup yet",
            font=("Arial", FONT_SIZE_SMALL),
            fg_color="transparent",
            text_color=self.theme.get_color("STATUS_WARNING")
        )
        self.backup_label.pack(side="left", padx=5)
        
        # Spacer
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(side="left", fill="x", expand=True)
        
        # Profile indicator
        self.profile_label = ctk.CTkLabel(
            self,
            text="Profile: Default",
            font=("Arial", FONT_SIZE_SMALL),
            fg_color="transparent",
            text_color=self.theme.get_color("TEXT_SECONDARY")
        )
        self.profile_label.pack(side="right", padx=15, pady=10)
    
    def set_os_info(self, os_version: str) -> None:
        """
        Set OS version information.
        
        Args:
            os_version: OS version string.
        """
        self.os_label.configure(text=os_version)
    
    def set_backup_status(self, has_backup: bool, backup_time: str = "") -> None:
        """
        Update backup status.
        
        Args:
            has_backup: If True, backup exists.
            backup_time: Time of last backup.
        """
        if has_backup:
            text = f"Backup: {backup_time}"
            color = self.theme.get_color("STATUS_SUCCESS")
        else:
            text = "Backup: No backup yet"
            color = self.theme.get_color("STATUS_WARNING")
        
        self.backup_label.configure(text=text, text_color=color)
    
    def set_profile(self, profile_name: str) -> None:
        """
        Set current profile name.
        
        Args:
            profile_name: Name of the profile.
        """
        self.profile_label.configure(text=f"Profile: {profile_name}")
