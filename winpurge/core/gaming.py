import subprocess
import winreg
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from winpurge.constants import (
    POWER_PLAN_HIGH_PERFORMANCE,
    REG_GAME_BAR,
    REG_GAME_CONFIG,
    REG_GAME_DVR,
    REG_MOUSE,
)
from winpurge.utils import logger, run_command


@dataclass(frozen=True)
class RegistryValue:
    hive: int
    path: str
    name: str
    value: Any
    value_type: int


class GamingManager:
    def get_gaming_status(self) -> Dict[str, bool]:
        status = {
            "game_mode_enabled": self._read_reg_dword(winreg.HKEY_CURRENT_USER, REG_GAME_BAR, "AllowAutoGameMode", 0) == 1,
            "game_bar_disabled": self._read_reg_dword(winreg.HKEY_CURRENT_USER, REG_GAME_DVR, "AppCaptureEnabled", 1) == 0,
            "game_dvr_disabled": self._read_reg_dword(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_Enabled", 1) == 0,
            "high_performance_power": self._is_high_performance_power_active(),
            "mouse_acceleration_disabled": self._read_reg_str(winreg.HKEY_CURRENT_USER, REG_MOUSE, "MouseSpeed", "1") == "0",
            "fullscreen_optimizations_disabled": self._read_reg_dword(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_FSEBehaviorMode", 0) == 2,
            "nagle_disabled": self._is_nagle_disabled(),
        }
        return status

    def enable_game_mode(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Enabling Game Mode...")
        success = self._apply_registry_values([
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_BAR, "AllowAutoGameMode", 1, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_BAR, "AutoGameModeEnabled", 1, winreg.REG_DWORD),
        ])
        return (True, "Game Mode enabled successfully") if success else (False, "Failed to enable Game Mode")

    def disable_game_bar(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling Game Bar...")
        success = self._apply_registry_values([
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_DVR, "AppCaptureEnabled", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_BAR, "UseNexusForGameBarEnabled", 0, winreg.REG_DWORD),
        ])
        return (True, "Game Bar disabled successfully") if success else (False, "Failed to disable Game Bar")

    def disable_game_dvr(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling Game DVR...")
        success = self._apply_registry_values([
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_Enabled", 0, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_DVR, "AppCaptureEnabled", 0, winreg.REG_DWORD),
        ])
        return (True, "Game DVR disabled successfully") if success else (False, "Failed to disable Game DVR")

    def set_high_performance_power(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("Setting High Performance power plan...")
            success, output = run_command(["powercfg", "/setactive", POWER_PLAN_HIGH_PERFORMANCE])
            if success:
                return True, "High Performance power plan activated"
            run_command(["powercfg", "/duplicatescheme", POWER_PLAN_HIGH_PERFORMANCE])
            success, output = run_command(["powercfg", "/setactive", POWER_PLAN_HIGH_PERFORMANCE])
            return (True, "High Performance power plan activated") if success else (False, f"Failed to set power plan: {output}")
        except Exception as e:
            logger.error(f"Failed to set power plan: {e}")
            return False, f"Failed to set power plan: {e}"

    def disable_mouse_acceleration(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling mouse acceleration...")
        success = self._apply_registry_values([
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_MOUSE, "MouseSpeed", "0", winreg.REG_SZ),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_MOUSE, "MouseThreshold1", "0", winreg.REG_SZ),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_MOUSE, "MouseThreshold2", "0", winreg.REG_SZ),
        ])
        return (True, "Mouse acceleration disabled successfully") if success else (False, "Failed to disable mouse acceleration")

    def disable_fullscreen_optimizations(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        if progress_callback:
            progress_callback("Disabling fullscreen optimizations...")
        success = self._apply_registry_values([
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_FSEBehaviorMode", 2, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_HonorUserFSEBehaviorMode", 1, winreg.REG_DWORD),
            RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_FSEBehavior", 2, winreg.REG_DWORD),
        ])
        return (True, "Fullscreen optimizations disabled successfully") if success else (False, "Failed to disable fullscreen optimizations")

    def disable_nagle_algorithm(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("Disabling Nagle's Algorithm...")
            interfaces_key = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, interfaces_key) as key:
                i = 0
                changed = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey_path = f"{interfaces_key}\\{subkey_name}"
                        a = self._set_registry_value(winreg.HKEY_LOCAL_MACHINE, subkey_path, "TcpAckFrequency", 1, winreg.REG_DWORD)
                        b = self._set_registry_value(winreg.HKEY_LOCAL_MACHINE, subkey_path, "TCPNoDelay", 1, winreg.REG_DWORD)
                        if a or b:
                            changed += 1
                        i += 1
                    except OSError:
                        break
            return (True, "Nagle's Algorithm disabled for lower latency") if changed >= 0 else (False, "Failed to disable Nagle's Algorithm")
        except Exception as e:
            logger.error(f"Failed to disable Nagle's Algorithm: {e}")
            return False, f"Failed to disable Nagle's Algorithm: {e}"

    def apply_all_gaming_optimizations(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        operations = [
            ("Game Mode", self.enable_game_mode),
            ("Game Bar", self.disable_game_bar),
            ("Game DVR", self.disable_game_dvr),
            ("Power Plan", self.set_high_performance_power),
            ("Mouse Acceleration", self.disable_mouse_acceleration),
            ("Fullscreen Optimizations", self.disable_fullscreen_optimizations),
            ("Nagle's Algorithm", self.disable_nagle_algorithm),
        ]

        results: List[Tuple[str, bool]] = []
        for name, func in operations:
            if progress_callback:
                progress_callback(f"Applying {name}...")
            success, _ = func()
            results.append((name, success))

        success_count = sum(1 for _, ok in results if ok)
        total = len(results)
        if success_count == total:
            return True, "All gaming optimizations applied successfully"
        failed = [name for name, ok in results if not ok]
        return True, f"Applied {success_count}/{total} optimizations. Failed: {', '.join(failed)}"

    def reset_all_gaming_optimizations(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("Resetting gaming optimizations...")
            success = self._apply_registry_values([
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_BAR, "AllowAutoGameMode", 0, winreg.REG_DWORD),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_BAR, "AutoGameModeEnabled", 0, winreg.REG_DWORD),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_DVR, "AppCaptureEnabled", 1, winreg.REG_DWORD),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_BAR, "UseNexusForGameBarEnabled", 1, winreg.REG_DWORD),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_Enabled", 1, winreg.REG_DWORD),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_FSEBehaviorMode", 0, winreg.REG_DWORD),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_HonorUserFSEBehaviorMode", 0, winreg.REG_DWORD),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG, "GameDVR_FSEBehavior", 0, winreg.REG_DWORD),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_MOUSE, "MouseSpeed", "1", winreg.REG_SZ),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_MOUSE, "MouseThreshold1", "6", winreg.REG_SZ),
                RegistryValue(winreg.HKEY_CURRENT_USER, REG_MOUSE, "MouseThreshold2", "10", winreg.REG_SZ),
            ])
            return (True, "Gaming optimizations reset successfully") if success else (False, "Failed to reset gaming optimizations")
        except Exception as e:
            logger.error(f"Failed to reset gaming optimizations: {e}")
            return False, f"Failed to reset gaming optimizations: {e}"

    def _is_high_performance_power_active(self) -> bool:
        try:
            result = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return POWER_PLAN_HIGH_PERFORMANCE in (result.stdout or "")
        except Exception:
            return False

    def _is_nagle_disabled(self) -> bool:
        try:
            interfaces_key = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, interfaces_key) as key:
                i = 0
                found = False
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey_path = f"{interfaces_key}\\{subkey_name}"
                        ack = self._read_reg_dword(winreg.HKEY_LOCAL_MACHINE, subkey_path, "TcpAckFrequency", 0)
                        delay = self._read_reg_dword(winreg.HKEY_LOCAL_MACHINE, subkey_path, "TCPNoDelay", 0)
                        if ack == 1 and delay == 1:
                            found = True
                        i += 1
                    except OSError:
                        break
            return found
        except Exception:
            return False

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

    def _read_reg_str(self, hive: int, path: str, name: str, default: str = "") -> str:
        try:
            with winreg.OpenKey(hive, path) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return str(value)
        except Exception:
            return default


gaming_manager = GamingManager()