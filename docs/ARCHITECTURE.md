# Flexygent Ecosystem — Three-Layer Architecture Plan

> This document defines the **purpose, responsibilities, boundaries, and structure** of the three components in the Flexygent ecosystem.

---

## The Big Picture

Flex is **not** a web server that serves multiple users. It is a **personal agent daemon** — a continuously running program on your server that acts as your always-on AI assistant. It can respond to your messages, run background tasks autonomously, send you notifications, monitor things for you, and execute work without you being present.

Flexygent is the **framework** that makes building something like Flex possible. Anyone can use Flexygent to build their own personal agent daemon — a study bot, a trading assistant, a devops monitor — each would be a separate project.

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: CLIENT                          │
│          (Phone app, web app, CLI, Aiverse, etc.)           │
│                                                             │
│   • Sends messages to the daemon                            │
│   • Receives responses + notifications                      │
│   • Displays chat, tasks, alerts                            │
│   • Maintains persistent WebSocket connection               │
│   • Zero AI logic — pure display + interaction              │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTP / WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              LAYER 2: FLEX (Personal Agent Daemon)           │
│                                                             │
│   • Always-on process running on a server                   │
│   • Responds to user messages (chat)                        │
│   • Runs background tasks autonomously                      │
│   • Sends proactive notifications                           │
│   • Monitors things, schedules jobs                         │
│   • Single user — secured by API key                        │
│   • pip install flexygent                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │  import flexygent
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  LAYER 1: FLEXYGENT (Framework)             │
│               (Reusable agentic AI framework)               │
│                                                             │
│   • Agent loop, tools, skills, prompts, types               │
│   • Storage adapters, server utilities, auth helpers         │
│   • Everything generic — nothing project-specific           │
│   • Published on PyPI: pip install flexygent                │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Flexygent (Framework)

### Purpose

Flexygent is a **reusable agentic AI framework**. It provides building blocks that anyone can use to create their own AI agent. It should contain everything that is **generic** — things any agentic AI project would need — and nothing that is specific to any single project.

> **Rule of Thumb:** If two different people building two different agent projects would both need the same code, it belongs in Flexygent.

### Current State (v0.1.0 — Released ✅)

| Component | What It Does |
|-----------|-------------|
| Agent Loop | ReAct reasoning cycle with tool calling |
| Type System | `Message`, `Conversation`, `AgentConfig`, `Agent`, `Role` |
| Tool System | `Tool`, `ToolRegistry`, `get_tools()` with 8 built-in tools |
| Prompt System | `PromptBuilder` with composable sections |
| Skill System | `Skill`, `SkillRegistry` with 4 presets |
| IO Abstraction | Abstract `UserIO` + `CliUserIO` adapter |
| Memory | Abstract `ConversationMemory` + `FileStore` (JSON files) |
| LLM Client | OpenAI-compatible client via `pydantic-settings` |

### What Gets Added for v0.2.0

---

#### 1. Conversation Memory — PostgreSQL Backend

**Belongs in: FRAMEWORK ✅**

The same `ConversationMemory` abstract interface, now with a PostgreSQL implementation. Anyone building an agent daemon needs persistent, crash-safe conversation storage. JSON files work for local dev, but a database survives server restarts, crashes, and disk issues.

```
flexygent/memory/
├── base.py              # (existing) Abstract ConversationMemory
├── file_store.py        # (existing) JSON file implementation
└── postgres_store.py    # NEW — PostgreSQL implementation
```

The interface stays the same — `save()`, `load()`, `list_saved()`, `delete()`, `exists()`. The app just picks which backend to use:

```python
# Pick the backend — same API, different storage
from flexygent.memory.postgres_store import PostgresStore
memory = PostgresStore(connection_string="postgresql://...")
memory.save(conversation, "conv-123")
```

> [!IMPORTANT]
> The `ConversationMemory` interface gets an optional `user_id` parameter on all methods. Default is `None`. Single-user apps (Flex, CLI) never pass it. But it keeps the framework usable for anyone who builds a multi-user system on top of it.

**Updated abstract interface:**
```python
class ConversationMemory(ABC):
    def save(self, conversation, name, user_id=None): ...
    def load(self, name, user_id=None): ...
    def list_saved(self, user_id=None) -> list[str]: ...
    def delete(self, name, user_id=None): ...
    def exists(self, name, user_id=None) -> bool: ...
```

---

#### 2. Authentication Helpers

**Belongs in: FRAMEWORK ✅**

The framework provides reusable auth utilities. For Flex (single-user), only the API key check is needed. But the framework also provides JWT helpers for anyone building a multi-user system.

```python
# Framework provides:

# 1. API key check (what Flex uses)
def api_key_dependency(api_key_env="FLEXYGENT_API_KEY"):
    """FastAPI dependency — checks Authorization header against env var"""

# 2. JWT helpers (for multi-user projects built on Flexygent)
def create_jwt(payload, secret, expires_minutes=60) -> str:
def verify_jwt(token, secret) -> dict:
def jwt_dependency(secret_env="JWT_SECRET"):
```

---

#### 3. Communication Layer (FastAPI Routers)

**Belongs in: FRAMEWORK ✅ (as reusable routers)**

The framework provides pre-built FastAPI routers that any app can mount. These handle the common patterns — receiving chat messages, managing conversations, streaming responses.

```
flexygent/server/
├── __init__.py
├── auth.py                 # Auth helpers (API key + JWT)
├── schemas.py              # Request/response Pydantic models
├── chat_router.py          # POST /chat endpoint
├── conversation_router.py  # CRUD endpoints for conversations
├── streaming.py            # SSE streaming helpers
├── websocket_handler.py    # WebSocket connection handler
└── dependencies.py         # FastAPI dependency injection
```

**`chat_router.py`** — Chat endpoint:
```python
router = APIRouter(prefix="/chat")

@router.post("/")           # Send message, get full response
@router.post("/stream")     # Send message, get streaming SSE response
```

**`conversation_router.py`** — Conversation CRUD:
```python
router = APIRouter(prefix="/conversations")

@router.get("/")             # List conversations
@router.post("/")            # Create new conversation
@router.get("/{conv_id}")    # Load a conversation
@router.delete("/{conv_id}") # Delete a conversation
```

**`websocket_handler.py`** — WebSocket support:
```python
# Handles persistent WebSocket connections
# Used by: real-time chat, server-push notifications, task updates
# The app mounts this on a WebSocket endpoint
```

The app mounts these routers:
```python
from flexygent.server.chat_router import router as chat_router
from flexygent.server.conversation_router import router as conv_router

app = FastAPI()
app.include_router(chat_router)
app.include_router(conv_router)
```

---

#### 4. Agent Loop — Streaming Support

**Belongs in: FRAMEWORK ✅**

Add a `stream=True` parameter to `agent_loop()`:

- `stream=False` (default): Current behavior — returns complete response string
- `stream=True`: Returns a generator that yields tokens as they arrive from the LLM

Tool calls still execute synchronously in the background. Streaming only applies to the final text response.

---

### Flexygent v0.2.0 — Framework Additions Summary

| New Component | Location | What It Does |
|--------------|----------|-------------|
| **Postgres Memory Store** | `flexygent/memory/postgres_store.py` | `ConversationMemory` backed by PostgreSQL |
| **Auth Helpers** | `flexygent/server/auth.py` | API key check + JWT utilities |
| **Chat Router** | `flexygent/server/chat_router.py` | Pre-built `/chat` endpoint (full + streaming) |
| **Conversation Router** | `flexygent/server/conversation_router.py` | CRUD endpoints for conversations |
| **Streaming Helpers** | `flexygent/server/streaming.py` | SSE response utilities |
| **WebSocket Handler** | `flexygent/server/websocket_handler.py` | Persistent WebSocket connection handler |
| **Server Dependencies** | `flexygent/server/dependencies.py` | FastAPI dependency injection |
| **Request/Response Schemas** | `flexygent/server/schemas.py` | Pydantic models for API |
| **Agent Loop Streaming** | `flexygent/agent.py` | `stream=True` parameter |
| **Basic FastAPI Example** | `examples/fast_api.py` | Minimal working example |

### Flexygent v0.2.0 — Updated Project Structure

```
flexygent/
├── __init__.py
├── agent.py                    # Agent loop (updated with stream=True)
├── client.py                   # LLM client (existing)
├── interfaces.py               # UserIO abstract (existing)
├── types.py                    # Pydantic models (existing)
│
├── adapters/                   # IO adapters (existing)
│   ├── __init__.py
│   └── cli.py                  # CLI adapter (existing)
│
├── memory/                     # Conversation storage (extended)
│   ├── __init__.py
│   ├── base.py                 # Abstract ConversationMemory (updated with user_id)
│   ├── file_store.py           # JSON file backend (existing)
│   └── postgres_store.py       # NEW — PostgreSQL backend
│
├── prompts/                    # Prompt system (existing)
│   └── ...
│
├── server/                     # NEW — Server/communication utilities
│   ├── __init__.py
│   ├── auth.py                 # API key + JWT auth helpers
│   ├── schemas.py              # Request/response Pydantic models
│   ├── chat_router.py          # Pre-built chat endpoint router
│   ├── conversation_router.py  # Pre-built CRUD router
│   ├── streaming.py            # SSE streaming helpers
│   ├── websocket_handler.py    # WebSocket connection handler
│   └── dependencies.py         # FastAPI dependency injection
│
├── skills/                     # Skill system (existing)
│   └── ...
│
└── tools/                      # Tool system (existing)
    └── ...
```

---

## Layer 2: Flex (Personal Agent Daemon)

### Purpose

Flex is a **personal agent daemon** — a continuously running program on your server that acts as your always-on AI assistant. It is **not** a multi-user web service. It is **your** personal agent, running on **your** server, accessible only by **you**.

Think of it like this:
- A web server (like Aiverse) waits for requests from many users, processes them, and responds. It is stateless. It has no opinions, no goals, no initiative.
- A daemon (like Flex) is **alive**. It runs continuously. It can do things on its own — check stock prices, monitor repos, send you weekly summaries. It doesn't just respond to you; it can **initiate contact** with you. It's a single-user personal system, like having a dedicated assistant running 24/7.

### What Makes It Different From a Web Server

| Web Server (Aiverse-style) | Personal Agent Daemon (Flex) |
|---------------------------|------------------------------|
| Stateless — request in, response out | **Stateful** — always running, maintains context |
| Multi-user — serves many users | **Single-user** — serves only you |
| Reactive — only responds when asked | **Proactive** — can initiate actions and notifications |
| No background work | **Background tasks** — monitoring, scheduling, autonomous work |
| User auth (registration, login) | **API key only** — one key, one user |
| Frontend drives everything | **Server can act independently** |

### The Internal Architecture of Flex

Flex is one Python process with multiple subsystems running concurrently:

```
Flex Server Process (always running on your server)
│
├── Communication Layer (FastAPI + uvicorn)
│   │
│   │   This is the "front door" — how clients talk to Flex.
│   │   FastAPI runs on uvicorn, which uses Python's asyncio event loop.
│   │   The same event loop powers the task engine below.
│   │
│   ├── REST Endpoints
│   │   ├── POST /chat              → send message, get response
│   │   ├── POST /chat/stream       → send message, get streaming response
│   │   ├── GET  /conversations     → list conversations
│   │   ├── POST /conversations     → create new conversation
│   │   ├── GET  /conversations/{id}→ load conversation
│   │   ├── DELETE /conversations/{id} → delete conversation
│   │   ├── GET  /tasks             → list background tasks
│   │   ├── POST /tasks             → create a task
│   │   └── GET  /health            → server status
│   │
│   └── WebSocket Endpoint
│       ├── ws://flex-server/ws     → persistent connection
│       ├── Real-time chat (bidirectional)
│       ├── Server-push notifications ("AAPL dropped below $150!")
│       └── Task status updates ("Report generation: 80% complete")
│
├── Task Engine (asyncio tasks + scheduler)
│   │
│   │   Runs alongside FastAPI in the same process.
│   │   Uses asyncio.create_task() for concurrent work.
│   │   Uses APScheduler (or similar) for cron-like scheduling.
│   │
│   ├── One-off Tasks
│   │   └── "Generate a summary report of my week"
│   │       → Runs once, completes, stores result, notifies you
│   │
│   ├── Scheduled Tasks
│   │   └── "Every Sunday at 9am, send me a weekly summary"
│   │       → Cron-like, runs at scheduled times
│   │
│   ├── Monitoring Tasks
│   │   └── "Watch AAPL, alert me if it drops below $150"
│   │       → Polls at intervals, triggers on condition
│   │
│   └── Task Persistence
│       └── Tasks stored in PostgreSQL — survive server restarts
│
├── Notification System
│   │
│   │   How Flex reaches out to YOU when something happens.
│   │
│   ├── WebSocket Push    → instant notification to connected clients
│   ├── Push Notification → phone notification (Firebase Cloud Messaging)
│   └── Email             → for non-urgent or long-form notifications
│
├── Agent Engine (powered by Flexygent)
│   ├── agent_loop()      → processes chat messages
│   ├── Tool execution    → runs tools on the server
│   └── Skills            → determines agent personality and capabilities
│
└── Database (PostgreSQL)
    ├── Conversations     → chat history (via Flexygent's PostgresStore)
    ├── Tasks             → scheduled/running/completed tasks
    └── Agent state       → preferences, memory, context
```

### Why FastAPI Still Fits

Even though Flex is a daemon, FastAPI is still the right foundation because:

1. **FastAPI runs on `uvicorn`**, which is built on `asyncio`. The same event loop that handles HTTP requests can also run background tasks concurrently. No separate process needed.

2. **FastAPI supports WebSocket natively** — you can have a persistent connection to your phone alongside REST endpoints.

3. **FastAPI is the communication layer, not the whole server.** It handles the "how do I talk to Flex" part. The task engine, scheduler, and notification system run as asyncio tasks in the same process.

4. For a single-user personal daemon, `asyncio` is more than sufficient. You don't need Celery, Redis, or distributed task queues. Those are for multi-worker production systems serving thousands of users.

### What Flex Does (Application-Specific)

| Responsibility | Details |
|---------------|---------|
| **Agent Configuration** | Which model, which skills, personality, behavior rules |
| **Server Assembly** | Creates FastAPI app, mounts framework routers, starts task engine |
| **Task Definitions** | What tasks can Flex run (stock monitoring, report generation, etc.) |
| **Custom Tools** | Project-specific tools (calendar, email, trading API, etc.) |
| **Notification Config** | How to send push notifications, which email to use |
| **Database Setup** | PostgreSQL connection string, any custom tables |
| **Deployment** | Dockerfile, docker-compose, environment variables |

### What Flex Does NOT Do

- ❌ Implement the agent loop (uses `flexygent.agent.agent_loop`)
- ❌ Implement conversation storage (uses `flexygent.memory.PostgresStore`)
- ❌ Implement the chat/conversation API endpoints (mounts `flexygent.server` routers)
- ❌ Implement tool execution mechanics (uses `flexygent.tools`)
- ❌ Implement auth verification (uses `flexygent.server.auth`)
- ❌ Implement prompt building (uses `flexygent.prompts`)

### Auth — Simplified

Since Flex is single-user, auth is just an API key:

```
# .env
FLEX_API_KEY=your-secret-key-here
```

Every request must include `Authorization: Bearer <key>`. If it matches, you're in. If not, 401.

No user registration. No login screen. No password hashing. No JWT tokens. No user database.

The frontend stores the API key and sends it with every request. That's it.

### Flex Project Structure

```
flex/                               # /Users/joydipchakraborty/Projects/flex/
├── .env                            # API keys, DB connection string, LLM config
├── .env.example                    # Template
├── pyproject.toml                  # Dependencies: flexygent, apscheduler, etc.
├── Dockerfile                      # Container for deployment
├── docker-compose.yml              # Flex + PostgreSQL containers
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app + task engine startup
│   ├── config.py                   # Agent config — model, skills, personality
│   │
│   ├── tasks/                      # Task definitions (app-specific)
│   │   ├── __init__.py
│   │   ├── stock_monitor.py        # "Watch AAPL stock price"
│   │   ├── weekly_summary.py       # "Send weekly summary every Sunday"
│   │   └── report_generator.py     # "Generate a project report"
│   │
│   ├── custom_tools/               # Flex-specific tools
│   │   ├── __init__.py
│   │   ├── calendar.py             # Calendar integration
│   │   └── email_sender.py         # Send email notifications
│   │
│   └── notifications/              # How Flex reaches you
│       ├── __init__.py
│       ├── push.py                 # Firebase Cloud Messaging
│       └── email.py                # Email notifications
│
└── tests/
    └── ...
```

### How Flex's `main.py` Looks

```python
# flex/app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends

# Framework imports
from flexygent.server.chat_router import router as chat_router
from flexygent.server.conversation_router import router as conv_router
from flexygent.server.auth import api_key_dependency
from flexygent.server.dependencies import configure_agent
from flexygent.memory.postgres_store import PostgresStore
from flexygent.types import Agent, AgentConfig
from flexygent.skills import skill_registry, flex_skills
from flexygent.tools import tool_registry, get_tools
from flexygent.client import client

# App-specific
from app.config import AGENT_CONFIG
from app.tasks import start_task_engine, stop_task_engine

# Lifespan — runs on startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Start the background task engine
    await start_task_engine()
    yield
    # SHUTDOWN: Gracefully stop tasks
    await stop_task_engine()

app = FastAPI(title="Flex — Personal AI Agent", lifespan=lifespan)

# Configure agent
agent = Agent(name="flex", config=AGENT_CONFIG)
agent.apply_skills(flex_skills, skill_registry)
tools = get_tools(tool_registry, agent.get_tool_filter(skill_registry))
memory = PostgresStore(connection_string="postgresql://...")

configure_agent(app, agent=agent, memory=memory,
                tool_registry=tool_registry, tools=tools, client=client)

# Auth — single API key
require_key = api_key_dependency()

# Mount framework routers
app.include_router(chat_router, dependencies=[Depends(require_key)])
app.include_router(conv_router, dependencies=[Depends(require_key)])

@app.get("/health")
async def health():
    return {"status": "alive", "agent": agent.name}
```

Key difference from the old plan: the `lifespan` context manager starts the task engine on boot and stops it on shutdown. The task engine runs background tasks in the same asyncio event loop as FastAPI.

---

## Layer 3: Client

### Purpose

The client is the **interface between you and Flex**. It could be:
- A web app (Aiverse or custom)
- A mobile app
- A CLI
- `curl` from a terminal
- Any app that can make HTTP requests and/or hold a WebSocket connection

### Client Responsibilities

| Responsibility | Details |
|---------------|---------|
| **API Key Storage** | Store the API key securely, send with every request |
| **Chat Interface** | Text input, send button, message display |
| **Streaming Display** | Consume SSE stream and render tokens as they arrive |
| **Conversation List** | Fetch and display conversations from `GET /conversations` |
| **WebSocket Connection** | Maintain persistent connection for real-time updates |
| **Notification Display** | Show alerts pushed from server (task completed, stock alert, etc.) |
| **Task Dashboard** | View running tasks, their status, results |
| **UI/UX** | Themes, animations, responsive design |

### Client Does NOT Do

- ❌ Run the agent loop
- ❌ Call LLM APIs directly
- ❌ Execute tools
- ❌ Manage conversation state/memory
- ❌ Run background tasks
- ❌ Make decisions about model or skills

### How Client Talks to Flex

**Chat (REST):**
```
POST /chat              { message, conversation_id }       → { response, conversation_id }
POST /chat/stream       { message, conversation_id }       → SSE stream of tokens
```

**Conversations (REST):**
```
GET    /conversations                → [{ id, created_at, message_count }]
POST   /conversations                → { id }
GET    /conversations/{id}           → { id, messages: [...] }
DELETE /conversations/{id}           → { success: true }
```

**Real-time (WebSocket):**
```
ws://flex-server/ws

← Server pushes: notifications, task updates, proactive messages
→ Client sends: chat messages (alternative to REST)
```

**All requests include:** `Authorization: Bearer <api-key>`

No login. No registration. Just the API key.

### Aiverse Compatibility

Aiverse already has a chat UI, conversation list, and streaming support. To connect it to Flex:
1. Change the API base URL to point to Flex
2. Replace Firebase auth with a simple API key header
3. Match response format (or add a thin adapter layer)
4. Add WebSocket listener for server-push notifications

---

## Feature Ownership Matrix

| Feature | Flexygent (Framework) | Flex (Daemon) | Client |
|---------|:--------------------:|:-------------:|:------:|
| **Agent Loop (ReAct)** | ✅ Owns | Uses | — |
| **Tool System** | ✅ Owns | Uses + adds custom | — |
| **Skill System** | ✅ Owns | Uses + configures | — |
| **Prompt System** | ✅ Owns | Uses | — |
| **Type System** | ✅ Owns | Uses | — |
| **LLM Client** | ✅ Owns | Uses | — |
| **Conversation Storage (Abstract)** | ✅ Owns | Uses | — |
| **FileStore Backend** | ✅ Owns | — | — |
| **Postgres Backend** | ✅ Owns | Uses | — |
| **Chat Endpoint (Router)** | ✅ Owns | Mounts | Calls |
| **Conversation CRUD (Router)** | ✅ Owns | Mounts | Calls |
| **Streaming Helpers** | ✅ Owns | Uses | Consumes |
| **WebSocket Handler** | ✅ Owns | Uses | Connects |
| **API Key Auth** | ✅ Owns | Uses | Sends key |
| **JWT Helpers** | ✅ Owns | — | — |
| **Agent Configuration** | — | ✅ Owns | — |
| **Task Engine** | — | ✅ Owns | Views status |
| **Task Definitions** | — | ✅ Owns | — |
| **Notification System** | — | ✅ Owns | Receives |
| **Custom Tools** | — | ✅ Owns | — |
| **Deployment (Docker)** | — | ✅ Owns | — |
| **Chat UI** | — | — | ✅ Owns |
| **Conversation List UI** | — | — | ✅ Owns |
| **Task Dashboard UI** | — | — | ✅ Owns |
| **Notification Display** | — | — | ✅ Owns |

---

## The Flexibility Principle

### What Makes This Architecture Flexible

1. **Flexygent is pluggable.** Anyone can build their own personal daemon using it — a study bot, a trading assistant, a devops monitor. They all `pip install flexygent` and wire things together.

2. **Storage is swappable.** `FileStore` for local dev, `PostgresStore` for production. Same interface, different backend.

3. **Communication is modular.** The framework provides REST routers and WebSocket handlers. The app mounts what it needs.

4. **Client is independent.** Any app that speaks HTTP/WebSocket works. Web, mobile, CLI, curl.

5. **Tools are extensible.** The framework has 8 built-in tools. The app adds custom tools without modifying framework code.

6. **Tasks are app-specific.** The framework will eventually provide task infrastructure (v0.3.0). The app defines what tasks actually do.

### What Stays Fixed

- The `agent_loop()` function signature
- The `Conversation` / `Message` data models
- The `ConversationMemory` abstract interface
- The API endpoint shapes (`POST /chat`, `GET /conversations`, etc.)

---

## Implementation Order

### Phase 1: Framework Server Utilities (Flexygent v0.2.0)

1. Update `ConversationMemory` base with `user_id` support
2. Build `PostgresStore` implementing the updated interface
3. Build `flexygent/server/auth.py` — API key + JWT helpers
4. Build `flexygent/server/schemas.py` — request/response models
5. Build `flexygent/server/dependencies.py` — FastAPI dependency injection
6. Update `agent.py` — add `stream=True` support
7. Build `flexygent/server/streaming.py` — SSE helpers
8. Build `flexygent/server/chat_router.py` — chat endpoint
9. Build `flexygent/server/conversation_router.py` — CRUD endpoints
10. Build `flexygent/server/websocket_handler.py` — WebSocket support
11. Update `examples/fast_api.py` with a working example
12. Update `pyproject.toml` — dependencies
13. Write tests
14. Release v0.2.0 on PyPI

### Phase 2: Flex Daemon (Separate Project)

1. Create `/Projects/flex/`, `pip install flexygent[server]`
2. Wire up FastAPI with framework routers
3. Configure agent (model, skills, personality)
4. Set up PostgreSQL database
5. Build the task engine (asyncio + scheduler)
6. Build notification system (WebSocket push)
7. Add Dockerfile + docker-compose (Flex + PostgreSQL)
8. Deploy to server
9. Test end-to-end

### Phase 3: Client

1. Either adapt Aiverse or build a new client
2. Connect to Flex daemon API (API key auth)
3. Build chat interface with streaming
4. Build WebSocket connection for real-time notifications
5. Build task dashboard
6. Build conversation management UI

---

## Decisions Made

| Decision | Choice |
|----------|--------|
| **Database** | PostgreSQL |
| **Auth** | API key (single-user) — framework also provides JWT helpers for others |
| **Streaming** | `stream=True` parameter on existing `agent_loop()` |
| **Flex location** | `/Users/joydipchakraborty/Projects/flex/` (new repo) |
| **`collect_input` in API** | Pause-and-ask mechanism (server sends `requires_input` to client) |
| **Server type** | Personal daemon — not a multi-user web service |
| **Concurrency model** | asyncio (single process, no Celery/Redis needed) |
