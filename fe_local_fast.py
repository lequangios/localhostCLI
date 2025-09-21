#!/usr/bin/env python3
"""
Fast wrapper script for FE Local CLI
This script provides a faster alternative to the PyInstaller binary
by running the Python script directly with the virtual environment.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Paths
    venv_python = script_dir / "env" / "bin" / "python"
    main_script = script_dir / "mphm_cli.py"
    
    # Check if virtual environment exists
    if not venv_python.exists():
        print("❌ Virtual environment not found. Please run ./build.sh first.")
        sys.exit(1)
    
    # Check if main script exists
    if not main_script.exists():
        print("❌ Main script not found: mphm_cli.py")
        sys.exit(1)
    
    # Run the main script with virtual environment
    try:
        # Pass all command line arguments to the main script
        cmd = [str(venv_python), str(main_script)] + sys.argv[1:]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()
