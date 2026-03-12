import threading

from winpurge.gui.pages.bloatware import BasePage
from winpurge.gui.components.category_frame import CategoryFrame
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.core.gaming import GamingManager
from winpurge.utils import get_logger


class GamingPage(BasePage):
    """Gaming optimizations page offering toggles for common tweaks."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Gaming Optimization", **kwargs)
        self.logger = get_logger(__name__)
        self.gaming = GamingManager()
        self._create_content()

    def _create_content(self) -> None:
        cat = CategoryFrame(self.scroll_frame, category_title="Gaming Tweaks")
        cat.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        opts = [
            ("Enable Game Mode", "Turns on Game Mode", "safe"),
            ("Disable Game Bar", "Disable overlay and DVR", "safe"),
            ("High Performance Power Plan", "Set High Performance power plan", "moderate"),
            ("Disable Nagle", "Lower network latency for games", "moderate"),
            ("Disable Mouse Acceleration", "Improve aiming precision", "safe"),
            ("Disable Fullscreen Optimizations", "Avoid compatibility fullscreen optimizations", "moderate"),
        ]

        for title, desc, risk in opts:
            card = cat.add_toggle_card(title=title, description=desc, risk_level=risk)

        apply_cat = CategoryFrame(self.scroll_frame, category_title="Actions")
        apply_cat.pack(fill="x", padx=10, pady=(10, 20))
        apply_card = apply_cat.add_toggle_card(title="Apply Selected", description="Apply selected gaming tweaks", icon="🎮", risk_level="moderate")

        def on_apply(_=None):
            selected = cat.get_selected_items()
            if not selected:
                return
            modal = ProgressModal(self.master, title="Applying Gaming Tweaks")

            def worker():
                total = len(selected)
                for i, item in enumerate(selected, 1):
                    modal.log_message(f"Applying: {item}")
                    modal.update_progress(i - 1, total, message=item)
                    try:
                        if item == "Enable Game Mode":
                            self.gaming.enable_game_mode()
                        elif item == "Disable Game Bar":
                            self.gaming.disable_game_bar()
                        elif item == "High Performance Power Plan":
                            self.gaming.set_high_performance()
                        elif item == "Disable Nagle":
                            self.gaming.disable_nagle()
                        elif item == "Disable Mouse Acceleration":
                            self.gaming.disable_mouse_acceleration()
                        elif item == "Disable Fullscreen Optimizations":
                            self.gaming.disable_fullscreen_optimizations()
                        modal.log_message(f"Applied: {item}")
                    except Exception as e:
                        modal.log_message(f"Failed: {item} — {e}")
                    modal.update_progress(i, total)

                modal.set_completed(True)

            threading.Thread(target=worker, daemon=True).start()

        apply_card.switch.configure(command=on_apply)
