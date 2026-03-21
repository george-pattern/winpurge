"""
WinPurge Backup Page
Backup and restore management with progress tracking.
"""

import customtkinter as ctk
import threading
import logging
from typing import Dict, List, Optional
from datetime import datetime

from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.backup import backup_manager

logger = logging.getLogger(__name__)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _format_file_size(size_bytes: int) -> str:
    """Human-readable file size."""
    if size_bytes < 0:
        return "Unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _format_relative_time(date_str: str) -> str:
    """Try to produce a relative time string like '2 hours ago'."""
    try:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M"):
            try:
                dt = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        else:
            return date_str

        delta = datetime.now() - dt
        seconds = int(delta.total_seconds())

        if seconds < 60:
            return t("backup.just_now")
        if seconds < 3600:
            mins = seconds // 60
            return t("backup.minutes_ago", count=mins)
        if seconds < 86400:
            hours = seconds // 3600
            return t("backup.hours_ago", count=hours)
        days = seconds // 86400
        return t("backup.days_ago", count=days)
    except Exception:
        return date_str


# ─── Backup Item Widget ─────────────────────────────────────────────────────

class BackupItem(ctk.CTkFrame):
    """Single backup entry with info and restore/delete actions."""

    def __init__(
        self,
        master,
        backup: Dict,
        on_restore: callable,
        on_delete: callable,
        **kwargs,
    ) -> None:
        self.theme = get_theme()

        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )

        self.backup = backup
        self.on_restore = on_restore
        self.on_delete = on_delete

        self._build_ui()
        self._bind_hover()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # ── Left: info ──
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.grid(row=0, column=0, sticky="nsew", padx=16, pady=14)

        # Title row: date + relative time
        title_row = ctk.CTkFrame(info, fg_color="transparent")
        title_row.pack(fill="x")

        date_str = self.backup.get("date", "Unknown")
        ctk.CTkLabel(
            title_row,
            text=f"📅  {date_str}",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")

        relative = _format_relative_time(date_str)
        if relative != date_str:
            ctk.CTkLabel(
                title_row,
                text=f"({relative})",
                font=self.theme.get_font("small"),
                text_color=self.theme.colors["text_disabled"],
            ).pack(side="left", padx=(8, 0))

        # Description
        desc = self.backup.get("description", "")
        if desc:
            ctk.CTkLabel(
                info,
                text=desc,
                font=self.theme.get_font("body"),
                text_color=self.theme.colors["text_secondary"],
                anchor="w",
            ).pack(anchor="w", pady=(4, 0))

        # Metadata row
        meta_frame = ctk.CTkFrame(info, fg_color="transparent")
        meta_frame.pack(anchor="w", pady=(6, 0))

        # Size
        size = self.backup.get("size", "Unknown")
        if isinstance(size, int):
            size = _format_file_size(size)

        ctk.CTkLabel(
            meta_frame,
            text=f"💾 {size}",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_disabled"],
        ).pack(side="left")

        # Item count
        contents = self.backup.get("contents", [])
        if contents:
            ctk.CTkLabel(
                meta_frame,
                text=f"  •  📋 {len(contents)} {t('backup.items')}",
                font=self.theme.get_font("small"),
                text_color=self.theme.colors["text_disabled"],
            ).pack(side="left")

        # Backup path (truncated)
        path = self.backup.get("path", "")
        if path:
            display_path = path if len(path) < 50 else f"...{path[-47:]}"
            ctk.CTkLabel(
                info,
                text=display_path,
                font=("Consolas", 9),
                text_color=self.theme.colors["text_disabled"],
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

        # ── Right: action buttons ──
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=1, padx=(0, 16), pady=14, sticky="e")

        ctk.CTkButton(
            actions,
            text=f"🔄  {t('backup.restore')}",
            width=100,
            height=32,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=lambda: self.on_restore(self.backup),
        ).pack(pady=(0, 6))

        ctk.CTkButton(
            actions,
            text=f"🗑  {t('backup.delete')}",
            width=100,
            height=32,
            fg_color="transparent",
            hover_color=self.theme.colors.get("bg_danger", "#3A0000"),
            text_color=self.theme.colors["danger"],
            border_width=1,
            border_color=self.theme.colors["danger"],
            command=lambda: self.on_delete(self.backup),
        ).pack()

    def _bind_hover(self) -> None:
        normal = self.theme.colors["bg_card"]
        hover = self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"])

        def on_enter(_):
            self.configure(fg_color=hover)

        def on_leave(_):
            self.configure(fg_color=normal)

        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)


# ─── Empty State Widget ─────────────────────────────────────────────────────

class EmptyBackupState(ctk.CTkFrame):
    """Shown when no backups exist."""

    def __init__(self, master, on_create: callable, **kwargs) -> None:
        theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        container = ctk.CTkFrame(
            self,
            fg_color=theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=theme.colors["card_border"],
        )
        container.pack(expand=True, pady=40, padx=60)

        inner = ctk.CTkFrame(container, fg_color="transparent")
        inner.pack(padx=40, pady=32)

        ctk.CTkLabel(
            inner,
            text="📂",
            font=("Inter", 48),
        ).pack()

        ctk.CTkLabel(
            inner,
            text=t("backup.no_backups"),
            font=theme.get_font("header", "bold"),
            text_color=theme.colors["text_primary"],
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            inner,
            text=t("backup.no_backups_hint"),
            font=theme.get_font("body"),
            text_color=theme.colors["text_secondary"],
            wraplength=300,
        ).pack()

        ctk.CTkButton(
            inner,
            text=f"💾  {t('backup.create_first_backup')}",
            height=40,
            fg_color=theme.colors["accent"],
            hover_color=theme.colors["accent_hover"],
            command=on_create,
        ).pack(pady=(16, 0))


# ─── Main Backup Page ────────────────────────────────────────────────────────

class BackupPage(ctk.CTkFrame):
    """Backup management page with create, restore, delete operations."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.backup_items: List[BackupItem] = []
        self._is_loading = False

        self._build_ui()
        self.refresh_list()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 0))

        ctk.CTkLabel(
            header,
            text=t("backup.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=t("backup.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 0))

        # ── Action Bar ──
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=32, pady=(16, 0))

        self.create_btn = ctk.CTkButton(
            action_bar,
            text=f"💾  {t('backup.create_backup')}",
            height=38,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._create_backup,
        )
        self.create_btn.pack(side="left")

        self.backup_count_label = ctk.CTkLabel(
            action_bar,
            text="",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.backup_count_label.pack(side="left", padx=(16, 0))

        self.refresh_btn = ctk.CTkButton(
            action_bar,
            text="🔄  Refresh",
            width=100,
            height=32,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.refresh_list,
        )
        self.refresh_btn.pack(side="right")

        # ── Separator ──
        ctk.CTkFrame(
            self,
            fg_color=self.theme.colors["card_border"],
            height=1,
        ).pack(fill="x", padx=32, pady=(16, 0))

        # ── List Area ──
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        self.list_frame.pack(fill="both", expand=True, padx=32, pady=(8, 24))

        # State label (loading / error)
        self.state_label = ctk.CTkLabel(
            self.list_frame,
            text="",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )

    # ── Data Loading ─────────────────────────────────────────────────────

    def refresh_list(self) -> None:
        """Reload backups from disk."""
        if self._is_loading:
            return

        self._is_loading = True
        self.refresh_btn.configure(state="disabled")
        self._show_state(f"⏳  {t('common.loading')}")
        self._clear_items()

        def _load():
            try:
                backups = backup_manager.get_backups()
                self.after(0, lambda: self._on_loaded(backups))
            except Exception as e:
                logger.exception("Failed to load backups")
                self.after(0, lambda: self._on_load_error(str(e)))

        threading.Thread(target=_load, daemon=True).start()

    def _on_loaded(self, backups: List[Dict]) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self._hide_state()
        self._populate_list(backups)

    def _on_load_error(self, error: str) -> None:
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self._show_state(f"❌  {t('common.error')}: {error}")
        self.backup_count_label.configure(text="")

    # ── List Management ──────────────────────────────────────────────────

    def _clear_items(self) -> None:
        for widget in self.list_frame.winfo_children():
            if widget is not self.state_label:
                widget.destroy()
        self.backup_items.clear()

    def _populate_list(self, backups: List[Dict]) -> None:
        self._clear_items()

        # Update counter
        self.backup_count_label.configure(
            text=t("backup.total_backups", count=len(backups))
        )

        if not backups:
            empty = EmptyBackupState(self.list_frame, on_create=self._create_backup)
            empty.pack(fill="both", expand=True)
            return

        # Sort newest first
        backups_sorted = sorted(backups, key=lambda b: b.get("date", ""), reverse=True)

        for backup_data in backups_sorted:
            item = BackupItem(
                self.list_frame,
                backup_data,
                on_restore=self._restore_backup,
                on_delete=self._delete_backup,
            )
            item.pack(fill="x", pady=4)
            self.backup_items.append(item)

    # ── Create Backup ────────────────────────────────────────────────────

    def _create_backup(self) -> None:
        """Create a new manual backup with progress modal."""
        self.create_btn.configure(state="disabled")
        modal = ProgressModal(self.winfo_toplevel(), t("backup.create_backup"))

        def _worker():
            try:
                modal.log(f"📦  {t('backup.creating_backup')}")
                modal.set_progress(0.3)

                success, message, path = backup_manager.create_backup("Manual backup")

                modal.set_progress(1.0)

                if success:
                    modal.log(f"✓  {t('backup.saved_to')}: {path}", "success")
                    modal.complete(True, t("backup.backup_success"))
                else:
                    modal.complete(False, t("backup.backup_failed", error=message))

            except Exception as e:
                logger.exception("Backup creation failed")
                modal.complete(False, t("backup.backup_failed", error=str(e)))
            finally:
                self.after(0, lambda: self.create_btn.configure(state="normal"))
                self.after(300, self.refresh_list)

        threading.Thread(target=_worker, daemon=True).start()

    # ── Restore Backup ───────────────────────────────────────────────────

    def _restore_backup(self, backup: Dict) -> None:
        """Restore from a selected backup."""
        dialog = ConfirmDialog(
            self.winfo_toplevel(),
            title=t("backup.confirm_restore_title"),
            message=t("backup.confirm_restore"),
            detail=f"📅  {backup.get('date', '?')}\n{backup.get('description', '')}",
            confirm_text=t("backup.restore"),
            confirm_color=self.theme.colors["accent"],
            icon="🔄",
        )

        if not dialog.result:
            return

        modal = ProgressModal(self.winfo_toplevel(), t("backup.restore"))

        def _worker():
            try:
                modal.log(f"🔄  {t('backup.restoring')}")
                modal.set_progress(0.5)

                success, message = backup_manager.restore_backup(backup["path"])

                if success:
                    modal.complete(True, t("backup.restore_success"))
                else:
                    modal.complete(False, t("backup.restore_failed", error=message))

            except Exception as e:
                logger.exception("Restore failed")
                modal.complete(False, t("backup.restore_failed", error=str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    # ── Delete Backup ────────────────────────────────────────────────────

    def _delete_backup(self, backup: Dict) -> None:
        """Delete a backup after confirmation."""
        dialog = ConfirmDialog(
            self.winfo_toplevel(),
            title=t("backup.confirm_delete_title"),
            message=t("backup.confirm_delete"),
            detail=f"📅  {backup.get('date', '?')}",
            confirm_text=t("backup.delete"),
            confirm_color=self.theme.colors["danger"],
            icon="🗑️",
            is_danger=True,
        )

        if not dialog.result:
            return

        try:
            success, message = backup_manager.delete_backup(backup["path"])

            if success:
                self.refresh_list()
            else:
                self._show_error(message)

        except Exception as e:
            logger.exception("Delete failed")
            self._show_error(str(e))

    # ── Helpers ──────────────────────────────────────────────────────────

    def _show_state(self, text: str) -> None:
        self.state_label.configure(text=text)
        self.state_label.pack(pady=40)

    def _hide_state(self) -> None:
        self.state_label.pack_forget()

    def _show_error(self, message: str) -> None:
        from tkinter import messagebox
        messagebox.showerror(t("common.error"), message)


# ─── Confirm Dialog ─────────────────────────────────────────────────────────

class ConfirmDialog(ctk.CTkToplevel):

    def __init__(
        self,
        master,
        title: str,
        message: str,
        detail: str = "",
        confirm_text: str = "OK",
        confirm_color: str = "#4A9EFF",
        icon: str = "⚠️",
        is_danger: bool = False,
    ) -> None:
        super().__init__(master)
        self.theme = get_theme()
        self.result = False

        self.title(title)
        self.geometry("440x240")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color=self.theme.colors.get("bg_main", "#1A1A2E"))

        self._build_ui(icon, message, detail, confirm_text, confirm_color, is_danger)
        self._center(master)

        self.wait_window()

    def _center(self, parent) -> None:
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _build_ui(self, icon, message, detail, confirm_text, confirm_color, is_danger) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            body,
            text=f"{icon}  {message}",
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["danger"] if is_danger else self.theme.colors["text_primary"],
            wraplength=380,
            anchor="w",
            justify="left",
        ).pack(anchor="w")

        if detail:
            ctk.CTkLabel(
                body,
                text=detail,
                font=self.theme.get_font("body"),
                text_color=self.theme.colors["text_secondary"],
                wraplength=380,
                anchor="w",
                justify="left",
            ).pack(anchor="w", pady=(8, 0))

        btn_frame = ctk.CTkFrame(body, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))

        ctk.CTkButton(
            btn_frame,
            text=t("common.cancel"),
            width=120,
            height=36,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._cancel,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            width=140,
            height=36,
            fg_color=confirm_color,
            hover_color="#FF8080" if is_danger else self.theme.colors.get("accent_hover", confirm_color),
            command=self._confirm,
        ).pack(side="right", padx=(0, 8))

    def _confirm(self) -> None:
        self.result = True
        self.destroy()

    def _cancel(self) -> None:
        self.result = False
        self.destroy()