# RedIMinute

A Redis-inspired asynchronous TCP server implemented in Python with asyncio.

## Overview

RedIMinute is an in-memory key-value store that communicates using JSON over TCP. It's designed to be lightweight, fast, and support multiple simultaneous connections.

## Features (Planned)

- Asynchronous TCP server using `asyncio`
- JSON-based communication
- Data validation with Pydantic
- In-memory key-value storage with namespaces
- Commands: SET, GET, DEL, PING
- Pub/Sub functionality
- Optimized with `uvloop` and `orjson`

## Development Stages

The project is being developed in stages:

1. **Stage 1**: Basic Echo TCP Server
2. **Stage 2**: JSON Handling
3. **Stage 3**: Message Validation with Pydantic
4. **Stage 4**: In-memory Storage Dictionary
5. **Stage 4.1**: Namespaces
6. **Stage 5**: Robustness, Logging, and Error Management
7. **Stage 6**: Concurrency Testing and Benchmarking
8. **Stage 7**: Optimization
9. **Stage 8**: Pub/Sub Functionality

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rediminute.git
cd rediminute

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Server

```bash
python -m rediminute.server
```

## Running Tests

```bash
pytest
```

## License

MIT 