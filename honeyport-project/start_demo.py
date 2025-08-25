#!/usr/bin/env python3
"""
HoneyPort Quick Start Demo
Perfect for presentations - everything works out of the box
"""

import subprocess
import sys
import time
import threading
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def start_dashboard():
    """Start dashboard in background"""
    print("🚀 Starting dashboard...")
    subprocess.Popen([sys.executable, "run_dashboard.py"])
    time.sleep(3)  # Give dashboard time to start

def start_honeypot():
    """Start main honeypot"""
    print("🍯 Starting HoneyPort honeypot...")
    subprocess.run([sys.executable, "demo_presentation.py"])

def main():
    """Main startup function"""
    print("🍯 HoneyPort AI-Powered Honeypot - Quick Start")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("config.yaml").exists():
        print("❌ Please run this script from the honeyport-project directory")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Create required directories
    Path("logs").mkdir(exist_ok=True)
    Path("ai_models").mkdir(exist_ok=True)
    
    print("\n🎯 Starting HoneyPort Demo...")
    print("📊 Dashboard: http://localhost:8080 (admin/honeyport2024)")
    print("🍯 Honeypot: http://localhost:8888")
    print("=" * 60)
    
    # Start dashboard in background
    dashboard_thread = threading.Thread(target=start_dashboard, daemon=True)
    dashboard_thread.start()
    
    # Start main honeypot (blocking)
    try:
        start_honeypot()
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped")

if __name__ == "__main__":
    main()
