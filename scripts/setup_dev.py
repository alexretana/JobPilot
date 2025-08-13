#!/usr/bin/env python3
"""
Development setup script for JobPilot.
Helps set up the development environment and validate everything is working.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Set up development environment."""
    print("🚀 JobPilot Development Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required. Current version:", sys.version)
        return 1
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Check if we're in the right directory
    if not Path("README.md").exists() or not Path("src").exists():
        print("❌ Please run this script from the JobPilot root directory")
        return 1
    
    print("✅ Running from correct directory")
    
    # Install minimal dependencies
    print("\n📦 Installing development dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return 1
    
    # Run validation
    print("\n🔍 Running setup validation...")
    try:
        result = subprocess.run([sys.executable, "scripts/test_setup.py"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Setup validation passed!")
            print("\n🎉 Development environment ready!")
            print("\nNext steps:")
            print("1. Copy .env.example to .env and configure as needed")
            print("2. Check out docs/phase-1-foundation-complete.md")
            print("3. Ready to start Phase 2: Discovery Engine!")
            return 0
        else:
            print("❌ Setup validation failed:")
            print(result.stdout)
            print(result.stderr)
            return 1
    except Exception as e:
        print(f"❌ Error running validation: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
