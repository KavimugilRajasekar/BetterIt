"""AI Writing Assistant — system-wide grammar correction via hotkey."""

import os
import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller onefile. """
    try:
        # PyInstaller creates a temporary folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal development mode
        # Relative to the project root (which is where run.py is)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    return os.path.join(base_path, relative_path)

__version__ = "0.1.0"
