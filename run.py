"""Entry point: `python run.py` from the project root."""
import sys
import os
from pathlib import Path

# Ensure the 'src' directory is in the Python path so we can import 'aiwriter'
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from aiwriter.app import main

if __name__ == "__main__":
    main()
