#!/usr/bin/env python3
"""
WinPurge Build Script
Builds the application into a single executable using PyInstaller.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def clean_build_artifacts() -> None:
    """Remove previous build artifacts."""
    artifacts = ["build", "dist", "WinPurge.spec"]
    for artifact in artifacts:
        path = Path(artifact)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"Removed: {artifact}")


def build_executable() -> int:
    """Build the executable using PyInstaller."""
    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--icon=assets/icon.ico",
        "--add-data=assets;assets",
        "--add-data=locales;locales",
        "--add-data=winpurge/data;winpurge/data",
        "--name=WinPurge",
        "--clean",
        "--noconfirm",
        # Hidden imports for CustomTkinter
        "--hidden-import=PIL._tkinter_finder",
        "--collect-all=customtkinter",
        "winpurge/main.py",
    ]
    
    print("Building WinPurge executable...")
    print(f"Command: {' '.join(pyinstaller_args)}")
    
    result = subprocess.run(pyinstaller_args, capture_output=False)
    return result.returncode


def main() -> None:
    """Main build process."""
    print("=" * 60)
    print("WinPurge Build Script")
    print("=" * 60)
    
    # Check if running from project root
    if not Path("winpurge/main.py").exists():
        print("Error: Run this script from the project root directory.")
        sys.exit(1)
    
    # Check for required files
    required_files = [
        "assets/icon.ico",
        "locales/en.json",
        "winpurge/data/bloatware_list.json",
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"Warning: Missing file: {file}")
    
    # Clean previous builds
    print("\nCleaning previous build artifacts...")
    clean_build_artifacts()
    
    # Build
    print("\nStarting build process...")
    return_code = build_executable()
    
    if return_code == 0:
        exe_path = Path("dist/WinPurge.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n" + "=" * 60)
            print("BUILD SUCCESSFUL!")
            print(f"Output: {exe_path.absolute()}")
            print(f"Size: {size_mb:.2f} MB")
            print("=" * 60)
        else:
            print("\nBuild completed but executable not found.")
            sys.exit(1)
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()