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


HKEY_NAMES = {
    winreg.HKEY_LOCAL_MACHINE: "HKLM",
    winreg.HKEY_CURRENT_USER: "HKCU",
}

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

START_TYPE_MAP = {
    "Automatic": "auto",
    "Manual": "demand",
    "Disabled": "disabled",
    "0": "Boot",
    "1": "System",
    "2": "auto",
    "3": "demand",
    "4": "disabled",
}


class BackupManager:
    def __init__(self) -> None:
        try:
            BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create backups directory: {e}")

    def create_backup(self, description: str = "") -> Tuple[bool, str, Optional[str]]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = BACKUPS_DIR / timestamp

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)

            reg_backup_dir = backup_dir / "registry"
            reg_backup_dir.mkdir(exist_ok=True)
            reg_count = self._backup_registry(reg_backup_dir)

            svc_ok = self._backup_services(backup_dir / "services_backup.json")
            hosts_ok = self._backup_hosts(backup_dir / "hosts.backup")
            appx_ok = self._backup_appx_list(backup_dir / "appx_backup.json")

            contents = []
            if reg_count > 0:
                contents.append("registry")
            if svc_ok:
                contents.append("services_backup.json")
            if hosts_ok:
                contents.append("hosts.backup")
            if appx_ok:
                contents.append("appx_backup.json")

            metadata = {
                "timestamp": timestamp,
                "date": format_timestamp(),
                "description": description or "Manual backup",
                "contents": contents,
            }

            metadata_path = backup_dir / "metadata.json"
            metadata_path.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            logger.info(f"Backup created: {backup_dir}")
            return True, "Backup created successfully", str(backup_dir)

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            if backup_dir.exists():
                shutil.rmtree(backup_dir, ignore_errors=True)
            return False, f"Failed to create backup: {e}", None

    def _backup_registry(self, backup_dir: Path) -> int:
        count = 0
        for hkey, subkey in REGISTRY_KEYS_TO_BACKUP:
            try:
                hkey_name = HKEY_NAMES.get(hkey, "UNKNOWN")
                safe_filename = subkey.replace("\\", "_").replace("/", "_")
                reg_file = backup_dir / f"{hkey_name}_{safe_filename}.reg"
                full_key = f"{hkey_name}\\{subkey}"

                result = subprocess.run(
                    ["reg", "export", full_key, str(reg_file), "/y"],
                    capture_output=True,
                    text=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )

                if result.returncode == 0:
                    count += 1
                else:
                    logger.debug(f"Could not export {full_key}: key may not exist")
            except Exception as e:
                logger.debug(f"Failed to backup registry key {subkey}: {e}")
        return count

    def _backup_services(self, backup_file: Path) -> bool:
        try:
            success, output = run_powershell(
                "Get-Service | Select-Object Name, Status, StartType | ConvertTo-Json -Depth 3"
            )
            if not success or not output:
                logger.warning("Could not get services list for backup")
                return False

            services = json.loads(output)
            if isinstance(services, dict):
                services = [services]

            backup_file.write_text(
                json.dumps(services, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to backup services: {e}")
            return False

    def _backup_hosts(self, backup_file: Path) -> bool:
        try:
            if HOSTS_FILE.exists():
                shutil.copy2(HOSTS_FILE, backup_file)
                return True
            logger.warning("Hosts file not found")
            return False
        except Exception as e:
            logger.error(f"Failed to backup hosts file: {e}")
            return False

    def _backup_appx_list(self, backup_file: Path) -> bool:
        try:
            success, output = run_powershell(
                "Get-AppxPackage | Select-Object Name, PackageFullName | ConvertTo-Json -Depth 3"
            )
            if not success or not output:
                logger.warning("Could not get Appx packages list for backup")
                return False

            packages = json.loads(output)
            if isinstance(packages, dict):
                packages = [packages]

            backup_file.write_text(
                json.dumps(packages, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to backup Appx packages: {e}")
            return False

    def restore_backup(self, backup_path) -> Tuple[bool, str]:
        try:
            backup_path = Path(backup_path) if not isinstance(backup_path, Path) else backup_path

            if not backup_path.exists():
                return False, "Backup directory not found"

            errors: List[str] = []

            reg_dir = backup_path / "registry"
            if reg_dir.exists():
                for reg_file in reg_dir.glob("*.reg"):
                    try:
                        result = subprocess.run(
                            ["reg", "import", str(reg_file)],
                            capture_output=True,
                            text=True,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                        )
                        if result.returncode != 0:
                            errors.append(f"Failed to import {reg_file.name}")
                    except Exception as e:
                        errors.append(f"Error importing {reg_file.name}: {e}")

            hosts_backup = backup_path / "hosts.backup"
            if hosts_backup.exists():
                try:
                    shutil.copy2(hosts_backup, HOSTS_FILE)
                except Exception as e:
                    errors.append(f"Failed to restore hosts file: {e}")

            services_backup = backup_path / "services_backup.json"
            if services_backup.exists():
                svc_errors = self._restore_services(services_backup)
                errors.extend(svc_errors)

            if errors:
                logger.warning(f"Backup restored with {len(errors)} warnings")
                return True, f"Backup restored with {len(errors)} warnings"

            logger.info(f"Backup restored: {backup_path}")
            return True, "Backup restored successfully"

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False, f"Failed to restore backup: {e}"

    def _restore_services(self, backup_file: Path) -> List[str]:
        errors: List[str] = []
        try:
            data = json.loads(backup_file.read_text(encoding="utf-8"))

            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                return ["Invalid services backup format"]

            for service in data:
                if not isinstance(service, dict):
                    continue

                name = str(service.get("Name", "")).strip()
                start_type_raw = str(service.get("StartType", "")).strip()

                if not name or not start_type_raw:
                    continue

                sc_start_type = START_TYPE_MAP.get(start_type_raw, "demand")

                try:
                    result = subprocess.run(
                        ["sc", "config", name, f"start={sc_start_type}"],
                        capture_output=True,
                        text=True,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    if result.returncode != 0:
                        pass
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Failed to restore services: {e}")
            errors.append(f"Services restore error: {e}")

        return errors

    def get_backups(self) -> List[Dict[str, Any]]:
        backups: List[Dict[str, Any]] = []

        try:
            if not BACKUPS_DIR.exists():
                return backups

            for backup_dir in sorted(BACKUPS_DIR.iterdir(), reverse=True):
                if not backup_dir.is_dir():
                    continue

                metadata_file = backup_dir / "metadata.json"
                if not metadata_file.exists():
                    continue

                try:
                    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                except Exception as e:
                    logger.debug(f"Failed to read metadata for {backup_dir.name}: {e}")
                    continue

                try:
                    size_bytes = get_folder_size(backup_dir)
                except Exception:
                    size_bytes = 0

                contents = metadata.get("contents", [])
                if isinstance(contents, str):
                    contents = [contents]
                if not isinstance(contents, list):
                    contents = []

                backups.append({
                    "path": str(backup_dir),
                    "timestamp": str(metadata.get("timestamp", backup_dir.name)),
                    "date": str(metadata.get("date", "Unknown")),
                    "description": str(metadata.get("description", "")),
                    "contents": contents,
                    "size": format_size(size_bytes),
                    "size_bytes": size_bytes,
                })

        except Exception as e:
            logger.error(f"Failed to get backups list: {e}")

        return backups

    def delete_backup(self, backup_path) -> Tuple[bool, str]:
        try:
            backup_path = Path(backup_path) if not isinstance(backup_path, Path) else backup_path

            if not backup_path.exists():
                return False, "Backup not found"

            if not str(backup_path).startswith(str(BACKUPS_DIR)):
                return False, "Invalid backup path"

            shutil.rmtree(backup_path)
            logger.info(f"Backup deleted: {backup_path}")
            return True, "Backup deleted successfully"

        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False, f"Failed to delete backup: {e}"

    def get_last_backup_time(self) -> Optional[datetime]:
        backups = self.get_backups()
        if not backups:
            return None

        timestamp = backups[0].get("timestamp", "")
        if not timestamp:
            return None

        for fmt in ("%Y%m%d_%H%M%S", "%Y-%m-%d_%H:%M:%S", "%Y%m%d%H%M%S"):
            try:
                return datetime.strptime(timestamp, fmt)
            except ValueError:
                continue

        return None

    def get_backup_count(self) -> int:
        return len(self.get_backups())


backup_manager = BackupManager()