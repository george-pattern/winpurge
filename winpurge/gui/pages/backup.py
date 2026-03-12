import threading
import customtkinter as ctk
from pathlib import Path

from tkinter import messagebox
from winpurge.gui.pages.bloatware import BasePage
from winpurge.gui.components.category_frame import CategoryFrame
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.backup import BackupManager
from winpurge.utils import get_logger


class BackupPage(BasePage):
    """Backup & restore page for managing backups created by WinPurge."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Backup & Restore", **kwargs)
        self.logger = get_logger(__name__)
        self.manager = BackupManager()
        self._create_content()

    def _create_content(self) -> None:
        actions = CategoryFrame(self.scroll_frame, category_title="Create Backup")
        actions.pack(fill="x", padx=10, pady=(0, 10))

        create_card = actions.add_toggle_card(title="Create Backup", description="Create a full backup before making changes", icon="💾")

        backups_cat = CategoryFrame(self.scroll_frame, category_title="Available Backups")
        backups_cat.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        self.backups_cat = backups_cat

        def create_backup(_=None):
            modal = ProgressModal(self.master, title="Creating Backup")

            def worker():
                try:
                    path = self.manager.create_backup()
                    modal.log_message(f"Backup created: {path}")
                    modal.set_completed(True)
                    self.refresh_list()
                except Exception as e:
                    modal.log_message(str(e))
                    modal.set_completed(False)

            threading.Thread(target=worker, daemon=True).start()

        create_card.switch.configure(command=create_backup)

        # initial populate
        self.refresh_list()

    def refresh_list(self) -> None:
        """Refresh the list of available backups."""

        try:
            items = self.manager.list_backups()
        except Exception:
            items = []

        self.backups_cat.clear_cards()
        for meta in items:
            ts = meta.get("timestamp", "unknown")
            size = meta.get("size", "-")

            # Build a custom card so we can add Restore/Delete buttons
            card = ctk.CTkFrame(self.backups_cat, fg_color=self.theme.bg_tertiary, border_width=1, border_color=self.theme.border_color, corner_radius=self.theme.border_radius)
            card.pack(fill="x", pady=8, padx=10)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=15, pady=12)

            time_label = ctk.CTkLabel(left, text=ts, font=(self.theme.get_font(12)[0], 12, "bold"), text_color=self.theme.text_primary)
            time_label.pack(anchor="w")

            size_label = ctk.CTkLabel(left, text=f"Size: {size}", font=(self.theme.get_font(11)[0], 11), text_color=self.theme.text_secondary)
            size_label.pack(anchor="w", pady=(4, 0))

            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=15, pady=12)

            def make_restore(p):
                def restore(_=None):
                    modal = ProgressModal(self.master, title="Restoring Backup")

                    def worker():
                        try:
                            self.manager.restore_backup(p)
                            modal.log_message("Restore completed")
                            modal.set_completed(True)
                            self.refresh_list()
                        except Exception as e:
                            modal.log_message(str(e))
                            modal.set_completed(False)

                    threading.Thread(target=worker, daemon=True).start()

                return restore

            def make_delete(p, parent_card):
                def delete(_=None):
                    ok = messagebox.askyesno("Delete Backup", f"Delete backup {ts}? This cannot be undone.")
                    if not ok:
                        return
                    modal = ProgressModal(self.master, title="Deleting Backup")

                    def worker():
                        try:
                            self.manager.delete_backup(Path(p))
                            modal.log_message("Backup deleted")
                            modal.set_completed(True)
                            self.refresh_list()
                        except Exception as e:
                            modal.log_message(str(e))
                            modal.set_completed(False)

                    threading.Thread(target=worker, daemon=True).start()

                return delete

            restore_btn = ctk.CTkButton(right, text="Restore", width=80, height=32, fg_color=self.theme.accent, hover_color=self.theme.accent_hover, command=make_restore(meta.get("path")))
            restore_btn.pack(side="left", padx=5)

            delete_btn = ctk.CTkButton(right, text="Delete", width=80, height=32, fg_color=self.theme.warning, hover_color=self.theme.accent_hover, command=make_delete(meta.get("path"), card))
            delete_btn.pack(side="left", padx=5)
