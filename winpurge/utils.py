from winpurge.constants import LOG_FILE
import ctypes
import json
import logging
import os
import platform
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

from winpurge.constants import (
    APP_DATA_DIR,
    APP_NAME,
    CONFIG_FILE,
    DEFAULT_CONFIG,
    LOG_FILE,
)


def setup_logging() -> logging.Logger:
    """
    Set up application logging with file and console handlers.
    
    Returns:
        Configured logger instance.
    """
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(module)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


def is_admin() -> bool:
    """
    Check if the current process has administrator privileges.
    
    Returns:
        True if running as administrator, False otherwise.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin() -> None:
    """
    Restart the current application with administrator privileges.
    Uses Windows ShellExecute to trigger UAC prompt.
    """
    try:
        if sys.executable.endswith("python.exe") or sys.executable.endswith("pythonw.exe"):
            script = sys.argv[0]
            params = " ".join(sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1
            )
        else:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1
            )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to restart as admin: {e}")


def get_windows_version() -> Dict[str, str]:
    """
    Get detailed Windows version information.
    
    Returns:
        Dictionary containing Windows version details.
    """
    try:
        version = platform.version()
        release = platform.release()
        build = platform.win32_ver()[1]
        edition = get_windows_edition()
        
        return {
            "version": version,
            "release": release,
            "build": build,
            "edition": edition,
            "display": f"Windows {release} {edition} (Build {build})",
        }
    except Exception as e:
        logger.error(f"Failed to get Windows version: {e}")
        return {
            "version": "Unknown",
            "release": "Unknown",
            "build": "Unknown",
            "edition": "Unknown",
            "display": "Windows (Unknown Version)",
        }


def get_windows_edition() -> str:
    """
    Get Windows edition (Home, Pro, Enterprise, etc.).
    
    Returns:
        Windows edition string.
    """
    try:
        result = subprocess.run(
            ["wmic", "os", "get", "Caption"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        output = result.stdout.strip().split("\n")
        if len(output) > 1:
            caption = output[1].strip()
            if "Pro" in caption:
                return "Pro"
            elif "Enterprise" in caption:
                return "Enterprise"
            elif "Education" in caption:
                return "Education"
            elif "Home" in caption:
                return "Home"
            else:
                return "Unknown"
    except Exception:
        pass
    return "Unknown"


def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.
    
    Returns:
        Dictionary containing CPU, RAM, disk, and uptime info.
    """
    try:
        cpu_name = platform.processor() or "Unknown CPU"
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "Name"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            output = result.stdout.strip().split("\n")
            if len(output) > 1:
                cpu_name = output[1].strip()
        except Exception:
            pass
        
        ram = psutil.virtual_memory()
        ram_total = ram.total / (1024 ** 3)
        ram_used = ram.used / (1024 ** 3)
        ram_percent = ram.percent
        
        disk = psutil.disk_usage("C:")
        disk_total = disk.total / (1024 ** 3)
        disk_used = disk.used / (1024 ** 3)
        disk_percent = disk.percent
        
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_str = format_timedelta(uptime)
        
        power_plan = get_power_plan()
        
        return {
            "cpu": cpu_name,
            "ram_total": f"{ram_total:.1f} GB",
            "ram_used": f"{ram_used:.1f} GB",
            "ram_percent": ram_percent,
            "disk_total": f"{disk_total:.0f} GB",
            "disk_used": f"{disk_used:.0f} GB",
            "disk_percent": disk_percent,
            "uptime": uptime_str,
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return {
            "cpu": "Unknown",
            "ram_total": "Unknown",
            "ram_used": "Unknown",
            "ram_percent": 0,
            "disk_total": "Unknown",
            "disk_used": "Unknown",
            "disk_percent": 0,
            "uptime": "Unknown",
        }


def get_power_plan() -> str:
    """
    Get the currently active power plan name.
    
    Returns:
        Name of the active power plan.
    """
    try:
        result = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        output = result.stdout.strip()
        if "(" in output and ")" in output:
            start = output.index("(") + 1
            end = output.index(")")
            return output[start:end]
    except Exception:
        pass
    return "Unknown"


def format_timedelta(td: timedelta) -> str:
    """
    Format a timedelta into a human-readable string.
    
    Args:
        td: Timedelta to format.
        
    Returns:
        Formatted string (e.g., "2 days, 5 hours").
    """
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0 and days == 0:
        parts.append(f"{minutes} min")
    
    return ", ".join(parts) if parts else "< 1 min"


def format_size(size_bytes: int) -> str:
    """
    Format bytes into human-readable size.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Formatted string (e.g., "1.5 GB").
    """
    if size_bytes < 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def run_powershell(command: str, admin: bool = False) -> Tuple[bool, str]:
    """
    Execute a PowerShell command.
    
    Args:
        command: PowerShell command to execute.
        admin: Whether to run with elevated privileges.
        
    Returns:
        Tuple of (success, output/error).
    """
    try:
        full_command = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-Command", command
        ]
        
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()
    except Exception as e:
        logger.error(f"PowerShell command failed: {e}")
        return False, str(e)


def run_command(command: List[str]) -> Tuple[bool, str]:
    """
    Execute a system command.
    
    Args:
        command: Command and arguments as a list.
        
    Returns:
        Tuple of (success, output/error).
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return False, str(e)


def load_config() -> Dict[str, Any]:
    """
    Load application configuration from file.
    
    Returns:
        Configuration dictionary.
    """
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
    
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """
    Save application configuration to file.
    
    Args:
        config: Configuration dictionary to save.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def get_folder_size(path: Path) -> int:
    """
    Calculate the total size of a folder.
    
    Args:
        path: Path to the folder.
        
    Returns:
        Total size in bytes.
    """
    total_size = 0
    try:
        if path.exists():
            for item in path.rglob("*"):
                try:
                    if item.is_file():
                        total_size += item.stat().st_size
                except (PermissionError, OSError):
                    continue
    except Exception as e:
        logger.error(f"Failed to calculate folder size for {path}: {e}")
    return total_size


def delete_folder_contents(path: Path) -> Tuple[int, int]:
    """
    Delete all contents of a folder.
    
    Args:
        path: Path to the folder.
        
    Returns:
        Tuple of (bytes_freed, files_deleted).
    """
    bytes_freed = 0
    files_deleted = 0
    
    try:
        if not path.exists():
            return 0, 0
        
        for item in path.iterdir():
            try:
                if item.is_file():
                    size = item.stat().st_size
                    item.unlink()
                    bytes_freed += size
                    files_deleted += 1
                elif item.is_dir():
                    sub_bytes, sub_files = delete_folder_contents(item)
                    bytes_freed += sub_bytes
                    files_deleted += sub_files
                    try:
                        item.rmdir()
                    except OSError:
                        pass
            except (PermissionError, OSError) as e:
                logger.debug(f"Could not delete {item}: {e}")
                continue
    except Exception as e:
        logger.error(f"Failed to delete contents of {path}: {e}")
    
    return bytes_freed, files_deleted


def get_resource_path(relative_path: str) -> Path:
    """
    Get the absolute path to a resource, works for dev and PyInstaller.
    
    Args:
        relative_path: Relative path to the resource.
        
    Returns:
        Absolute path to the resource.
    """
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).parent.parent
    
    return base_path / relative_path


def load_json_resource(relative_path: str) -> Dict[str, Any]:
    """
    Load a JSON resource file.
    
    Args:
        relative_path: Relative path to the JSON file.
        
    Returns:
        Parsed JSON as dictionary.
    """
    try:
        path = get_resource_path(relative_path)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON resource {relative_path}: {e}")
        return {}


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime for display.
    
    Args:
        dt: Datetime to format, defaults to now.
        
    Returns:
        Formatted datetime string.
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_relative_time(dt: datetime) -> str:
    """
    Get a human-readable relative time string.
    
    Args:
        dt: Datetime to compare against now.
        
    Returns:
        Relative time string (e.g., "2 hours ago").
    """
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d")


class LocaleManager:
    """Manages localization and string translations."""
    
    _instance: Optional["LocaleManager"] = None
    _strings: Dict[str, Any] = {}
    _current_locale: str = "en"
    
    def __new__(cls) -> "LocaleManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if not self._strings:
            self.load_locale("en")
    
    def load_locale(self, locale: str) -> bool:
        """
        Load a locale file.
        
        Args:
            locale: Locale code (e.g., "en", "de").
            
        Returns:
            True if loaded successfully.
        """
        try:
            path = get_resource_path(f"locales/{locale}.json")
            with open(path, "r", encoding="utf-8") as f:
                self._strings = json.load(f)
                self._current_locale = locale
                logger.info(f"Loaded locale: {locale}")
                return True
        except Exception as e:
            logger.error(f"Failed to load locale {locale}: {e}")
            if locale != "en":
                return self.load_locale("en")
            return False
    
    def get(self, key: str, **kwargs: Any) -> str:
        """
        Get a localized string by key path.
        
        Args:
            key: Dot-separated key path (e.g., "home.title").
            **kwargs: Format arguments for string interpolation.
            
        Returns:
            Localized string or key if not found.
        """
        try:
            parts = key.split(".")
            value = self._strings
            
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, key)
                else:
                    return key
            
            if isinstance(value, str):
                if kwargs:
                    try:
                        return value.format(**kwargs)
                    except KeyError:
                        return value
                return value
            return key
        except Exception:
            return key
    
    @property
    def current_locale(self) -> str:
        """Get the current locale code."""
        return self._current_locale


def get_locale() -> LocaleManager:
    """Get the locale manager instance."""
    return LocaleManager()


def t(key: str, **kwargs: Any) -> str:
    """
    Shorthand function for getting translated strings.
    
    Args:
        key: Translation key path.
        **kwargs: Format arguments.
        
    Returns:
        Translated string.
    """
    return get_locale().get(key, **kwargs)