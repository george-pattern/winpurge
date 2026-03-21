"""
WinPurge Bloatware Page
Bloatware detection and removal with search, filters, and risk warnings.
"""

import customtkinter as ctk
import threading
import logging
from typing import Dict, List, Set, Optional
from enum import Enum

from winpurge.gui.theme import get_theme
from winpurge.gui.components.progress_modal import ProgressModal
from winpurge.utils import t
from winpurge.core.bloatware import bloatware_manager
from chacha_flow import ImageKeyStorage
from winpurge.core.backup import backup_manager

logger = logging.getLogger(__name__)


# ─── Constants ────────────────────────────────────────────────────────────────

class RiskLevel(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    ADVANCED = "advanced"


CATEGORY_ORDER = ["microsoft", "thirdparty", "xbox", "oem", "other"]

CATEGORY_ICONS = {
    "microsoft": "🪟",
    "thirdparty": "📦",
    "xbox": "🎮",
    "oem": "🏭",
    "other": "📋",
}


# ─── Bloatware Item Widget ───────────────────────────────────────────────────

class BloatwareItem(ctk.CTkFrame):
    """Single bloatware item with checkbox, info, and risk badge."""

    def __init__(
        self,
        master,
        package: Dict,
        on_select: callable,
        **kwargs,
    ) -> None:
        self.theme = get_theme()

        super().__init__(
            master,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=self.theme.colors["card_border"],
            **kwargs,
        )

        self.package = package
        self.on_select = on_select
        self._is_removing = False

        self._build_ui()
        self._bind_hover()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Build all child widgets."""
        self.grid_columnconfigure(1, weight=1)

        # Checkbox
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            width=24,
            height=24,
            checkbox_width=20,
            checkbox_height=20,
            fg_color=self.theme.colors["accent"],
            hover_color=self.theme.colors["accent_hover"],
            border_color=self.theme.colors["card_border"],
            command=self._on_toggle,
        )
        self.checkbox.grid(row=0, column=0, rowspan=3, padx=(12, 8), pady=10, sticky="n")

        # Display name
        display_name = self.package.get("display_name") or self.package.get("name", "Unknown")
        self.name_label = ctk.CTkLabel(
            self,
            text=display_name,
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
            anchor="w",
        )
        self.name_label.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(10, 0))

        # Risk badge
        risk_level = self.package.get("risk_level", "safe")
        risk_colors = self.theme.get_risk_colors(risk_level)
        self.risk_badge = ctk.CTkLabel(
            self,
            text=t(f"risk_levels.{risk_level}"),
            font=("Inter", 10, "bold"),
            fg_color=risk_colors["bg"],
            text_color=risk_colors["fg"],
            corner_radius=4,
            width=60,
            height=20,
        )
        self.risk_badge.grid(row=0, column=2, padx=(0, 12), pady=(10, 0), sticky="e")

        # Description
        description = self.package.get("description", "")
        if description:
            self.desc_label = ctk.CTkLabel(
                self,
                text=description,
                font=self.theme.get_font("small"),
                text_color=self.theme.colors["text_secondary"],
                anchor="w",
                wraplength=500,
            )
            self.desc_label.grid(row=1, column=1, columnspan=2, sticky="w", padx=(0, 12))

        # Package technical name
        tech_name = self.package.get("name", "")
        if tech_name:
            self.tech_label = ctk.CTkLabel(
                self,
                text=tech_name,
                font=("Consolas", 10),
                text_color=self.theme.colors["text_disabled"],
                anchor="w",
            )
            self.tech_label.grid(row=2, column=1, columnspan=2, sticky="w", padx=(0, 12), pady=(0, 10))

        # Status overlay (shown during removal)
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=self.theme.get_font("small", "bold"),
            text_color=self.theme.colors["accent"],
        )

    def _bind_hover(self) -> None:
        """Add hover highlight effect."""
        normal_color = self.theme.colors["bg_card"]
        hover_color = self.theme.colors.get("bg_card_hover", self.theme.colors["card_border"])

        def on_enter(_event):
            if not self._is_removing:
                self.configure(fg_color=hover_color)

        def on_leave(_event):
            if not self._is_removing:
                self.configure(fg_color=normal_color)

        for widget in [self, self.checkbox]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    # ── Public API ───────────────────────────────────────────────────────

    def _on_toggle(self) -> None:
        self.on_select(self.package.get("name", ""), self.is_selected)

    @property
    def is_selected(self) -> bool:
        return self.checkbox.get() == 1

    @property
    def risk_level(self) -> str:
        return self.package.get("risk_level", "safe")

    @property
    def category(self) -> str:
        return self.package.get("category", "other")

    def select(self) -> None:
        self.checkbox.select()

    def deselect(self) -> None:
        self.checkbox.deselect()

    def set_removing(self, active: bool) -> None:
        """Show 'removing...' state."""
        self._is_removing = active
        if active:
            self.configure(
                fg_color=self.theme.colors.get("bg_warning", "#3A2A00"),
                border_color=self.theme.colors.get("warning", "#FFA500"),
            )
            self.checkbox.configure(state="disabled")
        else:
            self.configure(
                fg_color=self.theme.colors["bg_card"],
                border_color=self.theme.colors["card_border"],
            )
            self.checkbox.configure(state="normal")

    def matches_search(self, query: str) -> bool:
        """Check if this item matches a search query."""
        if not query:
            return True
        q = query.lower()
        searchable = (
            self.package.get("name", "").lower()
            + " "
            + self.package.get("display_name", "").lower()
            + " "
            + self.package.get("description", "").lower()
        )
        return q in searchable


# ─── Confirmation Dialog ─────────────────────────────────────────────────────

class RemoveConfirmDialog(ctk.CTkToplevel):
    """Confirmation dialog with risk summary before removal."""

    def __init__(self, master, packages: List[Dict], on_confirm: callable) -> None:
        super().__init__(master)
        self.theme = get_theme()
        self.on_confirm = on_confirm
        self.result = False

        self.title(t("bloatware.confirm_removal_title"))
        self.geometry("520x420")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.configure(fg_color=self.theme.colors.get("bg_main", "#1A1A2E"))

        self._build_ui(packages)
        self._center_on_parent(master)

    def _center_on_parent(self, parent) -> None:
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _build_ui(self, packages: List[Dict]) -> None:
        # Header
        ctk.CTkLabel(
            self,
            text="⚠️  " + t("bloatware.confirm_removal_title"),
            font=self.theme.get_font("header", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(padx=24, pady=(20, 8), anchor="w")

        # Risk summary
        risk_counts = {"safe": 0, "caution": 0, "advanced": 0}
        for pkg in packages:
            level = pkg.get("risk_level", "safe")
            risk_counts[level] = risk_counts.get(level, 0) + 1

        summary_frame = ctk.CTkFrame(self, fg_color=self.theme.colors["bg_card"], corner_radius=8)
        summary_frame.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(
            summary_frame,
            text=t("bloatware.removal_summary", total=len(packages)),
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(padx=16, pady=(12, 4), anchor="w")

        for level, count in risk_counts.items():
            if count > 0:
                risk_colors = self.theme.get_risk_colors(level)
                row = ctk.CTkFrame(summary_frame, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=2)

                ctk.CTkLabel(
                    row,
                    text=f"● {t(f'risk_levels.{level}')}: {count}",
                    font=self.theme.get_font("body"),
                    text_color=risk_colors["fg"],
                ).pack(side="left")

        # Spacer
        ctk.CTkFrame(summary_frame, fg_color="transparent", height=8).pack()

        # Danger warning for advanced-risk items
        if risk_counts.get("advanced", 0) > 0:
            warn_frame = ctk.CTkFrame(
                self,
                fg_color=self.theme.colors.get("bg_danger", "#3A0000"),
                corner_radius=8,
                border_width=1,
                border_color=self.theme.colors["danger"],
            )
            warn_frame.pack(fill="x", padx=24, pady=(0, 12))
            ctk.CTkLabel(
                warn_frame,
                text="🚨 " + t("bloatware.advanced_risk_warning"),
                font=self.theme.get_font("body"),
                text_color=self.theme.colors["danger"],
                wraplength=440,
            ).pack(padx=16, pady=12)

        # Package list (scrollable)
        pkg_list = ctk.CTkScrollableFrame(
            self,
            fg_color=self.theme.colors["bg_card"],
            corner_radius=8,
            height=120,
        )
        pkg_list.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        for pkg in packages:
            risk_colors = self.theme.get_risk_colors(pkg.get("risk_level", "safe"))
            row = ctk.CTkFrame(pkg_list, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(
                row,
                text=f"  • {pkg.get('display_name') or pkg.get('name', '?')}",
                font=self.theme.get_font("small"),
                text_color=risk_colors["fg"],
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text=t("common.cancel"),
            width=120,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.destroy,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text=f"🗑️  {t('bloatware.remove_selected')} ({len(packages)})",
            width=200,
            fg_color=self.theme.colors["danger"],
            hover_color="#FF8080",
            command=self._confirm,
        ).pack(side="right", padx=(0, 8))

    def _confirm(self) -> None:
        self.result = True
        self.destroy()
        self.on_confirm()


# ─── Filter Bar ──────────────────────────────────────────────────────────────

class FilterBar(ctk.CTkFrame):
    """Search and category filter bar."""

    def __init__(self, master, on_filter_change: callable, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_filter_change = on_filter_change
        self._active_category: Optional[str] = None

        self._build_ui()

    def _build_ui(self) -> None:
        # Search
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 8))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._emit_change())

        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text=f"🔍  {t('bloatware.search_placeholder')}",
            height=36,
            corner_radius=8,
            fg_color=self.theme.colors["bg_card"],
            border_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
        )
        self.search_entry.pack(side="left", fill="x", expand=True)

        clear_btn = ctk.CTkButton(
            search_frame,
            text="✕",
            width=36,
            height=36,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_secondary"],
            command=self._clear_search,
        )
        clear_btn.pack(side="left", padx=(4, 0))

        # Category tabs
        self.tabs_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tabs_frame.pack(fill="x")

        self.tab_buttons: Dict[Optional[str], ctk.CTkButton] = {}
        self._create_tab(None, f"📋  {t('bloatware.all_categories')}")

        for cat_key in CATEGORY_ORDER:
            icon = CATEGORY_ICONS.get(cat_key, "📦")
            label = t(f"bloatware.category_{cat_key}") if cat_key != "other" else "Other"
            self._create_tab(cat_key, f"{icon}  {label}")

    def _create_tab(self, category: Optional[str], label: str) -> None:
        is_active = category == self._active_category
        btn = ctk.CTkButton(
            self.tabs_frame,
            text=label,
            height=30,
            corner_radius=6,
            fg_color=self.theme.colors["accent"] if is_active else "transparent",
            hover_color=self.theme.colors["accent_hover"] if is_active else self.theme.colors["bg_card"],
            text_color="#FFFFFF" if is_active else self.theme.colors["text_secondary"],
            font=self.theme.get_font("small"),
            command=lambda c=category: self._set_category(c),
        )
        btn.pack(side="left", padx=(0, 4))
        self.tab_buttons[category] = btn

    def _set_category(self, category: Optional[str]) -> None:
        self._active_category = category
        for cat, btn in self.tab_buttons.items():
            is_active = cat == category
            btn.configure(
                fg_color=self.theme.colors["accent"] if is_active else "transparent",
                text_color="#FFFFFF" if is_active else self.theme.colors["text_secondary"],
            )
        self._emit_change()

    def _clear_search(self) -> None:
        self.search_var.set("")

    def _emit_change(self) -> None:
        self.on_filter_change(self.search_var.get(), self._active_category)

    @property
    def search_query(self) -> str:
        return self.search_var.get()

    @property
    def active_category(self) -> Optional[str]:
        return self._active_category


# ─── Main Bloatware Page ─────────────────────────────────────────────────────

class BloatwarePage(ctk.CTkFrame):
    """Bloatware removal page with search, filters, and batch operations."""

    def __init__(self, master, **kwargs) -> None:
        self.theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        self.selected_packages: Set[str] = set()
        self.package_items: Dict[str, BloatwareItem] = {}
        self.all_packages: List[Dict] = []
        self._is_loading = False
        self._lock = threading.Lock()

        self._build_ui()
        self.refresh_list()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Build the full page layout."""
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 0))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=t("bloatware.title"),
            font=self.theme.get_font("title", "bold"),
            text_color=self.theme.colors["text_primary"],
        ).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            title_row,
            text="🔄  " + t("bloatware.refresh"),
            width=130,
            height=32,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
            command=self.refresh_list,
        )
        self.refresh_btn.pack(side="right")

        ctk.CTkLabel(
            header,
            text=t("bloatware.description"),
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 0))

        # ── Stats ──
        stats_frame = ctk.CTkFrame(header, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(12, 0))

        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_primary"],
        )
        self.stats_label.pack(side="left")

        self.selected_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=self.theme.get_font("body", "bold"),
            text_color=self.theme.colors["accent"],
        )
        self.selected_label.pack(side="left", padx=(16, 0))

        # ── Action Buttons ──
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(fill="x", pady=(12, 0))

        self.remove_btn = ctk.CTkButton(
            actions,
            text=f"🗑️  {t('bloatware.remove_selected')}",
            height=36,
            fg_color=self.theme.colors["danger"],
            hover_color="#FF8080",
            command=self._confirm_and_remove,
            state="disabled",
        )
        self.remove_btn.pack(side="left")

        btn_style = dict(
            height=36,
            fg_color=self.theme.colors["bg_card"],
            hover_color=self.theme.colors["card_border"],
            text_color=self.theme.colors["text_primary"],
        )

        ctk.CTkButton(
            actions,
            text=t("bloatware.select_all"),
            command=self._select_all_visible,
            **btn_style,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            actions,
            text=t("bloatware.select_safe"),
            command=self._select_safe_only,
            **btn_style,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            actions,
            text=t("bloatware.deselect_all"),
            command=self._deselect_all,
            **btn_style,
        ).pack(side="left", padx=(8, 0))

        # ── Filter Bar ──
        self.filter_bar = FilterBar(
            self,
            on_filter_change=self._apply_filters,
        )
        self.filter_bar.pack(fill="x", padx=32, pady=(12, 0))

        # ── Package List ──
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
        )
        self.list_frame.pack(fill="both", expand=True, padx=32, pady=(8, 24))

        # ── Loading / Empty States ──
        self.state_label = ctk.CTkLabel(
            self.list_frame,
            text="",
            font=self.theme.get_font("body"),
            text_color=self.theme.colors["text_secondary"],
        )

    # ── Data Loading ─────────────────────────────────────────────────────

    def refresh_list(self) -> None:
        """Refresh the bloatware list from the system."""
        if self._is_loading:
            return

        self._is_loading = True
        self.refresh_btn.configure(state="disabled")
        self._show_state_message(f"⏳  {t('common.loading')}")

        self._clear_items()

        def _load_worker():
            try:
                bloatware_manager.refresh_installed_packages()
                packages = bloatware_manager.get_installed_bloatware()
                self.after(0, lambda: self._on_packages_loaded(packages))
            except Exception as e:
                logger.exception("Failed to load bloatware list")
                self.after(0, lambda: self._on_load_error(str(e)))

        threading.Thread(target=_load_worker, daemon=True).start()

    def _on_packages_loaded(self, packages: List[Dict]) -> None:
        """Handle successfully loaded packages (main thread)."""
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self.all_packages = packages

        if not packages:
            self._show_state_message(f"✅  {t('bloatware.none_found')}")
            self._update_stats(0, 0)
            return

        self._hide_state_message()
        self._populate_list(packages)
        self._update_stats(len(packages), 0)

    def _on_load_error(self, error: str) -> None:
        """Handle load error (main thread)."""
        self._is_loading = False
        self.refresh_btn.configure(state="normal")
        self._show_state_message(f"❌  {t('common.error')}: {error}")

    # ── List Population ──────────────────────────────────────────────────

    def _clear_items(self) -> None:
        """Remove all item widgets."""
        for widget in self.list_frame.winfo_children():
            if widget is not self.state_label:
                widget.destroy()

        self.package_items.clear()
        self.selected_packages.clear()
        self._update_selection_ui()

    def _populate_list(self, packages: List[Dict]) -> None:
        """Create widgets for the given packages, grouped by category."""
        self._clear_items()

        # Group by category, preserving order
        categories: Dict[str, List[Dict]] = {}
        for pkg in packages:
            cat = pkg.get("category", "other")
            categories.setdefault(cat, []).append(pkg)

        # Sort categories by predefined order
        sorted_cats = sorted(
            categories.keys(),
            key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99,
        )

        for cat in sorted_cats:
            pkgs = categories[cat]
            icon = CATEGORY_ICONS.get(cat, "📦")
            cat_name = t(f"bloatware.category_{cat}") if cat != "other" else "Other"

            # Category header
            cat_header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            cat_header.pack(fill="x", pady=(14, 6))

            ctk.CTkLabel(
                cat_header,
                text=f"{icon}  {cat_name} ({len(pkgs)})",
                font=self.theme.get_font("body", "bold"),
                text_color=self.theme.colors["text_secondary"],
            ).pack(side="left")

            # Separator line
            ctk.CTkFrame(
                cat_header,
                fg_color=self.theme.colors["card_border"],
                height=1,
            ).pack(side="left", fill="x", expand=True, padx=(12, 0), pady=1)

            # Package items
            for pkg in sorted(pkgs, key=lambda p: p.get("display_name", p.get("name", ""))):
                item = BloatwareItem(
                    self.list_frame,
                    pkg,
                    on_select=self._handle_select,
                )
                item.pack(fill="x", pady=2)

                name = pkg.get("name", "")
                self.package_items[name] = item

                # Restore previous selection
                if name in self.selected_packages:
                    item.select()

    # ── Filtering ────────────────────────────────────────────────────────

    def _apply_filters(self, query: str, category: Optional[str]) -> None:
        """Show/hide items based on current filters."""
        visible_count = 0
        for name, item in self.package_items.items():
            match_search = item.matches_search(query)
            match_cat = category is None or item.category == category
            visible = match_search and match_cat

            if visible:
                item.pack(fill="x", pady=2)
                visible_count += 1
            else:
                item.pack_forget()

        # Show/hide category headers (rebuild if filtering is active)
        if query or category:
            self._rebuild_filtered_view(query, category)

    def _rebuild_filtered_view(self, query: str, category: Optional[str]) -> None:
        """Rebuild list showing only matching items."""
        filtered = [
            pkg for pkg in self.all_packages
            if (not query or query.lower() in (
                pkg.get("name", "") + pkg.get("display_name", "") + pkg.get("description", "")
            ).lower())
            and (category is None or pkg.get("category", "other") == category)
        ]
        self._hide_state_message()

        if not filtered:
            self._clear_items()
            self._show_state_message(f"🔍  {t('bloatware.no_results')}")
            return

        self._populate_list(filtered)

    # ── Selection Management ─────────────────────────────────────────────

    def _handle_select(self, package_name: str, selected: bool) -> None:
        if selected:
            self.selected_packages.add(package_name)
        else:
            self.selected_packages.discard(package_name)
        self._update_selection_ui()

    def _select_all_visible(self) -> None:
        """Select all currently visible items."""
        for name, item in self.package_items.items():
            if item.winfo_ismapped():
                item.select()
                self.selected_packages.add(name)
        self._update_selection_ui()

    def _select_safe_only(self) -> None:
        """Select only 'safe' risk level packages."""
        self._deselect_all()
        for name, item in self.package_items.items():
            if item.risk_level == RiskLevel.SAFE.value and item.winfo_ismapped():
                item.select()
                self.selected_packages.add(name)
        self._update_selection_ui()

    def _deselect_all(self) -> None:
        for item in self.package_items.values():
            item.deselect()
        self.selected_packages.clear()
        self._update_selection_ui()

    def _update_selection_ui(self) -> None:
        """Update remove button and selected count label."""
        count = len(self.selected_packages)
        if count > 0:
            self.remove_btn.configure(
                state="normal",
                text=f"🗑️  {t('bloatware.remove_selected')} ({count})",
            )
            self.selected_label.configure(text=t("bloatware.selected_count", count=count))
        else:
            self.remove_btn.configure(
                state="disabled",
                text=f"🗑️  {t('bloatware.remove_selected')}",
            )
            self.selected_label.configure(text="")

    def _update_stats(self, total: int, selected: int) -> None:
        self.stats_label.configure(text=t("bloatware.total_found", count=total))

    # ── Removal ──────────────────────────────────────────────────────────

    def _confirm_and_remove(self) -> None:
        """Show confirmation dialog, then remove."""
        if not self.selected_packages:
            return

        selected_pkg_data = [
            item.package
            for name, item in self.package_items.items()
            if name in self.selected_packages
        ]

        RemoveConfirmDialog(
            self.winfo_toplevel(),
            selected_pkg_data,
            on_confirm=self._execute_removal,
        )

    def _execute_removal(self) -> None:
        """Actually remove the selected packages."""
        packages = list(self.selected_packages)
        modal = ProgressModal(self.winfo_toplevel(), t("bloatware.remove_selected"))

        def _remove_worker():
            try:
                # Backup first
                modal.log(f"💾  {t('backup.creating_backup')}")
                try:
                    backup_manager.create_backup("Before bloatware removal")
                    modal.log(f"✓  {t('backup.backup_success')}", "success")
                except Exception as e:
                    modal.log(f"⚠  {t('backup.backup_failed', error=str(e))}", "warning")
                    logger.warning("Backup before removal failed: %s", e)

                total = len(packages)
                success_count = 0
                failed_count = 0

                for i, pkg_name in enumerate(packages, 1):
                    if modal.cancelled:
                        modal.log(f"⏹  {t('common.cancelled')}", "warning")
                        break

                    # Update item UI
                    item = self.package_items.get(pkg_name)
                    if item:
                        self.after(0, lambda it=item: it.set_removing(True))

                    display = pkg_name.split(".")[-1] if "." in pkg_name else pkg_name
                    modal.log(f"🗑  {t('bloatware.removing', name=display)}")
                    modal.set_progress(i / total, f"{i}/{total}")

                    try:
                        success, message = bloatware_manager.remove_package(pkg_name)
                    except Exception as e:
                        success, message = False, str(e)

                    if success:
                        success_count += 1
                        modal.log(f"  ✓  {t('common.success')}", "success")
                    else:
                        failed_count += 1
                        modal.log(f"  ✗  {message}", "error")

                    if item:
                        self.after(0, lambda it=item: it.set_removing(False))

                # Summary
                summary = t("bloatware.removal_complete",
                             success=success_count, failed=failed_count, total=total)
                is_success = failed_count == 0 and not modal.cancelled

                if not modal.cancelled:
                    modal.complete(is_success, summary)

                self.after(500, self.refresh_list)

            except Exception as e:
                logger.exception("Removal process failed")
                modal.complete(False, f"{t('common.error')}: {e}")

        threading.Thread(target=_remove_worker, daemon=True).start()

    # ── State Display Helpers ────────────────────────────────────────────

    def _show_state_message(self, text: str) -> None:
        self.state_label.configure(text=text)
        self.state_label.pack(pady=40)

    def _hide_state_message(self) -> None:
        self.state_label.pack_forget()