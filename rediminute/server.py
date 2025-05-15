"""
rediminute Server - Asynchronous TCP Echo Server

A lightweight, asynchronous TCP server that accepts connections
and echoes back messages to clients.
"""
import asyncio
import logging
import signal
import time
from contextlib import suppress as contextlib_suppress
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

# Default server configuration
DEFAULT_HOST = "0.0.0.0"  # Listen on all interfaces
DEFAULT_PORT = 8379       # Default server port
DEFAULT_TIMEOUT = 300     # Default idle timeout in seconds
CLEANUP_INTERVAL = 60     # Interval for checking stale connections

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
    connected_at: float = field(default_factory=lambda: time.time())
    last_active_at: float = field(default_factory=lambda: time.time())
    state: ConnectionState = ConnectionState.CONNECTED

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_active_at = time.time()

    @property
    def idle_time(self) -> float:
        """Get the time in seconds since the last activity."""
        return time.time() - self.last_active_at


class RediminuteServer:
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

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 idle_timeout: int = DEFAULT_TIMEOUT) -> None:
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
        self.server = None  # Type: Optional[asyncio.Server]
        self.clients: Dict[asyncio.StreamWriter, ClientConnection] = {}
        self.is_running = False
        self.cleanup_task = None  # Type: Optional[asyncio.Task]

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

        # Start periodic cleanup task
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())

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

        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            with contextlib_suppress(asyncio.CancelledError):
                await self.cleanup_task

        # Close all client connections
        close_tasks = []
        for client in list(self.clients.values()):
            if client.state == ConnectionState.CONNECTED:
                close_tasks.append(self._close_client_connection(client.writer))

        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

        # Clear the clients dictionary to prevent memory leaks
        self.clients.clear()

        # Close the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info("Server shutdown complete")

    async def _periodic_cleanup(self) -> None:
        """
        Periodically check for and clean up stale connections.

        This runs as a background task to ensure dead connections
        don't remain in the clients dictionary.
        """
        while self.is_running:
            try:
                # Wait for the next cleanup interval
                await asyncio.sleep(CLEANUP_INTERVAL)

                # Check for stale connections
                stale_writers = []
                time.time()

                for writer, client in list(self.clients.items()):
                    # Check if connection is stale
                    if (client.state == ConnectionState.DISCONNECTED or
                            client.idle_time > self.idle_timeout or
                            writer.is_closing()):
                        stale_writers.append(writer)

                # Clean up stale connections
                for writer in stale_writers:
                    if writer in self.clients:
                        addr = self.clients[writer].address
                        logger.info(f"Cleaning up stale connection from {addr}")
                        await self._close_client_connection(writer)
                        del self.clients[writer]

                logger.debug(
                    f"Cleanup complete: removed {len(stale_writers)} stale connections,"
                    f" {len(self.clients)} active"
                )

            except asyncio.CancelledError:
                # Task was cancelled, exit cleanly
                break
            except Exception as e:
                # Log any errors but keep the cleanup task running
                logger.error(f"Error in periodic cleanup: {e}")

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

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
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
        except Exception as e:
            logger.error(f"Unexpected error handling client {addr}: {e}")
        finally:
            # Clean up the connection
            try:
                await self._close_client_connection(writer)
                if writer in self.clients:
                    del self.clients[writer]
                logger.info(f"Connection from {addr} closed")
            except Exception as e:
                logger.error(f"Error during client cleanup for {addr}: {e}")
                # Force removal from clients dictionary to prevent leaks
                if writer in self.clients:
                    del self.clients[writer]

    async def _process_client_messages(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
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

                # Update last activity timestamp
                if writer in self.clients:
                    self.clients[writer].update_activity()

                # Process the message (echo it back)
                message = data.decode().strip()
                logger.debug(f"Received: {message} from {addr}")

                # Send response
                writer.write(f"{message}\n".encode())
                await writer.drain()

            except asyncio.TimeoutError:
                logger.info(f"Client {addr} idle timeout")
                break
            except ConnectionError as e:
                logger.info(f"Connection error for {addr}: {e}")
                break
            except Exception as e:
                logger.error(f"Error handling client {addr}: {e}")
                break
