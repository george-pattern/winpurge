"""
WinPurge Services Module
Handles Windows service management.
"""

import subprocess
import winreg
from typing import Any, Callable, Dict, List, Optional, Tuple

from winpurge.utils import load_json_resource, logger, run_command


class ServicesManager:
    """Manages Windows services configuration."""
    
    def __init__(self) -> None:
        """Initialize the services manager."""
        self._services_data: Dict[str, Any] = {}
        self._load_services_data()
    
    def _load_services_data(self) -> None:
        """Load services definitions from JSON."""
        self._services_data = load_json_resource("winpurge/data/services_list.json")
        if not self._services_data:
            logger.warning("Could not load services list")
            self._services_data = {"services": [], "categories": {}}
    
    def get_services_list(self) -> List[Dict[str, Any]]:
        """
        Get list of manageable services with current status.
        
        Returns:
            List of service dictionaries with status info.
        """
        services = []
        defined_services = {s["name"]: s for s in self._services_data.get("services", [])}
        
        for service_name, service_info in defined_services.items():
            status = self._get_service_status(service_name)
            
            services.append({
                "name": service_name,
                "display_name": service_info.get("display_name", service_name),
                "description": service_info.get("description", ""),
                "risk_level": service_info.get("risk_level", "moderate"),
                "category": service_info.get("category", "system"),
                "status": status.get("status", "Unknown"),
                "start_type": status.get("start_type", "Unknown"),
            })
        
        return sorted(services, key=lambda x: (x["risk_level"], x["display_name"]))
    
    def _get_service_status(self, service_name: str) -> Dict[str, str]:
        """
        Get current status of a service.
        
        Args:
            service_name: Name of the service.
            
        Returns:
            Dictionary with status and start_type.
        """
        try:
            result = subprocess.run(
                ["sc", "query", service_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            
            status = "Unknown"
            if "RUNNING" in result.stdout:
                status = "Running"
            elif "STOPPED" in result.stdout:
                status = "Stopped"
            
            # Get start type
            result_config = subprocess.run(
                ["sc", "qc", service_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            
            start_type = "Unknown"
            if "AUTO_START" in result_config.stdout:
                start_type = "Automatic"
            elif "DEMAND_START" in result_config.stdout:
                start_type = "Manual"
            elif "DISABLED" in result_config.stdout:
                start_type = "Disabled"
            
            return {"status": status, "start_type": start_type}
            
        except Exception as e:
            logger.debug(f"Could not get status for {service_name}: {e}")
            return {"status": "Unknown", "start_type": "Unknown"}
    
    def get_categories(self) -> Dict[str, Dict[str, str]]:
        """
        Get service category definitions.
        
        Returns:
            Dictionary of category details.
        """
        return self._services_data.get("categories", {})
    
    def disable_service(
        self,
        service_name: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable a Windows service.
        
        Args:
            service_name: Name of the service to disable.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback(f"Stopping {service_name}...")
            
            # Stop the service first
            run_command(["sc", "stop", service_name])
            
            if progress_callback:
                progress_callback(f"Disabling {service_name}...")
            
            # Disable the service
            success, output = run_command(["sc", "config", service_name, "start=disabled"])
            
            if success:
                logger.info(f"Disabled service: {service_name}")
                return True, f"Service {service_name} disabled"
            else:
                logger.warning(f"Could not disable {service_name}: {output}")
                return False, f"Failed to disable {service_name}: {output}"
                
        except Exception as e:
            logger.error(f"Error disabling {service_name}: {e}")
            return False, f"Error disabling {service_name}: {str(e)}"
    
    def enable_service(
        self,
        service_name: str,
        start_type: str = "demand",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Enable a Windows service.
        
        Args:
            service_name: Name of the service to enable.
            start_type: Start type (auto, demand).
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback(f"Enabling {service_name}...")
            
            success, output = run_command(["sc", "config", service_name, f"start={start_type}"])
            
            if success:
                logger.info(f"Enabled service: {service_name}")
                return True, f"Service {service_name} enabled"
            else:
                logger.warning(f"Could not enable {service_name}: {output}")
                return False, f"Failed to enable {service_name}: {output}"
                
        except Exception as e:
            logger.error(f"Error enabling {service_name}: {e}")
            return False, f"Error enabling {service_name}: {str(e)}"
    
    def disable_services(
        self,
        services: List[str],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        Disable multiple services.
        
        Args:
            services: List of service names to disable.
            progress_callback: Optional callback(message, current, total).
            
        Returns:
            Tuple of (success_count, fail_count, error_messages).
        """
        success_count = 0
        fail_count = 0
        errors = []
        total = len(services)
        
        for i, service in enumerate(services, 1):
            if progress_callback:
                progress_callback(f"Disabling {service}...", i, total)
            
            success, message = self.disable_service(service)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                errors.append(message)
        
        return success_count, fail_count, errors
    
    def get_tracking_services_count(self) -> int:
        """
        Get count of running tracking/telemetry services.
        
        Returns:
            Number of active tracking services.
        """
        tracking_services = ["DiagTrack", "dmwappushservice", "CDPUserSvc", "WerSvc"]
        count = 0
        
        for service in tracking_services:
            status = self._get_service_status(service)
            if status.get("status") == "Running":
                count += 1
        
        return count
    
    def get_services_by_risk(self, risk_level: str) -> List[Dict[str, Any]]:
        """
        Get services filtered by risk level.
        
        Args:
            risk_level: Risk level to filter by (safe, moderate, advanced).
            
        Returns:
            List of matching services.
        """
        all_services = self.get_services_list()
        return [s for s in all_services if s.get("risk_level") == risk_level]


services_manager = ServicesManager()