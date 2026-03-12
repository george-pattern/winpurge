"""
WinPurge Telemetry Module
Handles disabling Windows telemetry and tracking services.
"""

import logging
from typing import Callable, Optional, Dict, Any
import winreg

from winpurge.utils import run_powershell, run_command, get_logger

logger = get_logger(__name__)


class TelemetryManager:
    """Manager for disabling telemetry and tracking services."""
    
    def disable_telemetry(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Disable Windows telemetry collection.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            logger.info("Disabling telemetry...")
            
            registry_settings = [
                {
                    "path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                    "key": "AllowTelemetry",
                    "value": 0,
                    "type": winreg.REG_DWORD
                },
                {
                    "path": r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection",
                    "key": "AllowTelemetry",
                    "value": 0,
                    "type": winreg.REG_DWORD
                },
                {
                    "path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\CloudContent",
                    "key": "DisableWindowsConsumerFeatures",
                    "value": 1,
                    "type": winreg.REG_DWORD
                }
            ]
            
            self._apply_registry_settings(registry_settings)
            
            if progress_callback:
                progress_callback("Disabling scheduled telemetry tasks...")
            
            self._disable_telemetry_tasks()
            
            logger.info("Telemetry disabled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to disable telemetry: {e}")
            return False
    
    def disable_cortana(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Disable Cortana voice assistant.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            logger.info("Disabling Cortana...")
            
            if progress_callback:
                progress_callback("Disabling Cortana...")
            
            registry_settings = [
                {
                    "path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                    "key": "AllowCortana",
                    "value": 0,
                    "type": winreg.REG_DWORD
                }
            ]
            
            self._apply_registry_settings(registry_settings)
            logger.info("Cortana disabled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to disable Cortana: {e}")
            return False
    
    def disable_copilot(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Disable Windows Copilot AI assistant.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            logger.info("Disabling Copilot...")
            
            if progress_callback:
                progress_callback("Disabling Copilot...")
            
            registry_settings = [
                {
                    "path": r"HKCU\Software\Policies\Microsoft\Windows\WindowsCopilot",
                    "key": "TurnOffWindowsCopilot",
                    "value": 1,
                    "type": winreg.REG_DWORD
                }
            ]
            
            self._apply_registry_settings(registry_settings)
            logger.info("Copilot disabled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to disable Copilot: {e}")
            return False
    
    def disable_recall(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Disable Windows Recall feature.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            logger.info("Disabling Windows Recall...")
            
            if progress_callback:
                progress_callback("Disabling Windows Recall...")
            
            registry_settings = [
                {
                    "path": r"HKCU\Software\Policies\Microsoft\Windows\WindowsAI",
                    "key": "DisableAIDataAnalysis",
                    "value": 1,
                    "type": winreg.REG_DWORD
                }
            ]
            
            self._apply_registry_settings(registry_settings)
            logger.info("Recall disabled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to disable Recall: {e}")
            return False
    
    def disable_activity_history(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Disable activity history tracking.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            logger.info("Disabling activity history...")
            
            if progress_callback:
                progress_callback("Disabling activity history...")
            
            registry_settings = [
                {
                    "path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System",
                    "key": "EnableActivityFeed",
                    "value": 0,
                    "type": winreg.REG_DWORD
                },
                {
                    "path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System",
                    "key": "PublishUserActivities",
                    "value": 0,
                    "type": winreg.REG_DWORD
                },
                {
                    "path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System",
                    "key": "UploadUserActivities",
                    "value": 0,
                    "type": winreg.REG_DWORD
                }
            ]
            
            self._apply_registry_settings(registry_settings)
            logger.info("Activity history disabled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to disable activity history: {e}")
            return False
    
    def disable_ads(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Disable Start Menu ads and suggestions.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            logger.info("Disabling ads and suggestions...")
            
            if progress_callback:
                progress_callback("Disabling ads and suggestions...")
            
            registry_settings = [
                {
                    "path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                    "key": "SubscribedContent-338388Enabled",
                    "value": 0,
                    "type": winreg.REG_DWORD
                },
                {
                    "path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                    "key": "SubscribedContent-338389Enabled",
                    "value": 0,
                    "type": winreg.REG_DWORD
                },
                {
                    "path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                    "key": "SystemPaneSuggestionsEnabled",
                    "value": 0,
                    "type": winreg.REG_DWORD
                },
                {
                    "path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                    "key": "RotatingLockScreenEnabled",
                    "value": 0,
                    "type": winreg.REG_DWORD
                }
            ]
            
            self._apply_registry_settings(registry_settings)
            logger.info("Ads and suggestions disabled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to disable ads: {e}")
            return False
    
    def _apply_registry_settings(self, settings: list) -> None:
        """
        Apply registry settings.
        
        Args:
            settings: List of registry setting dictionaries.
        """
        for setting in settings:
            try:
                # Convert registry path to PowerShell command
                path = setting.get("path")
                key = setting.get("key")
                value = setting.get("value")
                
                # Use PowerShell to set registry values
                script = f"""
                New-Item -Path "{path}" -Force -ErrorAction SilentlyContinue | Out-Null
                Set-ItemProperty -Path "{path}" -Name "{key}" -Value {value} -ErrorAction SilentlyContinue
                """
                
                run_powershell(script)
                logger.debug(f"Set registry: {path}\\{key} = {value}")
            
            except Exception as e:
                logger.warning(f"Failed to set registry value: {e}")
    
    def _disable_telemetry_tasks(self) -> None:
        """Disable scheduled telemetry tasks."""
        telemetry_tasks = [
            r"\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
            r"\Microsoft\Windows\Application Experience\ProgramDataUpdater",
            r"\Microsoft\Windows\Application Experience\Consolidator",
            r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
            r"\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
            r"\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector",
            r"\Microsoft\Windows\Autochk\Proxy",
            r"\Microsoft\Windows\Customer Experience Improvement Program\KernelCeipTask",
            r"\Microsoft\Windows\SettingSync\BackupTask",
            r"\Microsoft\Windows\SettingSync\MetadataSync"
        ]
        
        for task in telemetry_tasks:
            try:
                script = f'Disable-ScheduledTask -TaskName "{task}" -ErrorAction SilentlyContinue'
                run_powershell(script)
                logger.debug(f"Disabled task: {task}")
            except Exception as e:
                logger.warning(f"Failed to disable task {task}: {e}")
