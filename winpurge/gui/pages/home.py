"""
WinPurge Home Page
Dashboard with system overview and quick actions.
"""

import customtkinter as ctk
import psutil

from winpurge.gui.theme import Theme
from winpurge.constants import FONT_SIZE_HEADER, FONT_SIZE_BODY
from winpurge.utils import get_system_info, get_uptime, load_locale


class HomePage(ctk.CTkFrame):
    """Home page showing system overview."""
    
    def __init__(self, parent, **kwargs):
        """Initialize home page."""
        super().__init__(parent, **kwargs)
        
        self.theme = Theme(dark_mode=True)
        self.locale = load_locale("en")
        
        self.configure(fg_color=self.theme.bg_primary)
        
        # Create content
        self._create_content()
    
    def _create_content(self) -> None:
        """Create page content."""
        # Scrollable main container
        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.theme.bg_primary
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            scroll_frame,
            text="Dashboard",
            font=("Arial", FONT_SIZE_HEADER, "bold"),
            fg_color="transparent",
            text_color=self.theme.text_primary
        )
        title.pack(fill="x", pady=(0, 5))
        
        subtitle = ctk.CTkLabel(
            scroll_frame,
            text="System overview and quick actions",
            font=("Arial", FONT_SIZE_BODY),
            fg_color="transparent",
            text_color=self.theme.text_secondary
        )
        subtitle.pack(fill="x", pady=(0, 20))
        
        # System info section
        info_label = ctk.CTkLabel(
            scroll_frame,
            text="System Information",
            font=("Arial", 14, "bold"),
            fg_color="transparent",
            text_color=self.theme.text_primary
        )
        info_label.pack(fill="x", pady=(15, 10))
        
        sys_info = get_system_info()
        info_text = f"""
OS: {sys_info.get('os', 'N/A')}
CPU: {sys_info.get('cpu', 'N/A')}
RAM: {sys_info.get('ram_available', 'N/A')} / {sys_info.get('ram_total', 'N/A')}
Disk: {sys_info.get('disk_free', 'N/A')} free / {sys_info.get('disk_total', 'N/A')} total
Uptime: {get_uptime()}
        """.strip()
        
        info_text_label = ctk.CTkLabel(
            scroll_frame,
            text=info_text,
            font=("Courier", 11),
            fg_color=self.theme.bg_tertiary,
            text_color=self.theme.text_secondary,
            justify="left"
        )
        info_text_label.pack(fill="x", padx=10, pady=10)
        
        # Quick stats section
        stats_label = ctk.CTkLabel(
            scroll_frame,
            text="Quick Overview",
            font=("Arial", 14, "bold"),
            fg_color="transparent",
            text_color=self.theme.text_primary
        )
        stats_label.pack(fill="x", pady=(20, 10))
        
        # Stats cards
        stats_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        stats_frame.pack(fill="x")
        
        stats = [
            ("Bloatware Found", "12", self.theme.warning),
            ("Services Active", "7", self.theme.warning),
            ("Telemetry", "BLOCKED", self.theme.success),
            ("Last Backup", "None", self.theme.danger)
        ]
        
        for title, value, color in stats:
            card = ctk.CTkFrame(
                stats_frame,
                fg_color=self.theme.bg_tertiary,
                border_width=1,
                border_color=self.theme.border_color,
                corner_radius=8
            )
            card.pack(fill="x", pady=8)
            
            title_lbl = ctk.CTkLabel(
                card,
                text=title,
                font=("Arial", FONT_SIZE_BODY),
                fg_color="transparent",
                text_color=self.theme.text_secondary
            )
            title_lbl.pack(anchor="w", padx=12, pady=(8, 0))
            
            value_lbl = ctk.CTkLabel(
                card,
                text=value,
                font=("Arial", 16, "bold"),
                fg_color="transparent",
                text_color=color
            )
            value_lbl.pack(anchor="w", padx=12, pady=(0, 8))
        
        # Quick actions
        actions_label = ctk.CTkLabel(
            scroll_frame,
            text="Quick Actions",
            font=("Arial", 14, "bold"),
            fg_color="transparent",
            text_color=self.theme.text_primary
        )
        actions_label.pack(fill="x", pady=(20, 10))
        
        # Action buttons
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        btn1 = ctk.CTkButton(
            button_frame,
            text="Apply Recommended",
            fg_color=self.theme.accent,
            text_color="white"
        )
        btn1.pack(fill="x", pady=8)
        
        btn2 = ctk.CTkButton(
            button_frame,
            text="Create Backup",
            fg_color=self.theme.accent,
            text_color="white"
        )
        btn2.pack(fill="x", pady=8)
        
        btn3 = ctk.CTkButton(
            button_frame,
            text="Restore Last Backup",
            fg_color=self.theme.accent,
            text_color="white"
        )
        btn3.pack(fill="x", pady=8)
