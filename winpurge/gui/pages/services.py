from typing import List
import threading
import customtkinter as ctk

from winpurge.gui.pages.bloatware import BasePage
from winpurge.gui.components.category_frame import CategoryFrame
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.core.services import ServicesManager
from winpurge.utils import get_logger


class ServicesPage(BasePage):
    """Windows services management page."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Services Management", **kwargs)
        self.logger = get_logger(__name__)
        self.services = ServicesManager()

        self._create_content()

    def _create_content(self) -> None:
        """Build the services UI grouped by category and allow batch operations."""
        info = CategoryFrame(self.scroll_frame, category_title="Info")
        info.pack(fill="x", padx=10, pady=(0, 10))
        info.add_toggle_card(title="Note", description="Disabling services may break features. Use with care.")

        # Quick actions (Select All / Deselect All / Refresh)
        action_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=(6, 12))

        select_all_btn = ctk.CTkButton(action_frame, text="Select All", width=120, command=lambda: svc_cat.select_all())
        select_all_btn.pack(side="left", padx=(0, 8))

        deselect_all_btn = ctk.CTkButton(action_frame, text="Deselect All", width=120, command=lambda: svc_cat.deselect_all())
        deselect_all_btn.pack(side="left", padx=(0, 8))

        def refresh_services():
            try:
                svc_cat.clear_cards()
                svc_list_local = self.services.get_all_services_status()
                for svc in svc_list_local:
                    name = svc.get("Name") or svc.get("service_name") or "Unknown"
                    desc = svc.get("display_name", "")
                    enabled = (svc.get("current_status") or "").lower() == "running"
                    svc_cat.add_toggle_card(title=name, description=desc, enabled=enabled, risk_level=svc.get("risk_level", "moderate"))
            except Exception:
                pass

        refresh_btn = ctk.CTkButton(action_frame, text="Refresh", width=120, command=refresh_services)
        refresh_btn.pack(side="left")

        # Services list
        svc_cat = CategoryFrame(self.scroll_frame, category_title="Services")
        svc_cat.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Populate using services_list.json via manager
        try:
            svc_list = self.services.get_all_services_status()
        except Exception:
            svc_list = []

        for svc in svc_list:
            name = svc.get("Name") or svc.get("service_name") or "Unknown"
            desc = svc.get("display_name", "")
            enabled = (svc.get("current_status") or "").lower() == "running" or svc.get("Status", "Stopped").lower() == "running"
            svc_cat.add_toggle_card(title=name, description=desc, enabled=enabled, risk_level=svc.get("risk_level", "moderate"))

        # Actions
        actions = CategoryFrame(self.scroll_frame, category_title="Actions")
        actions.pack(fill="x", padx=10, pady=(10, 20))
        apply_card = actions.add_toggle_card(title="Apply Changes", description="Apply enable/disable actions for selected services", icon="🔧", risk_level="advanced")

        def on_apply(_=None):
            selected = svc_cat.get_selected_items()
            if not selected:
                return
            modal = ProgressModal(self.master, title="Applying Service Changes")

            def worker():
                total = len(selected)
                for i, svc_name in enumerate(selected, 1):
                    modal.log_message(f"Processing: {svc_name}")
                    modal.update_progress(i - 1, total, message=svc_name)
                    try:
                        # toggle the service: if running -> disable, else enable
                        st = self.services.get_service_status(svc_name)
                        if st and st.get("Status", "Stopped").lower() == "running":
                            self.services.disable_service(svc_name)
                        else:
                            self.services.enable_service(svc_name)
                        modal.log_message(f"Applied: {svc_name}")
                    except Exception as e:
                        modal.log_message(f"Failed: {svc_name} — {e}")
                    modal.update_progress(i, total)

                modal.set_completed(True)

            threading.Thread(target=worker, daemon=True).start()

        apply_card.switch.configure(command=lambda: on_apply())
