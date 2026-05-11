"""
OpenMacro XTernal - Python Edition
Main entry point.

Copyright 2026 (@anorexc) on Discord. All rights reserved.
Python port with modern CustomTkinter GUI.

Usage:
    python main.py
"""

import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openmacro_python.ui.app import OpenMacroApp


def main():
    """Launch the OpenMacro XTernal application."""
    app = OpenMacroApp()
    app.mainloop()


if __name__ == "__main__":
    main()
