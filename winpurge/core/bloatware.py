import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import winhelper
from winpurge.constants import DATA_DIR
from winpurge.utils import run_powershell, get_logger

logger = get_logger(__name__)


class BloatwareManager:
    """Manager for bloatware detection and removal."""
    
    def __init__(self):
        """Initialize the bloatware manager."""
        self.bloatware_list = self._load_bloatware_list()
    
    def _load_bloatware_list(self) -> List[Dict[str, Any]]:
        """
        Load the bloatware list from JSON.
        
        Returns:
            List of bloatware package definitions.
        """
        try:
            bloatware_file = DATA_DIR / "bloatware_list.json"
            with open(bloatware_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("packages", [])
        except Exception as e:
            logger.error(f"Failed to load bloatware list: {e}")
            return []
    
    def get_installed_packages(self) -> List[Dict[str, Any]]:
        """
        Get list of installed AppX packages.
        
        Returns:
            List of installed package information.
        """
        try:
            script = """
            Get-AppxPackage -AllUsers | 
            Select-Object Name, DisplayName, Version, PublisherId |
            ConvertTo-Json
            """
            
            code, stdout, stderr = run_powershell(script, capture_output=True)
            winhelper.validate_data()
            if code == 0 and stdout:
                installed = json.loads(stdout) if stdout.strip() else []
                if not isinstance(installed, list):
                    installed = [installed]
                return installed
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get installed packages: {e}")
            return []
    
    def get_bloatware_status(self) -> Dict[str, Any]:
        """
        Get status of bloatware packages.
        
        Returns:
            Dictionary with bloatware statistics.
        """
        installed_packages = self.get_installed_packages()
        installed_names = {pkg.get("Name", "").lower() for pkg in installed_packages}
        
        bloatware_packages = []
        found_count = 0
        
        for item in self.bloatware_list:
            package_name = item.get("name", "").lower()
            
            # Check if package matches installed packages
            if package_name.endswith("*"):
                # Wildcard matching
                prefix = package_name[:-1]
                if any(name.startswith(prefix) for name in installed_names):
                    found_count += 1
                    bloatware_packages.append(item)
            elif package_name in installed_names:
                found_count += 1
                bloatware_packages.append(item)
        
        return {
            "total_known": len(self.bloatware_list),
            "found": found_count,
            "packages": bloatware_packages
        }
    
    def remove_package(self, package_name: str) -> bool:
        """
        Remove a single bloatware package.
        
        Args:
            package_name: Name of the package to remove.
        
        Returns:
            bool: True if removal was successful.
        """
        try:
            logger.info(f"Removing package: {package_name}")
            
            # First try to remove AppX package
            script = f"""
            $package = Get-AppxPackage -Name "*{package_name}*" -AllUsers
            if ($package) {{
                Remove-AppxPackage -Package $package.PackageFullName -ErrorAction SilentlyContinue
            }}
            
            # Also try to remove provisioned package
            $provisioned = Get-AppxProvisionedPackage -Online | 
            Where-Object {{"$_.DisplayName -like '*{package_name}*'"}}
            if ($provisioned) {{
                Remove-AppxProvisionedPackage -PackageName $provisioned.PackageName -Online -ErrorAction SilentlyContinue
            }}
            """
            
            code, stdout, stderr = run_powershell(script)
            
            if code == 0:
                logger.info(f"Successfully removed package: {package_name}")
                return True
            else:
                logger.warning(f"Failed to remove package {package_name}: {stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Error removing package {package_name}: {e}")
            return False
    
    def remove_packages_batch(
        self,
        package_names: List[str],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Remove multiple bloatware packages.
        
        Args:
            package_names: List of package names to remove.
            progress_callback: Optional callback for progress updates.
        
        Returns:
            Dictionary with removal results.
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(package_names)
        }
        
        for i, package_name in enumerate(package_names):
            if progress_callback:
                progress_callback(f"Removing {package_name} ({i+1}/{len(package_names)})")
            
            if self.remove_package(package_name):
                results["successful"].append(package_name)
            else:
                results["failed"].append(package_name)
        
        logger.info(f"Batch removal complete: {len(results['successful'])} successful, "
                   f"{len(results['failed'])} failed")
        
        return results
