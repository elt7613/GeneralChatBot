#!/usr/bin/env python3
"""
Standalone Conversation Analyzer Scheduler Daemon

This runs the conversation analyzer scheduler as a completely separate process
to avoid blocking LangGraph operations. This ensures optimal performance for
parallel processing in LangGraph while maintaining automatic conversation analysis.

Usage:
    python scheduler_daemon.py

This daemon will:
- Run independently of LangGraph dev server
- Automatically trigger conversation analysis 2 minutes before session expiry
- Support multi-user and multi-session scenarios
- Restart automatically if it fails
"""

import asyncio
import signal
import sys
import logging
import os
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scheduler_service import SchedulerServiceManager
from graph import create_scheduler_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scheduler_daemon.log')
    ]
)

logger = logging.getLogger(__name__)

class SchedulerDaemon:
    """Standalone scheduler daemon for conversation analysis."""
    
    def __init__(self):
        self.scheduler_manager = None
        self.running = False
        
    async def start(self):
        """Start the scheduler daemon."""
        try:
            logger.info("🚀 Starting Conversation Analyzer Scheduler Daemon...")
            logger.info(f"Process ID: {os.getpid()}")
            logger.info(f"Started at: {datetime.now()}")
            
            # Initialize scheduler manager
            self.scheduler_manager = SchedulerServiceManager()
            
            # Start scheduler with graph factory
            success = await self.scheduler_manager.start(create_scheduler_graph)
            
            if not success:
                logger.error("❌ Failed to start scheduler")
                return False
                
            logger.info("✅ Scheduler daemon started successfully")
            self.running = True
            
            # Keep daemon running
            while self.running:
                try:
                    await asyncio.sleep(30)  # Check every 30 seconds
                    
                    # Health check
                    status = await self.scheduler_manager.get_status()
                    if not status.get('is_running'):
                        logger.warning("⚠️ Scheduler stopped, restarting...")
                        await self.scheduler_manager.start(create_scheduler_graph)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                    
            return True
            
        except Exception as e:
            logger.error(f"❌ Daemon startup failed: {e}")
            return False
    
    async def stop(self):
        """Stop the scheduler daemon gracefully."""
        logger.info("🛑 Stopping Conversation Analyzer Scheduler Daemon...")
        self.running = False
        
        if self.scheduler_manager:
            try:
                await self.scheduler_manager.stop()
                logger.info("✅ Scheduler stopped gracefully")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")

# Global daemon instance for signal handling
daemon = SchedulerDaemon()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(daemon.stop())

async def main():
    """Main daemon entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start daemon
        success = await daemon.start()
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Daemon error: {e}")
        sys.exit(1)
    finally:
        await daemon.stop()

if __name__ == "__main__":
    print("🔄 Starting Conversation Analyzer Scheduler Daemon...")
    print("📝 Logs: scheduler_daemon.log")
    print("🛑 Stop with: Ctrl+C")
    print("-" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Scheduler daemon stopped")
    except Exception as e:
        print(f"\n❌ Daemon failed: {e}")
        sys.exit(1)
