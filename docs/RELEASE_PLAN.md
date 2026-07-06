# Flexygent — Feature Release Plan

> A living document tracking what's built, what ships when, and what's on the horizon.

---

## Current State Audit

Before planning releases, here's an honest snapshot of where every component stands today.

### ✅ Implemented & Working

| Component | Files | Status | Notes |
|-----------|-------|--------|-------|
| **Agent Loop** | [agent.py](flexygent/agent.py) | ✅ Working | ReAct-style loop with max iteration guard, tool calling, warning injection at limit |
| **Type System** | [types.py](flexygent/types.py) | ✅ Working | `Message`, `Conversation`, `AgentConfig`, `Agent`, `Role` — all Pydantic models |
| **Tool System** | [base.py](flexygent/tools/base.py), [registry.py](flexygent/tools/registry.py) | ✅ Working | `Tool`, `ToolRegistry`, `get_tools()` — OpenAI-compatible tool schema generation, parameter filtering |
| **Built-in Tools** | 7 tools registered | ✅ Working | `run_command`, `get_weather`, `read_file`, `write_file`, `replace`, `web_fetch`, `python_repl`, `collect_input` |
| **Filesystem Tools** | [filesystem.py](flexygent/tools/filesystem.py) | ✅ Working | Read, write, replace with safety checks |
| **Web Fetch** | [web.py](flexygent/tools/web.py) | ✅ Working | BeautifulSoup HTML→text, truncation at 8000 chars |
| **Python REPL** | [python_repl.py](flexygent/tools/python_repl.py) | ✅ Working | Sandboxed subprocess execution with blocked imports, temp dir cleanup, 10s timeout |
| **System Tools** | [system.py](flexygent/tools/system.py) | ✅ Working | Shell command execution with blocklist, mock weather |
| **User Input Tool** | [user_input.py](flexygent/tools/user_input.py) | ✅ Working | Dynamic structured data collection from user |
| **Prompt System** | [builder.py](flexygent/prompts/builder.py) | ✅ Working | `PromptBuilder` with ordered sections — add/update/remove/build |
| **Prompt Sections** | identity, behavior, user_data, react, guardrails | ✅ Working | Full prompt engineering pipeline with identity, behavior rules, ReAct reasoning, guardrails, and user data instructions |
| **User Data System** | [user_data.py](flexygent/prompts/user_data.py) | ✅ Working | 4-type system: Profile (always injected), Bio (on-demand), Memory (auto-updated), Data Logs (on-demand). Local `~/.flexygent/user/` storage |
| **Skill System** | [base.py](flexygent/skills/base.py), [registry.py](flexygent/skills/registry.py) | ✅ Working | `Skill`, `SkillRegistry` with identity intro injection, config overrides, tool filtering per skill |
| **Skill Presets** | coding, ui_design, research, devops | ✅ Working | 4 presets with dedicated docs and tool allowlists |
| **I/O Abstraction** | [interfaces.py](flexygent/interfaces.py) | ✅ Working | Abstract `UserIO` base class with `get_input()` / `show_output()` |
| **CLI Adapter** | [cli.py](flexygent/adapters/cli.py) | ✅ Working | `CliUserIO` — concrete `UserIO` implementation for terminal |
| **Conversation Memory** | [base.py](flexygent/memory/base.py), [file_store.py](flexygent/memory/file_store.py) | ⚠️ Partial | Abstract `ConversationMemory` + `FileStore` (save/load/list work, `delete()` and `exists()` are stubs) |
| **LLM Client** | [client.py](flexygent/client.py) | ⚠️ Partial | Hardcoded `OpenAI` client with env vars. `LLMClient` class commented out. Cloudflare config exists but unused |
| **CLI Example** | [cli_app.py](examples/cli_app.py) | ✅ Working | Full working example using the framework: agent + skills + memory + IO adapter |
| **FastAPI Example** | [fast_api.py](examples/fast_api.py) | 🔴 Skeleton | Just a hello world — no agent integration |

### ✅ Test Coverage

| Test File | Lines | What It Covers |
|-----------|-------|----------------|
| [test_agent.py](tests/test_agent.py) | 236 | Agent loop logic, iteration limits, tool calling |
| [test_tools.py](tests/test_tools.py) | 295 | Individual tool functions (filesystem, system, web, repl) |
| [test_tools_base.py](tests/test_tools_base.py) | 155 | `Tool` and `ToolRegistry` classes |
| [test_types.py](tests/test_types.py) | 186 | `Message`, `Conversation`, `AgentConfig`, `Agent` models |
| [test_skills.py](tests/test_skills.py) | 221 | Skill registration, application, tool filtering |
| [test_memory.py](tests/test_memory.py) | 183 | FileStore save/load/list operations |
| [test_prompt_builder.py](tests/test_prompt_builder.py) | 110 | PromptBuilder add/update/remove/build |
| [test_adapters.py](tests/test_adapters.py) | 70 | CLI adapter I/O |
| [test_tool_registry.py](tests/test_tool_registry.py) | 53 | Tool registration and lookup |
| [test_web.py](tests/test_web.py) | 76 | Web fetch tool |
| **Total** | **1,585 lines** | **10 test files** |

---

## Release Plan

---

### ✅ v0.1.0 — Initial Release (Released on PyPI)

> **Goal:** Ship what works. Fix the gaps. Make it installable and usable.

This release packages everything that's already built into a clean, working foundation. No new features — just completing incomplete pieces, fixing issues, and making the framework ready for real use.

#### What Ships (Already Implemented)

| Feature | Description |
|---------|-------------|
| **Agent Loop** | ReAct-style reasoning loop with tool calling and max iteration guard |
| **Type System** | Full Pydantic models — `Message`, `Conversation`, `AgentConfig`, `Agent`, `Role` |
| **Tool Framework** | `Tool` + `ToolRegistry` + `get_tools()` with OpenAI-compatible schema generation |
| **8 Built-in Tools** | `run_command`, `get_weather`, `read_file`, `write_file`, `replace`, `web_fetch`, `python_repl`, `collect_input` |
| **Prompt Engineering** | `PromptBuilder` with ordered sections — identity, behavior, ReAct, guardrails, user data |
| **Skill System** | `Skill` + `SkillRegistry` — dynamic identity injection, config overrides, tool filtering per skill |
| **4 Skill Presets** | Coding, UI Design, Research, DevOps — each with docs and tool allowlists |
| **User Data System** | 4-type local data system (profile, bio, memory, data logs) with LLM read/write instructions |
| **I/O Abstraction** | Abstract `UserIO` interface for pluggable input/output |
| **CLI Adapter** | Terminal-based `CliUserIO` implementation |
| **Conversation Memory** | Abstract `ConversationMemory` + `FileStore` for JSON-based persistence |
| **CLI Example** | Full working example app demonstrating all framework features |
| **Test Suite** | 1,585 lines across 10 test files covering all core components |

#### What Needs Fixing for v0.1.0

| Fix | Priority | Details |
|-----|----------|---------|
| **`FileStore.delete()` & `exists()` are stubs** | 🔴 High | Currently just `print("aa")` — need actual implementations |
| **`LLMClient` class is commented out** | 🔴 High | Client is a raw module-level `OpenAI()` instance. Need a proper configurable `LLMClient` class |
| **Hardcoded model names** | 🟡 Medium | `main.py` and `cli_app.py` have hardcoded `"deepseek-v4-flash"` — should use config/env |
| **No `__init__.py` in root flexygent package** | 🟡 Medium | Missing top-level exports for clean `import flexygent` usage |
| **Duplicate `json` import in `main.py`** | 🟢 Low | Line 6 and line 12 both import json |
| **Typos in error messages** | 🟢 Low | e.g., `"unexpected errpr"`, `"doenst exist"`, `"direfctory"` scattered in tool code |
| **`get_weather` is a mock** | 🟢 Low | Returns hardcoded `25°C` — fine for v0.1.0 but document it as a placeholder |
| **Cloudflare client config unused** | 🟢 Low | `client.py` has cloudflare vars that aren't wired to anything |
| **No README** | 🟡 Medium | Needs a proper README with install instructions, quickstart, architecture overview |
| **No `__init__.py` export for adapters** | 🟢 Low | `adapters/` directory has no `__init__.py` |

#### Deliverables for v0.1.0

- [x] Agent loop with ReAct reasoning
- [x] Complete type system (Pydantic)
- [x] Tool framework + 8 built-in tools
- [x] Prompt system (builder + 5 sections)
- [x] Skill system + 4 presets
- [x] User data system (local file-based)
- [x] I/O abstraction + CLI adapter
- [x] Conversation memory (FileStore)
- [x] CLI example app
- [x] Test suite (10 files, 1585 lines)
- [x] Fix `FileStore.delete()` and `exists()` stubs
- [x] Implement proper `LLMClient` class
- [x] Add README.md
- [x] Clean up hardcoded values and typos
- [x] Add root `__init__.py` with public API exports

---

### 🏷️ v0.2.0 — FastAPI Example & Server Deployment

> **Goal:** Make Flexygent deployable as a web service.

#### New Features

| Feature | Description |
|---------|-------------|
| **FastAPI Example (Complete)** | Full agent integration — REST endpoints for chat, conversation management, tool execution. Not just hello world |
| **FastAPI IO Adapter** | New `FastApiUserIO` implementing `UserIO` — request/response based I/O instead of `input()`/`print()` |
| **WebSocket Support** | Streaming responses over WebSocket for real-time agent output |
| **API Authentication** | Basic API key auth middleware for the FastAPI server |
| **Conversation API** | REST endpoints for listing, loading, deleting saved conversations |
| **Docker Support** | Dockerfile + docker-compose for easy deployment |

#### What Already Exists to Build On

- `UserIO` abstract interface is ready — just need a new adapter
- `FileStore` memory system works — just expose it via API
- FastAPI is already a dependency in `pyproject.toml`
- Skeleton `fast_api.py` example exists

---

### 🏷️ v0.3.0 — Agent Task System

> **Goal:** Agents can execute autonomous tasks — both short-lived and long-running.

#### New Features

| Feature | Description |
|---------|-------------|
| **Task Model** | `Task` Pydantic model — `id`, `type` (short/long), `status`, `description`, `result`, `created_at`, `deadline`, `events[]` |
| **Short Tasks** | One-shot agent tasks — *"generate a project report"*, *"summarize these 5 documents"*, *"analyze this CSV"*. Agent runs, completes, returns result |
| **Long-Running Tasks** | Persistent agent tasks with indefinite or user-specified duration — *"watch AAPL stock and notify me if it drops below $150 for the next 7 days"* |
| **Task Scheduler** | Background task execution engine — manages task lifecycle, polling intervals for long tasks, timeout handling |
| **Event System** | Tasks can emit events (notifications, alerts, status updates). Events are logged and optionally pushed to the user |
| **Task Storage** | Persist tasks to disk (extending the existing `FileStore` pattern) so they survive restarts |
| **Task Management** | Create, pause, resume, cancel, list, and inspect tasks |

#### Architecture

```
flexygent/
├── tasks/
│   ├── base.py          # Task model, TaskStatus enum
│   ├── runner.py         # TaskRunner — executes short tasks
│   ├── scheduler.py      # TaskScheduler — manages long-running tasks
│   ├── events.py         # Event model, event emission
│   └── storage.py        # Task persistence (file-based)
```

#### Example Use Cases

| Type | Example | Duration |
|------|---------|----------|
| Short | *"Read all .py files in this project and write a summary report"* | Seconds to minutes |
| Short | *"Fetch data from these 3 APIs and combine into a spreadsheet"* | Seconds |
| Long | *"Monitor AAPL stock price every hour, alert if it drops below $150"* | Days (user-specified) |
| Long | *"Watch this GitHub repo for new issues and summarize them daily"* | Indefinite |
| Long | *"Track my DSA progress and send weekly summary every Sunday"* | Indefinite |

---

### 🏷️ v0.4.0 — User Task System

> **Goal:** Users can manage their own tasks, to-dos, and roadmaps through the agent.

#### New Features

| Feature | Description |
|---------|-------------|
| **User Task Model** | Personal tasks/to-dos with priority, due dates, categories, progress tracking |
| **Quick Tasks** | Short-lived to-dos — *"finish mock test"*, *"buy groceries for dinner"*, *"submit assignment"* |
| **Roadmap Tasks** | Long-term structured goals — *"complete DSA roadmap"*, *"finish system design course"*, *"read 12 books this year"* |
| **Progress Tracking** | Subtask decomposition, completion %, milestones for roadmap tasks |
| **Task Persistence** | Stored under the user data system (`~/.flexygent/user/data/tasks/`) — integrates with existing Type 4 data logs |
| **Natural Language Management** | User talks naturally — *"mark the array topic as done"*, *"add buy milk to my shopping list"*, *"how much of my DSA roadmap is left?"* |
| **Smart Suggestions** | Agent proactively suggests next steps based on task history and patterns |

#### Integration with User Data System

User tasks naturally extend the existing `data/` directory structure:

```
~/.flexygent/user/data/
├── tasks/
│   ├── active.json       # Current to-dos and quick tasks
│   ├── roadmaps/
│   │   ├── dsa.json      # DSA roadmap with subtopics
│   │   └── reading.json  # Reading list roadmap
│   └── completed.json    # Archive of done tasks
```

---

### 🏷️ v0.5.0 — RAG System

> **Goal:** Enable retrieval-augmented generation for knowledge-grounded responses.

#### New Features

| Feature | Description |
|---------|-------------|
| **Document Ingestion** | Load documents (PDF, MD, TXT, code files) into a vector store |
| **Chunking Pipeline** | Smart text splitting — respects code blocks, paragraphs, headers |
| **Embedding Generation** | Generate embeddings via API (OpenAI, Cloudflare, or local models) |
| **Vector Store Integration** | ChromaDB integration (already a dependency in `pyproject.toml`) |
| **RAG Tool** | New `rag_query` tool — agent can search ingested documents for relevant context |
| **Context Injection** | Retrieved chunks injected into the prompt before the LLM call |
| **Per-Skill RAG** | Skills can define their own document collections — coding skill searches code docs, research skill searches papers |

#### Architecture

```
flexygent/
├── rag/
│   ├── base.py           # RAGStore abstract interface
│   ├── chunker.py        # Document chunking strategies
│   ├── embeddings.py     # Embedding generation
│   ├── chroma_store.py   # ChromaDB implementation
│   └── pipeline.py       # Ingest → chunk → embed → store pipeline
```

> [!NOTE]
> ChromaDB is already listed as a dependency in [pyproject.toml](pyproject.toml). The `enable_rag` flag already exists in `AgentConfig`. This version activates all of it.

---

### 🏷️ v0.6.0 — User Data as MCP Server

> **Goal:** Make the user data system accessible to any LLM that supports the Model Context Protocol.

#### New Features

| Feature | Description |
|---------|-------------|
| **MCP Server** | Expose the user data system as a standalone MCP server |
| **MCP Tools** | `read_profile`, `read_bio`, `read_memory`, `read_data_log`, `update_profile`, `update_memory`, `update_data_log` |
| **Universal Access** | Any MCP-compatible LLM (Claude, GPT via plugins, etc.) can access user data without the user re-explaining context every time |
| **Authentication** | Local auth so only authorized LLMs can read/write user data |
| **Schema Validation** | MCP tools enforce the same strict schemas defined in `user_data.py` |

#### How It Works

```
┌──────────────────┐     MCP Protocol     ┌─────────────────────┐
│  Any LLM Client  │ ◄──────────────────► │  Flexygent MCP      │
│  (Claude, GPT,   │    read_profile()    │  Server             │
│   local models)  │    update_memory()   │                     │
└──────────────────┘    read_data_log()   │  ~/.flexygent/user/ │
                                          └─────────────────────┘
```

> [!IMPORTANT]
> This is a major architectural evolution — the user data system goes from "Flexygent-only" to "universal personal context layer". Any LLM the user talks to gets their preferences, context, and history without them repeating everything.

---

### 🏷️ v0.7.0 — Database Backend & Pluggable Storage

> **Goal:** Replace local file storage with database options for production use.

#### New Features

| Feature | Description |
|---------|-------------|
| **Database Memory Backend** | New `ConversationMemory` implementation backed by SQLite / PostgreSQL |
| **Storage Abstraction** | Clean interface so users can swap between `FileStore`, `SQLiteStore`, `PostgresStore` |
| **Task Database Storage** | Agent and user tasks stored in DB instead of JSON files |
| **User Data DB Option** | Optional DB-backed user data store (alternative to local files) |
| **Migration Tools** | Scripts to migrate existing local data → database |

#### Architecture

```
flexygent/
├── memory/
│   ├── base.py           # (existing) Abstract ConversationMemory
│   ├── file_store.py     # (existing) JSON file implementation
│   ├── sqlite_store.py   # NEW — SQLite implementation
│   └── postgres_store.py # NEW — PostgreSQL implementation
├── storage/
│   ├── base.py           # Abstract StorageBackend
│   ├── local.py          # Local filesystem
│   ├── sqlite.py         # SQLite
│   └── postgres.py       # PostgreSQL
```

---

### 🏷️ v0.8.0 — Platform-Specific IO Adapters & Example Implementations

> **Goal:** Prove the framework works across different platforms with real, deployable examples.

#### New IO Adapters

| Adapter | Description |
|---------|-------------|
| **FastAPI Adapter** | (Completed in v0.2.0 — refined here) |
| **Blender Adapter** | Custom `UserIO` for Blender's Python scripting environment — agent runs inside Blender |
| **Discord Bot Adapter** | `DiscordUserIO` — agent as a Discord bot |
| **Telegram Adapter** | `TelegramUserIO` — agent as a Telegram bot |

#### Example Implementations

| Example | Description | Adapter Used |
|---------|-------------|--------------|
| **Personal CLI Assistant** | Full-featured personal assistant with all skills, user data, and task management | CLI |
| **FastAPI Chat Server** | Deployable REST/WebSocket chat server with conversation management | FastAPI |
| **Blender AI Assistant** | Agent running inside Blender to help with 3D modeling tasks — requires custom IO adapter for Blender's event loop | Blender |
| **Discord Study Bot** | Agent in Discord helping with DSA practice, tracking progress, sending reminders | Discord |

> [!WARNING]
> The Blender adapter requires deep integration with Blender's Python API and event system. This is a non-trivial IO adapter — not just wrapping `input()`/`print()`. It will need its own mini-project to handle Blender's modal operators, UI panels, and background execution.

---

## Feature Matrix — What's in Each Release

| Feature | v0.1.0 | v0.2.0 | v0.3.0 | v0.4.0 | v0.5.0 | v0.6.0 | v0.7.0 | v0.8.0 |
|---------|--------|--------|--------|--------|--------|--------|--------|--------|
| Agent Loop (ReAct) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tool Framework + 8 Tools | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Prompt System | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Skill System (4 presets) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| User Data (Local) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CLI Adapter + Example | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Conversation Memory (FileStore) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Test Suite | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| FastAPI Example + Adapter | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Server Deployment (Docker) | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agent Tasks (Short + Long) | — | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Task Scheduler + Events | — | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| User Tasks + Roadmaps | — | — | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG System (ChromaDB) | — | — | — | — | ✅ | ✅ | ✅ | ✅ |
| User Data as MCP Server | — | — | — | — | — | ✅ | ✅ | ✅ |
| Database Storage Backend | — | — | — | — | — | — | ✅ | ✅ |
| Blender / Discord Adapters | — | — | — | — | — | — | — | ✅ |
| Platform Example Apps | — | — | — | — | — | — | — | ✅ |

---

## Codebase Stats (Current)

| Metric | Count |
|--------|-------|
| **Core source files** | ~20 Python files |
| **Test files** | 10 files, 1,585 lines |
| **Skill presets** | 4 (coding, ui_design, research, devops) |
| **Skill docs** | 4 markdown files |
| **Built-in tools** | 8 registered |
| **IO adapters** | 1 (CLI) |
| **Example apps** | 2 (CLI working, FastAPI skeleton) |
| **Dependencies** | openai, pydantic, httpx, python-dotenv, chromadb, pydantic-settings, requests, beautifulsoup4, fastapi, uvicorn |

---

## Guiding Principles

1. **Ship incrementally** — each version adds one major feature area, not everything at once
2. **Tests ship with features** — no release without test coverage for new code
3. **Backward compatible** — new versions don't break existing `v0.1.0` usage patterns
4. **Examples prove the framework** — every major feature gets a working example, not just library code
5. **Local-first, cloud-optional** — everything works on a single machine first; remote storage/deployment is additive
