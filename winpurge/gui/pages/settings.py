"""
WinPurge Settings Page
Application settings and preferences.
"""

import customtkinter as ctk
import threading
import webbrowser
from pathlib import Path

from winpurge.gui.theme import get_theme
from winpurge.utils import t, load_config, save_config, get_locale, LOG_FILE
from winpurge.constants import APP_VERSION, GITHUB_URL, LANGUAGES


class SettingsPage(ctk.CTkFrame):
    """Settings and preferences page."""
    
    def __init__(self, master: any, on_language_change: callable = None, **kwargs) -> None:
        self.theme = get_theme()
        
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs,
        )
        
        self.on_language_change = on_language_change
        self.config = load_config()
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create page widgets."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 16))
        
        title = ctk.CTkLabel(
            header,
            text=t("settings.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text=t("settings.description"),
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
        
        # Appearance section
        self._create_appearance_section(content)
        
        # Behavior section
        self._create_behavior_section(content)
        
        # Updates section
        self._create_updates_section(content)
        
        # About section
        self._create_about_section(content)
    
    def _create_appearance_section(self, parent: ctk.CTkFrame) -> None:
        """Create appearance settings section."""
        section_header = ctk.CTkLabel(
            parent,
            text=t("settings.appearance"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_header.pack(anchor="w", pady=(0, 12))
        
        card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        card.pack(fill="x", pady=(0, 16))
        
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=16)
        
        # Language
        lang_row = ctk.CTkFrame(container, fg_color="transparent")
        lang_row.pack(fill="x", pady=(0, 16))
        
        ctk.CTkLabel(
            lang_row,
            text=t("settings.language"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")
        
        current_lang = self.config.get("language", "en")
        lang_values = list(LANGUAGES.values())
        lang_keys = list(LANGUAGES.keys())
        current_index = lang_keys.index(current_lang) if current_lang in lang_keys else 0
        
        self.lang_dropdown = ctk.CTkOptionMenu(
            lang_row,
            values=lang_values,
            width=150,
            fg_color=self.theme.colors["bg_main"],
            button_color=self.theme.colors["accent"],
            button_hover_color=self.theme.colors["accent_hover"],
            dropdown_fg_color=self.theme.colors["bg_card"],
            command=self._on_language_select,
        )
        self.lang_dropdown.set(lang_values[current_index])
        self.lang_dropdown.pack(side="right")
        
        # Theme
        theme_row = ctk.CTkFrame(container, fg_color="transparent")
        theme_row.pack(fill="x")
        
        ctk.CTkLabel(
            theme_row,
            text=t("settings.theme"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")
        
        theme_frame = ctk.CTkFrame(theme_row, fg_color="transparent")
        theme_frame.pack(side="right")
        
        current_theme = self.config.get("theme", "dark")
        
        self.theme_var = ctk.StringVar(value=current_theme)
        
        themes = [
            ("dark", t("settings.theme_dark")),
            ("light", t("settings.theme_light")),
        ]
        
        for theme_id, theme_name in themes:
            rb = ctk.CTkRadioButton(
                theme_frame,
                text=theme_name,
                variable=self.theme_var,
                value=theme_id,
                fg_color=self.theme.colors["accent"],
                hover_color=self.theme.colors["accent_hover"],
                command=self._on_theme_change,
            )
            rb.pack(side="left", padx=(16, 0))
    
    def _create_behavior_section(self, parent: ctk.CTkFrame) -> None:
        """Create behavior settings section."""
        section_header = ctk.CTkLabel(
            parent,
            text=t("settings.behavior"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_header.pack(anchor="w", pady=(16, 12))
        
        card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        card.pack(fill="x", pady=(0, 16))
        
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=16)
        
        # Auto backup
        backup_row = ctk.CTkFrame(container, fg_color="transparent")
        backup_row.pack(fill="x")
        
        backup_left = ctk.CTkFrame(backup_row, fg_color="transparent")
        backup_left.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            backup_left,
            text=t("settings.auto_backup"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            backup_left,
            text=t("settings.auto_backup_desc"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w")
        
        self.auto_backup_switch = ctk.CTkSwitch(
            backup_row,
            text="",
            width=50,
            progress_color=self.theme.colors["accent"],
            button_color="#FFFFFF",
            fg_color=self.theme.colors["card_border"],
            command=self._on_auto_backup_change,
        )
        self.auto_backup_switch.pack(side="right")
        
        if self.config.get("auto_backup", True):
            self.auto_backup_switch.select()
    
    def _create_updates_section(self, parent: ctk.CTkFrame) -> None:
        """Create updates section."""
        section_header = ctk.CTkLabel(
            parent,
            text=t("settings.updates"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_header.pack(anchor="w", pady=(16, 12))
        
        card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        card.pack(fill="x", pady=(0, 16))
        
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=16)
        
        # Version info
        ctk.CTkLabel(
            container,
            text=t("settings.current_version", version=APP_VERSION),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")
        
        self.update_status_label = ctk.CTkLabel(
            container,
            text="",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.update_status_label.pack(anchor="w", pady=(4, 12))
        
        check_btn = ctk.CTkButton(
            container,
            text=t("settings.check_updates"),
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._check_updates,
        )
        check_btn.pack(anchor="w")
    
    def _create_about_section(self, parent: ctk.CTkFrame) -> None:
        """Create about section."""
        section_header = ctk.CTkLabel(
            parent,
            text=t("settings.about"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        )
        section_header.pack(anchor="w", pady=(16, 12))
        
        card = ctk.CTkFrame(
            parent,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme.colors["card_border"],
        )
        card.pack(fill="x", pady=(0, 16))
        
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=16)
        
        # About text
        ctk.CTkLabel(
            container,
            text=t("settings.about_text"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
            wraplength=600,
            justify="left",
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            container,
            text=t("settings.license"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_disabled"],
        ).pack(anchor="w", pady=(8, 12))
        
        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(anchor="w")
        
        github_btn = ctk.CTkButton(
            btn_frame,
            text=f"🔗 {t('settings.github')}",
            fg_color=self.theme.colors["bg_main"],
            hover_color=self.theme.colors["card_border"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=lambda: webbrowser.open(GITHUB_URL),
        )
        github_btn.pack(side="left")
        
        export_btn = ctk.CTkButton(
            btn_frame,
            text=f"📄 {t('settings.export_log')}",
            fg_color=self.theme.colors["bg_main"],
            hover_color=self.theme.colors["card_border"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self._export_log,
        )
        export_btn.pack(side="left", padx=(8, 0))
    
    def _on_language_select(self, value: str) -> None:
        """Handle language selection."""
        # Find key from value
        lang_key = None
        for key, val in LANGUAGES.items():
            if val == value:
                lang_key = key
                break
        
        if lang_key and lang_key != self.config.get("language"):
            self.config["language"] = lang_key
            save_config(self.config)
            
            # Reload locale
            get_locale().load_locale(lang_key)
            
            # Notify app
            if self.on_language_change:
                self.on_language_change(lang_key)
    
    def _on_theme_change(self) -> None:
        """Handle theme change."""
        theme = self.theme_var.get()
        
        if theme != self.config.get("theme"):
            self.config["theme"] = theme
            save_config(self.config)
            
            # Apply theme
            get_theme().set_theme(theme)
    
    def _on_auto_backup_change(self) -> None:
        """Handle auto backup toggle."""
        enabled = self.auto_backup_switch.get() == 1
        self.config["auto_backup"] = enabled
        save_config(self.config)
    
    def _check_updates(self) -> None:
        """Check for updates."""
        self.update_status_label.configure(text="Checking for updates...")
        
        def check():
            try:
                import urllib.request
                import json
                
                from winpurge.constants import GITHUB_API_RELEASES
                
                req = urllib.request.Request(
                    GITHUB_API_RELEASES,
                    headers={"User-Agent": "WinPurge"}
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data.get("tag_name", "").lstrip("v")
                    
                    if latest_version and latest_version != APP_VERSION:
                        self.after(0, lambda: self.update_status_label.configure(
                            text=t("settings.update_available", version=latest_version),
                            text_color=self.theme.colors["warning"]
                        ))
                    else:
                        self.after(0, lambda: self.update_status_label.configure(
                            text=t("settings.up_to_date"),
                            text_color=self.theme.colors["success"]
                        ))
                        
            except Exception as e:
                self.after(0, lambda: self.update_status_label.configure(
                    text=f"Could not check for updates: {e}",
                    text_color=self.theme.colors["danger"]
                ))
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()
    
    def _export_log(self) -> None:
        """Export application log."""
        from tkinter import filedialog, messagebox
        
        if not LOG_FILE.exists():
            messagebox.showwarning(t("common.warning"), "No log file found.")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="winpurge_log.txt",
        )
        
        if save_path:
            try:
                import shutil
                shutil.copy(LOG_FILE, save_path)
                messagebox.showinfo(
                    t("common.success"),
                    t("settings.log_exported", path=save_path)
                )
            except Exception as e:
                messagebox.showerror(t("common.error"), str(e))