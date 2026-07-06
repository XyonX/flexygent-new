# Flexygent v0.2.0 — Detailed Implementation Guide

> This document is your complete blueprint. Every file, every method, every detail — so you can implement it all yourself.

---

## Implementation Order

Follow this exact order — each step depends on the ones before it.

```
Step 1:  memory/base.py          (update interface)
Step 2:  memory/file_store.py    (update signatures)
Step 3:  memory/postgres_store.py (new file)
Step 4:  memory/__init__.py      (re-export)
Step 5:  server/__init__.py      (new module)
Step 6:  server/auth.py          (new file)
Step 7:  server/schemas.py       (new file)
Step 8:  server/dependencies.py  (new file)
Step 9:  agent.py                (add streaming)
Step 10: server/streaming.py     (new file)
Step 11: server/conversation_router.py (new file)
Step 12: server/chat_router.py   (new file)
Step 13: examples/fast_api.py    (update)
Step 14: pyproject.toml          (update deps)
Step 15: tests                   (new test files)
```

---

## Step 1: Update `flexygent/memory/base.py`

### What to Change
Add an optional `user_id: str = None` parameter to **every** abstract method.

### Why
In a multi-user server, conversations belong to specific users. The storage backend needs to filter by user. The `None` default means single-user apps (CLI) don't need to change anything.

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
- Don't change the class name
- Don't change the imports
- Keep `ABC` and `@abstractmethod`

---

## Step 2: Update `flexygent/memory/file_store.py`

### What to Change
Add `user_id: str = None` to the signature of `save()`, `load()`, `list_saved()`, `delete()`, and `exists()`.

### Important
FileStore **ignores** `user_id` — it doesn't use it internally. It just needs the parameter to satisfy the updated abstract interface. The logic inside each method stays exactly the same.

### Example (just the signature change)

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
This is a brand new file implementing `ConversationMemory` backed by PostgreSQL.

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
            table_name: Name of the table to use (default: "conversations")
        """
```

### Constructor Logic
1. Store `connection_string` and `table_name` as instance attributes
2. Call a private method `_ensure_table()` to create the table if it doesn't exist

### `_ensure_table()` Method
Connect to the database and run this SQL:

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
Create and return a `psycopg2.connect(self.connection_string)` connection. Each method should open a connection, do its work, commit, and close. Use `try/finally` or context managers to ensure connections are always closed.

### `save()` Method Logic
1. Serialize the conversation to a dict using `conversation.model_dump()`
2. Convert the dict to JSON string with `json.dumps()`
3. Use an **UPSERT** query (INSERT ... ON CONFLICT UPDATE):

```sql
INSERT INTO {table_name} (name, user_id, data, updated_at)
VALUES (%s, %s, %s, NOW())
ON CONFLICT (name, user_id)
DO UPDATE SET data = EXCLUDED.data, updated_at = NOW();
```

4. Pass `(name, user_id, json_data)` as parameters
5. Commit the transaction

### `load()` Method Logic
1. Query the database:

```sql
SELECT data FROM {table_name} WHERE name = %s AND user_id = %s;
```

2. If `user_id is None`, use: `WHERE name = %s AND user_id IS NULL`
3. Fetch one row
4. If no row found, raise `FileNotFoundError(f"Conversation '{name}' not found")`
5. Parse the JSON data back with `json.loads(row['data'])`
6. Return `Conversation.model_validate(parsed_data)`

### `list_saved()` Method Logic
1. Query:

```sql
SELECT name FROM {table_name} WHERE user_id = %s ORDER BY updated_at DESC;
```

2. If `user_id is None`, use: `WHERE user_id IS NULL`
3. Return a list of name strings: `[row['name'] for row in rows]`

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
Copy the same logic from `FileStore` — generates a timestamp-based name. This isn't abstract but it's useful to have on all backends:

```python
def gen_file_name(self) -> str:
    dt = datetime.now()
    return f"conversation-{dt.strftime('%Y-%m-%d_%H-%M-%S')}.json"
```

### Edge Cases to Handle
- If `psycopg2` is not installed, raise a clear error: `"psycopg2 is required for PostgresStore. Install with: pip install flexygent[server]"`
- Handle the `user_id IS NULL` case in SQL carefully (you can't use `= NULL` in SQL, must use `IS NULL`)
- Always close connections even if errors occur

---

## Step 4: Update `flexygent/memory/__init__.py`

### What to Change
Add `PostgresStore` to the imports:

```python
from flexygent.memory.base import ConversationMemory
from flexygent.memory.file_store import FileStore
from flexygent.memory.postgres_store import PostgresStore
```

### Consideration
Since `psycopg2` might not be installed for CLI-only users, you might want to wrap the PostgresStore import in a try/except:

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

### New Directory
Create the directory `flexygent/server/` and add `__init__.py`.

### Contents
Re-export the key components so users can do clean imports:

```python
from flexygent.server.auth import api_key_dependency, create_jwt, verify_jwt, jwt_dependency
from flexygent.server.dependencies import FlexygentApp, configure_agent, get_flexygent
from flexygent.server.chat_router import router as chat_router
from flexygent.server.conversation_router import router as conversation_router
```

Same as other `__init__.py` files — you may want to wrap in try/except since FastAPI might not be installed.

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

This is a **factory function** that returns a FastAPI dependency function.

**What it does:**
1. Returns an inner `async def verify(request: Request)` function
2. The inner function reads the `Authorization` header from the request
3. Extracts the key (expects format: `Bearer <key>` or just the raw key)
4. Compares it against `os.getenv(api_key_env)`
5. If match → returns `True` (request proceeds)
6. If no match → raises `HTTPException(status_code=401, detail="Invalid API key")`
7. If env var not set → raises `HTTPException(status_code=500, detail="API key not configured")`

**Usage pattern (by the app):**
```python
from flexygent.server.auth import api_key_dependency
require_api_key = api_key_dependency()  # reads FLEXYGENT_API_KEY from env
app.include_router(chat_router, dependencies=[Depends(require_api_key)])
```

### Function 2: `create_jwt(payload, secret, expires_minutes=60)`

**What it does:**
1. Takes a dict payload (e.g., `{"user_id": "123", "email": "user@example.com"}`)
2. Adds `exp` (expiry) claim: `datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)`
3. Adds `iat` (issued at) claim: `datetime.now(timezone.utc)`
4. Encodes with `jwt.encode(payload, secret, algorithm="HS256")`
5. Returns the token string

### Function 3: `verify_jwt(token, secret)`

**What it does:**
1. Calls `jwt.decode(token, secret, algorithms=["HS256"])`
2. Returns the decoded payload dict
3. If expired → raises `HTTPException(401, "Token expired")`
4. If invalid → raises `HTTPException(401, "Invalid token")`

### Function 4: `jwt_dependency(secret_env="JWT_SECRET")`

This is a **factory function** (same pattern as `api_key_dependency`) that returns a FastAPI dependency.

**What it does:**
1. Returns an inner `async def verify(request: Request)` function
2. Reads `Authorization: Bearer <token>` from the request
3. Calls `verify_jwt(token, os.getenv(secret_env))`
4. Returns the decoded payload (which contains `user_id`, etc.)
5. This payload then becomes available to route handlers via dependency injection

**Usage pattern:**
```python
require_jwt = jwt_dependency()

@router.get("/conversations")
async def list_conversations(user=Depends(require_jwt)):
    user_id = user["user_id"]  # extracted from the JWT payload
```

---

## Step 7: Create `flexygent/server/schemas.py`

### Imports
```python
from pydantic import BaseModel
from typing import Optional
```

### Models to Define

**`ChatRequest`** — What the frontend sends to `/chat`:
- `message: str` — the user's message
- `conversation_id: Optional[str] = None` — which conversation (None = start new)
- `stream: bool = False` — whether to stream the response

**`ChatResponse`** — What `/chat` returns:
- `response: Optional[str] = None` — the agent's response text
- `conversation_id: str` — the conversation ID (so frontend can use it next time)
- `requires_input: bool = False` — True if agent needs user input (pause-and-ask)
- `input_fields: Optional[list[dict]] = None` — fields to collect (if requires_input is True)

**`InputSubmission`** — What frontend sends to `/chat/input` (for pause-and-ask):
- `conversation_id: str`
- `data: dict` — the user's answers (key-value pairs)

**`ConversationSummary`** — Each item in the conversation list:
- `id: str` — the conversation name/ID
- `created_at: Optional[str] = None`
- `message_count: int = 0`

**`ConversationDetail`** — Full conversation with messages:
- `id: str`
- `messages: list[dict]` — the actual messages

**`CreateConversationRequest`** — What frontend sends to create a conversation:
- `title: Optional[str] = None` — optional title

---

## Step 8: Create `flexygent/server/dependencies.py`

### Imports
```python
from fastapi import FastAPI, Request
from flexygent.types import Agent, AgentConfig
from flexygent.memory.base import ConversationMemory
from flexygent.tools.base import ToolRegistry
```

### Class: `FlexygentApp`

A simple container that holds all the configured components:

```python
class FlexygentApp:
    def __init__(self, agent, memory, tool_registry, tools, client):
        self.agent = agent           # Agent instance
        self.memory = memory         # ConversationMemory instance
        self.tool_registry = tool_registry  # ToolRegistry instance
        self.tools = tools           # list of tool schemas (from get_tools)
        self.client = client         # OpenAI client instance
```

### Function: `configure_agent(app, *, agent, memory, tool_registry, tools, client)`

**What it does:**
1. Creates a `FlexygentApp` instance with all the provided components
2. Stores it on the FastAPI app using `app.state.flexygent = flexygent_app`
3. FastAPI's `app.state` is the standard way to store shared objects

### Function: `get_flexygent(request: Request) -> FlexygentApp`

**What it does:**
1. This is a FastAPI dependency function
2. Reads `request.app.state.flexygent` and returns it
3. If not configured, raises `HTTPException(500, "Agent not configured")`

**How routers use it:**
```python
@router.post("/chat")
async def chat(request: ChatRequest, fg: FlexygentApp = Depends(get_flexygent)):
    # fg.agent, fg.memory, fg.client, etc. are all available
    response = agent_loop(conversation, request.message, fg.tools, fg.tool_registry, fg.client, fg.agent.config)
```

---

## Step 9: Update `flexygent/agent.py`

### What to Change
Add a `stream: bool = False` parameter to `agent_loop()`.

### How It Works

**When `stream=False` (default):** Existing behavior — unchanged. Returns a complete response string.

**When `stream=True`:** The function should return a **generator** that yields chunks of text.

### Internal Design

```python
def agent_loop(conversation, input_message, tools, tool_registry, client, config, stream=False):
    if stream:
        return _agent_loop_stream(conversation, input_message, tools, tool_registry, client, config)
    
    # ... existing code (unchanged) ...
```

### The `_agent_loop_stream()` Private Function

This is a **generator function** (uses `yield`).

**The tricky part:** Tool calls still happen synchronously. You can't stream tool execution. Streaming only applies to the **final text response**.

**Logic:**
1. Add the user message to conversation (same as non-streaming)
2. Call `client.chat.completions.create(model=..., messages=..., tools=..., stream=True)`
3. **If the response is a tool call:**
   - Accumulate the tool call chunks (tool call arguments come in pieces when streaming)
   - Once you have the full tool call, execute it (same as non-streaming)
   - Add the tool response to conversation
   - Call the LLM again (loop, same as non-streaming)
   - Keep the max_iterations guard
4. **If the response is a text response (finish_reason="stop"):**
   - Yield each content chunk as it arrives: `yield chunk.choices[0].delta.content`
   - After all chunks, add the full accumulated response to conversation

**How to accumulate tool calls from stream chunks:**

When streaming, tool calls arrive as deltas:
```python
for chunk in response:
    delta = chunk.choices[0].delta
    if delta.tool_calls:
        # Accumulate: each delta has index, function.name (first chunk only), function.arguments (partial)
        # Build up the full arguments string by concatenating
    if delta.content:
        yield delta.content
```

**The iteration warning** (max_iterations reached) should still work the same — inject the warning message before the final LLM call.

### Important Note
The generator needs to also handle adding the final complete message to `conversation` after all chunks are yielded. You can do this by accumulating all yielded text into a variable and calling `conversation.add_assistant_message(full_text)` at the end of the generator.

---

## Step 10: Create `flexygent/server/streaming.py`

### Imports
```python
from fastapi.responses import StreamingResponse
import json
```

### Function: `sse_response(generator)`

**What it does:**
Takes an async or sync generator and wraps it into a proper SSE (Server-Sent Events) `StreamingResponse`.

**SSE Format:**
Each event is formatted as:
```
data: {"content": "Hello"}\n\n
```

The final event:
```
data: [DONE]\n\n
```

**Logic:**
1. Create an inner async generator `event_stream()` that:
   - Iterates over the provided generator
   - For each chunk of text, formats it as `f"data: {json.dumps({'content': chunk})}\n\n"`
   - Yields the formatted string
   - After the generator is exhausted, yields `"data: [DONE]\n\n"`
2. Return `StreamingResponse(event_stream(), media_type="text/event-stream")`

### Why This Format
This follows the same SSE format that OpenAI uses. Any frontend that can consume OpenAI streams can consume this. The `[DONE]` sentinel tells the frontend "the stream is complete, stop listening."

---

## Step 11: Create `flexygent/server/conversation_router.py`

### Imports
```python
from fastapi import APIRouter, Depends, HTTPException
from flexygent.server.dependencies import get_flexygent, FlexygentApp
from flexygent.server.schemas import ConversationSummary, ConversationDetail, CreateConversationRequest
from flexygent.types import Conversation
```

### Router Setup
```python
router = APIRouter(prefix="/conversations", tags=["Conversations"])
```

### Endpoint 1: `GET /conversations`

**Purpose:** List all saved conversations for the current user.

**Logic:**
1. Get `fg` (FlexygentApp) from dependency injection
2. Get `user_id` from the auth dependency (if using JWT) or `None` (if API key)
3. Call `fg.memory.list_saved(user_id=user_id)`
4. Return the list as `[ConversationSummary(id=name) for name in names]`

### Endpoint 2: `POST /conversations`

**Purpose:** Create a new empty conversation.

**Logic:**
1. Generate a conversation name using `fg.memory.gen_file_name()` (if the backend supports it) or generate a UUID
2. Create a fresh `Conversation()` with the system message from `fg.agent.get_system_message()`
3. Save it: `fg.memory.save(conversation, name, user_id=user_id)`
4. Return `{"id": name}`

### Endpoint 3: `GET /conversations/{conversation_id}`

**Purpose:** Load a specific conversation with all messages.

**Logic:**
1. Check if it exists: `fg.memory.exists(conversation_id, user_id=user_id)`
2. If not → raise `HTTPException(404, "Conversation not found")`
3. Load it: `conv = fg.memory.load(conversation_id, user_id=user_id)`
4. Return `ConversationDetail(id=conversation_id, messages=conv.to_dict())`

### Endpoint 4: `DELETE /conversations/{conversation_id}`

**Purpose:** Delete a conversation.

**Logic:**
1. Call `fg.memory.delete(conversation_id, user_id=user_id)`
2. Return `{"success": True, "message": "Deleted"}`

### How to Get `user_id`
This depends on which auth system is used. The router should accept `user_id` via dependency injection. You can design a small helper dependency that extracts `user_id` from the JWT payload, or returns `None` for API key auth.

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

### Router Setup
```python
router = APIRouter(prefix="/chat", tags=["Chat"])
```

### Endpoint: `POST /chat`

**Purpose:** The main chat endpoint. Send a message, get a response.

**Logic:**
1. Get `fg` (FlexygentApp) from dependency injection
2. Get `user_id` from auth (same pattern as conversation router)
3. **Load or create conversation:**
   - If `request.conversation_id` is provided AND exists → load it
   - If not provided OR doesn't exist → create a new `Conversation()` with system message, generate a name
4. **Run the agent loop:**
   - If `request.stream is False`:
     ```python
     response = agent_loop(conv, request.message, fg.tools, fg.tool_registry, fg.client, fg.agent.config, stream=False)
     ```
   - If `request.stream is True`:
     ```python
     generator = agent_loop(conv, request.message, fg.tools, fg.tool_registry, fg.client, fg.agent.config, stream=True)
     return sse_response(generator)
     ```
5. **Save the conversation:** `fg.memory.save(conv, conversation_id, user_id=user_id)`
6. **Return:** `ChatResponse(response=response, conversation_id=conversation_id)`

### Important: Streaming + Saving
When streaming, the conversation needs to be saved **after** the stream completes, not before. This is tricky because the SSE response starts sending before the full response is known. 

**Solution:** The `_agent_loop_stream` generator in `agent.py` should handle adding the message to conversation internally. After the last token is yielded, it calls `conversation.add_assistant_message(full_text)`. Then the chat router can save after the generator is exhausted.

One approach: wrap the generator in a helper that saves after exhaustion:

```python
async def stream_and_save(generator, memory, conv, conv_id, user_id):
    async for chunk in generator:
        yield chunk
    # Generator exhausted — conversation now has the full response
    memory.save(conv, conv_id, user_id=user_id)
```

---

## Step 13: Update `examples/fast_api.py`

### What to Write
A minimal but working example showing how to use the server module. Something like:

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
tool_filter = agent.get_tool_filter(skill_registry)
tools = get_tools(tool_registry, tool_filter)
memory = FileStore()

configure_agent(app, agent=agent, memory=memory, tool_registry=tool_registry, tools=tools, client=client)

# Mount routers with auth
require_key = api_key_dependency()
app.include_router(chat_router, dependencies=[Depends(require_key)])
app.include_router(conv_router, dependencies=[Depends(require_key)])

@app.get("/")
async def health():
    return {"status": "ok", "agent": agent.name}
```

Run with: `uvicorn examples.fast_api:app --reload`

---

## Step 14: Update `pyproject.toml`

### Changes

1. **Add optional `[server]` dependencies:**

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

2. **Remove `fastapi` and `uvicorn` from the main `dependencies` list** — they should only be required for server mode, not for CLI users.

3. **Add `psycopg2-binary` and `PyJWT`** to the server extras.

4. **Update version** to `0.2.0`.

### Install Commands
- CLI users: `pip install flexygent` (same as before, no extra deps)
- Server users: `pip install flexygent[server]` (includes FastAPI, Postgres, JWT)
- Developers: `pip install flexygent[dev]` or `pip install flexygent[server,dev]`

---

## Step 15: Tests

### What to Test

**`tests/test_postgres_store.py`:**
- Test that the table gets created
- Test save/load round-trip
- Test list_saved returns correct names
- Test delete removes the row
- Test exists returns True/False correctly
- Test user_id isolation (two users can have same conversation name)
- You'll need a test Postgres database, or you can mock `psycopg2`

**`tests/test_server_auth.py`:**
- Test `create_jwt` produces a valid token
- Test `verify_jwt` decodes correctly
- Test `verify_jwt` raises on expired token
- Test `verify_jwt` raises on invalid signature
- Test `api_key_dependency` allows correct key
- Test `api_key_dependency` blocks wrong key
- Test `api_key_dependency` blocks missing key

**`tests/test_server_chat.py`:**
- Use FastAPI's `TestClient` to test the chat endpoint
- Test POST /chat with a message returns a response
- Test POST /chat creates a new conversation when no ID provided
- Test POST /chat loads existing conversation when ID provided
- You'll need to mock the OpenAI client (so you're not making real API calls in tests)

**`tests/test_server_conversations.py`:**
- Test GET /conversations returns a list
- Test POST /conversations creates one
- Test GET /conversations/{id} loads it
- Test DELETE /conversations/{id} removes it
- Test 404 when loading non-existent conversation

**`tests/test_streaming.py`:**
- Test that `sse_response` produces proper SSE format
- Test that it includes the `[DONE]` sentinel
- Test that content arrives as `data: {"content": "..."}\n\n`

### Running Tests
```bash
pytest tests/ -v
```

Make sure existing tests (176 of them) still pass after your changes.

---

## File Dependency Graph

This shows which files import from which, so you know the build order:

```
memory/base.py          ← no dependencies (update first)
    ↑
memory/file_store.py    ← depends on base.py
memory/postgres_store.py ← depends on base.py
    ↑
server/schemas.py       ← depends on pydantic only (standalone)
server/auth.py          ← depends on PyJWT, FastAPI (standalone)
server/dependencies.py  ← depends on types.py, memory/base.py
    ↑
server/streaming.py     ← depends on FastAPI (standalone)
agent.py                ← update existing (standalone change)
    ↑
server/conversation_router.py ← depends on dependencies.py, schemas.py
server/chat_router.py        ← depends on dependencies.py, schemas.py, streaming.py, agent.py
    ↑
examples/fast_api.py    ← depends on everything above
```

---

## Quick Reference: What Goes Where

| Question | Answer |
|----------|--------|
| Where does SQL live? | `memory/postgres_store.py` only |
| Where does JWT logic live? | `server/auth.py` only |
| Where does streaming logic live? | `agent.py` (generating) + `server/streaming.py` (formatting SSE) |
| Where does conversation loading live? | `server/chat_router.py` (orchestration) + `memory/` (actual storage) |
| Where does the agent get configured? | `server/dependencies.py` (stores config) + the app's `main.py` (calls configure) |
| Where does auth get applied? | App's `main.py` adds `dependencies=[Depends(require_auth)]` to routers |
