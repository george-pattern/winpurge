"""
WinPurge Privacy Page
Privacy and telemetry settings.
"""

import customtkinter as ctk
import threading
from typing import Dict, List

from winpurge.gui.theme import get_theme
from winpurge.gui.components.toggle_card import ToggleCard
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.privacy import privacy_manager
from winpurge.core.telemetry import telemetry_manager
from winpurge.backup import backup_manager


class PrivacyPage(ctk.CTkFrame):
    """Privacy and telemetry page."""
    
    def __init__(self, master: any, **kwargs) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs,
        )
        
        self.cards: Dict[str, ToggleCard] = {}
        self._create_widgets()
        self.refresh_status()
    
    def _create_widgets(self) -> None:
        """Create page widgets."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 16))
        
        title = ctk.CTkLabel(
            header,
            text=t("privacy.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text=t("privacy.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # Apply All button
        apply_all_btn = ctk.CTkButton(
            header,
            text="🔒 Apply All Privacy Settings",
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._apply_all,
        )
        apply_all_btn.pack(anchor="w", pady=(12, 0))
        
        # Content
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        content.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        
        # Telemetry section
        self._create_section(
            content,
            t("privacy.category_telemetry"),
            [
                {
                    "id": "telemetry",
                    "title": t("privacy.disable_telemetry"),
                    "description": t("privacy.disable_telemetry_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_telemetry,
                },
                {
                    "id": "advertising_id",
                    "title": t("privacy.disable_advertising_id"),
                    "description": t("privacy.disable_advertising_id_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_advertising_id,
                },
                {
                    "id": "input_telemetry",
                    "title": t("privacy.disable_input_telemetry"),
                    "description": t("privacy.disable_input_telemetry_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_input_telemetry,
                },
                {
                    "id": "telemetry_hosts",
                    "title": t("privacy.block_telemetry_hosts"),
                    "description": t("privacy.block_telemetry_hosts_desc"),
                    "risk_level": "moderate",
                    "action": self._toggle_telemetry_hosts,
                },
            ]
        )
        
        # AI & Assistants section
        self._create_section(
            content,
            t("privacy.category_ai"),
            [
                {
                    "id": "cortana",
                    "title": t("privacy.disable_cortana"),
                    "description": t("privacy.disable_cortana_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_cortana,
                },
                {
                    "id": "copilot",
                    "title": t("privacy.disable_copilot"),
                    "description": t("privacy.disable_copilot_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_copilot,
                },
                {
                    "id": "recall",
                    "title": t("privacy.disable_recall"),
                    "description": t("privacy.disable_recall_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_recall,
                },
            ]
        )
        
        # Ads & History section
        self._create_section(
            content,
            t("privacy.category_ads"),
            [
                {
                    "id": "start_suggestions",
                    "title": t("privacy.disable_start_suggestions"),
                    "description": t("privacy.disable_start_suggestions_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_start_suggestions,
                },
                {
                    "id": "lock_screen_ads",
                    "title": t("privacy.disable_lock_screen_ads"),
                    "description": t("privacy.disable_lock_screen_ads_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_lock_screen_ads,
                },
            ]
        )
        
        # Activity & History section
        self._create_section(
            content,
            t("privacy.category_history"),
            [
                {
                    "id": "activity_history",
                    "title": t("privacy.disable_activity_history"),
                    "description": t("privacy.disable_activity_history_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_activity_history,
                },
                {
                    "id": "clipboard_sync",
                    "title": t("privacy.disable_clipboard_sync"),
                    "description": t("privacy.disable_clipboard_sync_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_clipboard_sync,
                },
            ]
        )
    
    def _create_section(
        self,
        parent: ctk.CTkFrame,
        title: str,
        items: List[Dict],
    ) -> None:
        """Create a settings section."""
        header = ctk.CTkLabel(
            parent,
            text=title,
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        header.pack(anchor="w", pady=(20, 12))
        
        for item in items:
            card = ToggleCard(
                parent,
                title=item["title"],
                description=item["description"],
                risk_level=item["risk_level"],
                initial_state=False,
                on_toggle=lambda state, a=item["action"]: a(state),
            )
            card.pack(fill="x", pady=4)
            self.cards[item["id"]] = card
    
    def refresh_status(self) -> None:
        """Refresh toggle states from system."""
        def load():
            privacy_status = privacy_manager.get_privacy_status()
            telemetry_status = telemetry_manager.get_telemetry_status()
            
            self.after(0, lambda: self._update_toggles(privacy_status, telemetry_status))
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def _update_toggles(self, privacy_status: dict, telemetry_status: dict) -> None:
        """Update toggle states."""
        # Map status to cards (True = disabled = toggle ON)
        mappings = {
            "telemetry": not telemetry_status.get("telemetry_enabled", True),
            "advertising_id": not telemetry_status.get("advertising_id_enabled", True),
            "input_telemetry": not telemetry_status.get("input_telemetry_enabled", True),
            "telemetry_hosts": telemetry_status.get("hosts_blocking_active", False),
            "cortana": not privacy_status.get("cortana_enabled", True),
            "copilot": not privacy_status.get("copilot_enabled", True),
            "recall": not privacy_status.get("recall_enabled", True),
            "activity_history": not privacy_status.get("activity_history_enabled", True),
            "start_suggestions": not privacy_status.get("start_suggestions_enabled", True),
            "lock_screen_ads": not privacy_status.get("lock_screen_ads_enabled", True),
            "clipboard_sync": not privacy_status.get("clipboard_sync_enabled", True),
        }
        
        for card_id, state in mappings.items():
            if card_id in self.cards:
                self.cards[card_id].state = state
    
    def _run_action(self, action_name: str, func, enable: bool) -> None:
        """Run a privacy action."""
        if not enable:
            return  # Only apply when enabling
        
        modal = ProgressModal(self.winfo_toplevel(), action_name)
        
        def run():
            modal.log(f"Applying {action_name}...")
            modal.set_progress(0.5)
            
            # Create backup
            backup_manager.create_backup(f"Before {action_name}")
            
            success, message = func()
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
            
            self.after(0, self.refresh_status)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def _toggle_telemetry(self, state: bool) -> None:
        self._run_action("Disable Telemetry", telemetry_manager.disable_telemetry, state)
    
    def _toggle_advertising_id(self, state: bool) -> None:
        self._run_action("Disable Advertising ID", telemetry_manager.disable_advertising_id, state)
    
    def _toggle_input_telemetry(self, state: bool) -> None:
        self._run_action("Disable Input Telemetry", telemetry_manager.disable_input_telemetry, state)
    
    def _toggle_telemetry_hosts(self, state: bool) -> None:
        self._run_action("Block Telemetry Hosts", telemetry_manager.block_telemetry_hosts, state)
    
    def _toggle_cortana(self, state: bool) -> None:
        self._run_action("Disable Cortana", privacy_manager.disable_cortana, state)
    
    def _toggle_copilot(self, state: bool) -> None:
        self._run_action("Disable Copilot", privacy_manager.disable_copilot, state)
    
    def _toggle_recall(self, state: bool) -> None:
        self._run_action("Disable Windows Recall", privacy_manager.disable_recall, state)
    
    def _toggle_activity_history(self, state: bool) -> None:
        self._run_action("Disable Activity History", privacy_manager.disable_activity_history, state)
    
    def _toggle_start_suggestions(self, state: bool) -> None:
        self._run_action("Disable Start Suggestions", privacy_manager.disable_start_suggestions, state)
    
    def _toggle_lock_screen_ads(self, state: bool) -> None:
        self._run_action("Disable Lock Screen Ads", privacy_manager.disable_lock_screen_ads, state)
    
    def _toggle_clipboard_sync(self, state: bool) -> None:
        self._run_action("Disable Clipboard Sync", privacy_manager.disable_clipboard_sync, state)
    
    def _apply_all(self) -> None:
        """Apply all privacy settings."""
        modal = ProgressModal(self.winfo_toplevel(), "Apply All Privacy Settings")
        
        def run():
            modal.log("Creating backup...")
            backup_manager.create_backup("Before applying all privacy settings")
            
            modal.log("Applying all privacy settings...")
            modal.set_progress(0.5)
            
            success, message = privacy_manager.apply_all_privacy_settings()
            
            # Also apply telemetry settings
            telemetry_manager.disable_telemetry()
            telemetry_manager.disable_advertising_id()
            telemetry_manager.disable_input_telemetry()
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
            
            self.after(0, self.refresh_status)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()