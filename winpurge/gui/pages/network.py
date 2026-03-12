"""
WinPurge Network Page
Network configuration and optimization.
"""

import customtkinter as ctk
import threading
from typing import Dict, Optional

from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.network import network_manager
from winpurge.constants import DNS_PRESETS


class NetworkPage(ctk.CTkFrame):
    """Network configuration page."""
    
    def __init__(self, master: any, **kwargs) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs,
        )
        
        self.selected_dns: Optional[str] = None
        self._create_widgets()
        self.refresh_status()
    
    def _create_widgets(self) -> None:
        """Create page widgets."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 16))
        
        title = ctk.CTkLabel(
            header,
            text=t("network.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text=t("network.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # Content
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        content.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        
        # DNS Section
        self._create_dns_section(content)
        
        # Hosts File Section
        self._create_hosts_section(content)
        
        # Network Optimization Section
        self._create_optimization_section(content)
    
    def _create_dns_section(self, parent: ctk.CTkFrame) -> None:
        """Create DNS configuration section."""
        section_header = ctk.CTkLabel(
            parent,
            text=t("network.dns_settings"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_header.pack(anchor="w", pady=(0, 12))
        
        dns_card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        dns_card.pack(fill="x", pady=(0, 16))
        
        container = ctk.CTkFrame(dns_card, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)
        
        # Current DNS display
        current_row = ctk.CTkFrame(container, fg_color="transparent")
        current_row.pack(fill="x", pady=(0, 16))
        
        ctk.CTkLabel(
            current_row,
            text=t("network.current_dns") + ":",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(side="left")
        
        self.current_dns_label = ctk.CTkLabel(
            current_row,
            text="Loading...",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        self.current_dns_label.pack(side="left", padx=(8, 0))
        
        # DNS presets
        presets_label = ctk.CTkLabel(
            container,
            text="Select DNS Provider:",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        presets_label.pack(anchor="w", pady=(0, 8))
        
        presets_frame = ctk.CTkFrame(container, fg_color="transparent")
        presets_frame.pack(fill="x", pady=(0, 16))
        
        self.dns_buttons: Dict[str, ctk.CTkButton] = {}
        
        dns_options = [
            ("cloudflare", t("network.dns_cloudflare")),
            ("google", t("network.dns_google")),
            ("adguard", t("network.dns_adguard")),
            ("quad9", t("network.dns_quad9")),
        ]
        
        for i, (preset_id, preset_name) in enumerate(dns_options):
            btn = ctk.CTkButton(
                presets_frame,
                text=preset_name,
                width=140,
                fg_color=self.theme.colors["bg_main"],
                hover_color=self.theme.colors["card_border"],
                border_width=1,
                border_color=self.theme.colors["card_border"],
                text_color=self.theme.colors["text_primary"],
                command=lambda p=preset_id: self._select_dns(p),
            )
            btn.grid(row=0, column=i, padx=(0, 8), pady=4)
            self.dns_buttons[preset_id] = btn
        
        # Custom DNS input
        custom_frame = ctk.CTkFrame(container, fg_color="transparent")
        custom_frame.pack(fill="x", pady=(0, 16))
        
        ctk.CTkLabel(
            custom_frame,
            text=t("network.dns_custom") + ":",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(side="left")
        
        self.custom_dns_entry = ctk.CTkEntry(
            custom_frame,
            width=200,
            placeholder_text="e.g., 1.1.1.1",
            fg_color=self.theme.colors["input_bg"],
            border_color=self.theme.colors["input_border"],
        )
        self.custom_dns_entry.pack(side="left", padx=(8, 0))
        
        # Action buttons
        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x")
        
        apply_btn = ctk.CTkButton(
            actions_frame,
            text=t("network.apply_dns"),
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._apply_dns,
        )
        apply_btn.pack(side="left")
        
        reset_btn = ctk.CTkButton(
            actions_frame,
            text=t("network.reset_dns"),
            fg_color=self.theme.colors["bg_main"],
            hover_color=self.theme.colors["card_border"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._reset_dns,
        )
        reset_btn.pack(side="left", padx=(8, 0))
    
    def _create_hosts_section(self, parent: ctk.CTkFrame) -> None:
        """Create hosts file section."""
        section_header = ctk.CTkLabel(
            parent,
            text=t("network.hosts_file"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_header.pack(anchor="w", pady=(16, 12))
        
        hosts_card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        hosts_card.pack(fill="x", pady=(0, 16))
        
        container = ctk.CTkFrame(hosts_card, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)
        
        # Hosts info
        info_row = ctk.CTkFrame(container, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 12))
        
        self.hosts_count_label = ctk.CTkLabel(
            info_row,
            text=t("network.hosts_entries", count="..."),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.hosts_count_label.pack(side="left")
        
        # Hosts text editor
        self.hosts_text = ctk.CTkTextbox(
            container,
            height=200,
            font=("Consolas", 11),
            fg_color=self.theme.colors["bg_main"],
            text_color=self.theme.colors["text_primary"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        self.hosts_text.pack(fill="x", pady=(0, 12))
        
        # Save button
        save_btn = ctk.CTkButton(
            container,
            text="Save Hosts File",
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._save_hosts,
        )
        save_btn.pack(anchor="w")
    
    def _create_optimization_section(self, parent: ctk.CTkFrame) -> None:
        """Create network optimization section."""
        section_header = ctk.CTkLabel(
            parent,
            text=t("network.network_optimization"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_header.pack(anchor="w", pady=(16, 12))
        
        # LSO card
        lso_card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        lso_card.pack(fill="x", pady=(0, 8))
        
        lso_container = ctk.CTkFrame(lso_card, fg_color="transparent")
        lso_container.pack(fill="both", expand=True, padx=16, pady=12)
        
        lso_left = ctk.CTkFrame(lso_container, fg_color="transparent")
        lso_left.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            lso_left,
            text=t("network.disable_lso"),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            lso_left,
            text=t("network.disable_lso_desc"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w")
        
        ctk.CTkButton(
            lso_container,
            text="Apply",
            width=80,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._disable_lso,
        ).pack(side="right")
        
        # RSS card
        rss_card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        rss_card.pack(fill="x", pady=(0, 8))
        
        rss_container = ctk.CTkFrame(rss_card, fg_color="transparent")
        rss_container.pack(fill="both", expand=True, padx=16, pady=12)
        
        rss_left = ctk.CTkFrame(rss_container, fg_color="transparent")
        rss_left.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            rss_left,
            text=t("network.enable_rss"),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            rss_left,
            text=t("network.enable_rss_desc"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w")
        
        ctk.CTkButton(
            rss_container,
            text="Apply",
            width=80,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._enable_rss,
        ).pack(side="right")
    
    def _select_dns(self, preset_id: str) -> None:
        """Select a DNS preset."""
        self.selected_dns = preset_id
        
        # Update button styles
        for pid, btn in self.dns_buttons.items():
            if pid == preset_id:
                btn.configure(
                    fg_color=self.theme.colors["accent"],
                    text_color="#FFFFFF",
                    border_width=0,
                )
            else:
                btn.configure(
                    fg_color=self.theme.colors["bg_main"],
                    text_color=self.theme.colors["text_primary"],
                    border_width=1,
                )
        
        # Clear custom entry
        self.custom_dns_entry.delete(0, "end")
    
    def refresh_status(self) -> None:
        """Refresh current network status."""
        def load():
            dns_config = network_manager.get_current_dns()
            hosts_content = network_manager.get_hosts_file_content()
            hosts_count = network_manager.get_hosts_entry_count()
            
            self.after(0, lambda: self._update_display(dns_config, hosts_content, hosts_count))
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def _update_display(self, dns_config: dict, hosts_content: str, hosts_count: int) -> None:
        """Update display with current status."""
        # DNS
        if dns_config:
            first_interface = list(dns_config.values())[0] if dns_config else "Unknown"
            self.current_dns_label.configure(text=first_interface)
        else:
            self.current_dns_label.configure(text="Automatic (DHCP)")
        
        # Hosts
        self.hosts_count_label.configure(text=t("network.hosts_entries", count=hosts_count))
        self.hosts_text.delete("1.0", "end")
        self.hosts_text.insert("1.0", hosts_content)
    
    def _apply_dns(self) -> None:
        """Apply selected DNS settings."""
        custom_dns = self.custom_dns_entry.get().strip()
        
        if custom_dns:
            # Use custom DNS
            modal = ProgressModal(self.winfo_toplevel(), "Applying Custom DNS")
            
            def apply():
                modal.log(f"Setting DNS to {custom_dns}...")
                interfaces = network_manager.get_network_interfaces()
                
                for interface in interfaces:
                    success, message = network_manager.set_dns(interface, custom_dns)
                    if success:
                        modal.log(f"✓ {interface}: {message}", "success")
                    else:
                        modal.log(f"✗ {interface}: {message}", "error")
                
                modal.complete(True, "DNS configured")
                self.after(0, self.refresh_status)
            
            thread = threading.Thread(target=apply, daemon=True)
            thread.start()
            
        elif self.selected_dns:
            # Use preset
            modal = ProgressModal(self.winfo_toplevel(), f"Applying {DNS_PRESETS[self.selected_dns]['name']} DNS")
            
            def apply():
                modal.log(f"Setting DNS to {DNS_PRESETS[self.selected_dns]['name']}...")
                success, message = network_manager.set_dns_preset(self.selected_dns)
                
                if success:
                    modal.complete(True, message)
                else:
                    modal.complete(False, message)
                
                self.after(0, self.refresh_status)
            
            thread = threading.Thread(target=apply, daemon=True)
            thread.start()
    
    def _reset_dns(self) -> None:
        """Reset DNS to automatic."""
        modal = ProgressModal(self.winfo_toplevel(), "Resetting DNS")
        
        def reset():
            modal.log("Resetting DNS to automatic...")
            success, message = network_manager.reset_dns()
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
            
            self.after(0, self.refresh_status)
        
        thread = threading.Thread(target=reset, daemon=True)
        thread.start()
    
    def _save_hosts(self) -> None:
        """Save hosts file changes."""
        content = self.hosts_text.get("1.0", "end-1c")
        
        modal = ProgressModal(self.winfo_toplevel(), "Saving Hosts File")
        
        def save():
            modal.log("Saving hosts file...")
            success, message = network_manager.save_hosts_file(content)
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
            
            self.after(0, self.refresh_status)
        
        thread = threading.Thread(target=save, daemon=True)
        thread.start()
    
    def _disable_lso(self) -> None:
        """Disable Large Send Offload."""
        modal = ProgressModal(self.winfo_toplevel(), "Disabling LSO")
        
        def run():
            modal.log("Disabling Large Send Offload...")
            success, message = network_manager.disable_large_send_offload()
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def _enable_rss(self) -> None:
        """Enable Receive Side Scaling."""
        modal = ProgressModal(self.winfo_toplevel(), "Enabling RSS")
        
        def run():
            modal.log("Enabling Receive Side Scaling...")
            success, message = network_manager.enable_receive_side_scaling()
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()