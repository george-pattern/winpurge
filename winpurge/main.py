"""
WinPurge Main Entry Point
Application start script.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from winpurge.gui.app import main

if __name__ == "__main__":
    main()
