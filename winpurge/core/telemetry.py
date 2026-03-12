"""
WinPurge Telemetry Module
Handles disabling Windows telemetry and tracking.
"""

import winreg
from typing import Any, Callable, Dict, List, Optional, Tuple

from winpurge.constants import (
    HOSTS_FILE,
    REG_ADVERTISING_INFO,
    REG_CLOUD_CONTENT,
    REG_EXPLORER_ADVANCED,
    REG_INPUT_PERSONALIZATION,
    REG_PERSONALIZATION,
    REG_TELEMETRY_CURRENT,
    REG_TELEMETRY_POLICY,
    TELEMETRY_TASKS,
)
from winpurge.utils import load_json_resource, logger, run_command, run_powershell


class TelemetryManager:
    """Manages Windows telemetry and tracking settings."""
    
    def __init__(self) -> None:
        """Initialize the telemetry manager."""
        self._endpoints_data: Dict[str, Any] = {}
        self._load_endpoints()
    
    def _load_endpoints(self) -> None:
        """Load telemetry endpoints from JSON."""
        self._endpoints_data = load_json_resource("winpurge/data/telemetry_endpoints.json")
        if not self._endpoints_data:
            logger.warning("Could not load telemetry endpoints")
            self._endpoints_data = {"endpoints": [], "categories": {}}
    
    def get_telemetry_status(self) -> Dict[str, bool]:
        """
        Check current telemetry settings status.
        
        Returns:
            Dictionary of telemetry settings and their enabled state.
        """
        status = {
            "telemetry_enabled": True,
            "advertising_id_enabled": True,
            "input_telemetry_enabled": True,
            "program_tracking_enabled": True,
            "hosts_blocking_active": False,
        }
        
        try:
            # Check telemetry policy
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_TELEMETRY_POLICY) as key:
                    value, _ = winreg.QueryValueEx(key, "AllowTelemetry")
                    status["telemetry_enabled"] = value != 0
            except WindowsError:
                pass
            
            # Check advertising ID
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_ADVERTISING_INFO) as key:
                    value, _ = winreg.QueryValueEx(key, "DisabledByGroupPolicy")
                    status["advertising_id_enabled"] = value != 1
            except WindowsError:
                pass
            
            # Check input telemetry
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_INPUT_PERSONALIZATION) as key:
                    value, _ = winreg.QueryValueEx(key, "Enabled")
                    status["input_telemetry_enabled"] = value != 0
            except WindowsError:
                pass
            
            # Check program tracking
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_EXPLORER_ADVANCED) as key:
                    value, _ = winreg.QueryValueEx(key, "Start_TrackProgs")
                    status["program_tracking_enabled"] = value != 0
            except WindowsError:
                pass
            
            # Check hosts file for blocking
            status["hosts_blocking_active"] = self._check_hosts_blocking()
            
        except Exception as e:
            logger.error(f"Failed to check telemetry status: {e}")
        
        return status
    
    def _check_hosts_blocking(self) -> bool:
        """Check if telemetry domains are blocked in hosts file."""
        try:
            if HOSTS_FILE.exists():
                content = HOSTS_FILE.read_text(encoding="utf-8", errors="ignore")
                endpoints = self._endpoints_data.get("endpoints", [])
                
                blocked_count = sum(
                    1 for ep in endpoints 
                    if ep.get("domain", "") in content
                )
                
                return blocked_count >= len(endpoints) // 2
        except Exception:
            pass
        return False
    
    def is_telemetry_blocked(self) -> bool:
        """
        Quick check if telemetry is mostly blocked.
        
        Returns:
            True if telemetry appears to be blocked.
        """
        status = self.get_telemetry_status()
        blocked_count = sum([
            not status["telemetry_enabled"],
            not status["advertising_id_enabled"],
            not status["input_telemetry_enabled"],
            status["hosts_blocking_active"],
        ])
        return blocked_count >= 2
    
    def disable_telemetry(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable Windows telemetry data collection.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        errors = []
        
        try:
            if progress_callback:
                progress_callback("Disabling telemetry policy...")
            
            # HKLM telemetry policies
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_TELEMETRY_POLICY,
                "AllowTelemetry",
                0,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_TELEMETRY_CURRENT,
                "AllowTelemetry",
                0,
                winreg.REG_DWORD,
            )
            
            if progress_callback:
                progress_callback("Disabling consumer features...")
            
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_CLOUD_CONTENT,
                "DisableWindowsConsumerFeatures",
                1,
                winreg.REG_DWORD,
            )
            
            logger.info("Telemetry disabled successfully")
            return True, "Telemetry disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable telemetry: {e}")
            return False, f"Failed to disable telemetry: {str(e)}"
    
    def disable_advertising_id(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable advertising ID tracking.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling advertising ID...")
            
            self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                REG_ADVERTISING_INFO,
                "DisabledByGroupPolicy",
                1,
                winreg.REG_DWORD,
            )
            
            logger.info("Advertising ID disabled")
            return True, "Advertising ID disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable advertising ID: {e}")
            return False, f"Failed to disable advertising ID: {str(e)}"
    
    def disable_input_telemetry(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable typing and inking data collection.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling input telemetry...")
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_INPUT_PERSONALIZATION,
                "Enabled",
                0,
                winreg.REG_DWORD,
            )
            
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_PERSONALIZATION,
                "AcceptedPrivacyPolicy",
                0,
                winreg.REG_DWORD,
            )
            
            # Disable program tracking
            self._set_registry_value(
                winreg.HKEY_CURRENT_USER,
                REG_EXPLORER_ADVANCED,
                "Start_TrackProgs",
                0,
                winreg.REG_DWORD,
            )
            
            logger.info("Input telemetry disabled")
            return True, "Input telemetry disabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to disable input telemetry: {e}")
            return False, f"Failed to disable input telemetry: {str(e)}"
    
    def block_telemetry_hosts(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Block telemetry domains in hosts file.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Reading hosts file...")
            
            # Read current hosts file
            current_content = ""
            if HOSTS_FILE.exists():
                current_content = HOSTS_FILE.read_text(encoding="utf-8", errors="ignore")
            
            if progress_callback:
                progress_callback("Adding telemetry blocks...")
            
            # Prepare new entries
            endpoints = self._endpoints_data.get("endpoints", [])
            new_entries = ["\n# WinPurge Telemetry Blocks"]
            
            for endpoint in endpoints:
                domain = endpoint.get("domain", "")
                if domain and domain not in current_content:
                    new_entries.append(f"0.0.0.0 {domain}")
            
            if len(new_entries) > 1:
                new_content = current_content.rstrip() + "\n" + "\n".join(new_entries) + "\n"
                
                # Write updated hosts file
                HOSTS_FILE.write_text(new_content, encoding="utf-8")
                
                # Flush DNS cache
                run_command(["ipconfig", "/flushdns"])
                
                logger.info(f"Blocked {len(new_entries) - 1} telemetry domains")
                return True, f"Blocked {len(new_entries) - 1} telemetry domains"
            else:
                return True, "Telemetry domains already blocked"
                
        except PermissionError:
            logger.error("Permission denied writing to hosts file")
            return False, "Permission denied. Run as administrator."
        except Exception as e:
            logger.error(f"Failed to block telemetry hosts: {e}")
            return False, f"Failed to block telemetry hosts: {str(e)}"
    
    def disable_scheduled_tasks(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable telemetry-related scheduled tasks.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        disabled_count = 0
        errors = []
        
        try:
            for task_path in TELEMETRY_TASKS:
                if progress_callback:
                    task_name = task_path.split("\\")[-1]
                    progress_callback(f"Disabling {task_name}...")
                
                success, output = run_command([
                    "schtasks", "/Change", "/TN", task_path, "/Disable"
                ])
                
                if success:
                    disabled_count += 1
                else:
                    logger.debug(f"Could not disable task {task_path}: {output}")
            
            logger.info(f"Disabled {disabled_count} scheduled tasks")
            return True, f"Disabled {disabled_count} telemetry tasks"
            
        except Exception as e:
            logger.error(f"Failed to disable scheduled tasks: {e}")
            return False, f"Failed to disable scheduled tasks: {str(e)}"
    
    def _set_registry_value(
        self,
        hkey: int,
        subkey: str,
        name: str,
        value: Any,
        value_type: int,
    ) -> bool:
        """
        Set a registry value, creating keys if necessary.
        
        Args:
            hkey: Registry hive.
            subkey: Registry subkey path.
            name: Value name.
            value: Value data.
            value_type: Registry value type.
            
        Returns:
            True if successful.
        """
        try:
            key = winreg.CreateKeyEx(hkey, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, name, 0, value_type, value)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"Failed to set registry value {subkey}\\{name}: {e}")
            return False
    
    def get_endpoints(self) -> List[Dict[str, str]]:
        """
        Get list of telemetry endpoints.
        
        Returns:
            List of endpoint dictionaries.
        """
        return self._endpoints_data.get("endpoints", [])


telemetry_manager = TelemetryManager()