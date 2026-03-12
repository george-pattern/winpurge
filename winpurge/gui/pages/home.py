"""
WinPurge Home Page
Dashboard with system info and quick actions.
"""

import customtkinter as ctk
import threading
from typing import Callable, Optional

from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import get_system_info, get_windows_version, t, get_relative_time
from winpurge.backup import backup_manager
from winpurge.core.bloatware import bloatware_manager
from winpurge.core.services import services_manager
from winpurge.core.telemetry import telemetry_manager


class StatCard(ctk.CTkFrame):
    """Quick stat card component."""
    
    def __init__(
        self,
        master: any,
        title: str,
        value: str,
        color: str = "normal",
        on_click: Optional[Callable] = None,
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            corner_radius=12,
            fg_color=self.theme.colors["bg_card"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            cursor="hand2" if on_click else "arrow",
            **kwargs,
        )
        
        self.on_click = on_click
        
        if on_click:
            self.bind("<Button-1>", lambda e: on_click())
        
        self._create_widgets(title, value, color)
    
    def _create_widgets(self, title: str, value: str, color: str) -> None:
        """Create card widgets."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=12)
        
        colors = {
            "normal": self.theme.colors["text_primary"],
            "success": self.theme.colors["success"],
            "warning": self.theme.colors["warning"],
            "danger": self.theme.colors["danger"],
        }
        
        self.value_label = ctk.CTkLabel(
            container,
            text=value,
            font=self.theme.get_font("header", "bold"),
            text_color=colors.get(color, colors["normal"]),
        )
        self.value_label.pack(anchor="w")
        
        self.title_label = ctk.CTkLabel(
            container,
            text=title,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.title_label.pack(anchor="w", pady=(4, 0))
    
    def update_value(self, value: str, color: str = "normal") -> None:
        """Update card value."""
        colors = {
            "normal": self.theme.colors["text_primary"],
            "success": self.theme.colors["success"],
            "warning": self.theme.colors["warning"],
            "danger": self.theme.colors["danger"],
        }
        self.value_label.configure(
            text=value,
            text_color=colors.get(color, colors["normal"])
        )


class HomePage(ctk.CTkFrame):
    """Dashboard home page."""
    
    def __init__(
        self,
        master: any,
        on_navigate: Callable[[str], None],
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs,
        )
        
        self.on_navigate = on_navigate
        self._create_widgets()
        self.refresh_data()
    
    def _create_widgets(self) -> None:
        """Create page widgets."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 16))
        
        title = ctk.CTkLabel(
            header,
            text=t("home.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text=t("home.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # Main content area with scroll
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        content.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        
        # System Info Section
        self._create_system_info_section(content)
        
        # Quick Stats Section
        self._create_quick_stats_section(content)
        
        # Quick Actions Section
        self._create_quick_actions_section(content)
    
    def _create_system_info_section(self, parent: ctk.CTkFrame) -> None:
        """Create system information section."""
        section_label = ctk.CTkLabel(
            parent,
            text=t("home.system_info"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_label.pack(anchor="w", pady=(0, 12))
        
        info_frame = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        info_frame.pack(fill="x", pady=(0, 24))
        
        info_container = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_container.pack(fill="x", padx=20, pady=16)
        
        # Create info rows
        self.info_labels = {}
        info_items = [
            ("os", t("home.os")),
            ("cpu", t("home.cpu")),
            ("ram", t("home.ram")),
            ("disk", t("home.disk")),
            ("uptime", t("home.uptime")),
        ]
        
        for i, (key, label) in enumerate(info_items):
            row = ctk.CTkFrame(info_container, fg_color="transparent")
            row.pack(fill="x", pady=4)
            
            label_widget = ctk.CTkLabel(
                row,
                text=f"{label}:",
                font=self.theme.get_font("body"),
                text_color=self.theme.colors["text_secondary"],
                width=140,
                anchor="w",
            )
            label_widget.pack(side="left")
            
            value_widget = ctk.CTkLabel(
                row,
                text="Loading...",
                font=self.theme.get_font("body"),
                text_color=self.theme.colors["text_primary"],
                anchor="w",
            )
            value_widget.pack(side="left", fill="x", expand=True)
            
            self.info_labels[key] = value_widget
    
    def _create_quick_stats_section(self, parent: ctk.CTkFrame) -> None:
        """Create quick stats section."""
        section_label = ctk.CTkLabel(
            parent,
            text=t("home.quick_stats"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_label.pack(anchor="w", pady=(0, 12))
        
        stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 24))
        
        # Configure grid
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)
        
        # Bloatware stat
        self.bloatware_card = StatCard(
            stats_frame,
            title=t("home.bloatware_found", count="..."),
            value="...",
            on_click=lambda: self.on_navigate("bloatware"),
        )
        self.bloatware_card.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="nsew")
        
        # Services stat
        self.services_card = StatCard(
            stats_frame,
            title=t("home.tracking_services", count="..."),
            value="...",
            on_click=lambda: self.on_navigate("services"),
        )
        self.services_card.grid(row=0, column=1, padx=8, pady=4, sticky="nsew")
        
        # Telemetry stat
        self.telemetry_card = StatCard(
            stats_frame,
            title="Telemetry Status",
            value="...",
            on_click=lambda: self.on_navigate("privacy"),
        )
        self.telemetry_card.grid(row=0, column=2, padx=8, pady=4, sticky="nsew")
        
        # Backup stat
        self.backup_card = StatCard(
            stats_frame,
            title="Last Backup",
            value="...",
            on_click=lambda: self.on_navigate("backup"),
        )
        self.backup_card.grid(row=0, column=3, padx=(8, 0), pady=4, sticky="nsew")
    
    def _create_quick_actions_section(self, parent: ctk.CTkFrame) -> None:
        """Create quick actions section."""
        section_label = ctk.CTkLabel(
            parent,
            text=t("home.quick_actions"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_label.pack(anchor="w", pady=(0, 12))
        
        actions_frame = ctk.CTkFrame(parent, fg_color="transparent")
        actions_frame.pack(fill="x")
        
        # Apply Recommended button
        apply_frame = ctk.CTkFrame(
            actions_frame,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        apply_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        apply_container = ctk.CTkFrame(apply_frame, fg_color="transparent")
        apply_container.pack(fill="both", expand=True, padx=16, pady=16)
        
        ctk.CTkLabel(
            apply_container,
            text="🚀 " + t("home.apply_recommended"),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            apply_container,
            text=t("home.apply_recommended_desc"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 12))
        
        ctk.CTkButton(
            apply_container,
            text=t("home.apply_recommended"),
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._apply_recommended,
        ).pack(anchor="w")
        
        # Create Backup button
        backup_frame = ctk.CTkFrame(
            actions_frame,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        backup_frame.pack(side="left", fill="both", expand=True, padx=8)
        
        backup_container = ctk.CTkFrame(backup_frame, fg_color="transparent")
        backup_container.pack(fill="both", expand=True, padx=16, pady=16)
        
        ctk.CTkLabel(
            backup_container,
            text="💾 " + t("home.create_backup"),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            backup_container,
            text=t("home.create_backup_desc"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 12))
        
        ctk.CTkButton(
            backup_container,
            text=t("home.create_backup"),
            fg_color=self.theme.colors["success"],
            hover_color="#00E676",
            command=self._create_backup,
        ).pack(anchor="w")
        
        # Restore button
        restore_frame = ctk.CTkFrame(
            actions_frame,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        restore_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))
        
        restore_container = ctk.CTkFrame(restore_frame, fg_color="transparent")
        restore_container.pack(fill="both", expand=True, padx=16, pady=16)
        
        ctk.CTkLabel(
            restore_container,
            text="🔄 " + t("home.restore_backup"),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            restore_container,
            text=t("home.restore_backup_desc"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 12))
        
        self.restore_btn = ctk.CTkButton(
            restore_container,
            text=t("home.restore_backup"),
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._restore_backup,
        )
        self.restore_btn.pack(anchor="w")
    
    def refresh_data(self) -> None:
        """Refresh all dashboard data."""
        def load_data():
            # System info
            sys_info = get_system_info()
            win_ver = get_windows_version()
            
            self.after(0, lambda: self._update_system_info(sys_info, win_ver))
            
            # Quick stats
            bloatware_count = bloatware_manager.get_bloatware_count()
            tracking_count = services_manager.get_tracking_services_count()
            telemetry_blocked = telemetry_manager.is_telemetry_blocked()
            last_backup = backup_manager.get_last_backup_time()
            
            self.after(0, lambda: self._update_quick_stats(
                bloatware_count, tracking_count, telemetry_blocked, last_backup
            ))
        
        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()
    
    def _update_system_info(self, sys_info: dict, win_ver: dict) -> None:
        """Update system info labels."""
        self.info_labels["os"].configure(text=win_ver.get("display", "Unknown"))
        self.info_labels["cpu"].configure(text=sys_info.get("cpu", "Unknown"))
        self.info_labels["ram"].configure(
            text=f"{sys_info.get('ram_used', '?')} / {sys_info.get('ram_total', '?')} ({sys_info.get('ram_percent', 0)}%)"
        )
        self.info_labels["disk"].configure(
            text=f"{sys_info.get('disk_used', '?')} / {sys_info.get('disk_total', '?')} ({sys_info.get('disk_percent', 0)}%)"
        )
        self.info_labels["uptime"].configure(text=sys_info.get("uptime", "Unknown"))
    
    def _update_quick_stats(
        self,
        bloatware_count: int,
        tracking_count: int,
        telemetry_blocked: bool,
        last_backup,
    ) -> None:
        """Update quick stats cards."""
        # Bloatware
        self.bloatware_card.update_value(
            str(bloatware_count),
            "warning" if bloatware_count > 0 else "success"
        )
        self.bloatware_card.title_label.configure(
            text=t("home.bloatware_found", count=bloatware_count)
        )
        
        # Tracking services
        self.services_card.update_value(
            str(tracking_count),
            "danger" if tracking_count > 0 else "success"
        )
        self.services_card.title_label.configure(
            text=t("home.tracking_services", count=tracking_count)
        )
        
        # Telemetry
        if telemetry_blocked:
            self.telemetry_card.update_value(t("home.telemetry_blocked"), "success")
        else:
            self.telemetry_card.update_value(t("home.telemetry_enabled"), "danger")
        
        # Backup
        if last_backup:
            backup_text = get_relative_time(last_backup)
            self.backup_card.update_value(backup_text, "success")
        else:
            self.backup_card.update_value(t("home.no_backup"), "warning")
    
    def _apply_recommended(self) -> None:
        """Apply recommended safe tweaks."""
        modal = ProgressModal(self.winfo_toplevel(), t("home.apply_recommended"))
        
        def apply():
            from winpurge.core.privacy import privacy_manager
            from winpurge.core.telemetry import telemetry_manager
            
            steps = [
                ("Disabling telemetry...", telemetry_manager.disable_telemetry),
                ("Disabling advertising ID...", telemetry_manager.disable_advertising_id),
                ("Disabling input telemetry...", telemetry_manager.disable_input_telemetry),
                ("Disabling Cortana...", privacy_manager.disable_cortana),
                ("Disabling Copilot...", privacy_manager.disable_copilot),
                ("Disabling Start suggestions...", privacy_manager.disable_start_suggestions),
                ("Disabling lock screen ads...", privacy_manager.disable_lock_screen_ads),
            ]
            
            total = len(steps)
            success_count = 0
            
            for i, (msg, func) in enumerate(steps, 1):
                if modal.cancelled:
                    break
                
                modal.log(msg)
                modal.set_progress(i / total, f"{i}/{total}")
                
                try:
                    success, _ = func()
                    if success:
                        success_count += 1
                        modal.log(f"✓ Done", "success")
                    else:
                        modal.log(f"✗ Failed", "error")
                except Exception as e:
                    modal.log(f"✗ Error: {e}", "error")
            
            if not modal.cancelled:
                modal.complete(True, f"Applied {success_count}/{total} optimizations")
                self.after(0, self.refresh_data)
        
        thread = threading.Thread(target=apply, daemon=True)
        thread.start()
    
    def _create_backup(self) -> None:
        """Create a system backup."""
        modal = ProgressModal(self.winfo_toplevel(), t("home.create_backup"))
        
        def create():
            modal.log("Creating backup...")
            modal.set_progress(0.5)
            
            success, message, path = backup_manager.create_backup("Manual backup from dashboard")
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
            
            self.after(0, self.refresh_data)
        
        thread = threading.Thread(target=create, daemon=True)
        thread.start()
    
    def _restore_backup(self) -> None:
        """Restore the last backup."""
        backups = backup_manager.get_backups()
        
        if not backups:
            from tkinter import messagebox
            messagebox.showwarning(
                t("common.warning"),
                t("backup.no_backups")
            )
            return
        
        from tkinter import messagebox
        if not messagebox.askyesno(
            t("common.confirm"),
            t("backup.confirm_restore")
        ):
            return
        
        modal = ProgressModal(self.winfo_toplevel(), t("home.restore_backup"))
        
        def restore():
            modal.log("Restoring backup...")
            modal.set_progress(0.5)
            
            latest_backup = backups[0]
            success, message = backup_manager.restore_backup(latest_backup["path"])
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
            
            self.after(0, self.refresh_data)
        
        thread = threading.Thread(target=restore, daemon=True)
        thread.start()