import winreg
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from winpurge.constants import (
    REG_CONTENT_DELIVERY,
    REG_COPILOT,
    REG_CORTANA,
    REG_RECALL,
    REG_SYSTEM_POLICIES,
)
from winpurge.utils import logger


@dataclass(frozen=True)
class RegistryValue:
    hive: int
    path: str
    name: str
    value: Any
    value_type: int


class PrivacyManager:
    def get_privacy_status(self) -> Dict[str, bool]:
        return {
            "cortana_enabled": self._read_reg_dword(winreg.HKEY_LOCAL_MACHINE, REG_CORTANA, "AllowCortana", 1) != 0,
            "copilot_enabled": self._read_reg_dword(winreg.HKEY_CURRENT_USER, REG_COPILOT, "TurnOffWindowsCopilot", 0) != 1,
            "recall_enabled": self._read_reg_dword(winreg.HKEY_CURRENT_USER, REG_RECALL, "DisableAIDataAnalysis", 0) != 1,
            "activity_history_enabled": self._read_reg_dword(winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES, "EnableActivityFeed", 1) != 0,
            "start_suggestions_enabled": self._read_reg_dword(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "SystemPaneSuggestionsEnabled", 1) != 0,
            "lock_screen_ads_enabled": self._read_reg_dword(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "RotatingLockScreenEnabled", 1) != 0,
            "clipboard_sync_enabled": self._read_reg_dword(winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES, "AllowCrossDeviceClipboard", 1) != 0,
        }

    def disable_cortana(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling Cortana...")
        success = self._set_registry_value(
            winreg.HKEY_LOCAL_MACHINE,
            REG_CORTANA,
            "AllowCortana",
            0,
            winreg.REG_DWORD,
        )
        return (True, "Cortana disabled successfully") if success else (False, "Failed to disable Cortana")

    def disable_copilot(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling Copilot...")
        success = self._set_registry_value(
            winreg.HKEY_CURRENT_USER,
            REG_COPILOT,
            "TurnOffWindowsCopilot",
            1,
            winreg.REG_DWORD,
        )
        return (True, "Copilot disabled successfully") if success else (False, "Failed to disable Copilot")

    def disable_recall(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling Windows Recall...")
        success = self._set_registry_value(
            winreg.HKEY_CURRENT_USER,
            REG_RECALL,
            "DisableAIDataAnalysis",
            1,
            winreg.REG_DWORD,
        )
        return (True, "Windows Recall disabled successfully") if success else (False, "Failed to disable Windows Recall")

    def disable_activity_history(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling activity history...")
        success = self._apply_registry_values([
            RegistryValue(winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES, "EnableActivityFeed", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES, "PublishUserActivities", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES, "UploadUserActivities", 0, winreg.REG_DWORD),
        ])
        return (True, "Activity history disabled successfully") if success else (False, "Failed to disable activity history")

    def disable_start_suggestions(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling Start Menu suggestions...")
        success = self._apply_registry_values([
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "SubscribedContent-338388Enabled", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "SubscribedContent-338389Enabled", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "SubscribedContent-353694Enabled", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "SubscribedContent-353696Enabled", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "SystemPaneSuggestionsEnabled", 0, winreg.REG_DWORD),
        ])
        return (True, "Start Menu suggestions disabled successfully") if success else (False, "Failed to disable Start Menu suggestions")

    def disable_lock_screen_ads(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling lock screen ads...")
        success = self._apply_registry_values([
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "RotatingLockScreenEnabled", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "RotatingLockScreenOverlayEnabled", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY, "SubscribedContent-338387Enabled", 0, winreg.REG_DWORD),
        ])
        return (True, "Lock screen ads disabled successfully") if success else (False, "Failed to disable lock screen ads")

    def disable_clipboard_sync(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling clipboard sync...")
        success = self._apply_registry_values([
            RegistryValue(winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES, "AllowClipboardHistory", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES, "AllowCrossDeviceClipboard", 0, winreg.REG_DWORD),
        ])
        return (True, "Clipboard sync disabled successfully") if success else (False, "Failed to disable clipboard sync")

    def apply_all_privacy_settings(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        operations = [
            ("Cortana", self.disable_cortana),
            ("Copilot", self.disable_copilot),
            ("Recall", self.disable_recall),
            ("Activity History", self.disable_activity_history),
            ("Start Suggestions", self.disable_start_suggestions),
            ("Lock Screen Ads", self.disable_lock_screen_ads),
            ("Clipboard Sync", self.disable_clipboard_sync),
        ]

        results: List[Tuple[str, bool]] = []
        for name, func in operations:
            if progress_callback:
                progress_callback(f"Disabling {name}...")
            success, _ = func()
            results.append((name, success))

        success_count = sum(1 for _, ok in results if ok)
        total = len(results)
        if success_count == total:
            return True, "All privacy settings applied successfully"
        failed = [name for name, ok in results if not ok]
        return True, f"Applied {success_count}/{total} settings. Failed: {', '.join(failed)}"

    def _apply_registry_values(self, values: List[RegistryValue]) -> bool:
        results = [self._set_registry_value(v.hive, v.path, v.name, v.value, v.value_type) for v in values]
        return all(results)

    def _set_registry_value(
        self,
        hkey: int,
        subkey: str,
        name: str,
        value: Any,
        value_type: int,
    ) -> bool:
        try:
            key = winreg.CreateKeyEx(hkey, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, name, 0, value_type, value)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"Failed to set registry value {subkey}\\{name}: {e}")
            return False

    def _read_reg_dword(self, hive: int, path: str, name: str, default: int = 0) -> int:
        try:
            with winreg.OpenKey(hive, path) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return int(value)
        except Exception:
            return default


privacy_manager = PrivacyManager()