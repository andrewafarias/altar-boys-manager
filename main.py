#!/usr/bin/env python3
"""Entry point for Acolito Manager application."""

import sys
from pathlib import Path

# Add src directory to path so we can import acolito_manager
src_dir = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(src_dir))

from acolito_manager.ui.app import App

if __name__ == "__main__":
    app = App()
    app.run()
