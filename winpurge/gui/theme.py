"""
WinPurge Theme Module
Manages dark/light themes, styling, fonts, and provides
pre-mixed colors safe for CustomTkinter (no alpha hex).
"""

import customtkinter as ctk
import logging
from typing import Dict, Any, Optional, Callable, List

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

logger = logging.getLogger(__name__)


# ─── Pre-mixed Color Extensions ─────────────────────────────────────────────
# CustomTkinter does NOT support 8-digit hex colors (#RRGGBBAA).
# All colors must be strict 6-digit hex (#RRGGBB) or named colors.
# These are pre-mixed overlay colors for dark and light themes.

DARK_EXTRA_COLORS = {
    "sidebar_active_bg": "#252540",
    "sidebar_hover": "#1F1F35",
    "bg_card_hover": "#2A2A42",
    "card_border_active": "#5A4FCF",
    "bg_disabled": "#1E1E30",
    "bg_warning": "#3A2A00",
    "bg_danger": "#3A0000",
    "tooltip_bg": "#2A2A42",
    "tooltip_border": "#3A3A55",
    "tooltip_text": "#E0E0E0",
    "warning": "#FFA500",
    "input_bg": "#1E1E32",
    "input_border": "#3A3A55",
}

LIGHT_EXTRA_COLORS = {
    "sidebar_active_bg": "#E8E5F8",
    "sidebar_hover": "#F0EFF5",
    "bg_card_hover": "#F0F0FA",
    "card_border_active": "#8B7FE8",
    "bg_disabled": "#F5F5F5",
    "bg_warning": "#FFF8E1",
    "bg_danger": "#FFEBEE",
    "tooltip_bg": "#FFFFFF",
    "tooltip_border": "#E0E0E0",
    "tooltip_text": "#333333",
    "warning": "#FF9800",
    "input_bg": "#FFFFFF",
    "input_border": "#D0D0D0",
}


# ─── Font Size Map ──────────────────────────────────────────────────────────

FONT_SIZES = {
    "small": FONT_SIZE_SMALL,
    "body": FONT_SIZE_BODY,
    "header": FONT_SIZE_HEADER,
    "title": FONT_SIZE_TITLE,
}


# ─── Button Style Presets ───────────────────────────────────────────────────

def _get_button_styles(colors: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """Generate button style presets from current colors."""
    return {
        "primary": {
            "fg_color": colors["accent"],
            "hover_color": colors["accent_hover"],
            "text_color": "#FFFFFF",
        },
        "secondary": {
            "fg_color": colors["bg_card"],
            "hover_color": colors["card_border"],
            "text_color": colors["text_primary"],
            "border_width": 1,
            "border_color": colors["card_border"],
        },
        "danger": {
            "fg_color": colors["danger"],
            "hover_color": "#FF8080",
            "text_color": "#FFFFFF",
        },
        "success": {
            "fg_color": colors["success"],
            "hover_color": "#00E676",
            "text_color": "#FFFFFF",
        },
        "ghost": {
            "fg_color": "transparent",
            "hover_color": colors.get("bg_card_hover", colors["card_border"]),
            "text_color": colors["text_primary"],
            "border_width": 1,
            "border_color": colors["card_border"],
        },
        "ghost_danger": {
            "fg_color": "transparent",
            "hover_color": colors.get("bg_danger", "#3A0000"),
            "text_color": colors["danger"],
            "border_width": 1,
            "border_color": colors["danger"],
        },
    }


# ─── Theme Manager ──────────────────────────────────────────────────────────

class ThemeManager:
    """
    Singleton theme manager.

    Provides:
    - Color palette with pre-mixed overlay colors (no alpha)
    - Font helpers
    - Risk level color accessors
    - Widget style helpers
    - Theme change callback system
    """

    _instance: Optional["ThemeManager"] = None

    def __new__(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._initialized = True
        self._current_theme: str = "dark"
        self._colors: Dict[str, str] = {}
        self._callbacks: List[Callable[[str], None]] = []

        # Initialize with dark theme
        self._apply_colors("dark")
        self._setup_customtkinter()

    # ── Setup ────────────────────────────────────────────────────────────

    def _setup_customtkinter(self) -> None:
        """Configure CustomTkinter defaults."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def _apply_colors(self, theme: str) -> None:
        """Build the full color dictionary for the given theme."""
        if theme == "dark":
            base = DARK_THEME.copy()
            extra = DARK_EXTRA_COLORS
        else:
            base = LIGHT_THEME.copy()
            extra = LIGHT_EXTRA_COLORS

        # Merge: base colors + extra pre-mixed colors
        # Extra colors only fill in missing keys (don't override base)
        for key, value in extra.items():
            if key not in base:
                base[key] = value

        self._colors = base

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def colors(self) -> Dict[str, str]:
        """Get current theme colors (all 6-digit hex, no alpha)."""
        return self._colors

    @property
    def current_theme(self) -> str:
        """Get current theme name ('dark' or 'light')."""
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark."""
        return self._current_theme == "dark"

    # ── Theme Switching ──────────────────────────────────────────────────

    def set_theme(self, theme: str) -> None:
        """
        Set the application theme.

        Args:
            theme: 'dark', 'light', or 'system'.
        """
        if theme == "system":
            theme = self._detect_system_theme()

        if theme not in ("dark", "light"):
            logger.warning("Unknown theme '%s', falling back to 'dark'", theme)
            theme = "dark"

        if theme == self._current_theme:
            return

        self._current_theme = theme
        self._apply_colors(theme)

        ctk.set_appearance_mode(theme)

        # Notify listeners
        for callback in self._callbacks:
            try:
                callback(theme)
            except Exception as e:
                logger.error("Theme callback error: %s", e)

    @staticmethod
    def _detect_system_theme() -> str:
        """Detect system dark/light preference."""
        try:
            import darkdetect
            return "dark" if darkdetect.isDark() else "light"
        except ImportError:
            logger.debug("darkdetect not installed, defaulting to dark")
            return "dark"
        except Exception:
            return "dark"

    # ── Callbacks ────────────────────────────────────────────────────────

    def register_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for theme changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[str], None]) -> None:
        """Unregister a theme change callback."""
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass

    # ── Fonts ────────────────────────────────────────────────────────────

    def get_font(
        self,
        size: str = "body",
        weight: str = "normal",
    ) -> tuple:
        """
        Get a font tuple for CustomTkinter widgets.

        Args:
            size: 'small', 'body', 'header', or 'title'.
            weight: 'normal' or 'bold'.

        Returns:
            Tuple of (family, size, weight).
        """
        font_size = FONT_SIZES.get(size, FONT_SIZE_BODY)
        font_weight = "bold" if weight == "bold" else "normal"
        return (FONT_FAMILY, font_size, font_weight)

    def get_mono_font(
        self,
        size: str = "body",
        weight: str = "normal",
    ) -> tuple:
        """Get a monospace font tuple."""
        font_size = FONT_SIZES.get(size, FONT_SIZE_BODY)
        font_weight = "bold" if weight == "bold" else "normal"
        return ("Consolas", font_size, font_weight)

    # ── Risk Colors ──────────────────────────────────────────────────────

    def get_risk_colors(self, risk_level: str) -> Dict[str, str]:
        """
        Get colors for a risk level.

        Args:
            risk_level: 'safe', 'moderate', or 'advanced'.

        Returns:
            Dict with 'bg', 'fg', and optionally 'bg_light' keys.
        """
        return RISK_COLORS.get(risk_level, RISK_COLORS.get("moderate", {
            "bg": "#3A2A00",
            "fg": "#FFA500",
        }))

    # ── Color Helpers ────────────────────────────────────────────────────

    def get_color(self, key: str, fallback: str = "#888888") -> str:
        """
        Safely get a color by key with fallback.

        Args:
            key: Color key name.
            fallback: Fallback color if key not found.

        Returns:
            6-digit hex color string.
        """
        return self._colors.get(key, fallback)

    def get_status_color(self, status: str) -> str:
        """Get color for a status level."""
        status_map = {
            "success": self._colors.get("success", "#4CAF50"),
            "warning": self._colors.get("warning", "#FFA500"),
            "danger": self._colors.get("danger", "#FF6B6B"),
            "error": self._colors.get("danger", "#FF6B6B"),
            "info": self._colors.get("accent", "#6C5CE7"),
            "disabled": self._colors.get("text_disabled", "#555555"),
        }
        return status_map.get(status, self._colors.get("text_secondary", "#888888"))

    # ── Widget Style Helpers ─────────────────────────────────────────────

    def apply_card_style(self, widget: ctk.CTkFrame) -> None:
        """Apply standard card styling to a frame."""
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
        Apply preset button styling.

        Args:
            widget: Button widget.
            style: 'primary', 'secondary', 'danger', 'success', 'ghost', 'ghost_danger'.
        """
        styles = _get_button_styles(self._colors)
        config = styles.get(style, styles["primary"])
        widget.configure(corner_radius=BUTTON_RADIUS, **config)

    def get_button_style(self, style: str = "primary") -> Dict[str, Any]:
        """
        Get button style config dict for inline use.

        Args:
            style: Style preset name.

        Returns:
            Dict of kwargs for CTkButton.
        """
        styles = _get_button_styles(self._colors)
        config = styles.get(style, styles["primary"]).copy()
        config["corner_radius"] = BUTTON_RADIUS
        return config

    def get_input_style(self) -> Dict[str, Any]:
        """Get standard input field styling."""
        return {
            "fg_color": self._colors.get("input_bg", self._colors["bg_card"]),
            "border_color": self._colors.get("input_border", self._colors["card_border"]),
            "text_color": self._colors["text_primary"],
            "corner_radius": 8,
        }

    def get_scrollbar_style(self) -> Dict[str, str]:
        """Get scrollbar color config."""
        return {
            "scrollbar_button_color": self._colors.get("scrollbar", "#3A3A55"),
            "scrollbar_button_hover_color": self._colors.get("scrollbar_hover", "#4A4A65"),
        }


# ─── Module-level accessor ──────────────────────────────────────────────────

def get_theme() -> ThemeManager:
    """Get the singleton ThemeManager instance."""
    return ThemeManager()