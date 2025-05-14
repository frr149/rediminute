"""
Tests for the Echo Server (Stage 1)
"""
import asyncio
import pytest
import signal
import socket
from unittest.mock import patch

from rediminute.server import RedIMinuteServer


@pytest.fixture
async def server():
    """Create and start a server instance for testing."""
    # Use a non-standard port for testing
    server = RedIMinuteServer(port=6380)
    task = asyncio.create_task(server.start())
    
    # Give the server time to start
    await asyncio.sleep(0.1)
    
    yield server
    
    # Clean up after the test
    await server.stop()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def connect_client(host="127.0.0.1", port=6380):
    """Helper function to create a client connection."""
    reader, writer = await asyncio.open_connection(host, port)
    return reader, writer


async def send_and_receive(message, reader, writer):
    """Send a message and get the response."""
    writer.write(f"{message}\n".encode())
    await writer.drain()
    
    response = await reader.readline()
    return response.decode().strip()


@pytest.mark.asyncio
async def test_echo_server(server):
    """Test that the server echoes back what it receives."""
    # Connect a client
    reader, writer = await connect_client()
    
    # Send a message and check the response
    message = "Hello, server!"
    response = await send_and_receive(message, reader, writer)
    
    assert response == message
    
    # Close the connection
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_multiple_clients(server):
    """Test that the server can handle multiple clients simultaneously."""
    # Connect first client
    reader1, writer1 = await connect_client()
    
    # Connect second client
    reader2, writer2 = await connect_client()
    
    # Send messages from both clients
    message1 = "Message from client 1"
    message2 = "Message from client 2"
    
    # Send messages simultaneously
    task1 = asyncio.create_task(send_and_receive(message1, reader1, writer1))
    task2 = asyncio.create_task(send_and_receive(message2, reader2, writer2))
    
    # Wait for responses
    response1 = await task1
    response2 = await task2
    
    # Check responses
    assert response1 == message1
    assert response2 == message2
    
    # Close connections
    writer1.close()
    writer2.close()
    await writer1.wait_closed()
    await writer2.wait_closed()


@pytest.mark.asyncio
async def test_client_disconnect(server):
    """Test that the server handles client disconnects gracefully."""
    # Connect a client
    reader, writer = await connect_client()
    
    # Send a message and check the response
    message = "Hello, server!"
    response = await send_and_receive(message, reader, writer)
    
    assert response == message
    
    # Close the connection abruptly
    writer.close()
    await writer.wait_closed()
    
    # Server should not crash
    assert server.running is True


@pytest.mark.asyncio
async def test_graceful_shutdown(server):
    """Test that the server shuts down gracefully."""
    # Connect a client
    reader, writer = await connect_client()
    
    # Send a message
    message = "Hello, server!"
    response = await send_and_receive(message, reader, writer)
    
    assert response == message
    
    # Stop the server
    await server.stop()
    
    # The client connection should be closed
    with pytest.raises((ConnectionResetError, ConnectionRefusedError, BrokenPipeError)):
        writer.write(b"Test after shutdown\n")
        await writer.drain()
        
    # Try to make a new connection - should fail
    with pytest.raises((ConnectionRefusedError, socket.timeout)):
        await asyncio.wait_for(connect_client(), timeout=0.5) 