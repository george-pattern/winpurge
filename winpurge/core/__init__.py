"""
WinPurge Core Module
Contains all system modification functionality.
"""

from winpurge.core.bloatware import BloatwareManager
from winpurge.core.telemetry import TelemetryManager
from winpurge.core.services import ServicesManager
from winpurge.core.privacy import PrivacyManager
from winpurge.core.gaming import GamingManager
from winpurge.core.network import NetworkManager
from winpurge.core.cleanup import CleanupManager

__all__ = [
    "BloatwareManager",
    "TelemetryManager",
    "ServicesManager",
    "PrivacyManager",
    "GamingManager",
    "NetworkManager",
    "CleanupManager",
]