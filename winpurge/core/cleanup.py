"""
WinPurge Cleanup Module
Handles disk cleanup and temporary file removal.
"""

import ctypes
import os
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from winpurge.constants import (
    DELIVERY_OPTIMIZATION,
    PREFETCH_DIR,
    SOFTWARE_DISTRIBUTION,
    WINDOWS_TEMP,
)
from winpurge.utils import (
    delete_folder_contents,
    format_size,
    get_folder_size,
    logger,
)


class CleanupManager:
    """Manages disk cleanup operations."""
    
    def __init__(self) -> None:
        """Initialize the cleanup manager."""
        self._user_temp = Path(os.environ.get("TEMP", ""))
        self._thumbnail_cache = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Explorer"
    
    def get_cleanup_items(self) -> List[Dict[str, Any]]:
        """
        Get list of cleanable items with their sizes.
        
        Returns:
            List of cleanup item dictionaries.
        """
        items = [
            {
                "id": "user_temp",
                "name": "Temporary Files",
                "path": self._user_temp,
                "size": 0,
                "size_display": "Calculating...",
                "safe": True,
            },
            {
                "id": "windows_temp",
                "name": "Windows Temp",
                "path": WINDOWS_TEMP,
                "size": 0,
                "size_display": "Calculating...",
                "safe": True,
            },
            {
                "id": "prefetch",
                "name": "Prefetch Cache",
                "path": PREFETCH_DIR,
                "size": 0,
                "size_display": "Calculating...",
                "safe": True,
            },
            {
                "id": "update_cache",
                "name": "Windows Update Cache",
                "path": SOFTWARE_DISTRIBUTION,
                "size": 0,
                "size_display": "Calculating...",
                "safe": True,
            },
            {
                "id": "delivery_opt",
                "name": "Delivery Optimization Cache",
                "path": DELIVERY_OPTIMIZATION,
                "size": 0,
                "size_display": "Calculating...",
                "safe": True,
            },
            {
                "id": "thumbnail_cache",
                "name": "Thumbnail Cache",
                "path": self._thumbnail_cache,
                "size": 0,
                "size_display": "Calculating...",
                "safe": True,
                "pattern": "thumbcache_*.db",
            },
            {
                "id": "recycle_bin",
                "name": "Recycle Bin",
                "path": None,
                "size": 0,
                "size_display": "Calculating...",
                "safe": True,
            },
        ]
        
        return items
    
    def calculate_sizes(
        self,
        items: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculate sizes for cleanup items.
        
        Args:
            items: List of cleanup items.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Updated items with sizes.
        """
        for item in items:
            if progress_callback:
                progress_callback(f"Calculating {item['name']}...")
            
            try:
                if item["id"] == "recycle_bin":
                    item["size"] = self._get_recycle_bin_size()
                elif item.get("pattern"):
                    item["size"] = self._get_pattern_size(item["path"], item["pattern"])
                elif item["path"] and item["path"].exists():
                    item["size"] = get_folder_size(item["path"])
                else:
                    item["size"] = 0
                
                item["size_display"] = format_size(item["size"])
                
            except Exception as e:
                logger.debug(f"Could not calculate size for {item['name']}: {e}")
                item["size"] = 0
                item["size_display"] = "Unknown"
        
        return items
    
    def _get_pattern_size(self, path: Path, pattern: str) -> int:
        """Get total size of files matching a pattern."""
        total_size = 0
        try:
            if path.exists():
                for file in path.glob(pattern):
                    try:
                        if file.is_file():
                            total_size += file.stat().st_size
                    except (PermissionError, OSError):
                        continue
        except Exception:
            pass
        return total_size
    
    def _get_recycle_bin_size(self) -> int:
        """Get total size of Recycle Bin."""
        try:
            from ctypes import wintypes
            
            shell32 = ctypes.windll.shell32
            
            class SHQUERYRBINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("i64Size", ctypes.c_longlong),
                    ("i64NumItems", ctypes.c_longlong),
                ]
            
            info = SHQUERYRBINFO()
            info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
            
            result = shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
            
            if result == 0:
                return info.i64Size
                
        except Exception as e:
            logger.debug(f"Could not get Recycle Bin size: {e}")
        
        return 0
    
    def clean_item(
        self,
        item: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, int, str]:
        """
        Clean a single cleanup item.
        
        Args:
            item: Cleanup item dictionary.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, bytes_freed, message).
        """
        try:
            if progress_callback:
                progress_callback(f"Cleaning {item['name']}...")
            
            if item["id"] == "recycle_bin":
                bytes_freed = self._empty_recycle_bin()
                return True, bytes_freed, f"Emptied Recycle Bin"
            
            elif item.get("pattern"):
                bytes_freed = self._clean_pattern(item["path"], item["pattern"])
                return True, bytes_freed, f"Cleaned {item['name']}"
            
            elif item["path"] and item["path"].exists():
                bytes_freed, _ = delete_folder_contents(item["path"])
                return True, bytes_freed, f"Cleaned {item['name']}"
            
            return True, 0, f"{item['name']} already clean"
            
        except PermissionError:
            return False, 0, f"Permission denied for {item['name']}"
        except Exception as e:
            logger.error(f"Failed to clean {item['name']}: {e}")
            return False, 0, f"Failed to clean {item['name']}: {str(e)}"
    
    def _clean_pattern(self, path: Path, pattern: str) -> int:
        """Clean files matching a pattern."""
        bytes_freed = 0
        try:
            if path.exists():
                for file in path.glob(pattern):
                    try:
                        if file.is_file():
                            size = file.stat().st_size
                            file.unlink()
                            bytes_freed += size
                    except (PermissionError, OSError):
                        continue
        except Exception:
            pass
        return bytes_freed
    
    def _empty_recycle_bin(self) -> int:
        """Empty the Recycle Bin and return bytes freed."""
        try:
            size_before = self._get_recycle_bin_size()
            
            # SHEmptyRecycleBin flags
            SHERB_NOCONFIRMATION = 0x00000001
            SHERB_NOPROGRESSUI = 0x00000002
            SHERB_NOSOUND = 0x00000004
            
            flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
            
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
            
            if result == 0 or result == -2147418113:  # S_OK or "bin already empty"
                logger.info("Recycle Bin emptied")
                return size_before
            else:
                logger.warning(f"SHEmptyRecycleBin returned: {result}")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to empty Recycle Bin: {e}")
            return 0
    
    def clean_items(
        self,
        items: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        Clean multiple items.
        
        Args:
            items: List of cleanup items.
            progress_callback: Optional callback(message, current, total).
            
        Returns:
            Tuple of (total_bytes_freed, items_cleaned, error_messages).
        """
        total_bytes = 0
        items_cleaned = 0
        errors = []
        total = len(items)
        
        for i, item in enumerate(items, 1):
            if progress_callback:
                progress_callback(f"Cleaning {item['name']}...", i, total)
            
            success, bytes_freed, message = self.clean_item(item)
            
            if success:
                total_bytes += bytes_freed
                items_cleaned += 1
            else:
                errors.append(message)
        
        return total_bytes, items_cleaned, errors
    
    def get_total_cleanable_size(self) -> int:
        """
        Get total size of all cleanable items.
        
        Returns:
            Total cleanable size in bytes.
        """
        items = self.get_cleanup_items()
        items = self.calculate_sizes(items)
        return sum(item.get("size", 0) for item in items)


cleanup_manager = CleanupManager()