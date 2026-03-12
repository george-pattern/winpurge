"""
WinPurge Category Frame Component
Scrollable frame containing toggle cards grouped by category.
"""

import customtkinter as ctk
from typing import Any, Callable, Dict, List, Optional

from winpurge.gui.theme import get_theme
from winpurge.gui.components.toggle_card import ToggleCard


class CategoryFrame(ctk.CTkScrollableFrame):
    """Scrollable frame with categorized toggle cards."""
    
    def __init__(
        self,
        master: any,
        items: List[Dict[str, Any]],
        on_item_toggle: Optional[Callable[[str, bool], None]] = None,
        show_toggle: bool = True,
        show_checkbox: bool = False,
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
        self.cards: Dict[str, ToggleCard] = {}
        
        self._create_cards()
    
    def _create_cards(self) -> None:
        """Create toggle cards for all items."""
        # Group items by category
        categories: Dict[str, List[Dict[str, Any]]] = {}
        
        for item in self.items:
            category = item.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # Create cards for each category
        for category, items in categories.items():
            # Category header
            header = ctk.CTkLabel(
                self,
                text=category.replace("_", " ").title(),
                font=self.theme.get_font("body", "bold"),
                text_color=self.theme.colors["text_secondary"],
                anchor="w",
            )
            header.pack(fill="x", padx=4, pady=(16, 8))
            
            # Cards
            for item in items:
                card = ToggleCard(
                    self,
                    title=item.get("display_name", item.get("name", "")),
                    description=item.get("description", ""),
                    risk_level=item.get("risk_level", "safe"),
                    initial_state=item.get("selected", False),
                    on_toggle=lambda state, i=item: self._handle_toggle(i, state),
                    icon=item.get("icon", ""),
                    show_toggle=self.show_toggle,
                    show_checkbox=self.show_checkbox,
                )
                card.pack(fill="x", padx=4, pady=4)
                
                item_id = item.get("name", item.get("id", ""))
                self.cards[item_id] = card
    
    def _handle_toggle(self, item: Dict[str, Any], state: bool) -> None:
        """Handle card toggle."""
        item_id = item.get("name", item.get("id", ""))
        
        if self.on_item_toggle:
            self.on_item_toggle(item_id, state)
    
    def get_selected_items(self) -> List[str]:
        """Get list of selected item IDs."""
        return [item_id for item_id, card in self.cards.items() if card.get()]
    
    def select_all(self) -> None:
        """Select all items."""
        for card in self.cards.values():
            card.state = True
    
    def deselect_all(self) -> None:
        """Deselect all items."""
        for card in self.cards.values():
            card.state = False
    
    def set_item_state(self, item_id: str, state: bool) -> None:
        """Set state of a specific item."""
        if item_id in self.cards:
            self.cards[item_id].state = state
    
    def refresh(self, items: List[Dict[str, Any]]) -> None:
        """Refresh cards with new items."""
        # Clear existing cards
        for widget in self.winfo_children():
            widget.destroy()
        
        self.items = items
        self.cards.clear()
        self._create_cards()