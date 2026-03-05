@echo off
REM Acolitos Project - Windows Setup and Run Script
REM This script automatically sets up and runs the application on Windows machines

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

REM Run the Python setup and run script
python setup_and_run.py

REM Check if the script failed
if %errorlevel% neq 0 (
    echo.
    echo ❌ An error occurred. Press any key to exit...
    pause
    exit /b %errorlevel%
)

exit /b 0
