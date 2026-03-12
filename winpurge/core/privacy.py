"""
WinPurge Privacy Module
Handles privacy hardening features.
"""

import winreg
from typing import Any, Callable, Dict, Optional, Tuple

from winpurge.constants import (
    REG_CONTENT_DELIVERY,
    REG_COPILOT,
    REG_CORTANA,
    REG_RECALL,
    REG_SYSTEM_POLICIES,
)
from winpurge.utils import logger


class PrivacyManager:
    """Manages Windows privacy settings."""
    
    def __init__(self) -> None:
        """Initialize the privacy manager."""
        pass
    
    def get_privacy_status(self) -> Dict[str, bool]:
        """
        Check current privacy settings status.
        
        Returns:
            Dictionary of privacy settings and their enabled state.
        """
        status = {
            "cortana_enabled": True,
            "copilot_enabled": True,
            "recall_enabled": True,
            "activity_history_enabled": True,
            "start_suggestions_enabled": True,
            "lock_screen_ads_enabled": True,
            "clipboard_sync_enabled": True,
        }
        
        try:
            # Check Cortana
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_CORTANA) as key:
                    value, _ = winreg.QueryValueEx(key, "AllowCortana")
                    status["cortana_enabled"] = value != 0
            except WindowsError:
                pass
            
            # Check Copilot
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_COPILOT) as key:
                    value, _ = winreg.QueryValueEx(key, "TurnOffWindowsCopilot")
                    status["copilot_enabled"] = value != 1
            except WindowsError:
                pass
            
            # Check Recall
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RECALL) as key:
                    value, _ = winreg.QueryValueEx(key, "DisableAIDataAnalysis")
                    status["recall_enabled"] = value != 1
            except WindowsError:
                pass
            
            # Check Activity History
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES) as key:
                    value, _ = winreg.QueryValueEx(key, "EnableActivityFeed")
                    status["activity_history_enabled"] = value != 0
            except WindowsError:
                pass
            
            # Check Start Menu suggestions
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY) as key:
                    value, _ = winreg.QueryValueEx(key, "SystemPaneSuggestionsEnabled")
                    status["start_suggestions_enabled"] = value != 0
            except WindowsError:
                pass
            
            # Check Lock Screen ads
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY) as key:
                    value, _ = winreg.QueryValueEx(key, "RotatingLockScreenEnabled")
                    status["lock_screen_ads_enabled"] = value != 0
            except WindowsError:
                pass
            
            # Check Clipboard sync
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES) as key:
                    value, _ = winreg.QueryValueEx(key, "AllowCrossDeviceClipboard")
                    status["clipboard_sync_enabled"] = value != 0
            except WindowsError:
                pass
            
        except Exception as e:
            logger.error(f"Failed to check privacy status: {e}")
        
        return status
    
    def disable_cortana(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable Cortana assistant.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling Cortana...")
            
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_CORTANA,
                "AllowCortana",
                0,
                winreg.REG_DWORD,
            )
            
            logger.info("Cortana disabled")
            return True, "Cortana disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable Cortana: {e}")
            return False, f"Failed to disable Cortana: {str(e)}"
    
    def disable_copilot(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable Windows Copilot AI assistant.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling Copilot...")
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_COPILOT,
                "TurnOffWindowsCopilot",
                1,
                winreg.REG_DWORD,
            )
            
            logger.info("Copilot disabled")
            return True, "Copilot disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable Copilot: {e}")
            return False, f"Failed to disable Copilot: {str(e)}"
    
    def disable_recall(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable Windows Recall feature.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling Windows Recall...")
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_RECALL,
                "DisableAIDataAnalysis",
                1,
                winreg.REG_DWORD,
            )
            
            logger.info("Windows Recall disabled")
            return True, "Windows Recall disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable Windows Recall: {e}")
            return False, f"Failed to disable Windows Recall: {str(e)}"
    
    def disable_activity_history(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable activity history tracking.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling activity history...")
            
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_SYSTEM_POLICIES,
                "EnableActivityFeed",
                0,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_SYSTEM_POLICIES,
                "PublishUserActivities",
                0,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_SYSTEM_POLICIES,
                "UploadUserActivities",
                0,
                winreg.REG_DWORD,
            )
            
            logger.info("Activity history disabled")
            return True, "Activity history disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable activity history: {e}")
            return False, f"Failed to disable activity history: {str(e)}"
    
    def disable_start_suggestions(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable Start Menu suggestions and ads.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling Start Menu suggestions...")
            
            values = [
                ("SubscribedContent-338388Enabled", 0),
                ("SubscribedContent-338389Enabled", 0),
                ("SubscribedContent-353694Enabled", 0),
                ("SubscribedContent-353696Enabled", 0),
                ("SystemPaneSuggestionsEnabled", 0),
            ]
            
            for name, value in values:
                self._set_registry_value(
                    winreg.HKEY_CURRENT_USER,
                    REG_CONTENT_DELIVERY,
                    name,
                    value,
                    winreg.REG_DWORD,
                )
            
            logger.info("Start Menu suggestions disabled")
            return True, "Start Menu suggestions disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable Start Menu suggestions: {e}")
            return False, f"Failed to disable Start Menu suggestions: {str(e)}"
    
    def disable_lock_screen_ads(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable lock screen spotlight and ads.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling lock screen ads...")
            
            values = [
                ("RotatingLockScreenEnabled", 0),
                ("RotatingLockScreenOverlayEnabled", 0),
                ("SubscribedContent-338387Enabled", 0),
            ]
            
            for name, value in values:
                self._set_registry_value(
                    winreg.HKEY_CURRENT_USER,
                    REG_CONTENT_DELIVERY,
                    name,
                    value,
                    winreg.REG_DWORD,
                )
            
            logger.info("Lock screen ads disabled")
            return True, "Lock screen ads disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable lock screen ads: {e}")
            return False, f"Failed to disable lock screen ads: {str(e)}"
    
    def disable_clipboard_sync(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable clipboard history and cross-device sync.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling clipboard sync...")
            
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_SYSTEM_POLICIES,
                "AllowClipboardHistory",
                0,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_SYSTEM_POLICIES,
                "AllowCrossDeviceClipboard",
                0,
                winreg.REG_DWORD,
            )
            
            logger.info("Clipboard sync disabled")
            return True, "Clipboard sync disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable clipboard sync: {e}")
            return False, f"Failed to disable clipboard sync: {str(e)}"
    
    def apply_all_privacy_settings(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Apply all privacy hardening settings.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        results = []
        
        operations = [
            ("Cortana", self.disable_cortana),
            ("Copilot", self.disable_copilot),
            ("Recall", self.disable_recall),
            ("Activity History", self.disable_activity_history),
            ("Start Suggestions", self.disable_start_suggestions),
            ("Lock Screen Ads", self.disable_lock_screen_ads),
            ("Clipboard Sync", self.disable_clipboard_sync),
        ]
        
        for name, func in operations:
            if progress_callback:
                progress_callback(f"Disabling {name}...")
            
            success, message = func()
            results.append((name, success))
        
        success_count = sum(1 for _, s in results if s)
        total = len(results)
        
        if success_count == total:
            return True, "All privacy settings applied successfully"
        else:
            failed = [name for name, s in results if not s]
            return True, f"Applied {success_count}/{total} settings. Failed: {', '.join(failed)}"
    
    def _set_registry_value(
        self,
        hkey: int,
        subkey: str,
        name: str,
        value: Any,
        value_type: int,
    ) -> bool:
        """Set a registry value, creating keys if necessary."""
        try:
            key = winreg.CreateKeyEx(hkey, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, name, 0, value_type, value)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"Failed to set registry value {subkey}\\{name}: {e}")
            return False


privacy_manager = PrivacyManager()