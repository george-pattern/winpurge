"""
WinPurge Constants Module
Centralized configuration and theme colors for the application.
"""

import os
from pathlib import Path
from typing import Dict, Tuple

# Application Info
APP_NAME: str = "WinPurge"
APP_VERSION: str = "1.0.0"
APP_AUTHOR: str = "WinPurge Team"
APP_LICENSE: str = "MIT"
APP_GITHUB: str = "https://github.com/example/WinPurge"

# Paths
APPDATA_DIR: Path = Path(os.path.expanduser("~")) / "WinPurge"
BACKUP_DIR: Path = APPDATA_DIR / "backups"
LOG_FILE: Path = APPDATA_DIR / "winpurge.log"
ASSETS_DIR: Path = Path(__file__).parent.parent / "assets"
LOCALES_DIR: Path = Path(__file__).parent.parent / "locales"
DATA_DIR: Path = Path(__file__).parent / "data"

# Ensure directories exist
APPDATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Window Settings
WINDOW_WIDTH: int = 1100
WINDOW_HEIGHT: int = 700
WINDOW_MIN_WIDTH: int = 900
WINDOW_MIN_HEIGHT: int = 600

# Sidebar
SIDEBAR_WIDTH: int = 220
SIDEBAR_CORNER_RADIUS: int = 0
# General UI border radius (used by theme and components)
BORDER_RADIUS: int = 12

# Colors - Dark Theme (Default)
class DarkTheme:
    """Dark theme color palette."""
    BG_PRIMARY: str = "#0F0F0F"  # Main background
    BG_SECONDARY: str = "#1A1A1A"  # Sidebar background
    BG_TERTIARY: str = "#242424"  # Card background
    
    ACCENT_PRIMARY: str = "#6C5CE7"  # Purple accent
    ACCENT_HOVER: str = "#7C6CF7"  # Purple hover
    
    TEXT_PRIMARY: str = "#FFFFFF"  # Primary text
    TEXT_SECONDARY: str = "#8B8B8B"  # Secondary text
    
    STATUS_SUCCESS: str = "#00D26A"  # Green
    STATUS_WARNING: str = "#FFB347"  # Amber
    STATUS_DANGER: str = "#FF6B6B"  # Red
    
    BORDER_COLOR: str = "#2A2A2A"  # Card border
    BORDER_RADIUS: int = 12

# Colors - Light Theme
class LightTheme:
    """Light theme color palette."""
    BG_PRIMARY: str = "#F5F5F7"  # Main background
    BG_SECONDARY: str = "#FFFFFF"  # Sidebar background
    BG_TERTIARY: str = "#FFFFFF"  # Card background
    
    ACCENT_PRIMARY: str = "#6C5CE7"  # Purple accent (same)
    ACCENT_HOVER: str = "#7C6CF7"  # Purple hover (same)
    
    TEXT_PRIMARY: str = "#1A1A1A"  # Primary text
    TEXT_SECONDARY: str = "#6B6B6B"  # Secondary text
    
    STATUS_SUCCESS: str = "#00D26A"  # Green (same)
    STATUS_WARNING: str = "#FFB347"  # Amber (same)
    STATUS_DANGER: str = "#FF6B6B"  # Red (same)
    
    BORDER_COLOR: str = "#E0E0E0"  # Card border
    BORDER_RADIUS: int = 12

# Font Settings
FONT_FAMILY: str = "Inter"
FONT_SIZE_BODY: int = 13
FONT_SIZE_HEADER: int = 18
FONT_SIZE_TITLE: int = 24
FONT_SIZE_SMALL: int = 11

# Animation Timings (ms)
ANIMATION_HOVER: int = 150
ANIMATION_FADE: int = 100

# sidebar Navigation Items
NAVIGATION_ITEMS: Dict[str, str] = {
    "home": "🏠",
    "bloatware": "📦",
    "privacy": "🔒",
    "services": "⚙️",
    "gaming": "🎮",
    "network": "🌐",
    "cleanup": "🧹",
    "backup": "💾",
    "settings": "⚙️",
}

# Risk Levels
RISK_SAFE: str = "safe"
RISK_MODERATE: str = "moderate"
RISK_ADVANCED: str = "advanced"

# Service States
SERVICE_RUNNING: str = "running"
SERVICE_STOPPED: str = "stopped"

SERVICE_START_AUTO: str = "auto"
SERVICE_START_MANUAL: str = "manual"
SERVICE_START_DISABLED: str = "disabled"

# Default Language
DEFAULT_LANGUAGE: str = "en"
SUPPORTED_LANGUAGES: list = ["en", "de", "fr", "es", "pl"]

# Proxy Settings for Network
CLOUDFLARE_DNS: str = "1.1.1.1"
GOOGLE_DNS: str = "8.8.8.8"
ADGUARD_DNS: str = "94.140.14.14"
QUAD9_DNS: str = "9.9.9.9"
