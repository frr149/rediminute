"""
Entry point for the RedIMinute server.
"""
import asyncio
import logging
import sys
from rediminute.server import RedIMinuteServer


def main():
    """Run the server with command-line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RedIMinute Server")
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host address to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=6379, 
        help="Port to listen on (default: 6379)"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=300, 
        help="Idle connection timeout in seconds (default: 300)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and run server
    server = RedIMinuteServer(
        host=args.host, 
        port=args.port, 
        idle_timeout=args.timeout
    )
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main() 