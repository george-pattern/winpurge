"""
WinPurge Cleanup Module
Handles disk cleanup and temporary file removal.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict

from winpurge.utils import run_command, format_bytes, get_logger

logger = get_logger(__name__)


class CleanupManager:
    """Manager for disk cleanup operations."""
    
    def __init__(self):
        """Initialize the cleanup manager."""
        self.cleanup_paths = {
            "temp_files": Path(Path.home() / "AppData\\Local\\Temp"),
            "windows_temp": Path("C:\\Windows\\Temp"),
            "prefetch": Path("C:\\Windows\\Prefetch"),
            "update_cache": Path("C:\\Windows\\SoftwareDistribution\\Download"),
            "thumbnail_cache": Path(Path.home() / "AppData\\Local\\Microsoft\\Windows\\Explorer"),
            "font_cache": Path("C:\\Windows\\System32\\DriverStore\\FileRepository")
        }
    
    def analyze_cleanup(self) -> Dict[str, Dict]:
        """
        Analyze disk space that can be freed.
        
        Returns:
            Dictionary with cleanup statistics.
        """
        results = {}
        total_size = 0
        
        for name, path in self.cleanup_paths.items():
            try:
                if path.exists():
                    size = self._get_directory_size(path)
                    results[name] = {
                        "path": str(path),
                        "size": size,
                        "size_formatted": format_bytes(size)
                    }
                    total_size += size
            except Exception as e:
                logger.warning(f"Failed to analyze {name}: {e}")
                results[name] = {
                    "path": str(path),
                    "size": 0,
                    "size_formatted": "0 B",
                    "error": str(e)
                }
        
        results["total"] = {
            "size": total_size,
            "size_formatted": format_bytes(total_size)
        }
        
        return results
    
    def cleanup_selected(
        self,
        cleanup_items: list,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, any]:
        """
        Clean up selected items.
        
        Args:
            cleanup_items: List of items to clean (keys from cleanup_paths).
            progress_callback: Optional callback for progress updates.
        
        Returns:
            Dictionary with cleanup results.
        """
        results = {
            "successful": [],
            "failed": [],
            "total_freed": 0
        }
        
        for item in cleanup_items:
            if item not in self.cleanup_paths:
                continue
            
            if progress_callback:
                progress_callback(f"Cleaning {item}...")
            
            try:
                path = self.cleanup_paths[item]
                
                if path.exists():
                    # Calculate size before cleanup
                    initial_size = self._get_directory_size(path)
                    
                    # Attempt cleanup
                    self._cleanup_path(path)
                    
                    # Calculate freed space
                    remaining_size = self._get_directory_size(path)
                    freed_size = initial_size - remaining_size
                    
                    results["successful"].append(item)
                    results["total_freed"] += freed_size
                    
                    logger.info(f"Cleaned {item}: freed {format_bytes(freed_size)}")
            
            except Exception as e:
                logger.error(f"Failed to clean {item}: {e}")
                results["failed"].append(item)
        
        logger.info(f"Cleanup complete: {format_bytes(results['total_freed'])} freed")
        return results
    
    def empty_recycle_bin(self) -> bool:
        """
        Empty the Recycle Bin.
        
        Returns:
            bool: True if successful.
        """
        try:
            logger.info("Emptying Recycle Bin...")
            
            script = """
            $RecycleBin = (New-Object -ComObject Shell.Application).NameSpace(10)
            $RecycleBin.Self.InvokeVerb("Empty")
            """
            
            import subprocess
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True
            )
            
            logger.info("Recycle Bin emptied successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to empty Recycle Bin: {e}")
            return False
    
    def _get_directory_size(self, path: Path) -> int:
        """
        Calculate total size of a directory.
        
        Args:
            path: Path to the directory.
        
        Returns:
            int: Total size in bytes.
        """
        total_size = 0
        
        try:
            if path.exists():
                for file_path in path.rglob("*"):
                    try:
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        pass
        except Exception as e:
            logger.warning(f"Error calculating directory size: {e}")
        
        return total_size
    
    def _cleanup_path(self, path: Path) -> None:
        """
        Clean up files in a directory.
        
        Args:
            path: Path to clean.
        """
        if not path.exists():
            return
        
        try:
            # Try to remove all files in the directory
            for file_path in path.glob("*"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path, ignore_errors=True)
                except (OSError, PermissionError, RuntimeError):
                    # Skip files we can't delete
                    pass
        
        except Exception as e:
            logger.warning(f"Error cleaning path {path}: {e}")
