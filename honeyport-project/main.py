#!/usr/bin/env python3
"""
HoneyPort Main Entry Point
Complete AI-powered honeypot with blockchain logging
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.honeyport import HoneyPortEngine

class HoneyPortMain:
    """Main application controller"""
    
    def __init__(self):
        self.engine = None
        self.running = False
    
    async def start(self):
        """Start the HoneyPort system"""
        print("🍯 Starting HoneyPort AI-Powered Honeypot System")
        print("=" * 60)
        
        try:
            # Initialize honeypot engine
            self.engine = HoneyPortEngine("config.yaml")
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.running = True
            
            # Start the honeypot engine
            await self.engine.start()
            
        except KeyboardInterrupt:
            print("\n🛑 Received shutdown signal")
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            await self.shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, initiating shutdown...")
        self.running = False
    
    async def shutdown(self):
        """Graceful shutdown"""
        print("🔄 Shutting down HoneyPort...")
        
        if self.engine:
            await self.engine.stop()
        
        print("✅ HoneyPort shutdown complete")

def main():
    """Main entry point"""
    app = HoneyPortMain()
    
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
