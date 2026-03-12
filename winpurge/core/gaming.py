"""
WinPurge Gaming Module
Handles gaming optimization settings.
"""

import subprocess
import winreg
from typing import Any, Callable, Dict, List, Optional, Tuple

from winpurge.constants import (
    POWER_PLAN_HIGH_PERFORMANCE,
    REG_GAME_BAR,
    REG_GAME_CONFIG,
    REG_GAME_DVR,
    REG_MOUSE,
)
from winpurge.utils import logger, run_command


class GamingManager:
    """Manages gaming optimization settings."""
    
    def __init__(self) -> None:
        """Initialize the gaming manager."""
        pass
    
    def get_gaming_status(self) -> Dict[str, bool]:
        """
        Check current gaming optimization status.
        
        Returns:
            Dictionary of gaming settings and their state.
        """
        status = {
            "game_mode_enabled": False,
            "game_bar_disabled": False,
            "game_dvr_disabled": False,
            "high_performance_power": False,
            "mouse_acceleration_disabled": False,
            "fullscreen_optimizations_disabled": False,
        }
        
        try:
            # Check Game Mode
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_GAME_BAR) as key:
                    value, _ = winreg.QueryValueEx(key, "AllowAutoGameMode")
                    status["game_mode_enabled"] = value == 1
            except WindowsError:
                pass
            
            # Check Game Bar
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_GAME_DVR) as key:
                    value, _ = winreg.QueryValueEx(key, "AppCaptureEnabled")
                    status["game_bar_disabled"] = value == 0
            except WindowsError:
                pass
            
            # Check Game DVR
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG) as key:
                    value, _ = winreg.QueryValueEx(key, "GameDVR_Enabled")
                    status["game_dvr_disabled"] = value == 0
            except WindowsError:
                pass
            
            # Check Power Plan
            result = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            status["high_performance_power"] = POWER_PLAN_HIGH_PERFORMANCE in result.stdout
            
            # Check Mouse Acceleration
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_MOUSE) as key:
                    value, _ = winreg.QueryValueEx(key, "MouseSpeed")
                    status["mouse_acceleration_disabled"] = value == "0"
            except WindowsError:
                pass
            
            # Check Fullscreen Optimizations
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG) as key:
                    value, _ = winreg.QueryValueEx(key, "GameDVR_FSEBehaviorMode")
                    status["fullscreen_optimizations_disabled"] = value == 2
            except WindowsError:
                pass
            
        except Exception as e:
            logger.error(f"Failed to check gaming status: {e}")
        
        return status
    
    def enable_game_mode(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Enable Windows Game Mode.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Enabling Game Mode...")
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_GAME_BAR,
                "AllowAutoGameMode",
                1,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_GAME_BAR,
                "AutoGameModeEnabled",
                1,
                winreg.REG_DWORD,
            )
            
            logger.info("Game Mode enabled")
            return True, "Game Mode enabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to enable Game Mode: {e}")
            return False, f"Failed to enable Game Mode: {str(e)}"
    
    def disable_game_bar(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable Xbox Game Bar overlay.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling Game Bar...")
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_GAME_DVR,
                "AppCaptureEnabled",
                0,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_GAME_BAR,
                "UseNexusForGameBarEnabled",
                0,
                winreg.REG_DWORD,
            )
            
            logger.info("Game Bar disabled")
            return True, "Game Bar disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable Game Bar: {e}")
            return False, f"Failed to disable Game Bar: {str(e)}"
    
    def disable_game_dvr(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable Game DVR background recording.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling Game DVR...")
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_GAME_CONFIG,
                "GameDVR_Enabled",
                0,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_GAME_DVR,
                "AppCaptureEnabled",
                0,
                winreg.REG_DWORD,
            )
            
            logger.info("Game DVR disabled")
            return True, "Game DVR disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable Game DVR: {e}")
            return False, f"Failed to disable Game DVR: {str(e)}"
    
    def set_high_performance_power(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Set power plan to High Performance.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Setting High Performance power plan...")
            
            success, output = run_command([
                "powercfg", "/setactive", POWER_PLAN_HIGH_PERFORMANCE
            ])
            
            if success:
                logger.info("High Performance power plan activated")
                return True, "High Performance power plan activated"
            else:
                # Try to create the plan if it doesn't exist
                run_command(["powercfg", "/duplicatescheme", POWER_PLAN_HIGH_PERFORMANCE])
                success, _ = run_command([
                    "powercfg", "/setactive", POWER_PLAN_HIGH_PERFORMANCE
                ])
                
                if success:
                    return True, "High Performance power plan activated"
                else:
                    return False, f"Failed to set power plan: {output}"
                    
        except Exception as e:
            logger.error(f"Failed to set power plan: {e}")
            return False, f"Failed to set power plan: {str(e)}"
    
    def disable_mouse_acceleration(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable mouse acceleration for better gaming precision.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling mouse acceleration...")
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_MOUSE,
                "MouseSpeed",
                "0",
                winreg.REG_SZ,
            )
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_MOUSE,
                "MouseThreshold1",
                "0",
                winreg.REG_SZ,
            )
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_MOUSE,
                "MouseThreshold2",
                "0",
                winreg.REG_SZ,
            )
            
            logger.info("Mouse acceleration disabled")
            return True, "Mouse acceleration disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable mouse acceleration: {e}")
            return False, f"Failed to disable mouse acceleration: {str(e)}"
    
    def disable_fullscreen_optimizations(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable fullscreen optimizations globally.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling fullscreen optimizations...")
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_GAME_CONFIG,
                "GameDVR_FSEBehaviorMode",
                2,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_GAME_CONFIG,
                "GameDVR_HonorUserFSEBehaviorMode",
                1,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_GAME_CONFIG,
                "GameDVR_FSEBehavior",
                2,
                winreg.REG_DWORD,
            )
            
            logger.info("Fullscreen optimizations disabled")
            return True, "Fullscreen optimizations disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable fullscreen optimizations: {e}")
            return False, f"Failed to disable fullscreen optimizations: {str(e)}"
    
    def disable_nagle_algorithm(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable Nagle's Algorithm for lower network latency.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling Nagle's Algorithm...")
            
            # Get network interfaces
            interfaces_key = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, interfaces_key) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey_path = f"{interfaces_key}\\{subkey_name}"
                        
                        self._set_registry_value(
                            winreg.HKEY_LOCAL_MACHINE,
                            subkey_path,
                            "TcpAckFrequency",
                            1,
                            winreg.REG_DWORD,
                        )
                        
                        self._set_registry_value(
                            winreg.HKEY_LOCAL_MACHINE,
                            subkey_path,
                            "TCPNoDelay",
                            1,
                            winreg.REG_DWORD,
                        )
                        
                        i += 1
                    except WindowsError:
                        break
            
            logger.info("Nagle's Algorithm disabled")
            return True, "Nagle's Algorithm disabled for lower latency"
            
        except Exception as e:
            logger.error(f"Failed to disable Nagle's Algorithm: {e}")
            return False, f"Failed to disable Nagle's Algorithm: {str(e)}"
    
    def apply_all_gaming_optimizations(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Apply all gaming optimizations.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        results = []
        
        operations = [
            ("Game Mode", self.enable_game_mode),
            ("Game Bar", self.disable_game_bar),
            ("Game DVR", self.disable_game_dvr),
            ("Power Plan", self.set_high_performance_power),
            ("Mouse Acceleration", self.disable_mouse_acceleration),
            ("Fullscreen Optimizations", self.disable_fullscreen_optimizations),
            ("Nagle's Algorithm", self.disable_nagle_algorithm),
        ]
        
        for name, func in operations:
            if progress_callback:
                progress_callback(f"Applying {name}...")
            
            success, message = func()
            results.append((name, success))
        
        success_count = sum(1 for _, s in results if s)
        total = len(results)
        
        if success_count == total:
            return True, "All gaming optimizations applied successfully"
        else:
            failed = [name for name, s in results if not s]
            return True, f"Applied {success_count}/{total} optimizations. Failed: {', '.join(failed)}"
    
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


gaming_manager = GamingManager()