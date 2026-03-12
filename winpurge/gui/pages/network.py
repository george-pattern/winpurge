from typing import List
import threading

from winpurge.gui.pages.bloatware import BasePage
from winpurge.gui.components.category_frame import CategoryFrame
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.core.network import NetworkManager
from winpurge.utils import get_logger


class NetworkPage(BasePage):
    """Network configuration and telemetry blocking page."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="Network Settings", **kwargs)
        self.logger = get_logger(__name__)
        self.net = NetworkManager()
        self._create_content()

    def _create_content(self) -> None:
        cat = CategoryFrame(self.scroll_frame, category_title="DNS Presets")
        cat.pack(fill="x", padx=10, pady=(0, 10))

        dns_options = [
            ("Default", None),
            ("Cloudflare (1.1.1.1)", "cloudflare"),
            ("Google (8.8.8.8)", "google"),
            ("AdGuard (94.140.14.14)", "adguard"),
            ("Quad9 (9.9.9.9)", "quad9"),
        ]

        # create a simple button for each preset
        for label, key in dns_options:
            card = cat.add_toggle_card(title=label, description="Apply this DNS preset")
            # use toggle as a quick action
            def make_action(k):
                def action(_=None):
                    if k is None:
                        return
                    modal = ProgressModal(self.master, title=f"Applying DNS: {label}")

                    def worker():
                        try:
                            self.net.apply_dns_preset(k)
                            modal.log_message(f"Applied {label}")
                            modal.set_completed(True)
                        except Exception as e:
                            modal.log_message(str(e))
                            modal.set_completed(False)

                    threading.Thread(target=worker, daemon=True).start()

                return action

            card.switch.configure(command=make_action(key))

        # Telemetry blocking
        block_cat = CategoryFrame(self.scroll_frame, category_title="Telemetry Blocking")
        block_cat.pack(fill="x", padx=10, pady=(10, 20))
        block_card = block_cat.add_toggle_card(title="Block Known Telemetry Domains", description="Add entries to hosts file to block known telemetry endpoints", icon="🔒", risk_level="moderate")

        def block_action(_=None):
            modal = ProgressModal(self.master, title="Blocking telemetry domains")

            def worker():
                try:
                    self.net.block_telemetry_domains()
                    modal.log_message("Hosts file updated")
                    modal.set_completed(True)
                except Exception as e:
                    modal.log_message(str(e))
                    modal.set_completed(False)

            threading.Thread(target=worker, daemon=True).start()

        block_card.switch.configure(command=block_action)
