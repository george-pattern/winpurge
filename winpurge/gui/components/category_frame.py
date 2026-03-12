"""
WinPurge GUI Category Frame Component
Scrollable frame for displaying toggle cards in categories.
"""

from typing import List
import customtkinter as ctk

from winpurge.gui.theme import get_theme_manager
from winpurge.gui.components.toggle_card import ToggleCard
from winpurge.constants import FONT_SIZE_HEADER


class CategoryFrame(ctk.CTkScrollableFrame):
    """Scrollable frame for displaying categorized toggle cards."""
    
    def __init__(self, parent, category_title: str = "", **kwargs):
        """
        Initialize the category frame.
        
        Args:
            parent: Parent widget.
            category_title: Title of the category.
        """
        super().__init__(parent, **kwargs)
        
        self.category_title = category_title
        self.theme = get_theme_manager()
        self.cards: List[ToggleCard] = []
        
        # Configure frame
        self.configure(
            fg_color=self.theme.get_color("BG_PRIMARY"),
            scrollbar_button_color=self.theme.get_color("ACCENT_PRIMARY")
        )
        
        # Add category title if provided
        if category_title:
            title_label = ctk.CTkLabel(
                self,
                text=category_title,
                font=("Arial", FONT_SIZE_HEADER - 4, " bold"),
                fg_color="transparent",
                text_color=self.theme.get_color("TEXT_PRIMARY")
            )
            title_label.pack(fill="x", padx=15, pady=(15, 10))
    
    def add_toggle_card(
        self,
        title: str,
        description: str = "",
        icon: str = "⚙️",
        risk_level: str = "safe",
        enabled: bool = False,
        on_toggle=None
    ) -> ToggleCard:
        """
        Add a toggle card to the category.
        
        Args:
            title: Card title.
            description: Card description.
            icon: Icon emoji.
            risk_level: Risk level.
            enabled: Initial state.
            on_toggle: Toggle callback.
        
        Returns:
            The created ToggleCard.
        """
        card = ToggleCard(
            self,
            title=title,
            description=description,
            icon=icon,
            risk_level=risk_level,
            on_toggle=on_toggle,
            enabled=enabled,
            fg_color=self.theme.get_color("BG_TERTIARY")
        )
        card.pack(fill="x", padx=15, pady=8)
        self.cards.append(card)
        
        return card
    
    def get_selected_items(self) -> List[str]:
        """
        Get all selected card titles.
        
        Returns:
            List of selected card titles.
        """
        return [card.title for card in self.cards if card.get_enabled()]
    
    def clear_cards(self) -> None:
        """Clear all cards from the frame."""
        for card in self.cards:
            card.destroy()
        self.cards.clear()

    def select_all(self) -> None:
        """Select (enable) all toggle cards in this category."""
        for card in self.cards:
            try:
                card.set_enabled(True)
            except Exception:
                pass

    def deselect_all(self) -> None:
        """Deselect (disable) all toggle cards in this category."""
        for card in self.cards:
            try:
                card.set_enabled(False)
            except Exception:
                pass
