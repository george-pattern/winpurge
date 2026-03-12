"""Page package for WinPurge GUI.
This package exposes page classes for dynamic imports by the main app.
"""

from .home import HomePage
from .bloatware import BloatwarePage
from .privacy import PrivacyPage
from .services import ServicesPage
from .gaming import GamingPage
from .network import NetworkPage
from .cleanup import CleanupPage
from .backup import BackupPage
from .settings import SettingsPage

__all__ = [
    "HomePage", "BloatwarePage", "PrivacyPage", "ServicesPage",
    "GamingPage", "NetworkPage", "CleanupPage", "BackupPage", "SettingsPage"
]
