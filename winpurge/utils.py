"""
WinPurge Utilities Module
Helper functions for admin checks, logging, and system operations.
"""

import logging
import subprocess
import ctypes
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from winpurge.constants import LOG_FILE, APPDATA_DIR, LOCALES_DIR, DEFAULT_LANGUAGE


def is_admin() -> bool:
    """
    Check if the current process has administrator privileges.
    
    Returns:
        bool: True if running as admin, False otherwise.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def request_admin() -> None:
    """
    Request administrator privileges by relaunching the application with UAC prompt.
    This function does not return if successful (process is replaced).
    """
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                os.sys.executable,
                os.sys.argv[0],
                None,
                1
            )
        except Exception as e:
            logging.error(f"Failed to request admin privileges: {e}")
        os.sys.exit()


def setup_logging() -> None:
    """
    Configure the logging system to write to the application log file.
    """
    log_format = "[%(asctime)s] %(levelname)s - %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.info(f"WinPurge started at {datetime.now().isoformat()}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: The module name.
    
    Returns:
        logging.Logger: A configured logger instance.
    """
    return logging.getLogger(name)


def load_locale(language: str = DEFAULT_LANGUAGE) -> Dict[str, Any]:
    """
    Load localization strings from JSON file.
    
    Args:
        language: Language code (en, de, fr, es, pl).
    
    Returns:
        Dict[str, Any]: Localization dictionary, falls back to English if file not found.
    """
    locale_file = LOCALES_DIR / f"{language}.json"
    
    if not locale_file.exists():
        locale_file = LOCALES_DIR / "en.json"
    
    try:
        with open(locale_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load localization {language}: {e}")
        return {}


def run_command(
    command: List[str],
    capture_output: bool = False,
    timeout: int = 30,
    check: bool = False
) -> tuple[int, str, str]:
    """
    Execute a system command safely with timeout.
    
    Args:
        command: Command and arguments as list.
        capture_output: If True, capture stdout and stderr.
        timeout: Command timeout in seconds.
        check: If True, raise exception on non-zero exit code.
    
    Returns:
        Tuple of (return_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            timeout=timeout,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logging.error(f"Command timeout: {' '.join(command)}")
        return -1, "", "Command timeout"
    except Exception as e:
        logging.error(f"Command execution failed: {e}")
        return -1, "", str(e)


def run_powershell(
    script: str,
    capture_output: bool = False,
    timeout: int = 30
) -> tuple[int, str, str]:
    """
    Execute a PowerShell script safely.
    
    Args:
        script: PowerShell script code.
        capture_output: If True, capture output.
        timeout: Command timeout in seconds.
    
    Returns:
        Tuple of (return_code, stdout, stderr).
    """
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", script
    ]
    return run_command(command, capture_output, timeout)


def format_bytes(bytes_size: int) -> str:
    """
    Convert bytes to human-readable format.
    
    Args:
        bytes_size: Size in bytes.
    
    Returns:
        str: Formatted size string (e.g., "1.5 GB", "256 MB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"


def get_system_info() -> Dict[str, Any]:
    """
    Get basic system information.
    
    Returns:
        Dict containing OS version, CPU, RAM, and disk info.
    """
    import platform
    import psutil
    
    try:
        return {
            "os": f"{platform.system()} {platform.release()}",
            "cpu": platform.processor(),
            "ram_total": format_bytes(psutil.virtual_memory().total),
            "ram_available": format_bytes(psutil.virtual_memory().available),
            "disk_total": format_bytes(psutil.disk_usage("C:").total),
            "disk_used": format_bytes(psutil.disk_usage("C:").used),
            "disk_free": format_bytes(psutil.disk_usage("C:").free)
        }
    except Exception as e:
        logging.error(f"Failed to get system info: {e}")
        return {}


def get_uptime() -> str:
    """
    Get system uptime.
    
    Returns:
        str: Human-readable uptime.
    """
    try:
        import psutil
        uptime_seconds = datetime.now().timestamp() - psutil.boot_time()
        days = int(uptime_seconds // (24 * 3600))
        hours = int((uptime_seconds % (24 * 3600)) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except Exception as e:
        logging.error(f"Failed to get uptime: {e}")
        return "Unknown"


def ensure_backup_dir() -> Path:
    """
    Ensure the backup directory exists and return its path.
    
    Returns:
        Path: The backup directory path.
    """
    backup_dir = APPDATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir
