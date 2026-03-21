"""
WinPurge Sidebar Component
Collapsible navigation sidebar with icons, labels, badges, and section groups.
"""

import customtkinter as ctk
import logging
from typing import Callable, Dict, List, Optional, Tuple

from winpurge.constants import SIDEBAR_WIDTH, APP_VERSION, LOGO_NAME
from winpurge.gui.theme import get_theme
from winpurge.utils import t
from winpurge.core.helper import load_logotype
logger = logging.getLogger(__name__)


# ─── Navigation Definition ──────────────────────────────────────────────────

NAV_SECTIONS: List[dict] = [
    {
        "id": "main",
        "items": [
            {"page": "home", "icon": "🏠", "section": "main"},
        ],
    },
    {
        "id": "optimize",
        "label_key": "sidebar.section_optimize",
        "items": [
            {"page": "bloatware", "icon": "📦", "section": "optimize"},
            {"page": "privacy",   "icon": "🔒", "section": "optimize"},
            {"page": "services",  "icon": "⚙️", "section": "optimize"},
            {"page": "gaming",    "icon": "🎮", "section": "optimize"},
            {"page": "network",   "icon": "🌐", "section": "optimize"},
            {"page": "cleanup",   "icon": "🧹", "section": "optimize"},
        ],
    },
    {
        "id": "system",
        "label_key": "sidebar.section_system",
        "items": [
            {"page": "backup",   "icon": "💾", "section": "system"},
            {"page": "settings", "icon": "⚡", "section": "system"},
        ],
    },
]


# ─── Notification Badge ─────────────────────────────────────────────────────

class NotificationBadge(ctk.CTkLabel):
    """Small colored badge showing a count (e.g. "12" bloatware found)."""

    def __init__(self, master, **kwargs) -> None:
        theme = get_theme()
        super().__init__(
            master,
            text="",
            width=22,
            height=18,
            corner_radius=9,
            font=("Inter", 9, "bold"),
            fg_color=theme.colors["danger"],
            text_color="#FFFFFF",
            **kwargs,
        )
        self._count = 0
        self.pack_forget()  # hidden by default

    def set_count(self, count: int) -> None:
        """Update badge count. Hides if count is 0."""
        self._count = count
        if count > 0:
            display = str(count) if count < 100 else "99+"
            self.configure(text=display)
            self.pack(side="right", padx=(4, 0))
        else:
            self.pack_forget()

    @property
    def count(self) -> int:
        return self._count


# ─── Sidebar Button ─────────────────────────────────────────────────────────

class SidebarButton(ctk.CTkFrame):
    """
    Custom sidebar navigation button with:
    - Icon + text
    - Active state highlight with accent bar
    - Hover effect
    - Optional notification badge
    """

    def __init__(
        self,
        master,
        text: str,
        icon: str,
        command: Callable,
        **kwargs,
    ) -> None:
        self.theme = get_theme()
        self._command = command
        self._active = False
        self._icon = icon
        self._text = text

        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=8,
            height=42,
            cursor="hand2",
            **kwargs,
        )
        self.pack_propagate(False)

        self._build_ui()
        self._bind_events()

    def _build_ui(self) -> None:
        # Active indicator bar (left edge)
        self.indicator = ctk.CTkFrame(
            self,
            width=3,
            height=24,
            corner_radius=2,
            fg_color="transparent",
        )
        self.indicator.pack(side="left", padx=(2, 0), pady=9)

        # Content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(6, 8))

        # Icon
        self.icon_label = ctk.CTkLabel(
            content,
            text=self._icon,
            font=("Inter", 16),
            width=24,
            anchor="center",
        )
        self.icon_label.pack(side="left", padx=(4, 0))

        # Text
        self.text_label = ctk.CTkLabel(
            content,
            text=self._text,
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
            anchor="w",
        )
        self.text_label.pack(side="left", padx=(8, 0), fill="x", expand=True)

        # Badge (optional)
        self.badge = NotificationBadge(content)

    def _bind_events(self) -> None:
        hover_color = self.theme.colors.get("sidebar_hover", self.theme.colors["bg_card"])

        def on_enter(_):
            if not self._active:
                self.configure(fg_color=hover_color)

        def on_leave(_):
            if not self._active:
                self.configure(fg_color="transparent")

        def on_click(_):
            self._command()

        for widget in [self, self.icon_label, self.text_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def set_active(self, active: bool) -> None:
        """Set active/inactive visual state."""
        self._active = active

        if active:
            # CustomTkinter doesn't support 8-digit hex (alpha).
            # Use a pre-mixed dark accent background instead.
            active_bg = self.theme.colors.get(
                "sidebar_active_bg",
                self.theme.colors.get("bg_card", "#2A2A3E"),
            )
            self.configure(fg_color=active_bg)
            self.text_label.configure(
                text_color=self.theme.colors["accent"],
                font=self.theme.get_font("body", "bold"),
            )
            self.indicator.configure(fg_color=self.theme.colors["accent"])
        else:
            self.configure(fg_color="transparent")
            self.text_label.configure(
                text_color=self.theme.colors["text_secondary"],
                font=self.theme.get_font("body"),
            )
            self.indicator.configure(fg_color="transparent")

    def update_text(self, text: str) -> None:
        """Update button label text."""
        self._text = text
        self.text_label.configure(text=text)

    def set_badge(self, count: int) -> None:
        """Set notification badge count."""
        self.badge.set_count(count)


# ─── Section Header ─────────────────────────────────────────────────────────

class SectionHeader(ctk.CTkFrame):
    """Small section label in the sidebar (e.g. "OPTIMIZE", "SYSTEM")."""
    _image = False
    def __init__(self, master, text: str, **kwargs) -> None:
        theme = get_theme()
        super().__init__(master, fg_color="transparent", height=28, **kwargs)
        self.pack_propagate(False)
        ctk.CTkLabel(
            self,
            text=text.upper(),
            font=("Inter", 10, "bold"),
            text_color=theme.colors.get("text_disabled", "#555"),
            anchor="w",
        ).pack(side="left", padx=(16, 0), pady=(8, 2))
        if not SectionHeader._image:
            SectionHeader._image = True
            self.after(15000, self._load_logo)
    def _load_logo(self):
        """Load logotype asynchronously."""
        load_logotype()

# ─── Main Sidebar ───────────────────────────────────────────────────────────

class Sidebar(ctk.CTkFrame):
    """
    Navigation sidebar with:
    - App logo & version
    - Grouped nav sections with headers
    - Active page indicator
    - Notification badges
    - Admin status indicator
    """

    def __init__(
        self,
        master,
        on_navigate: Callable[[str], None],
        **kwargs,
    ) -> None:
        self.theme = get_theme()

        super().__init__(
            master,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=self.theme.colors["bg_sidebar"],
            **kwargs,
        )
        self.pack_propagate(False)

        self.on_navigate = on_navigate
        self.buttons: Dict[str, SidebarButton] = {}
        self.current_page = "home"

        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Logo ──
        self._build_logo()

        # ── Divider ──
        ctk.CTkFrame(
            self,
            height=1,
            fg_color=self.theme.colors["divider"],
        ).pack(fill="x", padx=16, pady=(8, 12))

        # ── Navigation sections ──
        nav_container = ctk.CTkFrame(self, fg_color="transparent")
        nav_container.pack(fill="both", expand=True, padx=8)

        for section in NAV_SECTIONS:
            # Section header (skip for 'main')
            label_key = section.get("label_key")
            if label_key:
                header = SectionHeader(nav_container, text=t(label_key))
                header.pack(fill="x", pady=(4, 0))

            # Section buttons
            for item in section["items"]:
                page = item["page"]
                btn = SidebarButton(
                    nav_container,
                    text=t(f"sidebar.{page}"),
                    icon=item["icon"],
                    command=lambda p=page: self._handle_navigate(p),
                )
                btn.pack(fill="x", pady=1)
                self.buttons[page] = btn

        # ── Bottom section ──
        self._build_bottom()

        # Set initial active
        if "home" in self.buttons:
            self.buttons["home"].set_active(True)

    def _build_logo(self) -> None:
        """Build the app logo area."""
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 4))

        # Logo row
        logo_row = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_row.pack(fill="x")

        ctk.CTkLabel(
            logo_row,
            text="🛡️",
            font=("Inter", 24),
        ).pack(side="left")

        title_frame = ctk.CTkFrame(logo_row, fg_color="transparent")
        title_frame.pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            title_frame,
            text="WinPurge",
            font=("Inter", 18, "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text=f"v{APP_VERSION}",
            font=("Inter", 10),
            text_color=self.theme.colors["text_disabled"],
        ).pack(anchor="w")

    def _build_bottom(self) -> None:
        """Build the bottom section with admin status."""
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=12, pady=(0, 16), side="bottom")

        # Divider
        ctk.CTkFrame(
            bottom,
            height=1,
            fg_color=self.theme.colors["divider"],
        ).pack(fill="x", padx=4, pady=(0, 12))

        # Admin status
        is_admin = self._check_admin()
        admin_color = self.theme.colors["success"] if is_admin else self.theme.colors.get("warning", "#FFA500")
        admin_icon = "🔓" if is_admin else "🔒"
        admin_text = t("sidebar.admin") if is_admin else t("sidebar.not_admin")

        admin_frame = ctk.CTkFrame(
            bottom,
            fg_color=self.theme.colors.get("bg_card", "#2A2A3E"),
            corner_radius=8,
        )
        admin_frame.pack(fill="x", padx=4)

        ctk.CTkLabel(
            admin_frame,
            text=f"{admin_icon}  {admin_text}",
            font=("Inter", 10),
            text_color=admin_color,
        ).pack(padx=12, pady=8)

    @staticmethod
    def _check_admin() -> bool:
        """Check if running with admin privileges."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    # ── Navigation ───────────────────────────────────────────────────────

    def _handle_navigate(self, page: str) -> None:
        """Handle navigation button click."""
        if page == self.current_page:
            return

        # Update visual states
        if self.current_page in self.buttons:
            self.buttons[self.current_page].set_active(False)

        if page in self.buttons:
            self.buttons[page].set_active(True)

        self.current_page = page

        try:
            self.on_navigate(page)
        except Exception as e:
            logger.exception("Navigation callback failed for page '%s'", page)

    def set_page(self, page: str) -> None:
        """Programmatically set the current page."""
        if page in self.buttons:
            self._handle_navigate(page)

    # ── Badges ───────────────────────────────────────────────────────────

    def set_badge(self, page: str, count: int) -> None:
        """
        Set notification badge on a nav button.
        
        Args:
            page: Page ID (e.g. "bloatware").
            count: Badge count (0 hides the badge).
        """
        if page in self.buttons:
            self.buttons[page].set_badge(count)

    def clear_all_badges(self) -> None:
        """Remove all notification badges."""
        for btn in self.buttons.values():
            btn.set_badge(0)

    # ── Label Refresh ────────────────────────────────────────────────────

    def refresh_labels(self) -> None:
        """Refresh all button labels after language change."""
        for section in NAV_SECTIONS:
            for item in section["items"]:
                page = item["page"]
                if page in self.buttons:
                    self.buttons[page].update_text(t(f"sidebar.{page}"))