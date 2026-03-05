#!/usr/bin/env python
"""
Cross-platform setup and run script for Acolitos project.
Handles virtual environment creation, dependency installation, and application execution.
Works on both Windows and Linux machines.
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path

# Get the root project directory (one level up from scripts)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = PROJECT_ROOT / "scripts"
VENV_DIR = PROJECT_ROOT / "venv"
DATA_DIR = PROJECT_ROOT / "data"
DATA_FILE = DATA_DIR / "acolitos_data.json"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
MAIN_SCRIPT = PROJECT_ROOT / "main.py"
GENERATE_DATA_SCRIPT = SCRIPT_DIR / "generate_data.py"

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MAC = platform.system() == "Darwin"

# Virtual environment executable paths
if IS_WINDOWS:
    PYTHON_EXECUTABLE = VENV_DIR / "Scripts" / "python.exe"
    PIP_EXECUTABLE = VENV_DIR / "Scripts" / "pip.exe"
else:
    PYTHON_EXECUTABLE = VENV_DIR / "bin" / "python"
    PIP_EXECUTABLE = VENV_DIR / "bin" / "pip"


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(text):
    """Print a step message."""
    print(f"\n▶️  {text}")


def print_success(text):
    """Print a success message."""
    print(f"✅ {text}")


def print_error(text):
    """Print an error message."""
    print(f"❌ {text}")


def print_info(text):
    """Print an info message."""
    print(f"ℹ️  {text}")


def run_command(command, description=""):
    """Run a shell command."""
    if description:
        print_step(description)
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            shell=IS_WINDOWS
        )
        return True
    except subprocess.CalledProcessError as e:
        if description:
            print_error(f"Failed to {description}")
        print(f"Error: {e.stderr}")
        return False


def create_venv():
    """Create virtual environment if it doesn't exist."""
    if VENV_DIR.exists():
        print_info("Virtual environment already exists")
        return True
    
    print_step("Creating virtual environment...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            capture_output=True
        )
        print_success("Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False


def install_dependencies():
    """Install required packages from requirements.txt."""
    if not REQUIREMENTS_FILE.exists():
        print_info("No requirements.txt found, skipping dependency installation")
        return True
    
    print_step("Installing dependencies...")
    
    try:
        subprocess.run(
            [str(PIP_EXECUTABLE), "install", "-r", str(REQUIREMENTS_FILE)],
            check=True,
            capture_output=True
        )
        print_success("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def generate_initial_data():
    """Generate initial data if it doesn't exist."""
    if DATA_FILE.exists():
        print_info("Data file already exists, skipping generation")
        return True
    
    if not GENERATE_DATA_SCRIPT.exists():
        print_error(f"Script {GENERATE_DATA_SCRIPT} not found")
        return False
    
    print_step("Generating initial data...")
    
    try:
        subprocess.run(
            [str(PYTHON_EXECUTABLE), str(GENERATE_DATA_SCRIPT)],
            check=True,
            cwd=str(SCRIPT_DIR)
        )
        print_success("Initial data generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to generate initial data: {e}")
        return False


def run_main_application():
    """Run the main application."""
    if not MAIN_SCRIPT.exists():
        print_error(f"Main script {MAIN_SCRIPT} not found")
        return False
    
    print_step("Starting application...")
    
    try:
        # Run without capturing output so the user can see the application
        subprocess.run(
            [str(PYTHON_EXECUTABLE), str(MAIN_SCRIPT)],
            check=True,
            cwd=str(SCRIPT_DIR)
        )
        print_success("Application completed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Application error: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
        return True


def main():
    """Main entry point."""
    print_header(f"ACOLITOS PROJECT SETUP & RUN")
    print_info(f"Platform: {platform.system()} ({platform.release()})")
    print_info(f"Python: {sys.version.split()[0]}")
    
    # Step 1: Create virtual environment
    if not create_venv():
        print_error("Failed to create virtual environment")
        return False
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print_error("Failed to install dependencies")
        return False
    
    # Step 3: Generate initial data if needed
    if not generate_initial_data():
        print_error("Failed to generate initial data")
        return False
    
    # Step 4: Run the main application
    print_header("STARTING APPLICATION")
    if not run_main_application():
        print_error("Application failed to run")
        return False
    
    print_header("SETUP & RUN COMPLETED")
    print_success("Everything completed successfully!")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
