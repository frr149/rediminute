"""
Simple client to test the rediminute server
"""
import asyncio
import sys
import argparse


async def run_client(host="127.0.0.1", port=6379):
    """Connect to server and send/receive messages."""
    writer = None
    try:
        # Connect to server
        reader, writer = await asyncio.open_connection(host, port)
        print(f"Connected to {host}:{port}")
        
        # Handle user input and server responses
        while True:
            # Get user input
            message = input("> ")
            if message.lower() in ("exit", "quit", "q"):
                break
                
            # Send message to server
            writer.write(f"{message}\n".encode())
            await writer.drain()
            
            # Get response from server
            response = await reader.readline()
            if not response:
                print("Server closed the connection")
                break
                
            # Print response
            print(f"Response: {response.decode().strip()}")
            
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


def main():
    """Parse arguments and run the client."""
    parser = argparse.ArgumentParser(description="rediminute Client")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=6379, help="Server port")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_client(args.host, args.port))
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main() 