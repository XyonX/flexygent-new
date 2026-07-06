# Flexygent Ecosystem — Three-Layer Architecture Plan

> This document defines the **purpose, responsibilities, boundaries, and structure** of the three components in the Flexygent ecosystem. The goal is maximum reusability in the framework so that any project built on Flexygent (not just Flex) gets the heavy lifting for free.

---

## The Three Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: FRONTEND CLIENT                 │
│              (Aiverse, or any web/mobile/desktop app)       │
│                                                             │
│   • Sends messages with conversation_id                     │
│   • Displays responses (text, streaming)                    │
│   • Handles user auth (login UI, token storage)             │
│   • Manages conversation list UI                            │
│   • Zero AI logic — pure display layer                      │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTP / WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   LAYER 2: FLEX (Backend Server)            │
│            (Personal AI Agent — uses Flexygent)             │
│                                                             │
│   • pip install flexygent                                   │
│   • Project-specific config, skills, deployment             │
│   • Wires together framework components                     │
│   • Runs as a deployed service                              │
└──────────────────────────┬──────────────────────────────────┘
                           │  import flexygent
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  LAYER 1: FLEXYGENT (Framework)             │
│               (Reusable agentic AI framework)               │
│                                                             │
│   • Agent loop, tools, skills, prompts, types               │
│   • Storage adapters, auth middleware, server utilities      │
│   • Everything generic — nothing project-specific           │
│   • Published on PyPI: pip install flexygent                │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Flexygent (Framework)

### Purpose

Flexygent is a **reusable agentic AI framework**. It provides building blocks that anyone can use to create their own AI agent backend. It should contain everything that is **generic** — things any agentic AI project would need — and nothing that is specific to any single project.

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

### What Needs to Be Added for v0.2.0

The key question is: **among auth, database storage, conversation management, multi-user support, and API server utilities — how much belongs in the framework?**

Here's the breakdown:

---

#### 1. Conversation Memory — Database Backends

**Belongs in: FRAMEWORK ✅**

You already have `ConversationMemory` (abstract) and `FileStore` (implementation). The exact same pattern should be extended with database backends.

Why framework? Because **anyone** building an agent server needs persistent conversation storage. Whether it's Flex, or someone else's chatbot, they all need the same thing.

```
flexygent/memory/
├── base.py              # (existing) Abstract ConversationMemory
├── file_store.py        # (existing) JSON file implementation
└── postgres_store.py    # NEW — PostgreSQL implementation
```

The interface stays the same — `save()`, `load()`, `list_saved()`, `delete()`, `exists()`. The app just picks which backend to use:

```python
# In Flex (app), you just pick the backend
from flexygent.memory.postgres_store import PostgresStore
memory = PostgresStore(connection_string="postgresql://...")

# Same API as FileStore — the framework handles the rest
memory.save(conversation, "conv-123")
conversation = memory.load("conv-123")
```

> [!IMPORTANT]
> The current `ConversationMemory` interface needs a small upgrade — it should support a **user_id** parameter so conversations can be isolated per user. This is essential for multi-user servers.

**Updated abstract interface:**
```python
class ConversationMemory(ABC):
    def save(self, conversation, name, user_id=None): ...
    def load(self, name, user_id=None): ...
    def list_saved(self, user_id=None) -> list[str]: ...
    def delete(self, name, user_id=None): ...
    def exists(self, name, user_id=None): ...
```

The `user_id=None` default keeps backward compatibility — single-user apps (like CLI) don't need to pass it.

---

#### 2. Authentication Middleware

**Basic API key auth: FRAMEWORK ✅**
**Full user system (registration, login, profiles): APPLICATION ❌**

Why split? API key auth is universal — any server exposing an agent endpoint needs to protect it. But a full user registration/login system is project-specific (some apps use Firebase like Aiverse, some use email/password, some use OAuth).

What the framework provides:

```
flexygent/server/
├── auth.py              # API key middleware + JWT token verification helper
```

```python
# Framework provides these reusable pieces:

# 1. Simple API key check (for single-user / service-to-service)
def api_key_auth(api_key: str) -> bool:
    """Verify API key against env var FLEXYGENT_API_KEY"""

# 2. JWT token verification helper (for multi-user)
def verify_jwt(token: str, secret: str) -> dict:
    """Decode and verify a JWT token, return the payload"""

# 3. FastAPI dependency for protecting routes
async def require_auth(request: Request) -> dict:
    """FastAPI dependency — extracts and verifies auth from request"""
```

What the **app** handles:
- User registration / signup flow
- Password hashing
- Token generation (login endpoint)
- User profiles, avatars, preferences
- Which auth provider to use (Firebase, custom JWT, OAuth)

---

#### 3. FastAPI Server Utilities

**Belongs in: FRAMEWORK ✅ (as reusable routers/blueprints)**

The framework should provide **pre-built FastAPI router blueprints** that any app can mount. Think of them as plug-and-play API modules.

```
flexygent/server/
├── __init__.py
├── auth.py              # Auth middleware (described above)
├── chat_router.py       # Pre-built chat endpoint (POST /chat)
├── conversation_router.py  # CRUD endpoints for conversations
├── streaming.py         # SSE/streaming response helpers
└── dependencies.py      # FastAPI dependencies (get current user, get memory store, etc.)
```

**`chat_router.py`** — A reusable router that any app can mount:
```python
# What the framework provides:
router = APIRouter(prefix="/chat")

@router.post("/")
async def chat(request: ChatRequest, ...):
    """
    Receives a message + conversation_id
    Loads the conversation from memory
    Runs agent_loop()
    Saves the conversation
    Returns the response
    """

@router.post("/stream")
async def chat_stream(request: ChatRequest, ...):
    """Same but returns Server-Sent Events for streaming"""
```

**`conversation_router.py`** — CRUD for conversations:
```python
router = APIRouter(prefix="/conversations")

@router.get("/")          # List conversations (for current user)
@router.post("/")         # Create new conversation
@router.get("/{conv_id}") # Load a specific conversation
@router.delete("/{conv_id}")  # Delete a conversation
```

The app then just **mounts** these routers:
```python
# In Flex (app) — server.py
from fastapi import FastAPI
from flexygent.server.chat_router import router as chat_router
from flexygent.server.conversation_router import router as conv_router

app = FastAPI()
app.include_router(chat_router)
app.include_router(conv_router)
```

> [!NOTE]
> The routers use FastAPI's **dependency injection** pattern. The app provides the actual memory store, auth handler, and agent config through dependencies. The framework routers are generic — they don't know or care which database or auth system the app uses.

---

#### 4. Multi-User Support

**Framework provides: user_id-aware interfaces ✅**
**App provides: the actual user management ❌**

The framework doesn't need to know what a "user" is. It just needs to know that conversations belong to someone, identified by a `user_id` string. The framework passes `user_id` through its interfaces:

- `ConversationMemory.save(conv, name, user_id="user_123")`
- `ConversationMemory.list_saved(user_id="user_123")`
- Chat router extracts `user_id` from the auth token

The app defines what a "user" actually is — database model, registration, login, etc.

---

### Flexygent v0.2.0 — Framework Additions Summary

| New Component | Location | What It Does |
|--------------|----------|-------------|
| **Postgres Memory Store** | `flexygent/memory/postgres_store.py` | `ConversationMemory` backed by PostgreSQL |
| **Auth Middleware** | `flexygent/server/auth.py` | API key check + JWT verification helper |
| **Chat Router** | `flexygent/server/chat_router.py` | Pre-built `/chat` endpoint (full + streaming) |
| **Conversation Router** | `flexygent/server/conversation_router.py` | CRUD endpoints for conversations |
| **Streaming Helpers** | `flexygent/server/streaming.py` | SSE response utilities for streaming agent output |
| **Server Dependencies** | `flexygent/server/dependencies.py` | FastAPI dependency injection for memory, auth, agent |
| **Basic FastAPI Example** | `examples/fast_api.py` | Minimal example showing how to use the server components |

### Flexygent v0.2.0 — Updated Project Structure

```
flexygent/
├── __init__.py
├── agent.py                    # Agent loop (existing)
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
├── server/                     # NEW — Server utilities
│   ├── __init__.py
│   ├── auth.py                 # API key + JWT auth middleware
│   ├── chat_router.py          # Pre-built chat endpoint router
│   ├── conversation_router.py  # Pre-built CRUD router
│   ├── streaming.py            # SSE streaming helpers
│   └── dependencies.py         # FastAPI dependency injection
│
├── skills/                     # Skill system (existing)
│   └── ...
│
└── tools/                      # Tool system (existing)
    └── ...
```

---

## Layer 2: Flex (Backend Server / Personal AI Agent)

### Purpose

Flex is a **complete, deployable personal AI agent backend** built using Flexygent. It is a **separate project** with its own repository, its own configuration, and its own deployment.

Think of it this way:
- **Flexygent** is like Django (the framework)
- **Flex** is like a specific website built with Django (the application)

Anyone could build their own "Flex" using Flexygent — an education bot, a customer support agent, a code review bot — each would be a separate project that `pip install flexygent` and wires things together.

### What Flex Does (Application-Specific)

| Responsibility | Details |
|---------------|---------|
| **Agent Configuration** | Which model to use, which skills to load, what the agent's personality is |
| **User System** | User registration, login, profile management (could use Firebase auth like Aiverse, or custom JWT) |
| **Database Setup** | Database connection, migrations, which storage backend to use |
| **Custom Skills** | Any skills specific to "Flex" that don't belong in the generic framework |
| **Custom Tools** | Project-specific tools (e.g., calendar integration, email, etc.) |
| **Server Assembly** | Creates the FastAPI app, mounts the framework routers, adds custom endpoints |
| **Deployment** | Dockerfile, docker-compose, environment variables, production config |
| **API Documentation** | OpenAPI/Swagger docs for the Flex-specific API |

### What Flex Does NOT Do

- ❌ Implement the agent loop (uses `flexygent.agent.agent_loop`)
- ❌ Implement conversation storage logic (uses `flexygent.memory.PostgresStore`)
- ❌ Implement tool execution (uses `flexygent.tools`)
- ❌ Implement prompt building (uses `flexygent.prompts`)
- ❌ Implement auth verification logic (uses `flexygent.server.auth`)

### Flex Project Structure

```
flex/
├── .env                        # Environment variables (API keys, DB config, auth secrets)
├── .env.example                # Template for .env
├── pyproject.toml              # Dependencies: flexygent, uvicorn, etc.
├── Dockerfile                  # Container for deployment
├── docker-compose.yml          # Container orchestration
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app — mounts routers, configures middleware
│   ├── config.py               # App config — model name, skills, agent setup
│   │
│   ├── auth/                   # User authentication (app-specific)
│   │   ├── __init__.py
│   │   ├── router.py           # Login, register, refresh token endpoints
│   │   ├── models.py           # User database model
│   │   └── utils.py            # Password hashing, token generation
│   │
│   └── custom_tools/           # Flex-specific tools (optional)
│       ├── __init__.py
│       └── calendar.py         # Example: calendar integration tool
│
├── migrations/                 # Database migrations
│   └── ...
│
└── tests/
    └── ...
```

### How Flex Wires Things Together

The beauty is in how little code the Flex `main.py` needs:

```python
# flex/app/main.py — The entire server in ~30 lines

from fastapi import FastAPI
from flexygent.server.chat_router import router as chat_router
from flexygent.server.conversation_router import router as conv_router
from flexygent.server.auth import require_auth
from flexygent.server.dependencies import configure_agent
from flexygent.memory.postgres_store import PostgresStore
from flexygent.types import Agent, AgentConfig
from flexygent.skills import skill_registry, flex_skills
from flexygent.tools import tool_registry, get_tools

from app.auth.router import router as auth_router

# Create app
app = FastAPI(title="Flex — Personal AI Agent")

# Configure the agent (framework handles the rest)
agent = Agent(name="flex", config=AgentConfig(model="deepseek-v4-flash"))
agent.apply_skills(flex_skills, skill_registry)
memory = PostgresStore(connection_string="postgresql://...")

configure_agent(app, agent=agent, memory=memory, tool_registry=tool_registry)

# Mount framework routers (chat + conversation CRUD)
app.include_router(chat_router, dependencies=[Depends(require_auth)])
app.include_router(conv_router, dependencies=[Depends(require_auth)])

# Mount app-specific routers
app.include_router(auth_router)  # Login, register (app-specific)
```

This is the power of putting the right things in the framework — the application becomes a thin configuration layer.

---

## Layer 3: Frontend Client

### Purpose

The frontend is a **display and interaction layer**. It has **zero AI logic**. It sends messages to the Flex backend and renders the responses. It could be:
- **Aiverse** (your existing React/JS chat app)
- A mobile app (React Native, Flutter)
- A desktop app (Electron)
- Any third-party client that speaks HTTP

### Frontend Responsibilities

| Responsibility | Details |
|---------------|---------|
| **Authentication UI** | Login/register screens, token storage in localStorage |
| **Conversation List** | Fetch and display conversations from `GET /conversations` |
| **Chat Interface** | Text input, send button, message display |
| **Streaming Display** | Consume SSE stream from `/chat/stream` and render tokens as they arrive |
| **Message History** | Load past messages when opening a conversation |
| **UI/UX** | Animations, themes, responsive design, accessibility |
| **Error Handling** | Display network errors, auth expiry, rate limits |

### Frontend Does NOT Do

- ❌ Run the agent loop
- ❌ Call LLM APIs directly
- ❌ Execute tools
- ❌ Manage conversation state/memory
- ❌ Handle prompt engineering
- ❌ Make decisions about which model or skills to use

### How Frontend Talks to Flex

The API contract is simple. The frontend only needs to know these endpoints:

**Auth:**
```
POST /auth/login        { email, password }     → { token }
POST /auth/register     { email, password, ... } → { token }
```

**Chat:**
```
POST /chat              { message, conversation_id }  → { response }
POST /chat/stream       { message, conversation_id }  → SSE stream
```

**Conversations:**
```
GET    /conversations                    → [{ id, title, last_message, ... }]
POST   /conversations                    → { id, title }
GET    /conversations/{id}               → { id, messages: [...] }
DELETE /conversations/{id}               → { success: true }
```

All requests include `Authorization: Bearer <token>` header.

### Aiverse Compatibility

Your existing Aiverse frontend already follows this exact pattern:
- It sends messages with a `conversationId`
- It displays streamed responses
- It has auth (Firebase)
- It has a conversation list

To connect Aiverse to the Flex backend, you would need to:
1. Update the API base URL to point to Flex
2. Adjust the auth flow (Flex uses JWT, Aiverse uses Firebase — you'd pick one)
3. Match the response format (or add a thin adapter)

The aiverse frontend is in JS/React, the Flex backend is in Python — that's fine because they only communicate via HTTP.

---

## Feature Ownership Matrix

This is the most important table. For each feature, it shows **where** the code lives:

| Feature | Flexygent (Framework) | Flex (Backend App) | Frontend Client |
|---------|:--------------------:|:------------------:|:---------------:|
| **Agent Loop (ReAct)** | ✅ Owns | Uses | — |
| **Tool System** | ✅ Owns | Uses + adds custom | — |
| **Skill System** | ✅ Owns | Uses + configures | — |
| **Prompt System** | ✅ Owns | Uses | — |
| **Type System** | ✅ Owns | Uses | — |
| **LLM Client** | ✅ Owns | Uses | — |
| **Conversation Storage (Abstract)** | ✅ Owns | Uses | — |
| **FileStore Backend** | ✅ Owns | Uses | — |
| **Postgres Backend** | ✅ Owns | Uses | — |
| **Chat Endpoint (Router)** | ✅ Owns | Mounts | Calls |
| **Conversation CRUD (Router)** | ✅ Owns | Mounts | Calls |
| **Streaming Response Helpers** | ✅ Owns | Uses | Consumes |
| **API Key Auth Middleware** | ✅ Owns | Uses | — |
| **JWT Verification Helper** | ✅ Owns | Uses | — |
| **User Registration/Login** | — | ✅ Owns | Calls |
| **User Database Model** | — | ✅ Owns | — |
| **Password Hashing** | — | ✅ Owns | — |
| **Token Generation** | — | ✅ Owns | — |
| **Agent Configuration** | — | ✅ Owns | — |
| **Custom Skills/Tools** | — | ✅ Owns | — |
| **Deployment (Docker)** | — | ✅ Owns | — |
| **Database Migrations** | — | ✅ Owns | — |
| **Login/Register UI** | — | — | ✅ Owns |
| **Chat Interface** | — | — | ✅ Owns |
| **Conversation List UI** | — | — | ✅ Owns |
| **Streaming Display** | — | — | ✅ Owns |
| **Themes/Animations** | — | — | ✅ Owns |

---

## The Flexibility Principle

### What Makes This Architecture Flexible

1. **Flexygent is pluggable.** Anyone can build their own "Flex" — a medical chatbot, a coding assistant, a study buddy. They all `pip install flexygent` and wire things together.

2. **Storage is swappable.** The abstract `ConversationMemory` means you can start with `FileStore` (local dev) and switch to `PostgresStore` (production) — without changing any other code.

3. **Auth is swappable.** The framework provides the verification utilities. The app decides what auth system to use (Firebase, custom JWT, OAuth, API keys).

4. **Frontend is independent.** Any client that can make HTTP requests works. React, Vue, mobile, curl, Postman — the backend doesn't care.

5. **Tools are extensible.** The framework has 8 built-in tools. The app can register its own custom tools into the same `ToolRegistry` without modifying framework code.

### What Stays Fixed

- The `agent_loop()` function signature — this is the core contract
- The `Conversation` / `Message` data models — these are the shared language
- The `ConversationMemory` abstract interface — all backends implement this
- The API endpoint shapes (`POST /chat`, `GET /conversations`, etc.) — clients depend on these

---

## Implementation Order

### Phase 1: Framework Server Utilities (Flexygent v0.2.0)

1. Update `ConversationMemory` base with `user_id` support
2. Build `PostgresStore` implementing the updated interface
3. Build `flexygent/server/auth.py` — API key + JWT helpers
4. Build `flexygent/server/chat_router.py` — reusable chat endpoint
5. Build `flexygent/server/conversation_router.py` — CRUD endpoints
6. Build `flexygent/server/streaming.py` — SSE helpers
7. Build `flexygent/server/dependencies.py` — FastAPI dependency injection
8. Update `examples/fast_api.py` with a basic working example
9. Write tests for all new components
10. Release Flexygent v0.2.0 on PyPI

### Phase 2: Flex Backend (Separate Project)

1. Create the Flex project, `pip install flexygent`
2. Wire up FastAPI with framework routers
3. Implement user auth (registration, login, JWT)
4. Configure the agent (model, skills, custom tools)
5. Set up PostgreSQL database
6. Add Dockerfile + docker-compose
7. Deploy to a server
8. Test end-to-end with curl/Postman

### Phase 3: Frontend Integration

1. Either adapt Aiverse or build a new frontend
2. Connect to Flex backend API
3. Implement auth flow
4. Build chat interface with streaming support
5. Build conversation management UI

---

## Open Questions

> [!IMPORTANT]
> These need your input before we start implementation:

1. **Database choice for Flex:** SQLite (simple, single-file, good for personal use) or PostgreSQL (production-grade, needed for multi-user at scale)? I suggest SQLite first, Postgres later.

2. **Auth system for Flex:** Custom JWT (self-contained, no external dependency) or Firebase (what Aiverse already uses, handles Google/GitHub login for free)? If we want Aiverse compatibility, Firebase makes sense.

3. **Streaming implementation:** The current `agent_loop()` waits for the full response. For streaming, we need to modify it to yield tokens. Should this be a separate `agent_loop_stream()` function, or should we add a `stream=True` parameter to the existing one?

4. **Flex project name and location:** Where should the Flex project live? `/Projects/flex/`? And should it be a new GitHub repo?

5. **Should `collect_input` tool work in API mode?** Currently it calls `input()` directly. In a server, that would block. Should it be disabled for API mode, or should we design a mechanism for the backend to "ask" the frontend for input mid-conversation?
