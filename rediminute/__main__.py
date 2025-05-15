"""
Command-line entry point for the rediminute server.

This module handles parsing command line arguments and
starting up the server with the appropriate configuration.
"""
import argparse
import asyncio
import logging
import sys

from rediminute.server import (
    RediminuteServer,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    logger
)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="rediminute Server")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host to bind to (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to listen on (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Idle timeout in seconds (default: {DEFAULT_TIMEOUT})"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
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