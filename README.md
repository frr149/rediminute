# rediminute

A Redis-inspired asynchronous TCP server implemented in Python with asyncio.

## Overview

rediminute is an in-memory key-value store that communicates over TCP. It's designed to be lightweight, fast, and support multiple simultaneous connections.

## Features (Planned)

- Asynchronous TCP server using `asyncio`
- In-memory storage with namespaces
- Support for various data types and operations
- Pub/Sub functionality
- Optimized with `uvloop` and `orjson`

## Development Stages

The project is being developed in stages:

1. **Stage 1**: Basic Echo TCP Server
2. **Stage 2**: Message Handling
3. **Stage 3**: In-memory Storage
4. **Stage 4**: Advanced Features

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rediminute.git
cd rediminute

# Create a virtual environment with uv
uv venv
source .venv/bin/activate  # On fish shell: source .venv/bin/activate.fish

# Install the project in development mode
uv pip install -e .
```

## Running the Server

```bash
python -m rediminute.server
```

## License

MIT 