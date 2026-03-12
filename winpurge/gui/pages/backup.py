"""
WinPurge Backup Page
Backup and restore management.
"""

import customtkinter as ctk
import threading
from typing import Dict, List
from pathlib import Path

from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.backup import backup_manager


class BackupItem(ctk.CTkFrame):
    """Single backup item with restore/delete actions."""
    
    def __init__(
        self,
        master: any,
        backup: Dict,
        on_restore: callable,
        on_delete: callable,
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )
        
        self.backup = backup
        self.on_restore = on_restore
        self.on_delete = on_delete
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create item widgets."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=12)
        
        # Info
        info_frame = ctk.CTkFrame(container, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Date
        ctk.CTkLabel(
            info_frame,
            text=f"📅 {self.backup.get('date', 'Unknown')}",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        # Description
        desc = self.backup.get("description", "")
        if desc:
            ctk.CTkLabel(
                info_frame,
                text=desc,
                font=self.theme.get_font("small"),
                text_color=self.theme.colors["text_secondary"],
            ).pack(anchor="w")
        
        # Details row
        details_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        details_frame.pack(anchor="w", pady=(4, 0))
        
        ctk.CTkLabel(
            details_frame,
            text=f"Size: {self.backup.get('size', 'Unknown')}",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_disabled"],
        ).pack(side="left")
        
        contents = self.backup.get("contents", [])
        if contents:
            ctk.CTkLabel(
                details_frame,
                text=f" • {len(contents)} items",
                font=self.theme.get_font("small"),
                text_color=self.theme.colors["text_disabled"],
            ).pack(side="left")
        
        # Actions
        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(side="right")
        
        restore_btn = ctk.CTkButton(
            actions_frame,
            text=t("backup.restore"),
            width=80,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=lambda: self.on_restore(self.backup),
        )
        restore_btn.pack(side="left", padx=(0, 8))
        
        delete_btn = ctk.CTkButton(
            actions_frame,
            text=t("backup.delete"),
            width=80,
            fg_color=self.theme.colors["danger"],
            hover_color="#FF8080",
            command=lambda: self.on_delete(self.backup),
        )
        delete_btn.pack(side="left")


class BackupPage(ctk.CTkFrame):
    """Backup and restore page."""
    
    def __init__(self, master: any, **kwargs) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs,
        )
        
        self.backup_items: List[BackupItem] = []
        
        self._create_widgets()
        self.refresh_list()
    
    def _create_widgets(self) -> None:
        """Create page widgets."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 16))
        
        title = ctk.CTkLabel(
            header,
            text=t("backup.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text=t("backup.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # Create backup button
        create_btn = ctk.CTkButton(
            header,
            text="💾 " + t("backup.create_backup"),
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._create_backup,
        )
        create_btn.pack(anchor="w", pady=(16, 0))
        
        # Backups list header
        list_header = ctk.CTkFrame(self, fg_color="transparent")
        list_header.pack(fill="x", padx=32, pady=(16, 8))
        
        ctk.CTkLabel(
            list_header,
            text=t("backup.available_backups"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")
        
        refresh_btn = ctk.CTkButton(
            list_header,
            text="🔄 Refresh",
            width=100,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.refresh_list,
        )
        refresh_btn.pack(side="right")
        
        # Backups list
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        self.list_frame.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        
        # No backups label
        self.no_backups_label = ctk.CTkLabel(
            self.list_frame,
            text=t("backup.no_backups"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
    
    def refresh_list(self) -> None:
        """Refresh the backups list."""
        # Clear existing items
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        self.backup_items.clear()
        
        def load():
            backups = backup_manager.get_backups()
            self.after(0, lambda: self._populate_list(backups))
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def _populate_list(self, backups: List[Dict]) -> None:
        """Populate the backups list."""
        if not backups:
            self.no_backups_label.pack(pady=40)
            return
        
        for backup in backups:
            item = BackupItem(
                self.list_frame,
                backup,
                on_restore=self._restore_backup,
                on_delete=self._delete_backup,
            )
            item.pack(fill="x", pady=4)
            self.backup_items.append(item)
    
    def _create_backup(self) -> None:
        """Create a new backup."""
        modal = ProgressModal(self.winfo_toplevel(), t("backup.create_backup"))
        
        def create():
            modal.log(t("backup.creating_backup"))
            modal.set_progress(0.5)
            
            success, message, path = backup_manager.create_backup("Manual backup")
            
            if success:
                modal.complete(True, t("backup.backup_success"))
            else:
                modal.complete(False, t("backup.backup_failed", error=message))
            
            self.after(0, self.refresh_list)
        
        thread = threading.Thread(target=create, daemon=True)
        thread.start()
    
    def _restore_backup(self, backup: Dict) -> None:
        """Restore a backup."""
        from tkinter import messagebox
        
        if not messagebox.askyesno(
            t("common.confirm"),
            t("backup.confirm_restore")
        ):
            return
        
        modal = ProgressModal(self.winfo_toplevel(), t("backup.restore"))
        
        def restore():
            modal.log(t("backup.restoring"))
            modal.set_progress(0.5)
            
            success, message = backup_manager.restore_backup(backup["path"])
            
            if success:
                modal.complete(True, t("backup.restore_success"))
            else:
                modal.complete(False, t("backup.restore_failed", error=message))
        
        thread = threading.Thread(target=restore, daemon=True)
        thread.start()
    
    def _delete_backup(self, backup: Dict) -> None:
        """Delete a backup."""
        from tkinter import messagebox
        
        if not messagebox.askyesno(
            t("common.confirm"),
            t("backup.confirm_delete")
        ):
            return
        
        success, message = backup_manager.delete_backup(backup["path"])
        
        if success:
            self.refresh_list()
        else:
            messagebox.showerror(t("common.error"), message)