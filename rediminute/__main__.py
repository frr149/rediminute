"""
Command-line entry point for the rediminute server.

This module handles parsing command line arguments and
starting up the server with the appropriate configuration.
"""
import argparse
import asyncio
import logging
import sys

from rediminute.server import RediminuteServer, logger


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="rediminute Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=6379, help="Port to listen on")
    parser.add_argument("--timeout", type=int, default=300, help="Idle timeout in seconds")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    return parser.parse_args()


async def run_server(args: argparse.Namespace) -> None:
    """
    Create and run the server with the given arguments.
    
    Args:
        args: Command line arguments
    """
    # Set log level
    if args.debug:
        logging.getLogger("rediminute").setLevel(logging.DEBUG)
    
    # Create and run server
    server = RediminuteServer(host=args.host, port=args.port, idle_timeout=args.timeout)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1)


def main() -> None:
    """
    Parse arguments and run the server.
    
    This is the main entry point for the command line interface.
    """
    args = parse_args()
    
    try:
        asyncio.run(run_server(args))
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main() 