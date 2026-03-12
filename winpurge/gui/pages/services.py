"""
WinPurge Services Page
Windows service management.
"""

import customtkinter as ctk
import threading
from typing import Dict, List

from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.services import services_manager
from winpurge.backup import backup_manager


class ServiceItem(ctk.CTkFrame):
    """Single service item with controls."""
    
    def __init__(
        self,
        master: any,
        service: Dict,
        on_action: callable,
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
        
        self.service = service
        self.on_action = on_action
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create item widgets."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=12)
        
        # Left side: info
        info_frame = ctk.CTkFrame(container, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Title row
        title_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_row.pack(fill="x")
        
        title = ctk.CTkLabel(
            title_row,
            text=self.service.get("display_name", ""),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(side="left")
        
        # Risk badge
        risk_level = self.service.get("risk_level", "moderate")
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
        
        # Status badge
        status = self.service.get("status", "Unknown")
        status_color = self.theme.colors["success"] if status == "Running" else self.theme.colors["text_secondary"]
        
        self.status_badge = ctk.CTkLabel(
            title_row,
            text=status,
            font=("Inter", 10),
            fg_color=self.theme.colors["bg_main"],
            text_color=status_color,
            corner_radius=4,
            padx=6,
            pady=1,
        )
        self.status_badge.pack(side="left", padx=(8, 0))
        
        # Description
        desc = ctk.CTkLabel(
            info_frame,
            text=self.service.get("description", ""),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
            wraplength=500,
            justify="left",
        )
        desc.pack(anchor="w", pady=(4, 0))
        
        # Service name and start type
        info_text = f"{self.service.get('name', '')} • {self.service.get('start_type', 'Unknown')}"
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Consolas", 10),
            text_color=self.theme.colors["text_disabled"],
        )
        info_label.pack(anchor="w", pady=(2, 0))
        
        # Right side: action button
        action_frame = ctk.CTkFrame(container, fg_color="transparent")
        action_frame.pack(side="right", padx=(16, 0))
        
        is_disabled = self.service.get("start_type") == "Disabled"
        
        self.action_btn = ctk.CTkButton(
            action_frame,
            text="Enable" if is_disabled else "Disable",
            width=80,
            fg_color=self.theme.colors["success"] if is_disabled else self.theme.colors["danger"],
            hover_color="#00E676" if is_disabled else "#FF8080",
            command=self._handle_action,
        )
        self.action_btn.pack()
    
    def _handle_action(self) -> None:
        """Handle action button click."""
        action = "enable" if self.service.get("start_type") == "Disabled" else "disable"
        self.on_action(self.service.get("name", ""), action)


class ServicesPage(ctk.CTkFrame):
    """Services management page."""
    
    def __init__(self, master: any, **kwargs) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs,
        )
        
        self.service_items: Dict[str, ServiceItem] = {}
        self.current_filter = "all"
        
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
            text=t("services.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(
            title_row,
            text="🔄 " + t("services.refresh"),
            width=120,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.refresh_list,
        )
        refresh_btn.pack(side="right")
        
        subtitle = ctk.CTkLabel(
            header,
            text=t("services.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(header, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(12, 0))
        
        filters = [
            ("all", t("services.filter_all")),
            ("safe", t("services.filter_safe")),
            ("moderate", t("services.filter_moderate")),
            ("advanced", t("services.filter_advanced")),
        ]
        
        self.filter_buttons = {}
        for filter_id, filter_label in filters:
            btn = ctk.CTkButton(
                filter_frame,
                text=filter_label,
                width=120,
                fg_color=self.theme.colors["accent"] if filter_id == "all" else self.theme.colors["bg_card"],
                hover_color=self.theme.colors["accent_hover"] if filter_id == "all" else self.theme.colors["card_border"],
                text_color="#FFFFFF" if filter_id == "all" else self.theme.colors["text_primary"],
                command=lambda f=filter_id: self._set_filter(f),
            )
            btn.pack(side="left", padx=(0, 8))
            self.filter_buttons[filter_id] = btn
        
        # Service list
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        self.list_frame.pack(fill="both", expand=True, padx=32, pady=(16, 24))
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.list_frame,
            text=t("common.loading"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.loading_label.pack(pady=40)
    
    def _set_filter(self, filter_id: str) -> None:
        """Set the current filter."""
        # Update button styles
        for fid, btn in self.filter_buttons.items():
            if fid == filter_id:
                btn.configure(
                    fg_color=self.theme.colors["accent"],
                    hover_color=self.theme.colors["accent_hover"],
                    text_color="#FFFFFF",
                )
            else:
                btn.configure(
                    fg_color=self.theme.colors["bg_card"],
                    hover_color=self.theme.colors["card_border"],
                    text_color=self.theme.colors["text_primary"],
                )
        
        self.current_filter = filter_id
        self.refresh_list()
    
    def refresh_list(self) -> None:
        """Refresh the services list."""
        self.loading_label.pack(pady=40)
        
        # Clear existing items
        for widget in self.list_frame.winfo_children():
            if widget != self.loading_label:
                widget.destroy()
        
        self.service_items.clear()
        
        def load():
            services = services_manager.get_services_list()
            
            # Apply filter
            if self.current_filter != "all":
                services = [s for s in services if s.get("risk_level") == self.current_filter]
            
            self.after(0, lambda: self._populate_list(services))
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def _populate_list(self, services: List[Dict]) -> None:
        """Populate the list with services."""
        self.loading_label.pack_forget()
        
        if not services:
            no_results = ctk.CTkLabel(
                self.list_frame,
                text="No services found matching the filter.",
                font=self.theme.get_font("body"),
                text_color=self.theme.colors["text_secondary"],
            )
            no_results.pack(pady=40)
            return
        
        # Group by category
        categories: Dict[str, List[Dict]] = {}
        for svc in services:
            cat = svc.get("category", "other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(svc)
        
        # Create items
        for cat, svcs in categories.items():
            # Category header
            cat_info = services_manager.get_categories().get(cat, {})
            header = ctk.CTkLabel(
                self.list_frame,
                text=cat_info.get("display_name", cat.title()),
                font=self.theme.get_font("body", "bold"),
                text_color=self.theme.colors["text_secondary"],
            )
            header.pack(anchor="w", pady=(16, 8))
            
            for svc in svcs:
                item = ServiceItem(
                    self.list_frame,
                    svc,
                    on_action=self._handle_service_action,
                )
                item.pack(fill="x", pady=2)
                self.service_items[svc.get("name", "")] = item
    
    def _handle_service_action(self, service_name: str, action: str) -> None:
        """Handle service enable/disable action."""
        modal = ProgressModal(
            self.winfo_toplevel(),
            f"{'Enabling' if action == 'enable' else 'Disabling'} {service_name}"
        )
        
        def run():
            modal.log("Creating backup...")
            backup_manager.create_backup(f"Before {action} {service_name}")
            
            modal.log(f"{'Enabling' if action == 'enable' else 'Disabling'} service...")
            modal.set_progress(0.5)
            
            if action == "disable":
                success, message = services_manager.disable_service(service_name)
            else:
                success, message = services_manager.enable_service(service_name)
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
            
            self.after(0, self.refresh_list)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()