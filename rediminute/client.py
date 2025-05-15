"""
Simple client to test the rediminute server.

This module provides a command-line client for connecting to
and interacting with the rediminute server.
"""
import argparse
import asyncio
import sys
from enum import Enum
from typing import Optional, Tuple


class CommandType(Enum):
    """Types of commands that can be entered by the user."""
    NORMAL = "normal"  # Regular message to be sent to server
    EXIT = "exit"      # Command to exit the client


class ClientCommand:
    """
    Represents a command entered by the user.
    
    This class parses and validates user input to determine
    if it's a control command (like exit) or a message to send.
    """
    
    def __init__(self, raw_input: str) -> None:
        """
        Parse the user input into a command.
        
        Args:
            raw_input: The string entered by the user
        """
        self.raw_input = raw_input.strip()
        
        if self.raw_input.lower() in ("exit", "quit", "q"):
            self.command_type = CommandType.EXIT
        else:
            self.command_type = CommandType.NORMAL
    
    @property
    def is_exit(self) -> bool:
        """Check if this command is an exit command."""
        return self.command_type == CommandType.EXIT
    
    @property
    def message(self) -> str:
        """Get the message to send to the server."""
        return self.raw_input


async def connect_to_server(host: str, port: int) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """
    Connect to the rediminute server.
    
    Args:
        host: The server hostname or IP
        port: The server port
        
    Returns:
        A tuple of (StreamReader, StreamWriter) for the connection
        
    Raises:
        ConnectionError: If the connection to the server fails
    """
    try:
        reader, writer = await asyncio.open_connection(host, port)
        return reader, writer
    except (ConnectionRefusedError, TimeoutError) as e:
        raise ConnectionError(f"Failed to connect to {host}:{port}: {e}") from e


async def run_client(host: str = "127.0.0.1", port: int = 6379) -> None:
    """
    Connect to server and manage the session with user interaction.
    
    This function handles user input, sends messages to the server,
    and displays server responses until the user exits.
    
    Args:
        host: The server hostname or IP
        port: The server port
        
    Raises:
        ConnectionError: If the connection to the server fails
    """
    writer = None
    try:
        # Connect to server
        reader, writer = await connect_to_server(host, port)
        print(f"Connected to {host}:{port}")
        
        # Handle user input and server responses
        while True:
            # Get user input
            command = ClientCommand(input("> "))
            
            if command.is_exit:
                break
            
            # Send message to server
            writer.write(f"{command.message}\n".encode())
            await writer.drain()
            
            # Get response from server
            response = await reader.readline()
            if not response:
                print("Server closed the connection")
                break
            
            # Print response
            print(f"Response: {response.decode().strip()}")
            
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except asyncio.CancelledError:
        # Handle cancellation (Ctrl+C)
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        if writer is not None:
            writer.close()
            await writer.wait_closed()
        print("Disconnected")


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="rediminute Client")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=6379, help="Server port")
    
    return parser.parse_args()


def main() -> None:
    """
    Parse command line arguments and run the client.
    
    This function handles the client lifecycle including startup,
    running, and proper error handling.
    """
    args = parse_args()
    
    try:
        asyncio.run(run_client(args.host, args.port))
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main() 