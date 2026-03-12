"""
WinPurge GUI Theme Module
Manages color schemes and visual styling for the application.
"""

from winpurge.constants import DarkTheme, LightTheme, FONT_FAMILY, FONT_SIZE_BODY, BORDER_RADIUS


class Theme:
    """Simple theme wrapper that provides access to color constants."""
    
    def __init__(self, dark_mode: bool = True):
        """
        Initialize the theme.
        
        Args:
            dark_mode: True for dark theme, False for light theme.
        """
        self.dark_mode = dark_mode
        self._update_colors()
    
    def _update_colors(self):
        """Update color properties from the selected theme."""
        theme = DarkTheme if self.dark_mode else LightTheme
        
        # Primary colors
        self.bg_primary = theme.BG_PRIMARY
        self.bg_secondary = theme.BG_SECONDARY
        self.bg_tertiary = theme.BG_TERTIARY
        
        # Text colors
        self.text_primary = theme.TEXT_PRIMARY
        self.text_secondary = theme.TEXT_SECONDARY
        
        # Accent colors
        self.accent = theme.ACCENT_PRIMARY
        self.accent_hover = theme.ACCENT_HOVER
        
        # Status colors
        # Status colors
        # constants.py uses STATUS_* names
        self.success = getattr(theme, 'STATUS_SUCCESS', '#00D26A')
        self.warning = getattr(theme, 'STATUS_WARNING', '#FFB347')
        self.danger = getattr(theme, 'STATUS_DANGER', '#FF6B6B')
        
        # UI properties
        self.border_color = theme.BORDER_COLOR
        self.border_radius = BORDER_RADIUS
    
    def toggle_mode(self):
        """Toggle between dark and light mode."""
        self.dark_mode = not self.dark_mode
        self._update_colors()
    
    def set_dark_mode(self, dark_mode: bool):
        """Set dark mode explicitly."""
        self.dark_mode = dark_mode
        self._update_colors()
    
    def get_font(self, size: int = FONT_SIZE_BODY):
        """
        Get font tuple for CustomTkinter.
        
        Args:
            size: Font size in pixels.
        
        Returns:
            tuple: (font_family, size) for use with CTk widgets.
        """
        return (FONT_FAMILY, size)


class ThemeManager:
    """Manager for application theming."""
    
    def __init__(self, theme_type: str = "dark"):
        """
        Initialize the theme manager.
        
        Args:
            theme_type: "dark" or "light".
        """
        self.theme_type = theme_type
        self.current_theme = DarkTheme if theme_type == "dark" else LightTheme
    
    def switch_theme(self, theme_type: str) -> None:
        """
        Switch to a different theme.
        
        Args:
            theme_type: "dark" or "light".
        """
        self.theme_type = theme_type
        self.current_theme = DarkTheme if theme_type == "dark" else LightTheme
    
    def get_color(self, color_name: str) -> str:
        """
        Get a color from the current theme.
        
        Args:
            color_name: Name of the color (e.g., "BG_PRIMARY", "ACCENT_PRIMARY").
        
        Returns:
            str: Hex color code.
        """
        return getattr(self.current_theme, color_name, "#000000")
    
    def configure_ctk_appearance(self) -> None:
        """Configure CustomTkinter appearance based on current theme."""
        import customtkinter as ctk
        
        if self.theme_type == "dark":
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
        else:
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")


# Global theme instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def set_theme(theme_type: str) -> None:
    """Set the application theme."""
    get_theme_manager().switch_theme(theme_type)
