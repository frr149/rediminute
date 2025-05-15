"""
rediminute Server - Asynchronous TCP Echo Server
"""
import asyncio
import logging
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rediminute.server")


class AsyncServer:
    """
    Basic asynchronous TCP echo server.
    
    Features:
    - Accepts multiple simultaneous connections
    - Echoes back client messages
    - Handles graceful shutdown on system signals
    - Error handling to prevent crashes
    """
    
    def __init__(self, host="127.0.0.1", port=6379, idle_timeout=300):
        """Initialize the server."""
        self.host = host
        self.port = port
        self.idle_timeout = idle_timeout
        self.server = None
        self.clients = set()
        self.running = False
    
    async def start(self):
        """Start the server and listen for connections."""
        self.running = True
        
        # Create the server
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
        
        logger.info(f"Server started on {self.host}:{self.port}")
        
        # Start serving
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        """Stop the server and close all connections."""
        if not self.running:
            return
        
        logger.info("Shutting down server...")
        self.running = False
        
        # Close all client connections
        for writer in list(self.clients):
            try:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing client connection: {e}")
        
        # Close the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Server shutdown complete")
    
    async def handle_client(self, reader, writer):
        """Handle a client connection."""
        # Get client info for logging
        addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {addr}")
        
        # Add client to set
        self.clients.add(writer)
        
        try:
            while self.running:
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
                    
        finally:
            # Clean up
            if writer in self.clients:
                self.clients.remove(writer)
            
            try:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
                
            logger.info(f"Connection from {addr} closed")


def main():
    """Run the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="rediminute Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=6379, help="Port to listen on")
    parser.add_argument("--timeout", type=int, default=300, help="Idle timeout in seconds")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
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
