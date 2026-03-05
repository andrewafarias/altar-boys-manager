#!/bin/bash
# Acolitos Project - Linux/Mac Setup and Run Script
# This script automatically sets up and runs the application on Linux/Mac machines

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the Python setup and run script
python3 setup_and_run.py

# Check if the script failed
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ An error occurred."
    exit 1
fi

exit 0
