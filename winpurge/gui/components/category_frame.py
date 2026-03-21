"""
WinPurge Category Frame Component
Scrollable frame containing toggle cards grouped by category,
with search, select/deselect, and batch state management.
"""

import customtkinter as ctk
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from winpurge.gui.theme import get_theme
from winpurge.gui.components.toggle_card import ToggleCard

logger = logging.getLogger(__name__)


# ─── Category Header ────────────────────────────────────────────────────────

class CategoryHeader(ctk.CTkFrame):
    """Section header with icon, title, count, and separator line."""

    def __init__(
        self,
        master,
        title: str,
        count: int = 0,
        icon: str = "📂",
        **kwargs,
    ) -> None:
        theme = get_theme()
        super().__init__(master, fg_color="transparent", **kwargs)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(
            left,
            text=f"{icon}  {title}",
            font=theme.get_font("body", "bold"),
            text_color=theme.colors["text_secondary"],
        ).pack(side="left")

        if count > 0:
            ctk.CTkLabel(
                left,
                text=f"({count})",
                font=theme.get_font("small"),
                text_color=theme.colors["text_disabled"],
            ).pack(side="left", padx=(6, 0))

        ctk.CTkFrame(
            self,
            fg_color=theme.colors["card_border"],
            height=1,
        ).pack(side="left", fill="x", expand=True, padx=(12, 0), pady=1)


# ─── Main Category Frame ────────────────────────────────────────────────────

class CategoryFrame(ctk.CTkScrollableFrame):
    """Scrollable frame with categorized toggle cards, search, and bulk ops."""

    def __init__(
        self,
        master,
        items: List[Dict[str, Any]],
        on_item_toggle: Optional[Callable[[str, bool], None]] = None,
        show_toggle: bool = True,
        show_checkbox: bool = False,
        category_icons: Optional[Dict[str, str]] = None,
        category_order: Optional[List[str]] = None,
        searchable: bool = False,
        **kwargs,
    ) -> None:
        self.theme = get_theme()

        super().__init__(
            master,
            fg_color="transparent",
            scrollbar_button_color=self.theme.colors["scrollbar"],
            scrollbar_button_hover_color=self.theme.colors["scrollbar_hover"],
            **kwargs,
        )

        self.items = items
        self.on_item_toggle = on_item_toggle
        self.show_toggle = show_toggle
        self.show_checkbox = show_checkbox
        self.category_icons = category_icons or {}
        self.category_order = category_order or []
        self.searchable = searchable

        self.cards: Dict[str, ToggleCard] = {}
        self._all_widgets: List[ctk.CTkBaseClass] = []
        self._search_query = ""

        self._build()

    # ── Build ────────────────────────────────────────────────────────────

    def _build(self) -> None:
        """Build all category headers and toggle cards."""
        # Group by category
        categories: Dict[str, List[Dict[str, Any]]] = {}
        for item in self.items:
            cat = item.get("category", "other")
            categories.setdefault(cat, []).append(item)

        # Sort categories
        if self.category_order:
            sorted_cats = sorted(
                categories.keys(),
                key=lambda c: (
                    self.category_order.index(c)
                    if c in self.category_order
                    else 999
                ),
            )
        else:
            sorted_cats = sorted(categories.keys())

        for cat in sorted_cats:
            items_in_cat = categories[cat]
            icon = self.category_icons.get(cat, "📂")
            display_name = cat.replace("_", " ").title()

            # Header
            header = CategoryHeader(
                self,
                title=display_name,
                count=len(items_in_cat),
                icon=icon,
            )
            header.pack(fill="x", padx=4, pady=(14, 6))
            self._all_widgets.append(header)

            # Cards
            for item in items_in_cat:
                item_id = item.get("name", item.get("id", ""))

                card = ToggleCard(
                    self,
                    title=item.get("display_name", item.get("name", "")),
                    description=item.get("description", ""),
                    risk_level=item.get("risk_level", "safe"),
                    initial_state=item.get("selected", False),
                    on_toggle=lambda state, iid=item_id: self._handle_toggle(iid, state),
                    icon=item.get("icon", ""),
                    show_toggle=self.show_toggle,
                    show_checkbox=self.show_checkbox,
                )
                card.pack(fill="x", padx=4, pady=3)
                card._item_data = item  # store reference for search
                self.cards[item_id] = card
                self._all_widgets.append(card)

    def _handle_toggle(self, item_id: str, state: bool) -> None:
        if self.on_item_toggle:
            try:
                self.on_item_toggle(item_id, state)
            except Exception as e:
                logger.error("Toggle callback error for %s: %s", item_id, e)

    # ── Public API ───────────────────────────────────────────────────────

    def get_selected_items(self) -> List[str]:
        """Get list of selected item IDs."""
        return [iid for iid, card in self.cards.items() if card.get()]

    def get_selected_count(self) -> int:
        """Get count of selected items."""
        return sum(1 for card in self.cards.values() if card.get())

    def select_all(self) -> None:
        """Select all visible items."""
        for card in self.cards.values():
            if card.winfo_ismapped():
                card.state = True

    def deselect_all(self) -> None:
        """Deselect all items."""
        for card in self.cards.values():
            card.state = False

    def select_by_risk(self, risk_level: str) -> None:
        """Select only items with the given risk level."""
        self.deselect_all()
        for card in self.cards.values():
            data = getattr(card, "_item_data", {})
            if data.get("risk_level") == risk_level:
                card.state = True

    def set_item_state(self, item_id: str, state: bool) -> None:
        """Set state of a specific item."""
        if item_id in self.cards:
            self.cards[item_id].state = state

    def get_item_state(self, item_id: str) -> Optional[bool]:
        """Get state of a specific item."""
        if item_id in self.cards:
            return self.cards[item_id].get()
        return None

    # ── Search / Filter ──────────────────────────────────────────────────

    def filter(self, query: str = "", risk_level: Optional[str] = None) -> int:
        """
        Filter visible items. Returns count of visible items.

        Args:
            query: Search query string.
            risk_level: If set, show only items with this risk level.

        Returns:
            Number of visible items.
        """
        self._search_query = query.lower()
        visible = 0

        for card in self.cards.values():
            data = getattr(card, "_item_data", {})

            match_search = not self._search_query or self._search_query in " ".join([
                data.get("name", ""),
                data.get("display_name", ""),
                data.get("description", ""),
            ]).lower()

            match_risk = risk_level is None or data.get("risk_level") == risk_level

            if match_search and match_risk:
                card.pack(fill="x", padx=4, pady=3)
                visible += 1
            else:
                card.pack_forget()

        return visible

    def clear_filter(self) -> None:
        """Show all items."""
        self._search_query = ""
        for card in self.cards.values():
            card.pack(fill="x", padx=4, pady=3)

    # ── Refresh ──────────────────────────────────────────────────────────

    def refresh(self, items: List[Dict[str, Any]]) -> None:
        """Completely rebuild with new items."""
        # Save selection state
        old_states = {iid: card.get() for iid, card in self.cards.items()}

        # Clear
        for widget in self.winfo_children():
            widget.destroy()

        self.items = items
        self.cards.clear()
        self._all_widgets.clear()

        # Rebuild
        self._build()

        # Restore selection
        for iid, state in old_states.items():
            if iid in self.cards:
                self.cards[iid].state = state

    def update_states(self, states: Dict[str, bool]) -> None:
        """Batch update multiple item states."""
        for iid, state in states.items():
            if iid in self.cards:
                self.cards[iid].state = state