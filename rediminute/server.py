"""
rediminute Server - Asynchronous TCP Echo Server

A lightweight, asynchronous TCP server that accepts connections
and echoes back messages to clients.
"""
import argparse
import asyncio
import logging
import signal
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rediminute.server")


class ConnectionState(Enum):
    """Connection states for client connections."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


@dataclass
class ClientConnection:
    """
    Client connection information.
    
    Note: This is intentionally not frozen to allow state updates,
    but we treat it as immutable for most operations.
    """
    writer: asyncio.StreamWriter
    address: tuple
    connected_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    state: ConnectionState = ConnectionState.CONNECTED


class AsyncServer:
    """
    Asynchronous TCP echo server with graceful shutdown and error handling.
    
    Features:
    - Accepts multiple simultaneous connections
    - Echoes back client messages
    - Handles graceful shutdown on system signals
    - Error handling to prevent crashes from client disconnections
    
    Raises:
        OSError: If the server cannot bind to the specified host and port
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 6379, idle_timeout: int = 300) -> None:
        """
        Initialize the server with configuration parameters.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
            idle_timeout: Seconds before closing an idle connection
        """
        self.host = host
        self.port = port
        self.idle_timeout = idle_timeout
        self.server: Optional[asyncio.Server] = None
        self.clients: Dict[asyncio.StreamWriter, ClientConnection] = {}
        self.is_running = False
    
    async def start(self) -> None:
        """
        Start the server and listen for connections.
        
        This is a blocking call that runs until the server is shutdown.
        
        Raises:
            OSError: If the server cannot bind to the specified host and port
        """
        self.is_running = True
        
        # Create the server
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
        
        logger.info(f"Server started on {self.host}:{self.port}")
        
        # Start serving
        if self.server:  # Type check to satisfy linter
            async with self.server:
                await self.server.serve_forever()
        else:
            raise RuntimeError("Server failed to initialize")
    
    async def stop(self) -> None:
        """
        Stop the server and close all client connections gracefully.
        
        This method ensures all resources are properly cleaned up.
        """
        if not self.is_running:
            return
        
        logger.info("Shutting down server...")
        self.is_running = False
        
        # Close all client connections
        close_tasks = []
        for client in list(self.clients.values()):
            if client.state == ConnectionState.CONNECTED:
                close_tasks.append(self._close_client_connection(client.writer))
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Close the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Server shutdown complete")
    
    async def _close_client_connection(self, writer: asyncio.StreamWriter) -> None:
        """
        Close a client connection gracefully.
        
        Args:
            writer: The StreamWriter associated with the client
        """
        try:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
        except Exception as e:
            # Just log the error, we're trying to clean up anyway
            logger.error(f"Error closing client connection: {e}")
        finally:
            # Update client state if it exists
            if writer in self.clients:
                client = self.clients[writer]
                # Update the state directly, as ClientConnection is mutable
                client.state = ConnectionState.DISCONNECTED
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """
        Handle a client connection by echoing back messages.
        
        Args:
            reader: Stream for reading client messages
            writer: Stream for sending responses
        """
        # Get client info for logging
        addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {addr}")
        
        # Register client
        self.clients[writer] = ClientConnection(writer=writer, address=addr)
        
        try:
            await self._process_client_messages(reader, writer)
        finally:
            # Clean up the connection
            await self._close_client_connection(writer)
            if writer in self.clients:
                del self.clients[writer]
            logger.info(f"Connection from {addr} closed")
    
    async def _process_client_messages(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """
        Process messages from a client, handling timeouts and errors.
        
        Args:
            reader: Stream for reading client messages
            writer: Stream for sending responses
        """
        addr = writer.get_extra_info('peername')
        
        while self.is_running:
            try:
                # Read data with timeout
                data = await asyncio.wait_for(
                    reader.readline(),
                    timeout=self.idle_timeout
                )
                
                if not data:  # Connection closed
                    break
                
                # Process the message (echo it back)
                message = data.decode().strip()
                logger.debug(f"Received: {message} from {addr}")
                
                # Send response
                writer.write(f"{message}\n".encode())
                await writer.drain()
                
            except asyncio.TimeoutError:
                logger.info(f"Client {addr} idle timeout")
                break
                
            except Exception as e:
                logger.error(f"Error handling client {addr}: {e}")
                break


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


def main() -> None:
    """
    Run the server with command line arguments.
    
    This function parses command line arguments, configures logging,
    and starts the server.
    """
    args = parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger("rediminute").setLevel(logging.DEBUG)
    
    # Create and run server
    server = AsyncServer(host=args.host, port=args.port, idle_timeout=args.timeout)
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
