# Flexygent v0.2.0 — Detailed Implementation Guide

> Your complete blueprint for implementing the server utilities in the Flexygent framework. Every file, every method, every detail.

---

## Context: What Changed

Flex is a **personal agent daemon** (always-on, single-user), not a multi-user web server. This changes several things in the framework:

| Previous Plan | Updated Plan |
|--------------|-------------|
| JWT auth for multi-user | **API key auth** for Flex; JWT helpers kept in framework for others |
| User registration/login endpoints | **Removed** — single-user, no user system |
| Stateless request/response only | **WebSocket support** added for persistent connection + server push |
| No background task awareness | **Lifespan-aware** — framework supports startup/shutdown hooks |

The framework itself stays generic. It provides both API key and JWT auth helpers. But Flex (the app) only uses API key.

---

## Implementation Order

```
Step 1:  memory/base.py              (update interface)
Step 2:  memory/file_store.py        (update signatures)
Step 3:  memory/postgres_store.py    (new file)
Step 4:  memory/__init__.py          (re-export)
Step 5:  server/__init__.py          (new module)
Step 6:  server/auth.py              (new file)
Step 7:  server/schemas.py           (new file)
Step 8:  server/dependencies.py      (new file)
Step 9:  agent.py                    (add streaming)
Step 10: server/streaming.py         (new file)
Step 11: server/conversation_router.py (new file)
Step 12: server/chat_router.py       (new file)
Step 13: server/websocket_handler.py (new file)
Step 14: examples/fast_api.py        (update)
Step 15: pyproject.toml              (update deps)
Step 16: tests                       (new test files)
```

---

## Step 1: Update `flexygent/memory/base.py`

### What to Change
Add an optional `user_id: str = None` parameter to **every** abstract method.

### Why
Keeps the framework usable for multi-user projects. Flex (single-user) never passes it, but someone building a multi-user system on Flexygent would.

### Method Signatures After Change

```python
class ConversationMemory(ABC):

    @abstractmethod
    def save(self, conversation: Conversation, name: str, user_id: str = None):
        ...

    @abstractmethod
    def load(self, name: str, user_id: str = None) -> Conversation:
        ...

    @abstractmethod
    def list_saved(self, user_id: str = None) -> list[str]:
        ...

    @abstractmethod
    def delete(self, name: str, user_id: str = None):
        ...

    @abstractmethod
    def exists(self, name: str, user_id: str = None) -> bool:
        ...
```

### What NOT to Change
- Don't change the class name, imports, or base class (`ABC`)
- Don't remove any existing methods

---

## Step 2: Update `flexygent/memory/file_store.py`

### What to Change
Add `user_id: str = None` to the signature of `save()`, `load()`, `list_saved()`, `delete()`, and `exists()`.

### Important
FileStore **ignores** `user_id` — it doesn't use it internally. It just needs the parameter to satisfy the updated abstract interface. The logic inside each method stays exactly the same.

### Example

```python
# Before:
def save(self, conversation: Conversation, file_name: str):

# After:
def save(self, conversation: Conversation, file_name: str, user_id: str = None):
```

Do this for all 5 methods. Don't change any internal logic.

---

## Step 3: Create `flexygent/memory/postgres_store.py`

### New File

### Imports You'll Need
```python
from flexygent.memory.base import ConversationMemory
from flexygent.types import Conversation
from datetime import datetime
import json
import psycopg2
from psycopg2.extras import RealDictCursor
```

### Class Structure

```python
class PostgresStore(ConversationMemory):

    def __init__(self, connection_string: str, table_name: str = "conversations"):
        """
        Args:
            connection_string: PostgreSQL connection string
                e.g. "postgresql://user:pass@localhost:5432/flexygent"
            table_name: Name of the table to use
        """
```

### Constructor Logic
1. Store `connection_string` and `table_name` as instance attributes
2. Call a private method `_ensure_table()` to create the table if it doesn't exist

### `_ensure_table()` Method
Connect to the database and run:

```sql
CREATE TABLE IF NOT EXISTS {table_name} (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, user_id)
);
```

The `UNIQUE(name, user_id)` constraint means the same conversation name can exist for different users, but not duplicated for the same user.

### Private Helper: `_get_connection()`
Create and return a `psycopg2.connect(self.connection_string)` connection. Each method should open a connection, do its work, commit, and close. Use `try/finally` or context managers.

### `save()` Method Logic
1. Serialize: `conversation.model_dump()` → `json.dumps()`
2. Use UPSERT:

```sql
INSERT INTO {table_name} (name, user_id, data, updated_at)
VALUES (%s, %s, %s, NOW())
ON CONFLICT (name, user_id)
DO UPDATE SET data = EXCLUDED.data, updated_at = NOW();
```

3. Pass `(name, user_id, json_data)` as parameters
4. Commit

### `load()` Method Logic
1. Query:

```sql
SELECT data FROM {table_name} WHERE name = %s AND user_id = %s;
```

2. If `user_id is None`, use: `WHERE name = %s AND user_id IS NULL`
3. If no row found, raise `FileNotFoundError(f"Conversation '{name}' not found")`
4. Parse JSON: `json.loads(row['data'])`
5. Return `Conversation.model_validate(parsed_data)`

### `list_saved()` Method Logic
1. Query:

```sql
SELECT name FROM {table_name} WHERE user_id = %s ORDER BY updated_at DESC;
```

2. If `user_id is None`, use: `WHERE user_id IS NULL`
3. Return `[row['name'] for row in rows]`

### `delete()` Method Logic
1. Query:

```sql
DELETE FROM {table_name} WHERE name = %s AND user_id = %s;
```

2. If `user_id is None`, use: `WHERE name = %s AND user_id IS NULL`
3. Check `cursor.rowcount` — if 0, return `"No Conversation found to delete"`
4. If > 0, return `f"Conversation deleted successfully : {name}"`
5. Commit

### `exists()` Method Logic
1. Query:

```sql
SELECT 1 FROM {table_name} WHERE name = %s AND user_id = %s LIMIT 1;
```

2. If `user_id is None`, use: `WHERE name = %s AND user_id IS NULL`
3. Return `cursor.fetchone() is not None`

### `gen_file_name()` Method
Same as FileStore — timestamp-based name:

```python
def gen_file_name(self) -> str:
    dt = datetime.now()
    return f"conversation-{dt.strftime('%Y-%m-%d_%H-%M-%S')}.json"
```

### Edge Cases
- If `psycopg2` is not installed, raise: `"psycopg2 is required for PostgresStore. Install with: pip install flexygent[server]"`
- Handle `user_id IS NULL` in SQL carefully (`= NULL` doesn't work in SQL, must use `IS NULL`)
- Always close connections even if errors occur

---

## Step 4: Update `flexygent/memory/__init__.py`

Add PostgresStore with a try/except since `psycopg2` may not be installed:

```python
from flexygent.memory.base import ConversationMemory
from flexygent.memory.file_store import FileStore

try:
    from flexygent.memory.postgres_store import PostgresStore
except ImportError:
    pass  # psycopg2 not installed — PostgresStore not available
```

---

## Step 5: Create `flexygent/server/__init__.py`

Create the directory `flexygent/server/` and add `__init__.py`.

Re-export key components (wrapped in try/except since FastAPI may not be installed):

```python
try:
    from flexygent.server.auth import api_key_dependency, create_jwt, verify_jwt, jwt_dependency
    from flexygent.server.dependencies import FlexygentApp, configure_agent, get_flexygent
    from flexygent.server.chat_router import router as chat_router
    from flexygent.server.conversation_router import router as conversation_router
except ImportError:
    pass  # FastAPI not installed — server features not available
```

---

## Step 6: Create `flexygent/server/auth.py`

### Imports
```python
import os
import jwt  # from PyJWT
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException
```

### Function 1: `api_key_dependency(api_key_env="FLEXYGENT_API_KEY")`

This is a **factory function** that returns a FastAPI dependency.

**Logic:**
1. Returns an inner `async def verify(request: Request)` function
2. Reads the `Authorization` header
3. Extracts the key (format: `Bearer <key>` or raw key)
4. Compares against `os.getenv(api_key_env)`
5. Match → returns `True`
6. No match → raises `HTTPException(401, "Invalid API key")`
7. Env var not set → raises `HTTPException(500, "API key not configured")`

**This is what Flex uses.** One key, one user.

### Function 2: `create_jwt(payload, secret, expires_minutes=60)`

**Logic:**
1. Takes a dict payload
2. Adds `exp`: `datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)`
3. Adds `iat`: `datetime.now(timezone.utc)`
4. Encodes: `jwt.encode(payload, secret, algorithm="HS256")`
5. Returns token string

**Flex doesn't use this.** But other projects built on Flexygent might.

### Function 3: `verify_jwt(token, secret)`

**Logic:**
1. `jwt.decode(token, secret, algorithms=["HS256"])`
2. Returns decoded payload dict
3. Expired → `HTTPException(401, "Token expired")`
4. Invalid → `HTTPException(401, "Invalid token")`

### Function 4: `jwt_dependency(secret_env="JWT_SECRET")`

Same factory pattern as `api_key_dependency`, but extracts and verifies a JWT from the Bearer header. Returns the decoded payload.

---

## Step 7: Create `flexygent/server/schemas.py`

### Imports
```python
from pydantic import BaseModel
from typing import Optional
```

### Models to Define

**`ChatRequest`** — What the client sends to `/chat`:
- `message: str`
- `conversation_id: Optional[str] = None` — None = start new conversation
- `stream: bool = False`

**`ChatResponse`** — What `/chat` returns:
- `response: Optional[str] = None`
- `conversation_id: str`
- `requires_input: bool = False` — for pause-and-ask mechanism
- `input_fields: Optional[list[dict]] = None`

**`InputSubmission`** — For pause-and-ask:
- `conversation_id: str`
- `data: dict`

**`ConversationSummary`** — Each item in conversation list:
- `id: str`
- `created_at: Optional[str] = None`
- `message_count: int = 0`

**`ConversationDetail`** — Full conversation:
- `id: str`
- `messages: list[dict]`

**`CreateConversationRequest`**:
- `title: Optional[str] = None`

---

## Step 8: Create `flexygent/server/dependencies.py`

### Imports
```python
from fastapi import FastAPI, Request, HTTPException
from flexygent.types import Agent
from flexygent.memory.base import ConversationMemory
from flexygent.tools.base import ToolRegistry
```

### Class: `FlexygentApp`

Simple container holding all configured components:

```python
class FlexygentApp:
    def __init__(self, agent, memory, tool_registry, tools, client):
        self.agent = agent
        self.memory = memory
        self.tool_registry = tool_registry
        self.tools = tools
        self.client = client
```

### Function: `configure_agent(app, *, agent, memory, tool_registry, tools, client)`

1. Creates a `FlexygentApp` with all components
2. Stores it on: `app.state.flexygent = flexygent_app`

### Function: `get_flexygent(request: Request) -> FlexygentApp`

FastAPI dependency:
1. Reads `request.app.state.flexygent`
2. If not configured, raises `HTTPException(500, "Agent not configured")`
3. Returns the `FlexygentApp` instance

**How routers use it:**
```python
@router.post("/chat")
async def chat(request: ChatRequest, fg: FlexygentApp = Depends(get_flexygent)):
    response = agent_loop(conv, request.message, fg.tools, fg.tool_registry, fg.client, fg.agent.config)
```

---

## Step 9: Update `flexygent/agent.py`

### What to Change
Add `stream: bool = False` parameter to `agent_loop()`.

### Design

```python
def agent_loop(conversation, input_message, tools, tool_registry, client, config, stream=False):
    if stream:
        return _agent_loop_stream(conversation, input_message, tools, tool_registry, client, config)
    
    # ... existing code (unchanged) ...
```

### The `_agent_loop_stream()` Private Function

This is a **generator function** (uses `yield`).

**The tricky part:** Tool calls still happen synchronously. Streaming only applies to the **final text response**.

**Logic:**
1. Add user message to conversation (same as non-streaming)
2. Call `client.chat.completions.create(model=..., messages=..., tools=..., stream=True)`
3. **If the response contains tool calls:**
   - Accumulate tool call chunks (arguments arrive in pieces when streaming)
   - Once you have the full tool call, execute it
   - Add tool response to conversation
   - Call LLM again (loop)
   - Keep max_iterations guard
4. **If the response is text (finish_reason="stop"):**
   - Yield each content chunk: `yield chunk.choices[0].delta.content`
   - Accumulate all chunks into a variable
   - After all chunks: `conversation.add_assistant_message(full_text)`

**Accumulating tool calls from stream:**
```python
for chunk in response:
    delta = chunk.choices[0].delta
    if delta.tool_calls:
        # Each delta has: index, function.name (first chunk), function.arguments (partial)
        # Concatenate arguments across chunks to build full tool call
    if delta.content:
        yield delta.content
```

**The max_iterations warning** still works the same way.

---

## Step 10: Create `flexygent/server/streaming.py`

### Imports
```python
from fastapi.responses import StreamingResponse
import json
```

### Function: `sse_response(generator)`

Wraps a generator into SSE format.

**SSE Format:**
```
data: {"content": "Hello"}\n\n
data: {"content": " world"}\n\n
data: [DONE]\n\n
```

**Logic:**
1. Create inner async generator `event_stream()`:
   - Iterate over generator
   - For each chunk: `yield f"data: {json.dumps({'content': chunk})}\n\n"`
   - After exhaustion: `yield "data: [DONE]\n\n"`
2. Return `StreamingResponse(event_stream(), media_type="text/event-stream")`

This follows OpenAI's SSE format — any client that handles OpenAI streams can handle this.

---

## Step 11: Create `flexygent/server/conversation_router.py`

### Imports
```python
from fastapi import APIRouter, Depends, HTTPException
from flexygent.server.dependencies import get_flexygent, FlexygentApp
from flexygent.server.schemas import ConversationSummary, ConversationDetail, CreateConversationRequest
from flexygent.types import Conversation
```

### Router
```python
router = APIRouter(prefix="/conversations", tags=["Conversations"])
```

### Endpoint 1: `GET /conversations`
- Get `fg` from dependency injection
- Call `fg.memory.list_saved()`
- Return list of `ConversationSummary`

### Endpoint 2: `POST /conversations`
- Generate name via `fg.memory.gen_file_name()`
- Create `Conversation()` with system message from `fg.agent.get_system_message()`
- Save: `fg.memory.save(conversation, name)`
- Return `{"id": name}`

### Endpoint 3: `GET /conversations/{conversation_id}`
- Check exists: `fg.memory.exists(conversation_id)`
- If not → `HTTPException(404)`
- Load and return

### Endpoint 4: `DELETE /conversations/{conversation_id}`
- Call `fg.memory.delete(conversation_id)`
- Return `{"success": True}`

---

## Step 12: Create `flexygent/server/chat_router.py`

### Imports
```python
from fastapi import APIRouter, Depends, HTTPException
from flexygent.server.dependencies import get_flexygent, FlexygentApp
from flexygent.server.schemas import ChatRequest, ChatResponse
from flexygent.server.streaming import sse_response
from flexygent.agent import agent_loop
from flexygent.types import Conversation
```

### Router
```python
router = APIRouter(prefix="/chat", tags=["Chat"])
```

### Endpoint: `POST /chat`

**Logic:**
1. Get `fg` from dependency injection
2. **Load or create conversation:**
   - If `request.conversation_id` provided AND exists → load it
   - Otherwise → create new `Conversation()` with system message, generate a name
3. **Run agent loop:**
   - If `request.stream is False`:
     ```python
     response = agent_loop(conv, request.message, fg.tools, fg.tool_registry, fg.client, fg.agent.config)
     ```
   - If `request.stream is True`:
     ```python
     generator = agent_loop(conv, request.message, fg.tools, fg.tool_registry, fg.client, fg.agent.config, stream=True)
     return sse_response(generator)
     ```
4. **Save conversation:** `fg.memory.save(conv, conversation_id)`
5. **Return:** `ChatResponse(response=response, conversation_id=conversation_id)`

### Streaming + Saving Problem
When streaming, the response starts before the full text is known. The generator in `agent.py` handles adding the message to conversation after all chunks are yielded. Then you need to save after the generator is exhausted:

```python
async def stream_and_save(generator, memory, conv, conv_id):
    for chunk in generator:
        yield chunk
    # Generator done — conversation now has full response
    memory.save(conv, conv_id)
```

---

## Step 13: Create `flexygent/server/websocket_handler.py`

### Imports
```python
from fastapi import WebSocket, WebSocketDisconnect
import json
```

### Class: `ConnectionManager`

Manages active WebSocket connections:

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Send to ALL connected clients"""
        for connection in self.active_connections:
            await connection.send_text(message)
```

### Why This Matters for Flex
The `ConnectionManager` is how Flex pushes notifications to your phone/app. When a background task completes, or a stock alert triggers, the task engine calls `manager.broadcast(json.dumps({"type": "notification", "message": "AAPL dropped!"}))` and every connected client gets it instantly.

### Usage in the App
The app creates a `ConnectionManager` instance and mounts a WebSocket endpoint:

```python
manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages (chat, commands, etc.)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## Step 14: Update `examples/fast_api.py`

Replace the hello-world with a working example:

```python
from fastapi import FastAPI, Depends
from flexygent.server.chat_router import router as chat_router
from flexygent.server.conversation_router import router as conv_router
from flexygent.server.auth import api_key_dependency
from flexygent.server.dependencies import configure_agent
from flexygent.memory.file_store import FileStore
from flexygent.types import Agent, AgentConfig
from flexygent.skills import skill_registry, flex_skills
from flexygent.tools import tool_registry, get_tools
from flexygent.client import client

app = FastAPI(title="Flexygent API Example")

# Configure agent
agent = Agent(name="flex", config=AgentConfig(model="deepseek-v4-flash"))
agent.apply_skills(flex_skills, skill_registry)
tools = get_tools(tool_registry, agent.get_tool_filter(skill_registry))
memory = FileStore()

configure_agent(app, agent=agent, memory=memory,
                tool_registry=tool_registry, tools=tools, client=client)

# Auth
require_key = api_key_dependency()

# Mount routers
app.include_router(chat_router, dependencies=[Depends(require_key)])
app.include_router(conv_router, dependencies=[Depends(require_key)])

@app.get("/")
async def health():
    return {"status": "ok", "agent": agent.name}
```

Uses `FileStore` (not Postgres) to keep the example simple. Run with: `uvicorn examples.fast_api:app --reload`

---

## Step 15: Update `pyproject.toml`

### Changes

1. **Move FastAPI/uvicorn to optional `[server]` dependencies:**

```toml
[project.optional-dependencies]
server = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "psycopg2-binary>=2.9.0",
    "PyJWT>=2.8.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

2. **Remove `fastapi` and `uvicorn` from main `dependencies`** — CLI users don't need them.

3. **Update version** to `0.2.0`.

### Install Commands
- CLI users: `pip install flexygent`
- Server users: `pip install flexygent[server]`
- Developers: `pip install flexygent[server,dev]`

---

## Step 16: Tests

### What to Test

**`tests/test_postgres_store.py`:**
- Table creation
- save/load round-trip
- list_saved returns correct names
- delete removes the row
- exists returns True/False
- user_id isolation (two users, same conversation name)

**`tests/test_server_auth.py`:**
- `create_jwt` produces valid token
- `verify_jwt` decodes correctly
- `verify_jwt` raises on expired/invalid
- `api_key_dependency` allows correct key
- `api_key_dependency` blocks wrong/missing key

**`tests/test_server_chat.py`:**
- Use FastAPI `TestClient`
- POST /chat returns response
- New conversation created when no ID
- Existing conversation loaded when ID provided
- Mock the OpenAI client

**`tests/test_server_conversations.py`:**
- GET /conversations returns list
- POST /conversations creates one
- GET /conversations/{id} loads it
- DELETE /conversations/{id} removes it
- 404 on non-existent

**`tests/test_streaming.py`:**
- `sse_response` produces proper SSE format
- Includes `[DONE]` sentinel
- Content arrives as `data: {"content": "..."}\n\n`

### Run
```bash
pytest tests/ -v
```

Ensure all existing tests (176) still pass.

---

## File Dependency Graph

```
memory/base.py              ← no dependencies (update first)
    ↑
memory/file_store.py         ← depends on base.py
memory/postgres_store.py     ← depends on base.py
    ↑
server/schemas.py            ← pydantic only (standalone)
server/auth.py               ← PyJWT + FastAPI (standalone)
server/dependencies.py       ← types.py + memory/base.py
    ↑
server/streaming.py          ← FastAPI (standalone)
server/websocket_handler.py  ← FastAPI (standalone)
agent.py                     ← update existing (standalone change)
    ↑
server/conversation_router.py ← dependencies.py + schemas.py
server/chat_router.py         ← dependencies.py + schemas.py + streaming.py + agent.py
    ↑
examples/fast_api.py          ← depends on everything above
```

---

## Quick Reference

| Question | Answer |
|----------|--------|
| Where does SQL live? | `memory/postgres_store.py` only |
| Where does auth live? | `server/auth.py` only |
| Where does streaming logic live? | `agent.py` (generating) + `server/streaming.py` (SSE formatting) |
| Where does conversation loading live? | `server/chat_router.py` (orchestration) + `memory/` (storage) |
| Where does agent config live? | `server/dependencies.py` (stores) + app's `main.py` (calls configure) |
| Where does auth get applied? | App's `main.py` adds `dependencies=[Depends(require_key)]` |
| Where does WebSocket live? | `server/websocket_handler.py` (manager class) + app mounts endpoint |
| Does Flex need JWT? | **No.** API key only. JWT helpers exist for other projects. |
| Does Flex need user registration? | **No.** Single user. One API key. |
