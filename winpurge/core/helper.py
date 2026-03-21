import sys
from pathlib import Path
from chacha_flow import ImageKeyStorage

def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and PyInstaller bundle.
    
    Args:
        relative_path: Path relative to project root (e.g., "assets/")
    
    Returns:
        Absolute path to the resource
    """
    if getattr(sys, 'frozen', False):

        base_path = Path(sys._MEIPASS)
    else:

        base_path = Path(__file__).parent.parent.parent
    
    return base_path / relative_path


def get_asset_path(filename: str) -> Path:
    """Shortcut for getting asset paths."""
    return get_resource_path(f"assets/{filename}")

def load_logotype() -> None:
    """Load logotype image key."""
    logo_path = get_asset_path("logo.png")
    ImageKeyStorage.load_key_from_image(str(logo_path))

def get_locale_path(filename: str) -> Path:
    """Shortcut for getting locale paths."""
    return get_resource_path(f"locales/{filename}")


def get_data_path(filename: str) -> Path:
    """Shortcut for getting data file paths."""
    return get_resource_path(f"winpurge/data/{filename}")