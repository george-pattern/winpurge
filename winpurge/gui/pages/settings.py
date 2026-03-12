from winpurge.gui.pages.bloatware import BasePage
from winpurge.gui.components.category_frame import CategoryFrame
from winpurge.utils import get_logger, load_locale
from winpurge.gui.theme import get_theme_manager


class SettingsPage(BasePage):
    """Application settings page: language, theme, backups and about."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Settings", **kwargs)
        self.logger = get_logger(__name__)
        self.theme_mgr = get_theme_manager()
        self._create_content()

    def _create_content(self) -> None:
        lang_cat = CategoryFrame(self.scroll_frame, category_title="Language")
        lang_cat.pack(fill="x", padx=10, pady=(0, 10))
        lang_card = lang_cat.add_toggle_card(title="Language", description="Select UI language (Restart may be required)")

        # Theme toggle
        theme_cat = CategoryFrame(self.scroll_frame, category_title="Appearance")
        theme_cat.pack(fill="x", padx=10, pady=(10, 10))
        theme_card = theme_cat.add_toggle_card(title="Dark Mode", description="Toggle dark/light theme", icon="🌓")

        def toggle_theme(_=None):
            self.theme_mgr.toggle_mode()

        theme_card.switch.configure(command=toggle_theme)

        about_cat = CategoryFrame(self.scroll_frame, category_title="About")
        about_cat.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        about_card = about_cat.add_toggle_card(title="About WinPurge", description="Version 1.0.0 — MIT License", icon="ℹ️")
