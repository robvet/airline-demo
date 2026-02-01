"""
Application Runner with Crash-Safe Port Cleanup

This script wraps uvicorn to ensure port cleanup happens even on crashes.
Use this instead of calling uvicorn directly.

Usage:
    python -m app.run
    
    Or from start-backend.ps1:
    python -m app.run
"""
import sys
import atexit
import signal
from .utils.port_cleanup import PortCleanup
from .config import settings


PORT = settings.server_port


def cleanup_on_exit():
    """Cleanup handler registered with atexit."""
    print(f"\n[CLEANUP] Releasing port {PORT}...")
    PortCleanup.kill_process_on_port(PORT)


def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) and SIGTERM gracefully."""
    print(f"\n[SIGNAL] Received signal {signum}, cleaning up...")
    cleanup_on_exit()
    sys.exit(0)


def main():
    """Run the application with crash-safe port cleanup."""
    import uvicorn
    
    # Register cleanup for normal exit
    atexit.register(cleanup_on_exit)
    
    # Register signal handlers for Ctrl+C and termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Clean port before starting (in case of previous crash)
    print(f"[STARTUP] Cleaning port {PORT}...")
    PortCleanup.kill_process_on_port(PORT)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=PORT,
            reload=True,
        )
    except Exception as e:
        print(f"[CRASH] Application crashed: {e}")
        raise
    finally:
        # This runs even if uvicorn crashes
        cleanup_on_exit()


if __name__ == "__main__":
    main()
