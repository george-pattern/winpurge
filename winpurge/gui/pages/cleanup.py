import threading
import customtkinter as ctk

from winpurge.gui.pages.bloatware import BasePage
from winpurge.gui.components.category_frame import CategoryFrame
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.core.cleanup import CleanupManager
from winpurge.utils import get_logger


class CleanupPage(BasePage):
    """Disk cleanup page with analysis and cleanup actions."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Disk Cleanup", **kwargs)
        self.logger = get_logger(__name__)
        self.cleanup = CleanupManager()
        self.analysis_results = {}
        self._create_content()

    def _create_content(self) -> None:
        info = CategoryFrame(self.scroll_frame, category_title="Analyze & Cleanup")
        info.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        analyze_card = info.add_toggle_card(title="Analyze Disk", description="Scan known cleanup locations to estimate reclaimable space", icon="🔎")

        result_cat = CategoryFrame(self.scroll_frame, category_title="Results")
        result_cat.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        self.result_cat = result_cat

        # Select/Deselect quick actions for results
        res_actions = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        res_actions.pack(fill="x", padx=10, pady=(6, 12))

        res_select = ctk.CTkButton(res_actions, text="Select All", width=120, command=lambda: result_cat.select_all())
        res_select.pack(side="left", padx=(0, 8))

        res_deselect = ctk.CTkButton(res_actions, text="Deselect All", width=120, command=lambda: result_cat.deselect_all())
        res_deselect.pack(side="left")

        def do_analyze(_=None):
            modal = ProgressModal(self.master, title="Analyzing Disk")

            def worker():
                try:
                    res = self.cleanup.analyze_cleanup()
                    self.analysis_results = res
                    modal.log_message("Analysis complete")
                    # populate result_cat
                    result_cat.clear_cards()
                    for path, info in res.items():
                        if path == "total":
                            continue
                        title = info.get("label", path)
                        size = info.get("size_formatted", "0 B")
                        result_cat.add_toggle_card(title=title, description=f"{path} • {size}")

                    modal.set_completed(True)
                except Exception as e:
                    modal.log_message(str(e))
                    modal.set_completed(False)

            threading.Thread(target=worker, daemon=True).start()

        analyze_card.switch.configure(command=do_analyze)

        # Cleanup action
        cleanup_card = info.add_toggle_card(title="Clean Selected", description="Remove selected cleanup items", icon="🧹", risk_level="moderate")

        def do_cleanup(_=None):
            selected = result_cat.get_selected_items()
            if not selected:
                return
            modal = ProgressModal(self.master, title="Cleaning Up")

            def worker():
                total = len(selected)
                for i, name in enumerate(selected, 1):
                    modal.log_message(f"Cleaning: {name}")
                    modal.update_progress(i - 1, total, message=name)
                    try:
                        # map title back to path
                        for path, info in self.analysis_results.items():
                            if info.get("label", path) == name:
                                self.cleanup.cleanup_selected([path])
                                modal.log_message(f"Cleaned: {name}")
                                break
                    except Exception as e:
                        modal.log_message(f"Failed: {name} — {e}")
                    modal.update_progress(i, total)
                modal.set_completed(True)

            threading.Thread(target=worker, daemon=True).start()

        cleanup_card.switch.configure(command=do_cleanup)
