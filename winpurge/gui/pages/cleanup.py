"""
WinPurge Cleanup Page
Disk cleanup and temporary file removal.
"""

import customtkinter as ctk
import threading
from typing import Dict, List

from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t, format_size
from winpurge.core.cleanup import cleanup_manager


class CleanupItem(ctk.CTkFrame):
    """Single cleanup item with checkbox and size."""
    
    def __init__(
        self,
        master: any,
        item: Dict,
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
        
        self.item = item
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create item widgets."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=12)
        
        # Checkbox
        self.checkbox = ctk.CTkCheckBox(
            container,
            text="",
            width=24,
            height=24,
            checkbox_width=20,
            checkbox_height=20,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            border_color=self.theme.colors["card_border"],
        )
        self.checkbox.pack(side="left", padx=(0, 12))
        self.checkbox.select()  # Selected by default
        
        # Info
        info_frame = ctk.CTkFrame(container, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            info_frame,
            text=self.item.get("name", ""),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        path_text = str(self.item.get("path", "")) if self.item.get("path") else "System"
        ctk.CTkLabel(
            info_frame,
            text=path_text,
            font=("Consolas", 10),
            text_color=self.theme.colors["text_disabled"],
        ).pack(anchor="w")
        
        # Size
        self.size_label = ctk.CTkLabel(
            container,
            text=self.item.get("size_display", "..."),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["accent"],
        )
        self.size_label.pack(side="right")
    
    def update_size(self, size_display: str) -> None:
        """Update size display."""
        self.size_label.configure(text=size_display)
    
    def is_selected(self) -> bool:
        """Check if item is selected."""
        return self.checkbox.get() == 1
    
    def select(self) -> None:
        """Select this item."""
        self.checkbox.select()
    
    def deselect(self) -> None:
        """Deselect this item."""
        self.checkbox.deselect()


class CleanupPage(ctk.CTkFrame):
    """Disk cleanup page."""
    
    def __init__(self, master: any, **kwargs) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs,
        )
        
        self.cleanup_items: Dict[str, CleanupItem] = {}
        self.items_data: List[Dict] = []
        
        self._create_widgets()
        self.refresh_sizes()
    
    def _create_widgets(self) -> None:
        """Create page widgets."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 16))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        
        title = ctk.CTkLabel(
            title_row,
            text=t("cleanup.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(
            title_row,
            text="🔄 Refresh",
            width=100,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.refresh_sizes,
        )
        refresh_btn.pack(side="right")
        
        subtitle = ctk.CTkLabel(
            header,
            text=t("cleanup.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # Total size card
        total_card = ctk.CTkFrame(
            header,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        total_card.pack(fill="x", pady=(16, 0))
        
        total_container = ctk.CTkFrame(total_card, fg_color="transparent")
        total_container.pack(fill="x", padx=20, pady=16)
        
        ctk.CTkLabel(
            total_container,
            text=t("cleanup.total_space"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(side="left")
        
        self.total_size_label = ctk.CTkLabel(
            total_container,
            text="Calculating...",
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["accent"],
        )
        self.total_size_label.pack(side="right")
        
        # Content
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        content.pack(fill="both", expand=True, padx=32, pady=(16, 16))
        
        self.items_frame = content
        
        # Loading
        self.loading_label = ctk.CTkLabel(
            content,
            text=t("cleanup.analyzing"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.loading_label.pack(pady=40)
        
        # Bottom actions
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=32, pady=(0, 24))
        
        self.clean_btn = ctk.CTkButton(
            actions,
            text=t("cleanup.clean_selected"),
            fg_color=self.theme.colors["danger"],
            hover_color="#FF8080",
            command=self._clean_selected,
        )
        self.clean_btn.pack(side="left")
        
        select_all_btn = ctk.CTkButton(
            actions,
            text="Select All",
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._select_all,
        )
        select_all_btn.pack(side="left", padx=(8, 0))
        
        deselect_btn = ctk.CTkButton(
            actions,
            text="Deselect All",
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._deselect_all,
        )
        deselect_btn.pack(side="left", padx=(8, 0))
    
    def refresh_sizes(self) -> None:
        """Refresh cleanup item sizes."""
        self.loading_label.pack(pady=40)
        
        # Clear existing items
        for widget in self.items_frame.winfo_children():
            if widget != self.loading_label:
                widget.destroy()
        
        self.cleanup_items.clear()
        
        def calculate():
            items = cleanup_manager.get_cleanup_items()
            items = cleanup_manager.calculate_sizes(items)
            self.items_data = items
            
            self.after(0, lambda: self._populate_items(items))
        
        thread = threading.Thread(target=calculate, daemon=True)
        thread.start()
    
    def _populate_items(self, items: List[Dict]) -> None:
        """Populate cleanup items."""
        self.loading_label.pack_forget()
        
        total_size = 0
        
        for item in items:
            cleanup_item = CleanupItem(self.items_frame, item)
            cleanup_item.pack(fill="x", pady=4)
            self.cleanup_items[item["id"]] = cleanup_item
            total_size += item.get("size", 0)
        
        self.total_size_label.configure(text=format_size(total_size))
    
    def _select_all(self) -> None:
        """Select all items."""
        for item in self.cleanup_items.values():
            item.select()
    
    def _deselect_all(self) -> None:
        """Deselect all items."""
        for item in self.cleanup_items.values():
            item.deselect()
    
    def _clean_selected(self) -> None:
        """Clean selected items."""
        selected = []
        
        for item_id, item_widget in self.cleanup_items.items():
            if item_widget.is_selected():
                for data in self.items_data:
                    if data["id"] == item_id:
                        selected.append(data)
                        break
        
        if not selected:
            return
        
        modal = ProgressModal(self.winfo_toplevel(), t("cleanup.clean_selected"))
        
        def clean():
            total = len(selected)
            total_freed = 0
            
            for i, item in enumerate(selected, 1):
                if modal.cancelled:
                    break
                
                modal.log(t("cleanup.cleaning", name=item["name"]))
                modal.set_progress(i / total, f"{i}/{total}")
                
                success, freed, message = cleanup_manager.clean_item(item)
                
                if success:
                    total_freed += freed
                    modal.log(f"✓ {message} ({format_size(freed)})", "success")
                else:
                    modal.log(f"✗ {message}", "error")
            
            if not modal.cancelled:
                modal.complete(True, t("cleanup.cleaned_success", size=format_size(total_freed)))
                self.after(0, self.refresh_sizes)
        
        thread = threading.Thread(target=clean, daemon=True)
        thread.start()