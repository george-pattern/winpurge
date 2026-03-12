"""GUI pages for WinPurge application."""

import customtkinter as ctk
from ..theme import Theme


class BasePage(ctk.CTkFrame):
    """Base class for all application pages."""
    
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = Theme(dark_mode=True)
        self.configure(fg_color=self.theme.bg_primary)
        
        # Create header frame
        header_frame = ctk.CTkFrame(self, fg_color=self.theme.bg_primary)
        header_frame.pack(pady=(20, 10), padx=20, fill="x")
        
        # Add title if provided
        if title:
            title_label = ctk.CTkLabel(
                header_frame,
                text=title,
                font=(self.theme.get_font(24)[0], 24, "bold"),
                text_color=self.theme.text_primary
            )
            title_label.pack(side="left", anchor="w")
        
        # Create scrollable content frame
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.theme.bg_primary,
            scrollbar_button_color=self.theme.accent
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))


class BloatwarePage(BasePage):
    """Bloatware removal page with category-based toggle cards."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Bloatware Removal", **kwargs)
        from ...core.bloatware import BloatwareManager
        from ...utils import get_logger
        
        self.logger = get_logger(__name__)
        self.bloatware_manager = BloatwareManager()
        self.selected_packages = []
        
        self._create_content()
    
    def _create_content(self):
        """Create bloatware removal interface."""
        try:
            status = self.bloatware_manager.get_bloatware_status()
            
            # Info section
            info_text = f"Found {status['found']} known bloatware apps out of {status['total_known']}"
            info_label = ctk.CTkLabel(
                self.scroll_frame,
                text=info_text,
                font=(self.theme.get_font(13)[0], 13),
                text_color=self.theme.text_secondary
            )
            info_label.pack(pady=(0, 20), padx=10)
            
            # Categories
            for package in status.get('packages', []):
                category = package.get('category', 'other')
                name = package.get('name', '')
                display_name = package.get('display_name', name)
                risk_level = package.get('risk_level', 'safe')
                
                # Create card frame
                card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color=self.theme.bg_tertiary,
                    border_width=1,
                    border_color=self.theme.border_color,
                    corner_radius=self.theme.border_radius
                )
                card.pack(fill="x", pady=8, padx=10)
                
                # Left side - info
                left_frame = ctk.CTkFrame(card, fg_color="transparent")
                left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)
                
                name_label = ctk.CTkLabel(
                    left_frame,
                    text=display_name,
                    font=(self.theme.get_font(13)[0], 13, "bold"),
                    text_color=self.theme.text_primary
                )
                name_label.pack(anchor="w")
                
                # Risk badge
                risk_colors = {
                    'safe': '#00D26A',
                    'moderate': '#FFB347',
                    'advanced': '#FF6B6B'
                }
                risk_color = risk_colors.get(risk_level, '#FFB347')
                
                risk_label = ctk.CTkLabel(
                    left_frame,
                    text=f"Risk: {risk_level.capitalize()}",
                    font=(self.theme.get_font(11)[0], 11),
                    text_color=risk_color
                )
                risk_label.pack(anchor="w", pady=(4, 0))
                
                # Right side - toggle
                right_frame = ctk.CTkFrame(card, fg_color="transparent")
                right_frame.pack(side="right", padx=15, pady=12)
                
                var = ctk.BooleanVar(value=False)
                toggle = ctk.CTkSwitch(
                    right_frame,
                    text="",
                    variable=var,
                    onvalue=True,
                    offvalue=False,
                    button_color=self.theme.accent,
                    command=lambda pkg=name, v=var: self._toggle_package(pkg, v.get())
                )
                toggle.pack()
            
            # Action button
            button_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            button_frame.pack(fill="x", pady=(20, 0), padx=10)
            
            remove_btn = ctk.CTkButton(
                button_frame,
                text=f"Remove Selected ({len(self.selected_packages)} selected)",
                fg_color=self.theme.accent,
                hover_color=self.theme.accent_hover,
                command=self._remove_selected,
                height=40
            )
            remove_btn.pack(side="left", fill="x", expand=True)
            
            self.remove_btn = remove_btn
            
        except Exception as e:
            self.logger.error(f"Error creating bloatware page: {e}")
            error_label = ctk.CTkLabel(
                self.scroll_frame,
                text=f"Error loading bloatware list: {str(e)}",
                text_color=self.theme.warning
            )
            error_label.pack(pady=20)
    
    def _toggle_package(self, package_name: str, enabled: bool):
        """Toggle package selection."""
        if enabled and package_name not in self.selected_packages:
            self.selected_packages.append(package_name)
        elif not enabled and package_name in self.selected_packages:
            self.selected_packages.remove(package_name)
        
        # Update button text
        self.remove_btn.configure(
            text=f"Remove Selected ({len(self.selected_packages)} selected)"
        )
    
    def _remove_selected(self):
        """Remove selected bloatware packages."""
        if not self.selected_packages:
            return
        from ..components.progress_modal import ProgressModal
        import threading

        total = len(self.selected_packages)

        modal = ProgressModal(self.master, title="Removing Bloatware")

        def progress_cb(message: str):
            # message like 'Removing pkg (i/n)'
            # attempt to parse progress
            try:
                # crude parse for (i/n)
                if "(" in message and "/" in message:
                    part = message.split("(")[-1].split(")")[0]
                    cur, tot = part.split("/")
                    cur = int(cur)
                    tot = int(tot)
                    modal.update_progress(cur, tot, message)
                else:
                    # fallback: increment progress by small step
                    modal.log_message(message)
            except Exception:
                modal.log_message(message)

        def run_removal():
            modal.log_message(f"Starting removal of {total} packages...")
            results = self.bloatware_manager.remove_packages_batch(self.selected_packages, progress_callback=progress_cb)
            # Log results
            for s in results.get("successful", []):
                modal.log_message(f"Removed: {s}")
            for f in results.get("failed", []):
                modal.log_message(f"Failed: {f}")

            success = len(results.get("failed", [])) == 0
            modal.set_completed(success=success)
            # Refresh page content after completion
            try:
                self.scroll_frame.destroy()
                self.scroll_frame = ctk.CTkScrollableFrame(
                    self,
                    fg_color=self.theme.bg_primary,
                    scrollbar_button_color=self.theme.accent
                )
                self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
                self.selected_packages = []
                self._create_content()
            except Exception:
                pass

        thread = threading.Thread(target=run_removal, daemon=True)
        thread.start()


class PrivacyPage(BasePage):
    """Privacy & telemetry hardening page."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Privacy & Telemetry", **kwargs)
        from ...core.telemetry import TelemetryManager
        from ...core.privacy import PrivacyManager
        from ...utils import get_logger
        
        self.logger = get_logger(__name__)
        self.telemetry_manager = TelemetryManager()
        self.privacy_manager = PrivacyManager()
        
        self._create_content()
    
    def _create_content(self):
        """Create privacy settings interface."""
        settings = [
            ("Windows Telemetry", "Disable data collection for analysis", "safe"),
            ("Cortana Integration", "Disable Cortana AI assistant", "safe"),
            ("Windows Copilot", "Disable Copilot AI suggestions", "safe"),
            ("Windows Recall", "Disable screenshot capture AI", "moderate"),
            ("Activity History", "Disable activity timeline tracking", "safe"),
            ("Start Menu Ads", "Remove ads from Start Menu", "safe"),
            ("Lock Screen Ads", "Remove ads from lock screen", "safe"),
            ("Web Activity Tracking", "Disable web history tracking", "safe"),
            ("Advertising ID", "Disable advertising personalization", "safe"),
        ]
        
        for title, desc, risk_level in settings:
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=self.theme.bg_tertiary,
                border_width=1,
                border_color=self.theme.border_color,
                corner_radius=self.theme.border_radius
            )
            card.pack(fill="x", pady=8, padx=10)
            
            left_frame = ctk.CTkFrame(card, fg_color="transparent")
            left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)
            
            title_label = ctk.CTkLabel(
                left_frame,
                text=title,
                font=(self.theme.get_font(13)[0], 13, "bold"),
                text_color=self.theme.text_primary
            )
            title_label.pack(anchor="w")
            
            desc_label = ctk.CTkLabel(
                left_frame,
                text=desc,
                font=(self.theme.get_font(11)[0], 11),
                text_color=self.theme.text_secondary
            )
            desc_label.pack(anchor="w", pady=(4, 0))
            
            right_frame = ctk.CTkFrame(card, fg_color="transparent")
            right_frame.pack(side="right", padx=15, pady=12)
            
            toggle = ctk.CTkSwitch(
                right_frame,
                text="",
                onvalue=True,
                offvalue=False,
                button_color=self.theme.accent
            )
            toggle.pack()


class ServicesPage(BasePage):
    """Windows services management page."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Services Management", **kwargs)
        from ...core.services import ServicesManager
        
        self.services_manager = ServicesManager()
        self._create_content()
    
    def _create_content(self):
        """Create services management interface."""
        info_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Manage Windows background services. Disabling services can improve performance but may break features.",
            font=(self.theme.get_font(12)[0], 12),
            text_color=self.theme.text_secondary
        )
        info_label.pack(pady=(0, 20), padx=10)
        
        # Service categories
        categories = {
            'Telemetry': ['DiagTrack', 'dmwappushservice'],
            'Location & Search': ['MapsBroker', 'WSearch'],
            'Gaming & Media': ['XboxGipSvc', 'XboxNetApiSvc', 'WMPNetworkSvc'],
            'Accessibility': ['WbioSrvc', 'TabletInputService'],
            'Diagnostics': ['WerSvc', 'wisvc'],
        }
        
        for category, services in categories.items():
            cat_label = ctk.CTkLabel(
                self.scroll_frame,
                text=category,
                font=(self.theme.get_font(14)[0], 14, "bold"),
                text_color=self.theme.accent
            )
            cat_label.pack(anchor="w", pady=(15, 10), padx=10)
            
            for service in services:
                card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color=self.theme.bg_tertiary,
                    border_width=1,
                    border_color=self.theme.border_color,
                    corner_radius=self.theme.border_radius
                )
                card.pack(fill="x", pady=4, padx=10)
                
                left_frame = ctk.CTkFrame(card, fg_color="transparent")
                left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)
                
                service_label = ctk.CTkLabel(
                    left_frame,
                    text=service,
                    font=(self.theme.get_font(12)[0], 12, "bold"),
                    text_color=self.theme.text_primary
                )
                service_label.pack(anchor="w")
                
                right_frame = ctk.CTkFrame(card, fg_color="transparent")
                right_frame.pack(side="right", padx=15, pady=12)
                
                toggle = ctk.CTkSwitch(
                    right_frame,
                    text="",
                    onvalue=True,
                    offvalue=False,
                    button_color=self.theme.accent
                )
                toggle.pack()


class GamingPage(BasePage):
    """Gaming optimization page."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Gaming Optimization", **kwargs)
        from ...core.gaming import GamingManager
        
        self.gaming_manager = GamingManager()
        self._create_content()
    
    def _create_content(self):
        """Create gaming optimization interface."""
        info_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Optimize Windows for gaming performance. Enable Game Mode and network tuning for better FPS.",
            font=(self.theme.get_font(12)[0], 12),
            text_color=self.theme.text_secondary
        )
        info_label.pack(pady=(0, 20), padx=10)
        
        optimizations = [
            ("Game Mode", "Enable Game Mode for better gaming performance", "safe"),
            ("Disable Game Bar", "Turn off Game Bar overlay for minimal overhead", "safe"),
            ("High Performance Power", "Force High Performance power plan", "moderate"),
            ("Disable Nagle", "Reduce network latency for online gaming", "moderate"),
            ("Disable Mouse Accel", "Remove mouse acceleration for precision aiming", "safe"),
            ("Disable Fullscreen Opt.", "Disable fullscreen optimizations", "moderate"),
        ]
        
        for title, desc, risk in optimizations:
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=self.theme.bg_tertiary,
                border_width=1,
                border_color=self.theme.border_color,
                corner_radius=self.theme.border_radius
            )
            card.pack(fill="x", pady=8, padx=10)
            
            left_frame = ctk.CTkFrame(card, fg_color="transparent")
            left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)
            
            title_label = ctk.CTkLabel(
                left_frame,
                text=title,
                font=(self.theme.get_font(12)[0], 12, "bold"),
                text_color=self.theme.text_primary
            )
            title_label.pack(anchor="w")
            
            desc_label = ctk.CTkLabel(
                left_frame,
                text=desc,
                font=(self.theme.get_font(11)[0], 11),
                text_color=self.theme.text_secondary
            )
            desc_label.pack(anchor="w", pady=(4, 0))
            
            right_frame = ctk.CTkFrame(card, fg_color="transparent")
            right_frame.pack(side="right", padx=15, pady=12)
            
            toggle = ctk.CTkSwitch(
                right_frame,
                text="",
                onvalue=True,
                offvalue=False,
                button_color=self.theme.accent
            )
            toggle.pack()


class NetworkPage(BasePage):
    """Network configuration page."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Network Settings", **kwargs)
        from ...core.network import NetworkManager
        
        self.network_manager = NetworkManager()
        self._create_content()
    
    def _create_content(self):
        """Create network settings interface."""
        info_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Configure DNS, block telemetry domains, and optimize network performance.",
            font=(self.theme.get_font(12)[0], 12),
            text_color=self.theme.text_secondary
        )
        info_label.pack(pady=(0, 20), padx=10)
        
        # DNS Presets
        dns_label = ctk.CTkLabel(
            self.scroll_frame,
            text="DNS Presets",
            font=(self.theme.get_font(14)[0], 14, "bold"),
            text_color=self.theme.accent
        )
        dns_label.pack(anchor="w", pady=(0, 10), padx=10)
        
        dns_options = ["Default", "Cloudflare (Fast)", "Google (Reliable)", "AdGuard (Blocking)", "Quad9 (Security)"]
        
        dns_var = ctk.StringVar(value="Default")
        
        for option in dns_options:
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=option,
                fg_color=self.theme.bg_tertiary,
                hover_color=self.theme.accent_hover,
                text_color=self.theme.text_primary,
                height=35
            )
            btn.pack(fill="x", pady=4, padx=10)
        
        # Telemetry Blocking
        block_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Block Telemetry Domains",
            font=(self.theme.get_font(14)[0], 14, "bold"),
            text_color=self.theme.accent
        )
        block_label.pack(anchor="w", pady=(20, 10), padx=10)
        
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.theme.bg_tertiary,
            border_width=1,
            border_color=self.theme.border_color,
            corner_radius=self.theme.border_radius
        )
        card.pack(fill="x", pady=8, padx=10)
        
        left_frame = ctk.CTkFrame(card, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)
        
        block_title = ctk.CTkLabel(
            left_frame,
            text="Add telemetry domains to hosts file",
            font=(self.theme.get_font(12)[0], 12, "bold"),
            text_color=self.theme.text_primary
        )
        block_title.pack(anchor="w")
        
        block_desc = ctk.CTkLabel(
            left_frame,
            text="Blocks 20+ known telemetry endpoints via hosts file",
            font=(self.theme.get_font(11)[0], 11),
            text_color=self.theme.text_secondary
        )
        block_desc.pack(anchor="w", pady=(4, 0))
        
        right_frame = ctk.CTkFrame(card, fg_color="transparent")
        right_frame.pack(side="right", padx=15, pady=12)
        
        toggle = ctk.CTkSwitch(
            right_frame,
            text="",
            onvalue=True,
            offvalue=False,
            button_color=self.theme.accent
        )
        toggle.pack()


class CleanupPage(BasePage):
    """Disk cleanup and optimization page."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Disk Cleanup", **kwargs)
        from ...core.cleanup import CleanupManager
        
        self.cleanup_manager = CleanupManager()
        self._create_content()
    
    def _create_content(self):
        """Create disk cleanup interface."""
        info_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Safely remove temporary files and caches. Click 'Analyze' to see current disk usage.",
            font=(self.theme.get_font(12)[0], 12),
            text_color=self.theme.text_secondary
        )
        info_label.pack(pady=(0, 20), padx=10)
        
        cleanup_items = [
            ("Temporary Files", "%TEMP%", "500 MB"),
            ("Windows Temp", "C:\\Windows\\Temp", "200 MB"),
            ("Prefetch Cache", "C:\\Windows\\Prefetch", "150 MB"),
            ("Update Cache", "C:\\Windows\\SoftwareDistribution\\Download", "2.5 GB"),
            ("Recycle Bin", "Recycle Bin", "1.2 GB"),
            ("Thumbnail Cache", "%APPDATA%\\Microsoft\\Windows\\Explorer", "300 MB"),
        ]
        
        for name, path, size in cleanup_items:
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=self.theme.bg_tertiary,
                border_width=1,
                border_color=self.theme.border_color,
                corner_radius=self.theme.border_radius
            )
            card.pack(fill="x", pady=8, padx=10)
            
            left_frame = ctk.CTkFrame(card, fg_color="transparent")
            left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)
            
            name_label = ctk.CTkLabel(
                left_frame,
                text=name,
                font=(self.theme.get_font(12)[0], 12, "bold"),
                text_color=self.theme.text_primary
            )
            name_label.pack(anchor="w")
            
            path_label = ctk.CTkLabel(
                left_frame,
                text=f"{path} • {size}",
                font=(self.theme.get_font(11)[0], 11),
                text_color=self.theme.text_secondary
            )
            path_label.pack(anchor="w", pady=(4, 0))
            
            right_frame = ctk.CTkFrame(card, fg_color="transparent")
            right_frame.pack(side="right", padx=15, pady=12)
            
            toggle = ctk.CTkSwitch(
                right_frame,
                text="",
                onvalue=True,
                offvalue=False,
                button_color=self.theme.accent
            )
            toggle.pack()
        
        # Analyze and Cleanup buttons
        button_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0), padx=10)
        
        analyze_btn = ctk.CTkButton(
            button_frame,
            text="Re-Analyze",
            fg_color=self.theme.bg_tertiary,
            hover_color=self.theme.accent_hover,
            text_color=self.theme.accent,
            height=40
        )
        analyze_btn.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        cleanup_btn = ctk.CTkButton(
            button_frame,
            text="Clean Up Selected",
            fg_color=self.theme.accent,
            hover_color=self.theme.accent_hover,
            height=40
        )
        cleanup_btn.pack(side="left", fill="both", expand=True)


class BackupPage(BasePage):
    """Backup & restore management page."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Backup & Restore", **kwargs)
        from ...backup import BackupManager
        
        self.backup_manager = BackupManager()
        self._create_content()
    
    def _create_content(self):
        """Create backup management interface."""
        # Create Backup Button
        create_btn = ctk.CTkButton(
            self.scroll_frame,
            text="Create New Backup",
            fg_color=self.theme.accent,
            hover_color=self.theme.accent_hover,
            height=40
        )
        create_btn.pack(fill="x", pady=(0, 20), padx=10)
        
        # Backups List
        backups_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Available Backups",
            font=(self.theme.get_font(14)[0], 14, "bold"),
            text_color=self.theme.accent
        )
        backups_label.pack(anchor="w", pady=(0, 10), padx=10)
        
        backups = [
            ("2024-01-15 10:30:00", "2.5 MB"),
            ("2024-01-14 14:45:00", "2.4 MB"),
            ("2024-01-13 09:15:00", "2.3 MB"),
        ]
        
        for timestamp, size in backups:
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=self.theme.bg_tertiary,
                border_width=1,
                border_color=self.theme.border_color,
                corner_radius=self.theme.border_radius
            )
            card.pack(fill="x", pady=8, padx=10)
            
            left_frame = ctk.CTkFrame(card, fg_color="transparent")
            left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)
            
            time_label = ctk.CTkLabel(
                left_frame,
                text=timestamp,
                font=(self.theme.get_font(12)[0], 12, "bold"),
                text_color=self.theme.text_primary
            )
            time_label.pack(anchor="w")
            
            size_label = ctk.CTkLabel(
                left_frame,
                text=f"Size: {size}",
                font=(self.theme.get_font(11)[0], 11),
                text_color=self.theme.text_secondary
            )
            size_label.pack(anchor="w", pady=(4, 0))
            
            right_frame = ctk.CTkFrame(card, fg_color="transparent")
            right_frame.pack(side="right", padx=15, pady=12)
            
            restore_btn = ctk.CTkButton(
                right_frame,
                text="Restore",
                width=80,
                height=32,
                fg_color=self.theme.accent,
                hover_color=self.theme.accent_hover
            )
            restore_btn.pack(side="left", padx=5)
            
            delete_btn = ctk.CTkButton(
                right_frame,
                text="Delete",
                width=80,
                height=32,
                fg_color=self.theme.warning,
                hover_color=self.theme.accent_hover
            )
            delete_btn.pack(side="left", padx=5)


class SettingsPage(BasePage):
    """Application settings and preferences page."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Settings", **kwargs)
        self._create_content()
    
    def _create_content(self):
        """Create settings interface."""
        # Language
        lang_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Language & Appearance",
            font=(self.theme.get_font(14)[0], 14, "bold"),
            text_color=self.theme.accent
        )
        lang_label.pack(anchor="w", pady=(0, 10), padx=10)
        
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.theme.bg_tertiary,
            border_width=1,
            border_color=self.theme.border_color,
            corner_radius=self.theme.border_radius
        )
        card.pack(fill="x", pady=8, padx=10)
        
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=15, pady=12)
        
        lang_title = ctk.CTkLabel(
            left,
            text="Language",
            font=(self.theme.get_font(12)[0], 12, "bold"),
            text_color=self.theme.text_primary
        )
        lang_title.pack(anchor="w")
        
        lang_desc = ctk.CTkLabel(
            left,
            text="English, Deutsch, Français, Español, Polski",
            font=(self.theme.get_font(11)[0], 11),
            text_color=self.theme.text_secondary
        )
        lang_desc.pack(anchor="w", pady=(4, 0))
        
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=15, pady=12)
        
        lang_dropdown = ctk.CTkComboBox(
            right,
            values=["English", "Deutsch", "Français", "Español", "Polski"],
            width=120,
            height=32,
            fg_color=self.theme.bg_primary,
            text_color=self.theme.text_primary,
            button_color=self.theme.accent
        )
        lang_dropdown.pack()
        lang_dropdown.set("English")
        
        # Theme
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.theme.bg_tertiary,
            border_width=1,
            border_color=self.theme.border_color,
            corner_radius=self.theme.border_radius
        )
        card.pack(fill="x", pady=8, padx=10)
        
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=15, pady=12)
        
        theme_title = ctk.CTkLabel(
            left,
            text="Theme",
            font=(self.theme.get_font(12)[0], 12, "bold"),
            text_color=self.theme.text_primary
        )
        theme_title.pack(anchor="w")
        
        theme_desc = ctk.CTkLabel(
            left,
            text="Select between dark and light mode",
            font=(self.theme.get_font(11)[0], 11),
            text_color=self.theme.text_secondary
        )
        theme_desc.pack(anchor="w", pady=(4, 0))
        
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=15, pady=12)
        
        theme_toggle = ctk.CTkSwitch(
            right,
            text="Dark Mode",
            onvalue=True,
            offvalue=False,
            button_color=self.theme.accent
        )
        theme_toggle.pack()
        theme_toggle.select()
        
        # Auto-Backup
        backup_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Backup Options",
            font=(self.theme.get_font(14)[0], 14, "bold"),
            text_color=self.theme.accent
        )
        backup_label.pack(anchor="w", pady=(20, 10), padx=10)
        
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.theme.bg_tertiary,
            border_width=1,
            border_color=self.theme.border_color,
            corner_radius=self.theme.border_radius
        )
        card.pack(fill="x", pady=8, padx=10)
        
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=15, pady=12)
        
        auto_title = ctk.CTkLabel(
            left,
            text="Auto-Backup Before Changes",
            font=(self.theme.get_font(12)[0], 12, "bold"),
            text_color=self.theme.text_primary
        )
        auto_title.pack(anchor="w")
        
        auto_desc = ctk.CTkLabel(
            left,
            text="Automatically create backup before applying changes",
            font=(self.theme.get_font(11)[0], 11),
            text_color=self.theme.text_secondary
        )
        auto_desc.pack(anchor="w", pady=(4, 0))
        
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=15, pady=12)
        
        auto_toggle = ctk.CTkSwitch(
            right,
            text="",
            onvalue=True,
            offvalue=False,
            button_color=self.theme.accent
        )
        auto_toggle.pack()
        auto_toggle.select()
        
        # About
        about_label = ctk.CTkLabel(
            self.scroll_frame,
            text="About",
            font=(self.theme.get_font(14)[0], 14, "bold"),
            text_color=self.theme.accent
        )
        about_label.pack(anchor="w", pady=(20, 10), padx=10)
        
        about_text = ctk.CTkLabel(
            self.scroll_frame,
            text="WinPurge v1.0.0\nProfessional Windows Debloater & Privacy Tool\n\n© 2024 WinPurge Team\nLicensed under MIT",
            font=(self.theme.get_font(11)[0], 11),
            text_color=self.theme.text_secondary,
            justify="left"
        )
        about_text.pack(anchor="w", pady=(0, 10), padx=10)
        
        export_btn = ctk.CTkButton(
            self.scroll_frame,
            text="Export Log File",
            fg_color=self.theme.bg_tertiary,
            hover_color=self.theme.accent_hover,
            text_color=self.theme.accent,
            height=35
        )
        export_btn.pack(fill="x", padx=10)
