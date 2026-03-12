"""
WinPurge Services Module
Handles Windows services management and optimization.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from winpurge.constants import DATA_DIR
from winpurge.utils import run_command, run_powershell, get_logger

logger = get_logger(__name__)


class ServicesManager:
    """Manager for Windows services."""
    
    def __init__(self):
        """Initialize the services manager."""
        self.services_list = self._load_services_list()
    
    def _load_services_list(self) -> List[Dict[str, Any]]:
        """
        Load the services list from JSON.
        
        Returns:
            List of service definitions.
        """
        try:
            services_file = DATA_DIR / "services_list.json"
            with open(services_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("services", [])
        except Exception as e:
            logger.error(f"Failed to load services list: {e}")
            return []
    
    def get_service_status(self, service_name: str) -> Dict[str, str]:
        """
        Get status of a Windows service.
        
        Args:
            service_name: Name of the service.
        
        Returns:
            Dictionary with service status information.
        """
        try:
            script = f"""
            $service = Get-Service -Name "{service_name}" -ErrorAction SilentlyContinue
            if ($service) {{
                @{{
                    Name = $service.Name
                    Status = $service.Status
                    StartType = $service.StartType
                }} | ConvertTo-Json
            }}
            """
            
            code, stdout, stderr = run_powershell(script, capture_output=True)
            
            if code == 0 and stdout:
                return json.loads(stdout)
            return {}
        
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return {}
    
    def get_all_services_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all tracked services.
        
        Returns:
            List of service status information.
        """
        services_status = []
        
        for service in self.services_list:
            status = self.get_service_status(service.get("service_name", ""))
            if status:
                services_status.append({
                    **service,
                    "current_status": status.get("Status"),
                    "current_start_type": status.get("StartType")
                })
        
        return services_status
    
    def disable_service(self, service_name: str) -> bool:
        """
        Disable a Windows service.
        
        Args:
            service_name: Name of the service to disable.
        
        Returns:
            bool: True if successful.
        """
        try:
            logger.info(f"Disabling service: {service_name}")
            
            script = f"""
            Stop-Service -Name "{service_name}" -ErrorAction SilentlyContinue -Force
            Set-Service -Name "{service_name}" -StartupType Disabled -ErrorAction SilentlyContinue
            """
            
            code, stdout, stderr = run_powershell(script)
            
            if code == 0:
                logger.info(f"Service disabled: {service_name}")
                return True
            else:
                logger.warning(f"Failed to disable service {service_name}")
                return False
        
        except Exception as e:
            logger.error(f"Error disabling service: {e}")
            return False
    
    def enable_service(self, service_name: str) -> bool:
        """
        Enable a Windows service.
        
        Args:
            service_name: Name of the service to enable.
        
        Returns:
            bool: True if successful.
        """
        try:
            logger.info(f"Enabling service: {service_name}")
            
            script = f"""
            Set-Service -Name "{service_name}" -StartupType Manual -ErrorAction SilentlyContinue
            Start-Service -Name "{service_name}" -ErrorAction SilentlyContinue
            """
            
            code, stdout, stderr = run_powershell(script)
            
            if code == 0:
                logger.info(f"Service enabled: {service_name}")
                return True
            else:
                logger.warning(f"Failed to enable service {service_name}")
                return False
        
        except Exception as e:
            logger.error(f"Error enabling service: {e}")
            return False
    
    def disable_tracking_services(
        self,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Disable all tracking-related services.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            Dictionary with disabling results.
        """
        tracking_services = [
            "DiagTrack",
            "dmwappushservice",
            "MapsBroker",
            "WMPNetworkSvc",
            "WerSvc"
        ]
        
        results = {
            "successful": [],
            "failed": []
        }
        
        for service in tracking_services:
            if progress_callback:
                progress_callback(f"Disabling {service}...")
            
            if self.disable_service(service):
                results["successful"].append(service)
            else:
                results["failed"].append(service)
        
        return results
    
    def disable_services_batch(
        self,
        service_names: List[str],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Disable multiple services.
        
        Args:
            service_names: List of service names.
            progress_callback: Optional callback for progress updates.
        
        Returns:
            Dictionary with disabling results.
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(service_names)
        }
        
        for i, service_name in enumerate(service_names):
            if progress_callback:
                progress_callback(f"Disabling {service_name} ({i+1}/{len(service_names)})")
            
            if self.disable_service(service_name):
                results["successful"].append(service_name)
            else:
                results["failed"].append(service_name)
        
        logger.info(f"Batch operation complete: {len(results['successful'])} successful, "
                   f"{len(results['failed'])} failed")
        
        return results
