"""
WinPurge Backup Module
Handles creation and restoration of system backups before making changes.
"""

import json
import shutil
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

from winpurge.constants import BACKUP_DIR
from winpurge.utils import run_command, format_bytes, get_logger

logger = get_logger(__name__)


class BackupManager:
    """Manager for creating and restoring system backups."""
    
    def __init__(self):
        """Initialize the backup manager."""
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> Optional[Path]:
        """
        Create a comprehensive system backup.
        
        Returns:
            Path to the backup directory, or None if failed.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / timestamp
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Creating backup at {backup_path}")
            
            # Backup registry keys
            self._backup_registry(backup_path)
            
            # Backup hosts file
            self._backup_hosts_file(backup_path)
            
            # Backup service states
            self._backup_services(backup_path)
            
            # Create metadata
            self._create_metadata(backup_path)
            
            logger.info(f"Backup created successfully at {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            return None
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore a system backup.
        
        Args:
            backup_path: Path to the backup directory to restore.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            logger.info(f"Restoring backup from {backup_path}")
            
            # Restore registry keys
            self._restore_registry(backup_path)
            
            # Restore hosts file
            self._restore_hosts_file(backup_path)
            
            # Restore service states
            self._restore_services(backup_path)
            
            logger.info("Backup restored successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.
        
        Returns:
            List of backup information dictionaries.
        """
        backups = []
        
        try:
            for backup_dir in sorted(self.backup_dir.iterdir(), reverse=True):
                if backup_dir.is_dir():
                    # Get backup metadata
                    metadata_file = backup_dir / "metadata.json"
                    
                    if metadata_file.exists():
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                    else:
                        metadata = {
                            "timestamp": backup_dir.name,
                            "created": backup_dir.name
                        }
                    
                    # Calculate backup size
                    total_size = sum(
                        f.stat().st_size
                        for f in backup_dir.rglob("*")
                        if f.is_file()
                    )
                    
                    backups.append({
                        "path": str(backup_dir),
                        "timestamp": metadata.get("timestamp"),
                        "created": metadata.get("created"),
                        "size": format_bytes(total_size),
                        "size_bytes": total_size
                    })
        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def delete_backup(self, backup_path: Path) -> bool:
        """
        Delete a backup directory.
        
        Args:
            backup_path: Path to the backup directory to delete.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if backup_path.exists() and backup_path.is_dir():
                shutil.rmtree(backup_path)
                logger.info(f"Backup deleted: {backup_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
        
        return False
    
    def _backup_registry(self, backup_path: Path) -> None:
        """
        Backup important registry keys to .reg files.
        
        Args:
            backup_path: Path to save registry backup.
        """
        registry_keys = [
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection",
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\CloudContent",
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo",
            r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            r"HKCU\SOFTWARE\Microsoft\Input\TIPC",
            r"HKCU\SOFTWARE\Microsoft\Personalization\Settings"
        ]
        
        reg_path = backup_path / "registry"
        reg_path.mkdir(exist_ok=True)
        
        for key in registry_keys:
            try:
                # Export registry key safely
                key_name = key.replace("\\", "_").replace(":", "")
                output_file = reg_path / f"{key_name}.reg"
                
                command = ["reg", "export", key, str(output_file), "/y"]
                run_command(command)
                logger.debug(f"Backed up registry key: {key}")
            
            except Exception as e:
                logger.warning(f"Failed to backup registry key {key}: {e}")
    
    def _restore_registry(self, backup_path: Path) -> None:
        """
        Restore registry keys from backup files.
        
        Args:
            backup_path: Path to the backup directory.
        """
        reg_path = backup_path / "registry"
        
        if not reg_path.exists():
            return
        
        for reg_file in reg_path.glob("*.reg"):
            try:
                command = ["reg", "import", str(reg_file)]
                run_command(command)
                logger.debug(f"Restored registry from {reg_file.name}")
            
            except Exception as e:
                logger.warning(f"Failed to restore registry from {reg_file}: {e}")
    
    def _backup_hosts_file(self, backup_path: Path) -> None:
        """
        Backup the Windows hosts file.
        
        Args:
            backup_path: Path to save hosts file backup.
        """
        hosts_file = Path("C:\\Windows\\System32\\drivers\\etc\\hosts")
        backup_file = backup_path / "hosts.backup"
        
        try:
            if hosts_file.exists():
                shutil.copy2(hosts_file, backup_file)
                logger.debug("Backed up hosts file")
        
        except Exception as e:
            logger.warning(f"Failed to backup hosts file: {e}")
    
    def _restore_hosts_file(self, backup_path: Path) -> None:
        """
        Restore the Windows hosts file from backup.
        
        Args:
            backup_path: Path to the backup directory.
        """
        backup_file = backup_path / "hosts.backup"
        hosts_file = Path("C:\\Windows\\System32\\drivers\\etc\\hosts")
        
        try:
            if backup_file.exists():
                shutil.copy2(backup_file, hosts_file)
                logger.debug("Restored hosts file")
        
        except Exception as e:
            logger.warning(f"Failed to restore hosts file: {e}")
    
    def _backup_services(self, backup_path: Path) -> None:
        """
        Backup current service states.
        
        Args:
            backup_path: Path to save services backup.
        """
        try:
            script = """
            Get-Service | Select-Object -Property Name, Status, StartType | 
            ConvertTo-Json |
            Out-File -FilePath $args[0] -Encoding UTF8
            """
            
            services_file = backup_path / "services.json"
            command = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command", script,
                str(services_file)
            ]
            
            run_command(command)
            logger.debug("Backed up service states")
        
        except Exception as e:
            logger.warning(f"Failed to backup services: {e}")
    
    def _restore_services(self, backup_path: Path) -> None:
        """
        Restore service states from backup.
        
        Args:
            backup_path: Path to the backup directory.
        """
        services_file = backup_path / "services.json"
        
        if not services_file.exists():
            return
        
        try:
            with open(services_file, "r") as f:
                services = json.load(f)
            
            # Restore service states (limited to key services)
            key_services = ["DiagTrack", "dmwappushservice", "MapsBroker"]
            
            for service in services:
                if service.get("Name") in key_services:
                    try:
                        start_type = service.get("StartType", "Manual")
                        command = [
                            "powershell",
                            "-NoProfile",
                            "-ExecutionPolicy", "Bypass",
                            "-Command",
                            f'Set-Service -Name {service.get("Name")} -StartupType {start_type}'
                        ]
                        
                        run_command(command)
                    
                    except Exception as e:
                        logger.warning(f"Failed to restore service {service.get('Name')}: {e}")
        
        except Exception as e:
            logger.warning(f"Failed to restore services: {e}")
    
    def _create_metadata(self, backup_path: Path) -> None:
        """
        Create backup metadata file.
        
        Args:
            backup_path: Path to save metadata.
        """
        try:
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0"
            }
            
            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
        
        except Exception as e:
            logger.warning(f"Failed to create metadata: {e}")
