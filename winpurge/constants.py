"""
WinPurge Constants
Central location for all application constants, colors, and configuration.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Application Info
APP_NAME: str = "WinPurge"
APP_VERSION: str = "1.0.0"
APP_AUTHOR: str = "WinPurge Contributors"
GITHUB_URL: str = "https://github.com/george-pattern/WinPurge"
GITHUB_API_RELEASES: str = "https://api.github.com/repos/george-pattern/WinPurge/releases/latest"

# Paths
USER_PROFILE: Path = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
APP_DATA_DIR: Path = USER_PROFILE / "WinPurge"
BACKUPS_DIR: Path = APP_DATA_DIR / "backups"
LOG_FILE: Path = APP_DATA_DIR / "winpurge.log"
CONFIG_FILE: Path = APP_DATA_DIR / "config.json"
HOSTS_FILE: Path = Path(r"C:\Windows\System32\drivers\etc\hosts")
WINDOWS_TEMP: Path = Path(r"C:\Windows\Temp")
PREFETCH_DIR: Path = Path(r"C:\Windows\Prefetch")
SOFTWARE_DISTRIBUTION: Path = Path(r"C:\Windows\SoftwareDistribution\Download")
DELIVERY_OPTIMIZATION: Path = Path(r"C:\Windows\ServiceProfiles\NetworkService\AppData\Local\Microsoft\Windows\DeliveryOptimization\Cache")

# Window Configuration
WINDOW_WIDTH: int = 1100
WINDOW_HEIGHT: int = 700
MIN_WIDTH: int = 900
MIN_HEIGHT: int = 600
SIDEBAR_WIDTH: int = 220

# Dark Theme Colors
DARK_THEME: Dict[str, str] = {
    "bg_main": "#0F0F0F",
    "bg_sidebar": "#1A1A1A",
    "bg_card": "#242424",
    "accent": "#6C5CE7",
    "accent_hover": "#7C6CF7",
    "accent_pressed": "#5B4ED6",
    "text_primary": "#FFFFFF",
    "text_secondary": "#8B8B8B",
    "text_disabled": "#5A5A5A",
    "success": "#00D26A",
    "warning": "#FFB347",
    "danger": "#FF6B6B",
    "info": "#54A0FF",
    "card_border": "#2A2A2A",
    "divider": "#333333",
    "input_bg": "#1A1A1A",
    "input_border": "#333333",
    "scrollbar": "#333333",
    "scrollbar_hover": "#444444",
}

# Light Theme Colors
LIGHT_THEME: Dict[str, str] = {
    "bg_main": "#F5F5F7",
    "bg_sidebar": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "accent": "#6C5CE7",
    "accent_hover": "#7C6CF7",
    "accent_pressed": "#5B4ED6",
    "text_primary": "#1A1A1A",
    "text_secondary": "#6B6B6B",
    "text_disabled": "#9A9A9A",
    "success": "#00D26A",
    "warning": "#FFB347",
    "danger": "#FF6B6B",
    "info": "#54A0FF",
    "card_border": "#E0E0E0",
    "divider": "#E5E5E5",
    "input_bg": "#F5F5F5",
    "input_border": "#D0D0D0",
    "scrollbar": "#D0D0D0",
    "scrollbar_hover": "#B0B0B0",
}

# Risk Level Colors
RISK_COLORS: Dict[str, Dict[str, str]] = {
    "safe": {"bg": "#00D26A", "fg": "#FFFFFF", "bg_light": "#E6F9F0"},
    "moderate": {"bg": "#FFB347", "fg": "#1A1A1A", "bg_light": "#FFF5E6"},
    "advanced": {"bg": "#FF6B6B", "fg": "#FFFFFF", "bg_light": "#FFE6E6"},
}

# Typography
FONT_FAMILY: str = "Inter"
FONT_FALLBACK: str = "Segoe UI"
FONT_SIZE_BODY: int = 13
FONT_SIZE_SMALL: int = 11
FONT_SIZE_HEADER: int = 18
FONT_SIZE_TITLE: int = 24
FONT_SIZE_LARGE: int = 32

# UI Configuration
CARD_RADIUS: int = 12
BUTTON_RADIUS: int = 8
INPUT_RADIUS: int = 8
ANIMATION_DURATION: int = 150
TOOLTIP_DELAY: int = 500

# Supported Languages
LANGUAGES: Dict[str, str] = {
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "pl": "Polski",
}

# Default Configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "language": "en",
    "theme": "dark",
    "auto_backup": True,
    "first_run": True,
}

# Registry Paths
REG_TELEMETRY_POLICY: str = r"SOFTWARE\Policies\Microsoft\Windows\DataCollection"
REG_TELEMETRY_CURRENT: str = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection"
REG_CLOUD_CONTENT: str = r"SOFTWARE\Policies\Microsoft\Windows\CloudContent"
REG_ADVERTISING_INFO: str = r"SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo"
REG_EXPLORER_ADVANCED: str = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
REG_INPUT_PERSONALIZATION: str = r"SOFTWARE\Microsoft\Input\TIPC"
REG_PERSONALIZATION: str = r"SOFTWARE\Microsoft\Personalization\Settings"
REG_CORTANA: str = r"SOFTWARE\Policies\Microsoft\Windows\Windows Search"
REG_COPILOT: str = r"Software\Policies\Microsoft\Windows\WindowsCopilot"
REG_RECALL: str = r"Software\Policies\Microsoft\Windows\WindowsAI"
REG_SYSTEM_POLICIES: str = r"SOFTWARE\Policies\Microsoft\Windows\System"
REG_CONTENT_DELIVERY: str = r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
REG_GAME_BAR: str = r"Software\Microsoft\GameBar"
REG_GAME_DVR: str = r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR"
REG_GAME_CONFIG: str = r"System\GameConfigStore"
REG_MOUSE: str = r"Control Panel\Mouse"

# Scheduled Tasks for Telemetry
TELEMETRY_TASKS: list = [
    r"\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
    r"\Microsoft\Windows\Application Experience\ProgramDataUpdater",
    r"\Microsoft\Windows\Autochk\Proxy",
    r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
    r"\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
    r"\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector",
    r"\Microsoft\Windows\Feedback\Siuf\DmClient",
    r"\Microsoft\Windows\Feedback\Siuf\DmClientOnScenarioDownload",
    r"\Microsoft\Windows\Windows Error Reporting\QueueReporting",
    r"\Microsoft\Windows\PI\Sqm-Tasks",
    r"\Microsoft\Windows\NetTrace\GatherNetworkInfo",
]

# Power Plans
POWER_PLAN_HIGH_PERFORMANCE: str = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
POWER_PLAN_BALANCED: str = "381b4222-f694-41f0-9685-ff5bb260df2e"
POWER_PLAN_POWER_SAVER: str = "a1841308-3541-4fab-bc81-f71556f20b4a"

# DNS Presets
DNS_PRESETS: Dict[str, Dict[str, str]] = {
    "cloudflare": {"primary": "1.1.1.1", "secondary": "1.0.0.1", "name": "Cloudflare"},
    "google": {"primary": "8.8.8.8", "secondary": "8.8.4.4", "name": "Google"},
    "adguard": {"primary": "94.140.14.14", "secondary": "94.140.15.15", "name": "AdGuard"},
    "quad9": {"primary": "9.9.9.9", "secondary": "149.112.112.112", "name": "Quad9"},
}