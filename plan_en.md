# Implementation Plan for the Asynchronous TCP Server

## 🧭 STAGE 1 — Asynchronous TCP Echo Server

🎯 **Goal**

Build a TCP server using `asyncio` that:

- Accepts multiple simultaneous connections.
- Receives plain text (bytes or str).
- Echoes back to the client exactly what it received.
- Shuts down cleanly with Ctrl+C or system signals.
- Doesn’t crash or hang due to trivial errors.

📘 **You’ll learn**

- How to use `asyncio.start_server()`.
- Basic handling of `StreamReader` and `StreamWriter`.
- Asynchronous read/write loops.
- Handling common network errors.
- Using `loop.add_signal_handler` for graceful shutdown.

🧠 **Key concepts to master by the end of this stage**

- `asyncio.StreamReader` and `StreamWriter`.
- `async def`, `async with`, and asynchronous `try/except`.
- Signal handling (`SIGINT`, `SIGTERM`).
- Decoupling networking logic from message processing.

✅ **Facts to be tested**

1. The server starts and listens on the expected port.
2. It accepts multiple simultaneous connections.
3. It echoes back exactly what the client sends.
4. It survives abrupt client disconnections.
5. It shuts down gracefully on receiving a signal.
6. No open sockets or leaks remain after shutdown.

🧪 **Tests (with `pytest-asyncio`)**

- Send text and verify the response is identical.
- Connect multiple simultaneous clients.
- Simulate shutdown via signal (`SIGINT`) and verify graceful stop.
- Ensure connection is closed when the server stops.

## 🧭 STAGE 2 — JSON Handling

🎯 **Goal**

Adapt the previous server so that:

- Incoming messages are JSON strings.
- Outgoing messages are also JSON.
- Malformed JSON is ignored gracefully without crashing.
- Use `json.loads` and `json.dumps` for parsing/serialization.

📘 **You’ll learn**

- How to read/write JSON over a text stream.
- Error handling with `json.loads`.
- Basic structure validation without Pydantic (yet).

✅ **Facts to be tested**

1. Valid JSON is received and echoed correctly.
2. Malformed JSON is ignored (or returns an error).
3. The connection stays alive despite client errors.
4. The server doesn’t crash due to serialization errors.

🧪 **Tests (with `pytest-asyncio`)**

- Send valid JSON → expect the same JSON back.
- Send garbage (non-JSON) → server doesn’t crash.
- Send a mix of valid and invalid messages in one session.

## 🧭 STAGE 3 — Message Validation with Pydantic

🎯 **Goal**

Define a message schema with Pydantic to validate input and structure the output.

📘 **You’ll learn**

- How to define models with `pydantic`.
- Convert JSON → object → safe dict.
- Handle client errors using `.parse_obj()`.

```python
from pydantic import BaseModel

class Command(BaseModel):
    action: str
    key: str | None = None
    value: str | None = None
```

✅ **Facts to be tested**

1. Valid JSON matching the schema is accepted.
2. Malformed JSON is rejected.
3. The response follows the defined schema.
4. The server doesn’t crash if validation fails.

## 🧭 STAGE 4 — In-memory Storage Dictionary

🎯 **Goal**

Create a global `dict` (shared across clients) that:

- Supports SET, GET, DEL, PING.
- Returns consistent responses in JSON.

```json
{ "action": "SET", "key": "foo", "value": "bar" }
{ "action": "GET", "key": "foo" } → { "result": "bar" }
```

## 🧭 STAGE 4.1 — Namespaces

Add namespaces to the system and adapt commands to support them. If no namespace is specified, fall back to the global one.

Namespaces should behave like a KVO-style key. The use of `^` as a separator is encouraged (nostalgia for MUMPS/Isis).

📘 **You’ll learn**

- Dispatcher with function mapping.
- Error control for missing keys.
- Returning errors with codes and descriptions.

✅ **Facts to be tested**

1. Values can be stored and retrieved.
2. Keys can be deleted.
3. Requesting a missing key does not raise exceptions.
4. Errors are returned for unknown actions or missing keys.

## 🧭 STAGE 5 — Robustness, Logging, and Error Management

🎯 **Goal**

Strengthen the server so that:

- It never crashes due to bad input or misbehaving clients.
- Everything is logged using the `logging` module.
- Idle connections are closed after a configurable timeout.

📘 **You’ll learn**

- Use of `asyncio.wait_for()` for timeouts.
- Structured logging with `logging`.
- Error logging with stack traces.
- Differentiating client errors from critical server issues.

✅ **Facts to be tested**

1. Network errors are ignored without crashing the server.
2. Idle connections are closed after X seconds.
3. Errors are logged without interrupting execution.

## 🧭 STAGE 6 — Concurrency Testing and Benchmarking

🎯 **Goal**

- Ensure many clients can operate concurrently without conflicts.
- Measure performance using `time.perf_counter()`.

📘 **You’ll learn**

- How to simulate many concurrent clients.
- Detecting race conditions and shared-access bugs.
- Introduction to `pytest-benchmark`.

✅ **Facts to be tested**

1. 1000 sequential SETs don’t overwrite values.
2. Concurrent access to the same key doesn’t cause errors.
3. Average response time stays below a threshold.

## 🧭 STAGE 7 — Optimization

🎯 **Goal**

- Integrate `uvloop`.
- Replace `json` with `orjson`.
- Measure gains under stress testing.

## 🧭 STAGE 8 — Pub/Sub Functionality

🎯 **Goal**

- Add pub/sub capabilities between processes.
- Evaluate whether to reuse [`beaconpy`](https://github.com/frr149/beaconpy).
- Consider use of weak references in pub/sub.
- Design subscriber registration and notification across processes.
- Determine if observers can remain as callables (like in `beaconpy`).
- Define behavior when an observer (client) disappears.
- Address security concerns such as those discussed here:  
  👉 https://rambo.codes/posts/2025-04-24-how-a-single-line-of-code-could-brick-your-iphone

## 🔚 Final Expected Result

An asynchronous TCP server that:

- Handles multiple simultaneous clients.
- Uses JSON with Pydantic validation.
- Supports basic operations like GET, SET, DEL.
- Is fault-tolerant, resilient to bad clients, and shuts down gracefully.
- Fully tested, with useful logs, and ready to be extended with authentication, TTLs, persistence, etc.
