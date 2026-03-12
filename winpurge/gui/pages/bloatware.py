"""
WinPurge Bloatware Page
Bloatware detection and removal.
"""

import customtkinter as ctk
import threading
from typing import Dict, List, Set

from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.bloatware import bloatware_manager
from winpurge.backup import backup_manager


class BloatwareItem(ctk.CTkFrame):
    """Single bloatware item with checkbox."""
    
    def __init__(
        self,
        master: any,
        package: Dict,
        on_select: callable,
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
        
        self.package = package
        self.on_select = on_select
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create item widgets."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=12, pady=8)
        
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
            command=self._handle_select,
        )
        self.checkbox.pack(side="left", padx=(0, 12))
        
        # Info
        info_frame = ctk.CTkFrame(container, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Title row
        title_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_row.pack(fill="x")
        
        title = ctk.CTkLabel(
            title_row,
            text=self.package.get("display_name", self.package.get("name", "")),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(side="left")
        
        # Risk badge
        risk_level = self.package.get("risk_level", "safe")
        risk_colors = self.theme.get_risk_colors(risk_level)
        
        badge = ctk.CTkLabel(
            title_row,
            text=t(f"risk_levels.{risk_level}"),
            font=("Inter", 10),
            fg_color=risk_colors["bg"],
            text_color=risk_colors["fg"],
            corner_radius=4,
            padx=6,
            pady=1,
        )
        badge.pack(side="left", padx=(8, 0))
        
        # Description
        desc = ctk.CTkLabel(
            info_frame,
            text=self.package.get("description", ""),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        desc.pack(anchor="w")
        
        # Package name
        pkg_name = ctk.CTkLabel(
            info_frame,
            text=self.package.get("name", ""),
            font=("Consolas", 10),
            text_color=self.theme.colors["text_disabled"],
        )
        pkg_name.pack(anchor="w")
    
    def _handle_select(self) -> None:
        """Handle checkbox selection."""
        self.on_select(self.package.get("name", ""), self.checkbox.get() == 1)
    
    def select(self) -> None:
        """Select this item."""
        self.checkbox.select()
    
    def deselect(self) -> None:
        """Deselect this item."""
        self.checkbox.deselect()
    
    def get(self) -> bool:
        """Get selection state."""
        return self.checkbox.get() == 1


class BloatwarePage(ctk.CTkFrame):
    """Bloatware removal page."""
    
    def __init__(self, master: any, **kwargs) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs,
        )
        
        self.selected_packages: Set[str] = set()
        self.package_items: Dict[str, BloatwareItem] = {}
        
        self._create_widgets()
        self.refresh_list()
    
    def _create_widgets(self) -> None:
        """Create page widgets."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 16))
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")
        
        title = ctk.CTkLabel(
            title_row,
            text=t("bloatware.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(side="left")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            title_row,
            text="🔄 " + t("bloatware.refresh"),
            width=120,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.refresh_list,
        )
        refresh_btn.pack(side="right")
        
        subtitle = ctk.CTkLabel(
            header,
            text=t("bloatware.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # Stats bar
        self.stats_label = ctk.CTkLabel(
            header,
            text=t("bloatware.total_found", count="..."),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_primary"],
        )
        self.stats_label.pack(anchor="w", pady=(8, 0))
        
        # Action buttons
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(fill="x", pady=(12, 0))
        
        self.remove_btn = ctk.CTkButton(
            actions,
            text=t("bloatware.remove_selected"),
            fg_color=self.theme.colors["danger"],
            hover_color="#FF8080",
            command=self._remove_selected,
            state="disabled",
        )
        self.remove_btn.pack(side="left")
        
        select_all_btn = ctk.CTkButton(
            actions,
            text=t("bloatware.select_all"),
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._select_all,
        )
        select_all_btn.pack(side="left", padx=(8, 0))
        
        deselect_btn = ctk.CTkButton(
            actions,
            text=t("bloatware.deselect_all"),
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._deselect_all,
        )
        deselect_btn.pack(side="left", padx=(8, 0))
        
        # Package list
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        self.list_frame.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.list_frame,
            text=t("common.loading"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.loading_label.pack(pady=40)
    
    def refresh_list(self) -> None:
        """Refresh the bloatware list."""
        self.loading_label.pack(pady=40)
        
        # Clear existing items
        for widget in self.list_frame.winfo_children():
            if widget != self.loading_label:
                widget.destroy()
        
        self.package_items.clear()
        self.selected_packages.clear()
        self._update_remove_button()
        
        def load():
            bloatware_manager.refresh_installed_packages()
            packages = bloatware_manager.get_installed_bloatware()
            self.after(0, lambda: self._populate_list(packages))
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def _populate_list(self, packages: List[Dict]) -> None:
        """Populate the list with packages."""
        self.loading_label.pack_forget()
        
        self.stats_label.configure(text=t("bloatware.total_found", count=len(packages)))
        
        # Group by category
        categories: Dict[str, List[Dict]] = {}
        for pkg in packages:
            cat = pkg.get("category", "other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(pkg)
        
        # Create category sections
        category_names = {
            "microsoft": t("bloatware.category_microsoft"),
            "thirdparty": t("bloatware.category_thirdparty"),
            "xbox": t("bloatware.category_xbox"),
            "oem": "OEM Bloatware",
            "other": "Other",
        }
        
        for cat, pkgs in categories.items():
            # Category header
            header = ctk.CTkLabel(
                self.list_frame,
                text=category_names.get(cat, cat.title()),
                font=self.theme.get_font("body", "bold"),
                text_color=self.theme.colors["text_secondary"],
            )
            header.pack(anchor="w", pady=(16, 8))
            
            # Package items
            for pkg in pkgs:
                item = BloatwareItem(
                    self.list_frame,
                    pkg,
                    on_select=self._handle_select,
                )
                item.pack(fill="x", pady=2)
                self.package_items[pkg.get("name", "")] = item
    
    def _handle_select(self, package_name: str, selected: bool) -> None:
        """Handle package selection."""
        if selected:
            self.selected_packages.add(package_name)
        else:
            self.selected_packages.discard(package_name)
        
        self._update_remove_button()
    
    def _update_remove_button(self) -> None:
        """Update remove button state."""
        count = len(self.selected_packages)
        
        if count > 0:
            self.remove_btn.configure(
                state="normal",
                text=f"{t('bloatware.remove_selected')} ({count})"
            )
        else:
            self.remove_btn.configure(
                state="disabled",
                text=t("bloatware.remove_selected")
            )
    
    def _select_all(self) -> None:
        """Select all packages."""
        for name, item in self.package_items.items():
            item.select()
            self.selected_packages.add(name)
        self._update_remove_button()
    
    def _deselect_all(self) -> None:
        """Deselect all packages."""
        for item in self.package_items.values():
            item.deselect()
        self.selected_packages.clear()
        self._update_remove_button()
    
    def _remove_selected(self) -> None:
        """Remove selected packages."""
        if not self.selected_packages:
            return
        
        packages = list(self.selected_packages)
        modal = ProgressModal(
            self.winfo_toplevel(),
            t("bloatware.remove_selected")
        )
        
        def remove():
            # Create backup first
            modal.log("Creating backup...")
            backup_manager.create_backup("Before bloatware removal")
            
            total = len(packages)
            success_count = 0
            
            for i, pkg in enumerate(packages, 1):
                if modal.cancelled:
                    break
                
                modal.log(t("bloatware.removing", name=pkg))
                modal.set_progress(i / total, f"{i}/{total}")
                
                success, message = bloatware_manager.remove_package(pkg)
                
                if success:
                    success_count += 1
                    modal.log(f"✓ Removed", "success")
                else:
                    modal.log(f"✗ {message}", "error")
            
            if not modal.cancelled:
                modal.complete(
                    True,
                    t("bloatware.removed_success", count=success_count)
                )
                self.after(0, self.refresh_list)
        
        thread = threading.Thread(target=remove, daemon=True)
        thread.start()