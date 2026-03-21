"""
WinPurge Progress Modal Component
Modal dialog with animated progress bar, colored log output,
copy-to-clipboard, and cancellation support.
"""

import customtkinter as ctk
import threading
import queue
import logging
import time
from typing import Optional

from winpurge.gui.theme import get_theme
from winpurge.utils import t

logger = logging.getLogger(__name__)


# ─── Log Color Tags ─────────────────────────────────────────────────────────

LOG_COLORS = {
    "info": None,  # uses default text color
    "success": "log_success",
    "warning": "log_warning",
    "error": "log_error",
}


# ─── Main Progress Modal ────────────────────────────────────────────────────

class ProgressModal(ctk.CTkToplevel):
    """
    Modal dialog showing operation progress with:
    - Animated progress bar
    - Colored log output
    - Cancel / close controls
    - Thread-safe API
    - Copy log to clipboard
    """

    def __init__(self, master, title: str, **kwargs) -> None:
        super().__init__(master, **kwargs)

        self.theme = get_theme()
        self.title(title)
        self._operation_title = title

        # Window config
        self.geometry("560x440")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.configure(fg_color=self.theme.colors.get("bg_main", "#1A1A2E"))

        # State
        self._log_queue: queue.Queue = queue.Queue()
        self._cancelled = False
        self._completed = False
        self._start_time = time.time()
        self._log_lines: list = []

        self._build_ui()
        self._center_on_parent(master)
        self._process_queue()

        # Prevent closing during operation
        self.protocol("WM_DELETE_WINDOW", self._handle_cancel)

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 0))

        self.title_label = ctk.CTkLabel(
            header,
            text=f"⏳  {t('common.please_wait')}",
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            header,
            text=self._operation_title,
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # ── Progress Bar ──
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=24, pady=(12, 0))

        self.progress = ctk.CTkProgressBar(
            progress_frame,
            height=8,
            progress_color=self.theme.colors["accent"],
            fg_color=self.theme.colors["card_border"],
            corner_radius=4,
        )
        self.progress.pack(fill="x")
        self.progress.set(0)

        # Progress text row
        info_row = ctk.CTkFrame(self, fg_color="transparent")
        info_row.pack(fill="x", padx=24, pady=(6, 0))

        self.progress_label = ctk.CTkLabel(
            info_row,
            text="0%",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.progress_label.pack(side="left")

        self.elapsed_label = ctk.CTkLabel(
            info_row,
            text="",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_disabled"],
        )
        self.elapsed_label.pack(side="right")

        # ── Log Frame ──
        log_container = ctk.CTkFrame(
            self,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        log_container.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        self.log_text = ctk.CTkTextbox(
            log_container,
            font=("Consolas", 11),
            fg_color="transparent",
            text_color=self.theme.colors["text_secondary"],
            wrap="word",
            state="disabled",
            corner_radius=0,
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Configure color tags
        self._setup_log_tags()

        # ── Bottom Bar ──
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=24, pady=(12, 20))

        # Copy log button (always visible)
        self.copy_btn = ctk.CTkButton(
            bottom,
            text=f"📋  {t('common.copy_log')}",
            width=100,
            height=34,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_secondary"],
            command=self._copy_log,
        )
        self.copy_btn.pack(side="left")

        # Cancel button
        self.cancel_btn = ctk.CTkButton(
            bottom,
            text=t("common.cancel"),
            width=100,
            height=34,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._handle_cancel,
        )
        self.cancel_btn.pack(side="right")

        # Close button (hidden initially)
        self.close_btn = ctk.CTkButton(
            bottom,
            text=t("common.close"),
            width=100,
            height=34,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._handle_close,
        )

    def _setup_log_tags(self) -> None:
        """Configure text widget color tags."""
        colors = {
            "log_success": self.theme.colors.get("success", "#4CAF50"),
            "log_warning": self.theme.colors.get("warning", "#FFA500"),
            "log_error": self.theme.colors.get("danger", "#FF6B6B"),
            "log_info": self.theme.colors.get("text_secondary", "#888"),
        }

        # CTkTextbox wraps a tkinter Text widget
        try:
            inner_text = self.log_text._textbox
            for tag_name, color in colors.items():
                inner_text.tag_configure(tag_name, foreground=color)
        except AttributeError:
            pass  # fallback if internal API changes

    def _center_on_parent(self, parent) -> None:
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    # ── Queue Processing ─────────────────────────────────────────────────

    def _process_queue(self) -> None:
        """Drain log queue and update elapsed time."""
        try:
            while True:
                msg_type, message = self._log_queue.get_nowait()
                self._append_log(message, msg_type)
        except queue.Empty:
            pass

        # Update elapsed time
        if not self._completed:
            elapsed = time.time() - self._start_time
            mins, secs = divmod(int(elapsed), 60)
            self.elapsed_label.configure(text=f"⏱  {mins:02d}:{secs:02d}")

        if not self._completed:
            self.after(100, self._process_queue)

    def _append_log(self, message: str, msg_type: str = "info") -> None:
        """Add a colored line to the log widget."""
        self._log_lines.append(f"[{msg_type.upper()}] {message}")

        self.log_text.configure(state="normal")

        tag = LOG_COLORS.get(msg_type)

        try:
            inner = self.log_text._textbox
            start = inner.index("end-1c")
            inner.insert("end", f"{message}\n")
            end = inner.index("end-1c")

            if tag:
                inner.tag_add(tag, start, end)
        except (AttributeError, Exception):
            # Fallback without coloring
            self.log_text.insert("end", f"{message}\n")

        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ── Thread-Safe Public API ───────────────────────────────────────────

    def log(self, message: str, msg_type: str = "info") -> None:
        """
        Add a log message (thread-safe).

        Args:
            message: The log text.
            msg_type: One of 'info', 'success', 'warning', 'error'.
        """
        self._log_queue.put((msg_type, message))

    def set_progress(self, value: float, text: str = "") -> None:
        """
        Set progress value (thread-safe).

        Args:
            value: Progress 0.0 to 1.0.
            text: Optional label like "3/10".
        """
        value = max(0.0, min(1.0, value))

        def _update():
            self.progress.set(value)
            display = text or f"{int(value * 100)}%"
            self.progress_label.configure(text=display)

        self.after(0, _update)

    def set_title(self, title: str) -> None:
        """Update the header title (thread-safe)."""
        self.after(0, lambda: self.title_label.configure(text=title))

    def complete(self, success: bool = True, message: str = "") -> None:
        """
        Mark the operation as complete (thread-safe).

        Args:
            success: Whether the operation succeeded.
            message: Final status message.
        """
        self._completed = True

        def _update():
            self.progress.set(1.0)

            elapsed = time.time() - self._start_time
            mins, secs = divmod(int(elapsed), 60)
            time_str = f"{mins:02d}:{secs:02d}"

            if success:
                self.title_label.configure(text=f"✅  {t('common.operation_complete')}")
                self.progress.configure(progress_color=self.theme.colors["success"])
                self.log(
                    message or t("common.operation_success"),
                    "success",
                )
            else:
                self.title_label.configure(text=f"❌  {t('common.operation_failed')}")
                self.progress.configure(progress_color=self.theme.colors["danger"])
                self.log(
                    message or t("common.operation_error"),
                    "error",
                )

            self.elapsed_label.configure(text=f"⏱  {time_str}")
            self.progress_label.configure(text="100%")

            # Swap buttons
            self.cancel_btn.pack_forget()
            self.close_btn.pack(side="right")

            # Allow X to close
            self.protocol("WM_DELETE_WINDOW", self._handle_close)

            # Process remaining log entries
            self._process_queue()

        self.after(0, _update)

    @property
    def cancelled(self) -> bool:
        """Check if the user cancelled."""
        return self._cancelled

    # ── Button Handlers ──────────────────────────────────────────────────

    def _handle_cancel(self) -> None:
        if self._completed:
            self._handle_close()
            return

        if not self._cancelled:
            self._cancelled = True
            self.cancel_btn.configure(
                text=t("common.cancelling"),
                state="disabled",
            )
            self.log(f"⏹  {t('common.cancel_requested')}", "warning")

    def _handle_close(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _copy_log(self) -> None:
        """Copy full log to clipboard."""
        full_log = "\n".join(self._log_lines)
        try:
            self.clipboard_clear()
            self.clipboard_append(full_log)

            # Visual feedback
            original = self.copy_btn.cget("text")
            self.copy_btn.configure(text=f"✅  {t('common.copied')}")
            self.after(1500, lambda: self.copy_btn.configure(text=original))
        except Exception as e:
            logger.error("Clipboard copy failed: %s", e)


# ─── Progress Callback Helper ───────────────────────────────────────────────

class ProgressCallback:
    """
    Helper for threading: wraps a ProgressModal for easy step-by-step updates.

    Usage:
        cb = ProgressCallback(modal, total=10)
        for item in items:
            if not cb.update(f"Processing {item}..."):
                break  # cancelled
    """

    def __init__(self, modal: ProgressModal, total: int = 100) -> None:
        self.modal = modal
        self.total = max(total, 1)
        self.current = 0
        self._success_count = 0
        self._error_count = 0

    def update(
        self,
        message: str,
        current: Optional[int] = None,
        msg_type: str = "info",
    ) -> bool:
        """
        Update progress by one step.

        Args:
            message: Log message.
            current: Override current step number.
            msg_type: Log message type.

        Returns:
            True to continue, False if cancelled.
        """
        if current is not None:
            self.current = current
        else:
            self.current += 1

        progress = self.current / self.total
        self.modal.set_progress(progress, f"{self.current}/{self.total}")
        self.modal.log(message, msg_type)

        return not self.modal.cancelled

    def mark_success(self, message: str = "") -> None:
        self._success_count += 1
        if message:
            self.modal.log(f"  ✓  {message}", "success")

    def mark_error(self, message: str = "") -> None:
        self._error_count += 1
        if message:
            self.modal.log(f"  ✗  {message}", "error")

    @property
    def success_count(self) -> int:
        return self._success_count

    @property
    def error_count(self) -> int:
        return self._error_count

    @property
    def is_cancelled(self) -> bool:
        return self.modal.cancelled

    def complete(self, message: str = "") -> None:
        """Auto-complete with success/error summary."""
        all_ok = self._error_count == 0 and not self.is_cancelled

        if not message:
            message = (
                f"✅  {self._success_count}/{self.total} succeeded"
                if all_ok
                else f"⚠  {self._success_count} succeeded, {self._error_count} failed"
            )

        self.modal.complete(all_ok, message)