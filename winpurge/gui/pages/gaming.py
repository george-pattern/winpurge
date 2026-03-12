"""
WinPurge Gaming Page
Gaming optimization settings.
"""

import customtkinter as ctk
import threading
from typing import Dict, List

from winpurge.gui.theme import get_theme
from winpurge.gui.components.toggle_card import ToggleCard
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.gaming import gaming_manager
from winpurge.backup import backup_manager


class GamingPage(ctk.CTkFrame):
    """Gaming optimization page."""
    
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
            text=t("gaming.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text=t("gaming.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )
        subtitle.pack(anchor="w", pady=(4, 0))
        
        # Apply All button
        apply_all_btn = ctk.CTkButton(
            header,
            text="🎮 Apply All Gaming Optimizations",
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
        
        # Performance section
        self._create_section(
            content,
            t("gaming.category_performance"),
            [
                {
                    "id": "game_mode",
                    "title": t("gaming.enable_game_mode"),
                    "description": t("gaming.enable_game_mode_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_game_mode,
                },
                {
                    "id": "game_bar",
                    "title": t("gaming.disable_game_bar"),
                    "description": t("gaming.disable_game_bar_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_game_bar,
                },
                {
                    "id": "game_dvr",
                    "title": t("gaming.disable_game_dvr"),
                    "description": t("gaming.disable_game_dvr_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_game_dvr,
                },
                {
                    "id": "power_plan",
                    "title": t("gaming.high_performance_power"),
                    "description": t("gaming.high_performance_power_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_power_plan,
                },
                {
                    "id": "fullscreen_opt",
                    "title": t("gaming.disable_fullscreen_opt"),
                    "description": t("gaming.disable_fullscreen_opt_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_fullscreen_opt,
                },
            ]
        )
        
        # Input section
        self._create_section(
            content,
            t("gaming.category_input"),
            [
                {
                    "id": "mouse_accel",
                    "title": t("gaming.disable_mouse_accel"),
                    "description": t("gaming.disable_mouse_accel_desc"),
                    "risk_level": "safe",
                    "action": self._toggle_mouse_accel,
                },
                {
                    "id": "nagle",
                    "title": t("gaming.disable_nagle"),
                    "description": t("gaming.disable_nagle_desc"),
                    "risk_level": "moderate",
                    "action": self._toggle_nagle,
                },
            ]
        )
        
        # HAGS Info card
        self._create_info_card(content)
    
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
    
    def _create_info_card(self, parent: ctk.CTkFrame) -> None:
        """Create HAGS info card."""
        header = ctk.CTkLabel(
            parent,
            text=t("gaming.category_visuals"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        header.pack(anchor="w", pady=(20, 12))
        
        info_card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        info_card.pack(fill="x", pady=4)
        
        container = ctk.CTkFrame(info_card, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=12)
        
        ctk.CTkLabel(
            container,
            text="ℹ️ " + t("gaming.hags_info"),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            container,
            text=t("gaming.hags_info_desc"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(4, 8))
        
        ctk.CTkButton(
            container,
            text="Open Windows Graphics Settings",
            fg_color=self.theme.colors["bg_main"],
            hover_color=self.theme.colors["card_border"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._open_graphics_settings,
        ).pack(anchor="w")
    
    def _open_graphics_settings(self) -> None:
        """Open Windows graphics settings."""
        import subprocess
        subprocess.Popen(["ms-settings:display-advancedgraphics"], shell=True)
    
    def refresh_status(self) -> None:
        """Refresh toggle states from system."""
        def load():
            status = gaming_manager.get_gaming_status()
            self.after(0, lambda: self._update_toggles(status))
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def _update_toggles(self, status: dict) -> None:
        """Update toggle states."""
        mappings = {
            "game_mode": status.get("game_mode_enabled", False),
            "game_bar": status.get("game_bar_disabled", False),
            "game_dvr": status.get("game_dvr_disabled", False),
            "power_plan": status.get("high_performance_power", False),
            "fullscreen_opt": status.get("fullscreen_optimizations_disabled", False),
            "mouse_accel": status.get("mouse_acceleration_disabled", False),
        }
        
        for card_id, state in mappings.items():
            if card_id in self.cards:
                self.cards[card_id].state = state
    
    def _run_action(self, action_name: str, func, enable: bool) -> None:
        """Run a gaming action."""
        if not enable:
            return
        
        modal = ProgressModal(self.winfo_toplevel(), action_name)
        
        def run():
            modal.log(f"Applying {action_name}...")
            modal.set_progress(0.5)
            
            backup_manager.create_backup(f"Before {action_name}")
            
            success, message = func()
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
            
            self.after(0, self.refresh_status)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def _toggle_game_mode(self, state: bool) -> None:
        self._run_action("Enable Game Mode", gaming_manager.enable_game_mode, state)
    
    def _toggle_game_bar(self, state: bool) -> None:
        self._run_action("Disable Game Bar", gaming_manager.disable_game_bar, state)
    
    def _toggle_game_dvr(self, state: bool) -> None:
        self._run_action("Disable Game DVR", gaming_manager.disable_game_dvr, state)
    
    def _toggle_power_plan(self, state: bool) -> None:
        self._run_action("High Performance Power", gaming_manager.set_high_performance_power, state)
    
    def _toggle_fullscreen_opt(self, state: bool) -> None:
        self._run_action("Disable Fullscreen Optimizations", gaming_manager.disable_fullscreen_optimizations, state)
    
    def _toggle_mouse_accel(self, state: bool) -> None:
        self._run_action("Disable Mouse Acceleration", gaming_manager.disable_mouse_acceleration, state)
    
    def _toggle_nagle(self, state: bool) -> None:
        self._run_action("Disable Nagle's Algorithm", gaming_manager.disable_nagle_algorithm, state)
    
    def _apply_all(self) -> None:
        """Apply all gaming optimizations."""
        modal = ProgressModal(self.winfo_toplevel(), "Apply All Gaming Optimizations")
        
        def run():
            modal.log("Creating backup...")
            backup_manager.create_backup("Before applying all gaming optimizations")
            
            modal.log("Applying all gaming optimizations...")
            modal.set_progress(0.5)
            
            success, message = gaming_manager.apply_all_gaming_optimizations()
            
            if success:
                modal.complete(True, message)
            else:
                modal.complete(False, message)
            
            self.after(0, self.refresh_status)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()