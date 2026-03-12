"""
WinPurge Progress Modal Component
Modal dialog with progress bar and live log.
"""

import customtkinter as ctk
from typing import Optional
import threading
import queue

from winpurge.gui.theme import get_theme
from winpurge.utils import t


class ProgressModal(ctk.CTkToplevel):
    """Modal dialog showing operation progress."""
    
    def __init__(
        self,
        master: any,
        title: str,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        
        self.theme = get_theme()
        self.title(title)
        
        # Window setup
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        parent_x = master.winfo_rootx()
        parent_y = master.winfo_rooty()
        parent_w = master.winfo_width()
        parent_h = master.winfo_height()
        x = parent_x + (parent_w - 500) // 2
        y = parent_y + (parent_h - 400) // 2
        self.geometry(f"+{x}+{y}")
        
        self.configure(fg_color=self.theme.colors["bg_main"])
        
        self._log_queue: queue.Queue = queue.Queue()
        self._cancelled = False
        self._completed = False
        
        self._create_widgets()
        self._process_log_queue()
    
    def _create_widgets(self) -> None:
        """Create modal widgets."""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text=t("common.please_wait"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        self.title_label.pack(pady=(24, 16))
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(
            self,
            width=440,
            height=8,
            progress_color=self.theme.colors["accent"],
            fg_color=self.theme.colors["card_border"],
        )
        self.progress.pack(pady=(0, 8))
        self.progress.set(0)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            self,
            text="0%",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.progress_label.pack(pady=(0, 16))
        
        # Log frame
        log_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=8,
        )
        log_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        
        # Log text
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=("Consolas", 11),
            fg_color="transparent",
            text_color=self.theme.colors["text_secondary"],
            wrap="word",
            state="disabled",
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text=t("common.cancel"),
            width=100,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._handle_cancel,
        )
        self.cancel_btn.pack(side="right")
        
        self.close_btn = ctk.CTkButton(
            btn_frame,
            text=t("common.close"),
            width=100,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._handle_close,
        )
        self.close_btn.pack(side="right", padx=(0, 8))
        self.close_btn.pack_forget()  # Hidden initially
        
        # Prevent closing with X button during operation
        self.protocol("WM_DELETE_WINDOW", self._handle_cancel)
    
    def _process_log_queue(self) -> None:
        """Process pending log messages."""
        try:
            while True:
                msg_type, message = self._log_queue.get_nowait()
                self._add_log_line(message, msg_type)
        except queue.Empty:
            pass
        
        if not self._completed:
            self.after(100, self._process_log_queue)
    
    def _add_log_line(self, message: str, msg_type: str = "info") -> None:
        """Add a line to the log."""
        self.log_text.configure(state="normal")
        
        # Color based on type
        colors = {
            "info": self.theme.colors["text_secondary"],
            "success": self.theme.colors["success"],
            "warning": self.theme.colors["warning"],
            "error": self.theme.colors["danger"],
        }
        
        # Add timestamp and message
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def log(self, message: str, msg_type: str = "info") -> None:
        """
        Add a log message (thread-safe).
        
        Args:
            message: Log message.
            msg_type: Message type ('info', 'success', 'warning', 'error').
        """
        self._log_queue.put((msg_type, message))
    
    def set_progress(self, value: float, text: str = "") -> None:
        """
        Set progress value (thread-safe).
        
        Args:
            value: Progress value (0.0 to 1.0).
            text: Optional progress text.
        """
        def update():
            self.progress.set(value)
            self.progress_label.configure(text=text or f"{int(value * 100)}%")
        
        self.after(0, update)
    
    def set_title(self, title: str) -> None:
        """Set modal title (thread-safe)."""
        self.after(0, lambda: self.title_label.configure(text=title))
    
    def complete(self, success: bool = True, message: str = "") -> None:
        """
        Mark operation as complete.
        
        Args:
            success: Whether operation succeeded.
            message: Completion message.
        """
        self._completed = True
        
        def update():
            self.progress.set(1.0)
            
            if success:
                self.title_label.configure(text=t("common.operation_complete"))
                self.progress.configure(progress_color=self.theme.colors["success"])
                self.log(message or "Operation completed successfully", "success")
            else:
                self.title_label.configure(text=t("common.operation_failed"))
                self.progress.configure(progress_color=self.theme.colors["danger"])
                self.log(message or "Operation failed", "error")
            
            # Show close button, hide cancel
            self.cancel_btn.pack_forget()
            self.close_btn.pack(side="right")
            
            # Allow closing with X
            self.protocol("WM_DELETE_WINDOW", self._handle_close)
        
        self.after(0, update)
    
    def _handle_cancel(self) -> None:
        """Handle cancel button click."""
        if not self._completed:
            self._cancelled = True
            self.log("Operation cancelled by user", "warning")
    
    def _handle_close(self) -> None:
        """Handle close button click."""
        self.grab_release()
        self.destroy()
    
    @property
    def cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._cancelled


class ProgressCallback:
    """Helper class for progress callbacks in threads."""
    
    def __init__(self, modal: ProgressModal, total: int = 100) -> None:
        self.modal = modal
        self.total = total
        self.current = 0
    
    def update(self, message: str, current: Optional[int] = None) -> bool:
        """
        Update progress.
        
        Args:
            message: Progress message.
            current: Current item number.
            
        Returns:
            False if cancelled, True otherwise.
        """
        if current is not None:
            self.current = current
        else:
            self.current += 1
        
        progress = self.current / self.total if self.total > 0 else 0
        self.modal.set_progress(progress, f"{self.current}/{self.total}")
        self.modal.log(message)
        
        return not self.modal.cancelled