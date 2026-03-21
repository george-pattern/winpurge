import ctypes
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from winpurge.constants import (
    DELIVERY_OPTIMIZATION,
    PREFETCH_DIR,
    SOFTWARE_DISTRIBUTION,
    WINDOWS_TEMP,
)
from winpurge.utils import delete_folder_contents, format_size, get_folder_size, logger


@dataclass
class CleanupItem:
    id: str
    name: str
    path: Optional[Path]
    size: int = 0
    size_display: str = "Calculating..."
    safe: bool = True
    pattern: Optional[str] = None
    category: str = "other"
    description: str = ""
    file_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CleanupManager:
    def __init__(self) -> None:
        self._user_temp = Path(os.environ.get("TEMP", ""))
        self._thumbnail_cache = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Explorer"

    def get_cleanup_items(self) -> List[Dict[str, Any]]:
        items = [
            CleanupItem(
                id="user_temp",
                name="Temporary Files",
                path=self._user_temp,
                safe=True,
                category="temp",
                description=str(self._user_temp) if str(self._user_temp) else "User temporary files",
            ),
            CleanupItem(
                id="windows_temp",
                name="Windows Temp",
                path=WINDOWS_TEMP,
                safe=True,
                category="temp",
                description=str(WINDOWS_TEMP),
            ),
            CleanupItem(
                id="prefetch",
                name="Prefetch Cache",
                path=PREFETCH_DIR,
                safe=True,
                category="cache",
                description=str(PREFETCH_DIR),
            ),
            CleanupItem(
                id="update_cache",
                name="Windows Update Cache",
                path=SOFTWARE_DISTRIBUTION,
                safe=True,
                category="updates",
                description=str(SOFTWARE_DISTRIBUTION),
            ),
            CleanupItem(
                id="delivery_opt",
                name="Delivery Optimization Cache",
                path=DELIVERY_OPTIMIZATION,
                safe=True,
                category="updates",
                description=str(DELIVERY_OPTIMIZATION),
            ),
            CleanupItem(
                id="thumbnail_cache",
                name="Thumbnail Cache",
                path=self._thumbnail_cache,
                safe=True,
                pattern="thumbcache_*.db",
                category="cache",
                description=str(self._thumbnail_cache),
            ),
            CleanupItem(
                id="recycle_bin",
                name="Recycle Bin",
                path=None,
                safe=True,
                category="recycle",
                description="System recycle bin",
            ),
        ]
        return [item.to_dict() for item in items]

    def calculate_sizes(
        self,
        items: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Dict[str, Any]]:
        for item in items:
            try:
                if progress_callback:
                    progress_callback(f"Calculating {item.get('name', 'item')}...")

                item_id = item.get("id")
                path = item.get("path")
                pattern = item.get("pattern")

                if item_id == "recycle_bin":
                    size, file_count = self._get_recycle_bin_stats()
                elif pattern and path and Path(path).exists():
                    size, file_count = self._get_pattern_stats(Path(path), pattern)
                elif path and Path(path).exists():
                    size, file_count = self._get_folder_stats(Path(path))
                else:
                    size, file_count = 0, 0

                item["size"] = size
                item["file_count"] = file_count
                item["size_display"] = format_size(size)
            except Exception as e:
                logger.debug(f"Could not calculate size for {item.get('name')}: {e}")
                item["size"] = 0
                item["file_count"] = 0
                item["size_display"] = "Unknown"

        return items

    def _get_folder_stats(self, path: Path) -> Tuple[int, int]:
        size = get_folder_size(path)
        count = 0
        try:
            for _ in path.rglob("*"):
                count += 1
        except Exception:
            pass
        return size, count

    def _get_pattern_stats(self, path: Path, pattern: str) -> Tuple[int, int]:
        total_size = 0
        file_count = 0
        try:
            for file in path.glob(pattern):
                try:
                    if file.is_file():
                        total_size += file.stat().st_size
                        file_count += 1
                except (PermissionError, OSError):
                    continue
        except Exception:
            pass
        return total_size, file_count

    def _get_recycle_bin_stats(self) -> Tuple[int, int]:
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
                return int(info.i64Size), int(info.i64NumItems)
        except Exception as e:
            logger.debug(f"Could not get Recycle Bin stats: {e}")

        return 0, 0

    def clean_item(
        self,
        item: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, int, str]:
        try:
            name = item.get("name", "item")
            if progress_callback:
                progress_callback(f"Cleaning {name}...")

            item_id = item.get("id")
            path = item.get("path")
            pattern = item.get("pattern")

            if item_id == "recycle_bin":
                bytes_freed = self._empty_recycle_bin()
                return True, bytes_freed, "Emptied Recycle Bin"

            if pattern and path and Path(path).exists():
                bytes_freed = self._clean_pattern(Path(path), pattern)
                return True, bytes_freed, f"Cleaned {name}"

            if path and Path(path).exists():
                bytes_freed, _ = delete_folder_contents(Path(path))
                return True, bytes_freed, f"Cleaned {name}"

            return True, 0, f"{name} already clean"
        except PermissionError:
            return False, 0, f"Permission denied for {item.get('name', 'item')}"
        except Exception as e:
            logger.error(f"Failed to clean {item.get('name', 'item')}: {e}")
            return False, 0, f"Failed to clean {item.get('name', 'item')}: {e}"

    def _clean_pattern(self, path: Path, pattern: str) -> int:
        bytes_freed = 0
        try:
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
        try:
            size_before, _ = self._get_recycle_bin_stats()
            flags = 0x00000001 | 0x00000002 | 0x00000004
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
            if result == 0 or result == -2147418113:
                logger.info("Recycle Bin emptied")
                return size_before
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
        total_bytes = 0
        items_cleaned = 0
        errors: List[str] = []
        total = len(items)

        for i, item in enumerate(items, 1):
            if progress_callback:
                progress_callback(f"Cleaning {item.get('name', 'item')}...", i, total)
            success, bytes_freed, message = self.clean_item(item)
            if success:
                total_bytes += bytes_freed
                items_cleaned += 1
            else:
                errors.append(message)

        return total_bytes, items_cleaned, errors

    def get_total_cleanable_size(self) -> int:
        items = self.calculate_sizes(self.get_cleanup_items())
        return sum(int(item.get("size", 0)) for item in items)


cleanup_manager = CleanupManager()