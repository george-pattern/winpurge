"""
WinPurge Theme Module
Manages dark/light themes and styling.
"""

import customtkinter as ctk
from typing import Dict, Any, Optional

from winpurge.constants import (
    DARK_THEME,
    LIGHT_THEME,
    RISK_COLORS,
    FONT_FAMILY,
    FONT_FALLBACK,
    FONT_SIZE_BODY,
    FONT_SIZE_SMALL,
    FONT_SIZE_HEADER,
    FONT_SIZE_TITLE,
    CARD_RADIUS,
    BUTTON_RADIUS,
)


class ThemeManager:
    """Manages application theming."""
    
    _instance: Optional["ThemeManager"] = None
    _current_theme: str = "dark"
    _colors: Dict[str, str] = DARK_THEME.copy()
    _callbacks: list = []
    
    def __new__(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._setup_customtkinter()
    
    def _setup_customtkinter(self) -> None:
        """Configure CustomTkinter defaults."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
    
    @property
    def colors(self) -> Dict[str, str]:
        """Get current theme colors."""
        return self._colors
    
    @property
    def current_theme(self) -> str:
        """Get current theme name."""
        return self._current_theme
    
    def set_theme(self, theme: str) -> None:
        """
        Set the application theme.
        
        Args:
            theme: Theme name ('dark', 'light', or 'system').
        """
        if theme == "system":
            import darkdetect
            theme = "dark" if darkdetect.isDark() else "light"
        
        self._current_theme = theme
        self._colors = DARK_THEME.copy() if theme == "dark" else LIGHT_THEME.copy()
        
        ctk.set_appearance_mode(theme)
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(theme)
            except Exception:
                pass
    
    def register_callback(self, callback) -> None:
        """Register a callback for theme changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def unregister_callback(self, callback) -> None:
        """Unregister a theme change callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_font(self, size: str = "body", weight: str = "normal") -> tuple:
        """
        Get a font tuple for CustomTkinter.
        
        Args:
            size: Size name ('small', 'body', 'header', 'title').
            weight: Font weight ('normal', 'bold').
            
        Returns:
            Font tuple (family, size, weight).
        """
        sizes = {
            "small": FONT_SIZE_SMALL,
            "body": FONT_SIZE_BODY,
            "header": FONT_SIZE_HEADER,
            "title": FONT_SIZE_TITLE,
        }
        
        font_size = sizes.get(size, FONT_SIZE_BODY)
        font_weight = "bold" if weight == "bold" else "normal"
        
        return (FONT_FAMILY, font_size, font_weight)
    
    def get_risk_colors(self, risk_level: str) -> Dict[str, str]:
        """
        Get colors for a risk level.
        
        Args:
            risk_level: Risk level ('safe', 'moderate', 'advanced').
            
        Returns:
            Dictionary with 'bg', 'fg', and 'bg_light' colors.
        """
        return RISK_COLORS.get(risk_level, RISK_COLORS["moderate"])
    
    def apply_card_style(self, widget: ctk.CTkFrame) -> None:
        """Apply card styling to a frame widget."""
        widget.configure(
            fg_color=self._colors["bg_card"],
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=self._colors["card_border"],
        )
    
    def apply_button_style(
        self,
        widget: ctk.CTkButton,
        style: str = "primary",
    ) -> None:
        """
        Apply button styling.
        
        Args:
            widget: Button widget.
            style: Style type ('primary', 'secondary', 'danger', 'success').
        """
        styles = {
            "primary": {
                "fg_color": self._colors["accent"],
                "hover_color": self._colors["accent_hover"],
                "text_color": "#FFFFFF",
            },
            "secondary": {
                "fg_color": self._colors["bg_card"],
                "hover_color": self._colors["card_border"],
                "text_color": self._colors["text_primary"],
                "border_width": 1,
                "border_color": self._colors["card_border"],
            },
            "danger": {
                "fg_color": self._colors["danger"],
                "hover_color": "#FF8080",
                "text_color": "#FFFFFF",
            },
            "success": {
                "fg_color": self._colors["success"],
                "hover_color": "#00E676",
                "text_color": "#FFFFFF",
            },
        }
        
        style_config = styles.get(style, styles["primary"])
        widget.configure(corner_radius=BUTTON_RADIUS, **style_config)


def get_theme() -> ThemeManager:
    """Get the theme manager instance."""
    return ThemeManager()