"""
WinPurge Backup Module
Handles creating and restoring system backups before modifications.
"""

import json
import shutil
import subprocess
import winreg
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from winpurge.constants import (
    BACKUPS_DIR,
    HOSTS_FILE,
    REG_ADVERTISING_INFO,
    REG_CLOUD_CONTENT,
    REG_CONTENT_DELIVERY,
    REG_COPILOT,
    REG_CORTANA,
    REG_EXPLORER_ADVANCED,
    REG_GAME_BAR,
    REG_GAME_CONFIG,
    REG_GAME_DVR,
    REG_INPUT_PERSONALIZATION,
    REG_MOUSE,
    REG_PERSONALIZATION,
    REG_RECALL,
    REG_SYSTEM_POLICIES,
    REG_TELEMETRY_CURRENT,
    REG_TELEMETRY_POLICY,
)
from winpurge.utils import (
    format_size,
    format_timestamp,
    get_folder_size,
    logger,
    run_powershell,
)


class BackupManager:
    """Manages system backups and restoration."""
    
    REGISTRY_KEYS_TO_BACKUP: List[Tuple[int, str]] = [
        (winreg.HKEY_LOCAL_MACHINE, REG_TELEMETRY_POLICY),
        (winreg.HKEY_LOCAL_MACHINE, REG_TELEMETRY_CURRENT),
        (winreg.HKEY_LOCAL_MACHINE, REG_CLOUD_CONTENT),
        (winreg.HKEY_LOCAL_MACHINE, REG_ADVERTISING_INFO),
        (winreg.HKEY_LOCAL_MACHINE, REG_SYSTEM_POLICIES),
        (winreg.HKEY_CURRENT_USER, REG_EXPLORER_ADVANCED),
        (winreg.HKEY_CURRENT_USER, REG_INPUT_PERSONALIZATION),
        (winreg.HKEY_CURRENT_USER, REG_PERSONALIZATION),
        (winreg.HKEY_CURRENT_USER, REG_CONTENT_DELIVERY),
        (winreg.HKEY_CURRENT_USER, REG_CORTANA),
        (winreg.HKEY_CURRENT_USER, REG_COPILOT),
        (winreg.HKEY_CURRENT_USER, REG_RECALL),
        (winreg.HKEY_CURRENT_USER, REG_GAME_BAR),
        (winreg.HKEY_CURRENT_USER, REG_GAME_DVR),
        (winreg.HKEY_CURRENT_USER, REG_GAME_CONFIG),
        (winreg.HKEY_CURRENT_USER, REG_MOUSE),
    ]
    
    def __init__(self) -> None:
        """Initialize the backup manager."""
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, description: str = "") -> Tuple[bool, str, Optional[Path]]:
        """
        Create a full system backup.
        
        Args:
            description: Optional description for the backup.
            
        Returns:
            Tuple of (success, message, backup_path).
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = BACKUPS_DIR / timestamp
        
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup registry
            reg_backup_dir = backup_dir / "registry"
            reg_backup_dir.mkdir(exist_ok=True)
            self._backup_registry(reg_backup_dir)
            
            # Backup services state
            self._backup_services(backup_dir / "services_backup.json")
            
            # Backup hosts file
            self._backup_hosts(backup_dir / "hosts.backup")
            
            # Backup installed Appx packages list
            self._backup_appx_list(backup_dir / "appx_backup.json")
            
            # Save backup metadata
            metadata = {
                "timestamp": timestamp,
                "date": format_timestamp(),
                "description": description,
                "contents": [
                    "registry",
                    "services_backup.json",
                    "hosts.backup",
                    "appx_backup.json",
                ],
            }
            
            with open(backup_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created: {backup_dir}")
            return True, f"Backup created successfully", backup_dir
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            if backup_dir.exists():
                shutil.rmtree(backup_dir, ignore_errors=True)
            return False, f"Failed to create backup: {str(e)}", None
    
    def _backup_registry(self, backup_dir: Path) -> None:
        """
        Export registry keys to .reg files.
        
        Args:
            backup_dir: Directory to save registry backups.
        """
        hkey_names = {
            winreg.HKEY_LOCAL_MACHINE: "HKLM",
            winreg.HKEY_CURRENT_USER: "HKCU",
        }
        
        for hkey, subkey in self.REGISTRY_KEYS_TO_BACKUP:
            try:
                hkey_name = hkey_names.get(hkey, "UNKNOWN")
                safe_filename = subkey.replace("\\", "_").replace("/", "_")
                reg_file = backup_dir / f"{hkey_name}_{safe_filename}.reg"
                
                full_key = f"{hkey_name}\\{subkey}"
                
                result = subprocess.run(
                    ["reg", "export", full_key, str(reg_file), "/y"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                
                if result.returncode != 0:
                    logger.debug(f"Could not export {full_key}: key may not exist")
                    
            except Exception as e:
                logger.debug(f"Failed to backup registry key {subkey}: {e}")
    
    def _backup_services(self, backup_file: Path) -> None:
        """
        Save current service states to JSON.
        
        Args:
            backup_file: Path to save services backup.
        """
        try:
            success, output = run_powershell(
                "Get-Service | Select-Object Name, Status, StartType | ConvertTo-Json"
            )
            
            if success and output:
                services = json.loads(output)
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(services, f, indent=2)
                logger.debug("Services backup created")
            else:
                logger.warning("Could not get services list for backup")
                
        except Exception as e:
            logger.error(f"Failed to backup services: {e}")
    
    def _backup_hosts(self, backup_file: Path) -> None:
        """
        Copy current hosts file.
        
        Args:
            backup_file: Path to save hosts backup.
        """
        try:
            if HOSTS_FILE.exists():
                shutil.copy2(HOSTS_FILE, backup_file)
                logger.debug("Hosts file backup created")
            else:
                logger.warning("Hosts file not found")
                
        except Exception as e:
            logger.error(f"Failed to backup hosts file: {e}")
    
    def _backup_appx_list(self, backup_file: Path) -> None:
        """
        Save list of installed Appx packages.
        
        Args:
            backup_file: Path to save Appx list.
        """
        try:
            success, output = run_powershell(
                "Get-AppxPackage | Select-Object Name, PackageFullName | ConvertTo-Json"
            )
            
            if success and output:
                packages = json.loads(output)
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(packages, f, indent=2)
                logger.debug("Appx packages backup created")
            else:
                logger.warning("Could not get Appx packages list for backup")
                
        except Exception as e:
            logger.error(f"Failed to backup Appx packages: {e}")
    
    def restore_backup(self, backup_path: Path) -> Tuple[bool, str]:
        """
        Restore a system backup.
        
        Args:
            backup_path: Path to the backup directory.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if not backup_path.exists():
                return False, "Backup directory not found"
            
            errors = []
            
            # Restore registry
            reg_dir = backup_path / "registry"
            if reg_dir.exists():
                for reg_file in reg_dir.glob("*.reg"):
                    try:
                        result = subprocess.run(
                            ["reg", "import", str(reg_file)],
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        if result.returncode != 0:
                            errors.append(f"Failed to import {reg_file.name}")
                    except Exception as e:
                        errors.append(f"Error importing {reg_file.name}: {e}")
            
            # Restore hosts file
            hosts_backup = backup_path / "hosts.backup"
            if hosts_backup.exists():
                try:
                    shutil.copy2(hosts_backup, HOSTS_FILE)
                except Exception as e:
                    errors.append(f"Failed to restore hosts file: {e}")
            
            # Restore services
            services_backup = backup_path / "services_backup.json"
            if services_backup.exists():
                self._restore_services(services_backup)
            
            if errors:
                return True, f"Backup restored with warnings: {'; '.join(errors)}"
            
            logger.info(f"Backup restored: {backup_path}")
            return True, "Backup restored successfully"
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False, f"Failed to restore backup: {str(e)}"
    
    def _restore_services(self, backup_file: Path) -> None:
        """
        Restore service states from backup.
        
        Args:
            backup_file: Path to services backup JSON.
        """
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                services = json.load(f)
            
            for service in services:
                if isinstance(service, dict):
                    name = service.get("Name", "")
                    start_type = service.get("StartType", "")
                    
                    if name and start_type:
                        start_type_map = {
                            "Automatic": "auto",
                            "Manual": "demand",
                            "Disabled": "disabled",
                        }
                        
                        sc_start_type = start_type_map.get(str(start_type), "demand")
                        
                        subprocess.run(
                            ["sc", "config", name, f"start={sc_start_type}"],
                            capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        
        except Exception as e:
            logger.error(f"Failed to restore services: {e}")
    
    def get_backups(self) -> List[Dict[str, Any]]:
        """
        Get list of available backups.
        
        Returns:
            List of backup metadata dictionaries.
        """
        backups = []
        
        try:
            for backup_dir in sorted(BACKUPS_DIR.iterdir(), reverse=True):
                if backup_dir.is_dir():
                    metadata_file = backup_dir / "metadata.json"
                    
                    if metadata_file.exists():
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        
                        size = get_folder_size(backup_dir)
                        
                        backups.append({
                            "path": backup_dir,
                            "timestamp": metadata.get("timestamp", ""),
                            "date": metadata.get("date", "Unknown"),
                            "description": metadata.get("description", ""),
                            "contents": metadata.get("contents", []),
                            "size": format_size(size),
                            "size_bytes": size,
                        })
                        
        except Exception as e:
            logger.error(f"Failed to get backups list: {e}")
        
        return backups
    
    def delete_backup(self, backup_path: Path) -> Tuple[bool, str]:
        """
        Delete a backup.
        
        Args:
            backup_path: Path to the backup directory.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if backup_path.exists():
                shutil.rmtree(backup_path)
                logger.info(f"Backup deleted: {backup_path}")
                return True, "Backup deleted successfully"
            return False, "Backup not found"
            
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False, f"Failed to delete backup: {str(e)}"
    
    def get_last_backup_time(self) -> Optional[datetime]:
        """
        Get the timestamp of the most recent backup.
        
        Returns:
            Datetime of last backup or None.
        """
        backups = self.get_backups()
        if backups:
            try:
                timestamp = backups[0].get("timestamp", "")
                return datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            except Exception:
                pass
        return None


backup_manager = BackupManager()