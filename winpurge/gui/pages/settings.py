"""
WinPurge Settings Page
Application settings, preferences, updates, and about info.
"""

import customtkinter as ctk
import threading
import webbrowser
import logging
import shutil
from pathlib import Path
from typing import Dict, Optional
from winpurge.gui.pages.backup import ConfirmDialog
from winpurge.gui.theme import get_theme
from winpurge.utils import t, load_config, save_config, get_locale, LOG_FILE
from winpurge.constants import APP_VERSION, GITHUB_URL, LANGUAGES, LOGO_NAME

logger = logging.getLogger(__name__)


# ─── Setting Row Components ─────────────────────────────────────────────────

class SettingRow(ctk.CTkFrame):
    """Base row for a single setting: label on left, control on right."""

    def __init__(
        self,
        master,
        label: str,
        description: str = "",
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", pady=6)

        ctk.CTkLabel(
            left,
            text=label,
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")

        if description:
            ctk.CTkLabel(
                left,
                text=description,
                font=self.theme.get_font("small"),
                text_color=self.theme.colors["text_secondary"],
                wraplength=400,
            ).pack(anchor="w")

        # Subclasses add controls to column 1
        self._control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._control_frame.grid(row=0, column=1, sticky="e", padx=(16, 0), pady=6)

    @property
    def control_frame(self) -> ctk.CTkFrame:
        return self._control_frame


class DropdownRow(SettingRow):
    """Setting row with dropdown menu."""

    def __init__(
        self,
        master,
        label: str,
        description: str,
        values: list,
        current: str,
        on_change: callable,
        **kwargs,
    ) -> None:
        super().__init__(master, label=label, description=description, **kwargs)
        self.theme = get_theme()

        self.dropdown = ctk.CTkOptionMenu(
            self.control_frame,
            values=values,
            width=160,
            height=32,
            fg_color=self.theme.colors.get("bg_main", "#1A1A2E"),
            button_color=self.theme.colors["accent"],
            button_hover_color=self.theme.colors["accent_hover"],
            dropdown_fg_color=self.theme.colors["bg_card"],
            dropdown_hover_color=self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"]),
            dropdown_text_color=self.theme.colors["text_primary"],
            text_color=self.theme.colors["text_primary"],
            command=on_change,
        )
        self.dropdown.set(current)
        self.dropdown.pack()


class SwitchRow(SettingRow):
    """Setting row with toggle switch."""

    def __init__(
        self,
        master,
        label: str,
        description: str,
        initial: bool,
        on_change: callable,
        **kwargs,
    ) -> None:
        super().__init__(master, label=label, description=description, **kwargs)
        self.theme = get_theme()

        self.switch = ctk.CTkSwitch(
            self.control_frame,
            text="",
            width=50,
            progress_color=self.theme.colors["accent"],
            button_color="#FFFFFF",
            fg_color=self.theme.colors["card_border"],
            command=on_change,
        )
        if initial:
            self.switch.select()
        self.switch.pack()

    @property
    def is_on(self) -> bool:
        return self.switch.get() == 1


class RadioRow(SettingRow):
    """Setting row with radio buttons."""

    def __init__(
        self,
        master,
        label: str,
        description: str,
        options: list,  # [(value, display), ...]
        current: str,
        on_change: callable,
        **kwargs,
    ) -> None:
        super().__init__(master, label=label, description=description, **kwargs)
        self.theme = get_theme()

        self.var = ctk.StringVar(value=current)

        for value, display in options:
            ctk.CTkRadioButton(
                self.control_frame,
                text=display,
                variable=self.var,
                value=value,
                fg_color=self.theme.colors["accent"],
                hover_color=self.theme.colors["accent_hover"],
                text_color=self.theme.colors["text_primary"],
                command=on_change,
            ).pack(side="left", padx=(12, 0))

    @property
    def value(self) -> str:
        return self.var.get()


# ─── Settings Section Card ──────────────────────────────────────────────────

class SettingsCard(ctk.CTkFrame):
    """Card container for a group of settings rows."""

    def __init__(self, master, **kwargs) -> None:
        theme = get_theme()
        super().__init__(
            master,
            fg_color=theme.colors["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=theme.colors["card_border"],
            **kwargs,
        )

        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(fill="x", padx=20, pady=16)

    def add_separator(self) -> None:
        theme = get_theme()
        ctk.CTkFrame(
            self.inner,
            fg_color=theme.colors["card_border"],
            height=1,
        ).pack(fill="x", pady=8)


# ─── Update Status Widget ───────────────────────────────────────────────────

class UpdateChecker(ctk.CTkFrame):
    """Update check UI with status display."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        # Version
        ctk.CTkLabel(
            self,
            text=f"📦  {t('settings.current_version', version=APP_VERSION)}",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")

        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_secondary"],
        )
        self.status_label.pack(anchor="w", pady=(4, 0))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=(10, 0))

        self.check_btn = ctk.CTkButton(
            btn_frame,
            text=f"🔍  {t('settings.check_updates')}",
            height=34,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            command=self._check,
        )
        self.check_btn.pack(side="left")

        self.download_btn = ctk.CTkButton(
            btn_frame,
            text=f"📥  {t('settings.download_update')}",
            height=34,
            fg_color=self.theme.colors["success"],
            hover_color="#00E676",
            command=lambda: webbrowser.open(f"{GITHUB_URL}/releases/latest"),
        )
        # Hidden until update found

    def _check(self) -> None:
        self.check_btn.configure(state="disabled")
        self.status_label.configure(
            text=f"⏳  {t('settings.checking_updates')}",
            text_color=self.theme.colors["text_secondary"],
        )

        def _worker():
            try:
                import urllib.request
                import json
                from winpurge.constants import GITHUB_API_RELEASES

                req = urllib.request.Request(
                    GITHUB_API_RELEASES,
                    headers={"User-Agent": "WinPurge"},
                )

                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    latest = data.get("tag_name", "").lstrip("v")

                    if latest and latest != APP_VERSION:
                        self.after(0, lambda: self._show_update_available(latest))
                    else:
                        self.after(0, self._show_up_to_date)

            except Exception as e:
                logger.exception("Update check failed")
                self.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_update_available(self, version: str) -> None:
        self.check_btn.configure(state="normal")
        self.status_label.configure(
            text=f"🆕  {t('settings.update_available', version=version)}",
            text_color=self.theme.colors.get("warning", "#FFA500"),
        )
        self.download_btn.pack(side="left", padx=(8, 0))

    def _show_up_to_date(self) -> None:
        self.check_btn.configure(state="normal")
        self.status_label.configure(
            text=f"✅  {t('settings.up_to_date')}",
            text_color=self.theme.colors["success"],
        )

    def _show_error(self, error: str) -> None:
        self.check_btn.configure(state="normal")
        self.status_label.configure(
            text=f"❌  {t('settings.update_check_failed')}: {error}",
            text_color=self.theme.colors["danger"],
        )


# ─── Main Settings Page ─────────────────────────────────────────────────────

class SettingsPage(ctk.CTkFrame):
    """Application settings and preferences page."""

    def __init__(
        self,
        master,
        on_language_change: Optional[callable] = None,
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_language_change = on_language_change
        self.config = load_config()

        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 0))

        ctk.CTkLabel(
            header,
            text=t("settings.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=t("settings.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 0))

        # Scrollable content
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        content.pack(fill="both", expand=True, padx=32, pady=(12, 24))

        self._build_appearance(content)
        self._build_behavior(content)
        self._build_updates(content)
        self._build_data(content)
        self._build_about(content)

    # ── Appearance ───────────────────────────────────────────────────────

    def _build_appearance(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"🎨  {t('settings.appearance')}")

        card = SettingsCard(parent)
        card.pack(fill="x", pady=(0, 16))

        # Language
        current_lang = self.config.get("language", "en")
        lang_values = list(LANGUAGES.values())
        lang_keys = list(LANGUAGES.keys())
        current_idx = lang_keys.index(current_lang) if current_lang in lang_keys else 0

        DropdownRow(
            card.inner,
            label=t("settings.language"),
            description=t("settings.language_desc"),
            values=lang_values,
            current=lang_values[current_idx],
            on_change=self._on_language_select,
        ).pack(fill="x")

        card.add_separator()

        # Theme
        current_theme = self.config.get("theme", "dark")

        self.theme_radio = RadioRow(
            card.inner,
            label=t("settings.theme"),
            description=t("settings.theme_desc"),
            options=[
                ("dark", f"🌙  {t('settings.theme_dark')}"),
                ("light", f"☀️  {t('settings.theme_light')}"),
            ],
            current=current_theme,
            on_change=self._on_theme_change,
        )
        self.theme_radio.pack(fill="x")

    # ── Behavior ─────────────────────────────────────────────────────────

    def _build_behavior(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"⚙️  {t('settings.behavior')}")

        card = SettingsCard(parent)
        card.pack(fill="x", pady=(0, 16))

        # Auto backup
        self.auto_backup_row = SwitchRow(
            card.inner,
            label=t("settings.auto_backup"),
            description=t("settings.auto_backup_desc"),
            initial=self.config.get("auto_backup", True),
            on_change=self._on_auto_backup_change,
        )
        self.auto_backup_row.pack(fill="x")

        card.add_separator()

        # Confirm before actions
        self.confirm_row = SwitchRow(
            card.inner,
            label=t("settings.confirm_actions"),
            description=t("settings.confirm_actions_desc"),
            initial=self.config.get("confirm_actions", True),
            on_change=self._on_confirm_change,
        )
        self.confirm_row.pack(fill="x")

    # ── Updates ──────────────────────────────────────────────────────────

    def _build_updates(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"🔄  {t('settings.updates')}")

        card = SettingsCard(parent)
        card.pack(fill="x", pady=(0, 16))

        self.update_checker = UpdateChecker(card.inner)
        self.update_checker.pack(fill="x")

    # ── Data Management ──────────────────────────────────────────────────

    def _build_data(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"💾  {t('settings.data_management')}")

        card = SettingsCard(parent)
        card.pack(fill="x", pady=(0, 16))

        btn_frame = ctk.CTkFrame(card.inner, fg_color="transparent")
        btn_frame.pack(fill="x")

        btn_style = dict(
            height=34,
            fg_color=self.theme.colors.get("bg_main", "#1A1A2E"),
            hover_color=self.theme.colors["card_border"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
        )

        ctk.CTkButton(
            btn_frame,
            text=f"📄  {t('settings.export_log')}",
            command=self._export_log,
            **btn_style,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text=f"📋  {t('settings.open_log')}",
            command=self._open_log,
            **btn_style,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            btn_frame,
            text=f"🗑️  {t('settings.reset_settings')}",
            command=self._reset_settings,
            fg_color="transparent",
            hover_color=self.theme.colors.get("bg_danger", "#3A0000"),
            text_color=self.theme.colors["danger"],
            border_width=1,
            border_color=self.theme.colors["danger"],
            height=34,
        ).pack(side="left", padx=(8, 0))

    # ── About ────────────────────────────────────────────────────────────

    def _build_about(self, parent: ctk.CTkFrame) -> None:
        self._section_header(parent, f"ℹ️  {t('settings.about')}")

        card = SettingsCard(parent)
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card.inner,
            text=t("settings.about_text"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
            wraplength=600,
            justify="left",
        ).pack(anchor="w")

        ctk.CTkLabel(
            card.inner,
            text=t("settings.license"),
            font=self.theme.get_font("small"),
            text_color=self.theme.colors["text_disabled"],
        ).pack(anchor="w", pady=(8, 0))

        btn_frame = ctk.CTkFrame(card.inner, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=(12, 0))

        link_style = dict(
            height=34,
            fg_color=self.theme.colors.get("bg_main", "#1A1A2E"),
            hover_color=self.theme.colors["card_border"],
            border_width=1,
            border_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
        )

        ctk.CTkButton(
            btn_frame,
            text=f"🔗  {t('settings.github')}",
            command=lambda: webbrowser.open(GITHUB_URL),
            **link_style,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text=f"🐛  {t('settings.report_bug')}",
            command=lambda: webbrowser.open(f"{GITHUB_URL}/issues/new"),
            **link_style,
        ).pack(side="left", padx=(8, 0))

    # ── Section Header ───────────────────────────────────────────────────

    def _section_header(self, parent: ctk.CTkFrame, text: str) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(16, 10))

        ctk.CTkLabel(
            frame,
            text=text,
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")

        ctk.CTkFrame(
            frame,
            fg_color=self.theme.colors["card_border"],
            height=1,
        ).pack(side="left", fill="x", expand=True, padx=(12, 0), pady=1)

    # ── Event Handlers ───────────────────────────────────────────────────

    def _on_language_select(self, display_value: str) -> None:
        lang_key = None
        for key, val in LANGUAGES.items():
            if val == display_value:
                lang_key = key
                break

        if lang_key and lang_key != self.config.get("language"):
            self.config["language"] = lang_key
            save_config(self.config)

            try:
                get_locale().load_locale(lang_key)
            except Exception as e:
                logger.error("Failed to load locale %s: %s", lang_key, e)

            if self.on_language_change:
                self.on_language_change(lang_key)

    def _on_theme_change(self) -> None:
        theme = self.theme_radio.value
        if theme != self.config.get("theme"):
            self.config["theme"] = theme
            save_config(self.config)
            try:
                get_theme().set_theme(theme)
            except Exception as e:
                logger.error("Failed to set theme: %s", e)

    def _on_auto_backup_change(self) -> None:
        self.config["auto_backup"] = self.auto_backup_row.is_on
        save_config(self.config)

    def _on_confirm_change(self) -> None:
        self.config["confirm_actions"] = self.confirm_row.is_on
        save_config(self.config)

    def _export_log(self) -> None:
        from tkinter import filedialog

        if not LOG_FILE.exists():
            self._show_message("warning", t("settings.no_log_file"))
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")],
            initialfile=f"winpurge_log_{APP_VERSION}.txt",
        )

        if save_path:
            try:
                shutil.copy(LOG_FILE, save_path)
                self._show_message("info", t("settings.log_exported", path=save_path))
            except Exception as e:
                logger.exception("Log export failed")
                self._show_message("error", str(e))

    def _open_log(self) -> None:
        """Open the log file in the default text editor."""
        import subprocess

        if not LOG_FILE.exists():
            self._show_message("warning", t("settings.no_log_file"))
            return

        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", str(LOG_FILE)],
                shell=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception as e:
            logger.error("Failed to open log: %s", e)

    def _reset_settings(self) -> None:
        """Reset all settings to defaults."""
        from winpurge.gui.pages.backup import ConfirmDialog

        dialog = ConfirmDialog(
            self.winfo_toplevel(),
            title=t("settings.reset_settings"),
            message=t("settings.confirm_reset"),
            detail=t("settings.confirm_reset_detail"),
            confirm_text=f"🗑️  {t('settings.reset_settings')}",
            confirm_color=self.theme.colors["danger"],
            icon="🗑️",
            is_danger=True,
        )

        if dialog.result:
            default_config = {
                "language": "en",
                "theme": "dark",
                "auto_backup": True,
                "confirm_actions": True,
            }
            save_config(default_config)
            self.config = default_config
            self._show_message("info", t("settings.reset_complete"))

    @staticmethod
    def _show_message(level: str, message: str) -> None:
        from tkinter import messagebox
        funcs = {
            "info": messagebox.showinfo,
            "warning": messagebox.showwarning,
            "error": messagebox.showerror,
        }
        func = funcs.get(level, messagebox.showinfo)
        titles = {"info": "Info", "warning": "Warning", "error": "Error"}
        func(titles.get(level, "Info"), message)