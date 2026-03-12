"""
PyInstaller Build Script for WinPurge
Compiles the Python application into a standalone .exe
"""

import subprocess
import sys
import os
from pathlib import Path

def build():
    """Build the application with PyInstaller."""
    
    script_dir = Path(__file__).parent
    icon_path = script_dir / "assets" / "icon.ico"
    
    # PyInstaller command
    command = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--add-data",
        f"{script_dir / 'assets'};assets",
        "--add-data",
        f"{script_dir / 'locales'};locales",
        "--add-data",
        f"{script_dir / 'winpurge' / 'data'};winpurge/data",
        "--name",
        "WinPurge",
        "--distpath",
        str(script_dir / "dist"),
        "--workpath",
        str(script_dir / "build"),
        "--specpath",
        str(script_dir),
        str(script_dir / "winpurge" / "main.py")
    ]
    
    # Add icon if it exists
    if icon_path.exists():
        command.insert(3, f"--icon={icon_path}")
    
    print("Building WinPurge...")
    print(f"Command: {' '.join(command)}\n")
    
    try:
        result = subprocess.run(command, check=False)
        
        if result.returncode == 0:
            print(f"\n[SUCCESS] Build successful!")
            print(f"Output: {script_dir / 'dist' / 'WinPurge.exe'}")
        else:
            print(f"\n[ERROR] Build failed with code {result.returncode}")
        
        return result.returncode
    
    except FileNotFoundError:
        print("[ERROR] PyInstaller not found. Install with: pip install pyinstaller")
        return 1
    except Exception as e:
        print(f"[ERROR] Build failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(build())
