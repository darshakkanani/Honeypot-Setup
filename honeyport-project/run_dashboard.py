#!/usr/bin/env python3
"""
HoneyPort Dashboard Runner
Standalone script to run the dashboard
"""

import uvicorn
import yaml
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run the dashboard"""
    # Load configuration
    try:
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ config.yaml not found. Please ensure it exists in the project root.")
        sys.exit(1)
    
    dashboard_config = config.get('dashboard', {})
    host = dashboard_config.get('host', '127.0.0.1')
    port = dashboard_config.get('port', 8080)
    
    print(f"🚀 Starting HoneyPort Dashboard on http://{host}:{port}")
    print(f"📊 Admin credentials: admin / honeyport2024")
    print("=" * 60)
    
    # Run the dashboard
    uvicorn.run(
        "dashboard.app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
