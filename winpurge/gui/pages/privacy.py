from typing import Dict
import threading
import customtkinter as ctk

from winpurge.gui.pages.bloatware import BasePage
from winpurge.gui.components.category_frame import CategoryFrame
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.core.telemetry import TelemetryManager
from winpurge.core.privacy import PrivacyManager
from winpurge.utils import get_logger


class PrivacyPage(BasePage):
    """Privacy & telemetry settings page.

    Presents a set of toggleable privacy options and applies them
    through the respective manager classes using a progress modal.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Privacy & Telemetry", **kwargs)
        self.logger = get_logger(__name__)
        self.telemetry = TelemetryManager()
        self.privacy = PrivacyManager()

        self.categories: Dict[str, CategoryFrame] = {}
        self._create_content()

    def _create_content(self) -> None:
        """Build the privacy UI with toggleable options."""
        # High level privacy actions
        cat = CategoryFrame(self.scroll_frame, category_title="Privacy Options")
        cat.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.categories["privacy"] = cat

        options = [
            ("Disable Telemetry", "Turns off Windows telemetry collection", "safe"),
            ("Disable Cortana", "Disable Cortana assistant and indexing", "safe"),
            ("Disable Copilot", "Disable Windows Copilot features", "moderate"),
            ("Disable Recall", "Disable Windows Recall / AI screenshot analysis", "moderate"),
            ("Disable Activity History", "Stop publishing user activities", "safe"),
            ("Remove Start Menu Ads", "Disable Start suggestions and promoted content", "safe"),
            ("Disable Advertising ID", "Turn off advertising personalization", "safe"),
        ]

        for title, desc, risk in options:
            cat.add_toggle_card(title=title, description=desc, risk_level=risk)

        # Select / Deselect quick actions
        action_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=(6, 12))

        select_btn = ctk.CTkButton(action_frame, text="Select All", width=120, command=lambda: cat.select_all())
        select_btn.pack(side="left", padx=(0, 8))

        deselect_btn = ctk.CTkButton(action_frame, text="Deselect All", width=120, command=lambda: cat.deselect_all())
        deselect_btn.pack(side="left")

        # Action buttons
        actions = CategoryFrame(self.scroll_frame, category_title="Actions")
        actions.pack(fill="x", padx=10, pady=(10, 20))

        apply_btn = actions.add_toggle_card(title="Apply Selected",
                                            description="Apply selected privacy changes",
                                            icon="⚡",
                                            risk_level="moderate")

        # Replace toggle card with a button-like behavior
        def on_apply(_=None):
            selected = self.categories["privacy"].get_selected_items()
            if not selected:
                return

            modal = ProgressModal(self.master, title="Applying Privacy Settings")

            def worker():
                total = len(selected)
                for i, item in enumerate(selected, 1):
                    modal.log_message(f"Applying: {item}")
                    modal.update_progress(i - 1, total, message=item)
                    try:
                        # Map item to manager call
                        if item == "Disable Telemetry":
                            self.telemetry.disable_telemetry()
                        elif item == "Disable Cortana":
                            self.telemetry.disable_cortana()
                        elif item == "Disable Copilot":
                            self.telemetry.disable_copilot()
                        elif item == "Disable Recall":
                            self.telemetry.disable_recall()
                        elif item == "Disable Activity History":
                            self.telemetry.disable_activity_history()
                        elif item == "Remove Start Menu Ads":
                            self.privacy.disable_start_menu_ads()
                        elif item == "Disable Advertising ID":
                            self.privacy.disable_advertising_id()
                        modal.log_message(f"Applied: {item}")
                    except Exception as e:
                        modal.log_message(f"Failed: {item} — {e}")
                    modal.update_progress(i, total, message=f"{i}/{total}")

                modal.set_completed(True)

            threading.Thread(target=worker, daemon=True).start()

        # Wire apply behavior: the action card's switch acts as button
        # We find the last added card (apply_btn) and bind click behavior
        apply_btn.switch.configure(command=lambda: on_apply())
