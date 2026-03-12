"""
WinPurge GUI Progress Modal Component
Modal window showing operation progress and live logs.
"""

from typing import Callable, Optional
import customtkinter as ctk

from winpurge.gui.theme import get_theme_manager
from winpurge.constants import FONT_SIZE_BODY


class ProgressModal(ctk.CTkToplevel):
    """Modal window for showing operation progress."""
    
    def __init__(
        self,
        parent,
        title: str = "Processing",
        operation_callback: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the progress modal.
        
        Args:
            parent: Parent window.
            title: Modal title.
            operation_callback: Async operation to run.
        """
        super().__init__(parent, **kwargs)
        
        self.title_str = title
        self.theme = get_theme_manager()
        self.operation_callback = operation_callback
        self.cancelled = False
        
        self.geometry("600x400")
        self.title(title)
        self.resizable(False, False)
        
        # Configure appearance
        self.configure(fg_color=self.theme.get_color("BG_PRIMARY"))
        
        # Create content
        self._create_content()
        
        # Center on parent
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        
        x = parent_x + (parent_w - 600) // 2
        y = parent_y + (parent_h - 400) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _create_content(self) -> None:
        """Create modal content."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text=self.title_str,
            font=("Arial", 16, "bold"),
            fg_color="transparent",
            text_color=self.theme.get_color("TEXT_PRIMARY")
        )
        title_label.pack(fill="x", padx=20, pady=(15, 10))
        
        # Progress info
        self.info_label = ctk.CTkLabel(
            self,
            text="Starting operation...",
            font=("Arial", FONT_SIZE_BODY),
            fg_color="transparent",
            text_color=self.theme.get_color("TEXT_SECONDARY")
        )
        self.info_label.pack(fill="x", padx=20, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self,
            fg_color=self.theme.get_color("BG_TERTIARY"),
            progress_color=self.theme.get_color("ACCENT_PRIMARY")
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.progress_bar.set(0)
        
        # Log text area
        log_label = ctk.CTkLabel(
            self,
            text="Operation Log:",
            font=("Arial", FONT_SIZE_BODY, "bold"),
            fg_color="transparent",
            text_color=self.theme.get_color("TEXT_PRIMARY")
        )
        log_label.pack(fill="x", padx=20, pady=(0, 5))
        
        log_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme.get_color("BG_TERTIARY")
        )
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            fg_color=self.theme.get_color("BG_SECONDARY"),
            text_color=self.theme.get_color("TEXT_SECONDARY"),
            font=("Courier", 10)
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        
        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            fg_color=self.theme.get_color("ACCENT_PRIMARY"),
            text_color=self.theme.get_color("TEXT_PRIMARY")
        )
        self.cancel_button.pack(side="right", padx=(5, 0))
        
        self.close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            state="disabled",
            fg_color=self.theme.get_color("ACCENT_PRIMARY"),
            text_color=self.theme.get_color("TEXT_PRIMARY")
        )
        self.close_button.pack(side="right")
    
    def update_progress(self, current: float, total: float, message: str = "") -> None:
        """
        Update progress bar.
        
        Args:
            current: Current progress value.
            total: Total value.
            message: Optional message to display.
        """
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
        
        if message:
            self.info_label.configure(text=message)
    
    def log_message(self, message: str, color: str = None) -> None:
        """
        Add a message to the log.
        
        Args:
            message: Message text.
            color: Optional text color.
        """
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        
        self.update_idletasks()
    
    def set_completed(self, success: bool = True) -> None:
        """
        Mark operation as completed.
        
        Args:
            success: If True, mark as successful.
        """
        self.cancel_button.configure(state="disabled")
        self.close_button.configure(state="normal")
        
        if success:
            self.info_label.configure(text="Operation completed successfully")
        else:
            self.info_label.configure(text="Operation failed")
    
    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.cancelled = True
        self.cancel_button.configure(state="disabled")
        self.log_message("Operation cancelled by user...")
