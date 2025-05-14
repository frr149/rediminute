#!/usr/bin/env python3
"""
RedIMinute Server - Asynchronous TCP Server
"""
import asyncio
import json
import logging
import signal
from typing import Dict, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rediminute.server")


class RedIMinuteServer:
    """
    Asynchronous TCP server that accepts JSON messages and processes commands.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 6379, 
                 idle_timeout: int = 300):
        """
        Initialize the server.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
            idle_timeout: Timeout for idle connections in seconds
        """
        self.host = host
        self.port = port
        self.idle_timeout = idle_timeout
        self.server = None
        self.storage: Dict[str, Dict[str, str]] = {"global": {}}
        self.clients: Set[asyncio.StreamWriter] = set()
        self.running = False
        
    async def start(self):
        """Start the server and handle connections."""
        self.running = True
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )

        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        logger.info(f"Server started on {self.host}:{self.port}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        """Stop the server and close all connections."""
        if not self.running:
            return
            
        logger.info("Shutting down server...")
        self.running = False
        
        # Close all client connections
        for writer in self.clients:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
        
        # Close the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        logger.info("Server shutdown complete")
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handle client connections.
        
        Args:
            reader: StreamReader for receiving data
            writer: StreamWriter for sending data
        """
        # Get client info for logging
        addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {addr}")
        
        # Add client to our set
        self.clients.add(writer)
        
        try:
            while self.running:
                try:
                    # Read data with timeout
                    data = await asyncio.wait_for(
                        reader.readline(), timeout=self.idle_timeout
                    )
                    
                    if not data:  # Connection closed by client
                        break
                        
                    # Process the message
                    response = await self._process_message(data.decode().strip())
                    
                    # Send response
                    writer.write(f"{response}\n".encode())
                    await writer.drain()
                    
                except asyncio.TimeoutError:
                    logger.info(f"Client {addr} idle timeout, closing connection")
                    break
                except Exception as e:
                    logger.error(f"Error handling client {addr}: {e}", exc_info=True)
                    break
        finally:
            # Clean up the connection
            if writer in self.clients:
                self.clients.remove(writer)
                
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
                
            logger.info(f"Connection from {addr} closed")
    
    async def _process_message(self, message: str) -> str:
        """
        Process incoming messages.
        
        Currently just echoes back the message.
        Will be extended in later stages.
        
        Args:
            message: The message received from the client
            
        Returns:
            The response to send back to the client
        """
        # For now, just echo the message back (Stage 1)
        return message


async def main():
    """Run the server."""
    server = RedIMinuteServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main()) 