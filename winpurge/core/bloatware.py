"""
WinPurge Bloatware Module
Handles detection and removal of pre-installed Windows apps.
"""

import fnmatch
import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from winpurge.utils import load_json_resource, logger, run_powershell


class BloatwareManager:
    """Manages detection and removal of bloatware applications."""
    
    def __init__(self) -> None:
        """Initialize the bloatware manager."""
        self._bloatware_data: Dict[str, Any] = {}
        self._installed_packages: List[Dict[str, str]] = []
        self._load_bloatware_data()
    
    def _load_bloatware_data(self) -> None:
        """Load bloatware definitions from JSON."""
        self._bloatware_data = load_json_resource("winpurge/data/bloatware_list.json")
        if not self._bloatware_data:
            logger.error("Failed to load bloatware list")
            self._bloatware_data = {"packages": [], "wildcards": [], "categories": {}}
    
    def refresh_installed_packages(self) -> List[Dict[str, str]]:
        """
        Get list of currently installed Appx packages.
        
        Returns:
            List of installed package dictionaries.
        """
        try:
            success, output = run_powershell(
                "Get-AppxPackage | Select-Object Name, PackageFullName | ConvertTo-Json"
            )
            
            if success and output:
                packages = json.loads(output)
                if isinstance(packages, dict):
                    packages = [packages]
                self._installed_packages = packages
                return packages
            else:
                logger.warning("Could not retrieve installed packages")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get installed packages: {e}")
            return []
    
    def get_installed_bloatware(self) -> List[Dict[str, Any]]:
        """
        Get list of installed packages that match bloatware definitions.
        
        Returns:
            List of bloatware package details.
        """
        if not self._installed_packages:
            self.refresh_installed_packages()
        
        installed_names = {pkg.get("Name", ""): pkg for pkg in self._installed_packages}
        bloatware_list = []
        
        # Check defined packages
        for package in self._bloatware_data.get("packages", []):
            pkg_name = package.get("name", "")
            if pkg_name in installed_names:
                bloatware_list.append({
                    "name": pkg_name,
                    "full_name": installed_names[pkg_name].get("PackageFullName", ""),
                    "display_name": package.get("display_name", pkg_name),
                    "category": package.get("category", "other"),
                    "risk_level": package.get("risk_level", "safe"),
                    "description": package.get("description", ""),
                    "installed": True,
                })
        
        # Check wildcard patterns for OEM bloatware
        for wildcard in self._bloatware_data.get("wildcards", []):
            pattern = wildcard.get("pattern", "")
            for pkg_name, pkg_info in installed_names.items():
                if fnmatch.fnmatch(pkg_name, pattern):
                    if not any(b["name"] == pkg_name for b in bloatware_list):
                        bloatware_list.append({
                            "name": pkg_name,
                            "full_name": pkg_info.get("PackageFullName", ""),
                            "display_name": pkg_name.split(".")[-1],
                            "category": wildcard.get("category", "oem"),
                            "risk_level": wildcard.get("risk_level", "safe"),
                            "description": wildcard.get("description", "OEM software"),
                            "installed": True,
                        })
        
        return sorted(bloatware_list, key=lambda x: (x["category"], x["display_name"]))
    
    def get_categories(self) -> Dict[str, Dict[str, str]]:
        """
        Get bloatware category definitions.
        
        Returns:
            Dictionary of category details.
        """
        return self._bloatware_data.get("categories", {})
    
    def remove_package(
        self,
        package_name: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Remove a single Appx package.
        
        Args:
            package_name: Name of the package to remove.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback(f"Removing {package_name}...")
            
            # Remove for current user
            cmd = f'Get-AppxPackage -Name "{package_name}" | Remove-AppxPackage -ErrorAction SilentlyContinue'
            success, output = run_powershell(cmd)
            
            # Remove provisioned package (prevents reinstall)
            cmd_provisioned = f'Get-AppxProvisionedPackage -Online | Where-Object {{$_.DisplayName -eq "{package_name}"}} | Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue'
            run_powershell(cmd_provisioned)
            
            if success:
                logger.info(f"Removed package: {package_name}")
                return True, f"Successfully removed {package_name}"
            else:
                logger.warning(f"Could not remove {package_name}: {output}")
                return False, f"Failed to remove {package_name}: {output}"
                
        except Exception as e:
            logger.error(f"Error removing {package_name}: {e}")
            return False, f"Error removing {package_name}: {str(e)}"
    
    def remove_packages(
        self,
        packages: List[str],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        Remove multiple Appx packages.
        
        Args:
            packages: List of package names to remove.
            progress_callback: Optional callback(message, current, total).
            
        Returns:
            Tuple of (success_count, fail_count, error_messages).
        """
        success_count = 0
        fail_count = 0
        errors = []
        total = len(packages)
        
        for i, package in enumerate(packages, 1):
            if progress_callback:
                progress_callback(f"Removing {package}...", i, total)
            
            success, message = self.remove_package(package)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                errors.append(message)
        
        self.refresh_installed_packages()
        return success_count, fail_count, errors
    
    def uninstall_onedrive(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Completely uninstall OneDrive.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Stopping OneDrive processes...")
            
            # Kill OneDrive process
            run_powershell("Stop-Process -Name OneDrive -Force -ErrorAction SilentlyContinue")
            
            if progress_callback:
                progress_callback("Uninstalling OneDrive...")
            
            # Try standard uninstall paths
            uninstall_paths = [
                r"%SystemRoot%\System32\OneDriveSetup.exe /uninstall",
                r"%SystemRoot%\SysWOW64\OneDriveSetup.exe /uninstall",
                r"%LocalAppData%\Microsoft\OneDrive\OneDriveSetup.exe /uninstall",
            ]
            
            for path in uninstall_paths:
                expanded_path = run_powershell(f'cmd /c echo {path}')[1].strip()
                run_powershell(f'Start-Process -FilePath "{expanded_path}" -ArgumentList "/uninstall" -Wait -ErrorAction SilentlyContinue')
            
            if progress_callback:
                progress_callback("Removing OneDrive integration...")
            
            # Remove OneDrive from Explorer
            reg_commands = [
                r'Remove-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace\{018D5C66-4533-4307-9B53-224DE2ED1FE6}" -Force -ErrorAction SilentlyContinue',
                r'Remove-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace\{04271989-C4D2-4FCC-B9A5-CE4EAC280E91}" -Force -ErrorAction SilentlyContinue',
            ]
            
            for cmd in reg_commands:
                run_powershell(cmd)
            
            logger.info("OneDrive uninstalled successfully")
            return True, "OneDrive uninstalled successfully"
            
        except Exception as e:
            logger.error(f"Failed to uninstall OneDrive: {e}")
            return False, f"Failed to uninstall OneDrive: {str(e)}"
    
    def get_bloatware_count(self) -> int:
        """
        Get count of installed bloatware.
        
        Returns:
            Number of installed bloatware packages.
        """
        return len(self.get_installed_bloatware())


bloatware_manager = BloatwareManager()