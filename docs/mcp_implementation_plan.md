# Flexygent MCP Client — Implementation Plan

> Make Flexygent a strong MCP client that can connect to external MCP servers and use their tools alongside built-in tools — transparently.

---

## What We're Building

| Doing | Not Doing |
|-------|-----------|
| MCP **client** — connect to remote MCP servers | MCP **server** — not exposing our tools via MCP |
| Remote MCP (HTTP/SSE) — **primary focus** | Making built-in tools (web_fetch, python_repl) MCP-compatible |
| Local MCP (stdio) — **secondary, basic support** | Building a complex local MCP runner |
| Adapt MCP tools into existing ToolRegistry | Replacing the existing tool system |

---

## The Core Idea

MCP tools discovered from external servers get **adapted** into Flexygent's existing `ToolRegistry`. From `agent_loop`'s perspective, it doesn't know or care whether a tool is a local Python function or an MCP tool on a remote server. It just calls `tool_registry.call("tool_name", params)` and gets a result.

```
                    ┌─────────────────────────────┐
                    │       agent_loop()           │
                    │                              │
                    │  tool_registry.call(name, p) │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │       ToolRegistry           │
                    │                              │
                    │  tools = {                   │
                    │    "web_fetch": local func,  │  ← built-in (existing)
                    │    "python_repl": local func,│  ← built-in (existing)
                    │    "github_search": MCP call,│  ← from remote MCP server
                    │    "slack_post": MCP call,   │  ← from remote MCP server
                    │  }                           │
                    └──────────┬──────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        Local Function    MCP Remote       MCP Local
        (direct call)     (HTTP/SSE)       (stdio)
```

**Zero changes to `agent_loop`.** That's the beauty of the adapter pattern.

---

## MCP Protocol — What You Need to Know

### Message Format: JSON-RPC 2.0

Every MCP message is a JSON-RPC 2.0 object:

**Request (client → server):**
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}
```

**Response (server → client):**
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "tools": [
            {
                "name": "github_search",
                "description": "Search GitHub repos",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        ]
    }
}
```

### Transport Mechanisms

| Transport | How It Works | When Used |
|-----------|-------------|-----------|
| **HTTP/SSE (Streamable HTTP)** | Client sends HTTP POST requests, server pushes updates via SSE stream | Remote servers on the internet |
| **stdio** | Client spawns a subprocess, communicates via stdin/stdout pipes | Local third-party MCP packages |

### The Three Key Operations

| Operation | Method | What It Does |
|-----------|--------|-------------|
| **Initialize** | `initialize` | Handshake — client and server agree on protocol version and capabilities |
| **List Tools** | `tools/list` | Discover what tools the server offers (names, descriptions, parameter schemas) |
| **Call Tool** | `tools/call` | Execute a specific tool with arguments, get the result |

That's it. For our MCP client, these three operations are all we need.

---

## Should We Use the Official `mcp` Python SDK?

The official `mcp` package on PyPI handles all the protocol details — JSON-RPC framing, transport management, session lifecycle.

### Recommendation: **Use the SDK**

| Build From Scratch | Use SDK |
|-------------------|---------|
| Full control, deeper learning | Handles protocol edge cases correctly |
| More code to write and maintain | ~5 lines to connect and call tools |
| Must handle JSON-RPC framing, reconnection, error codes yourself | Battle-tested, maintained by Anthropic |
| Risk of subtle protocol bugs | Guaranteed protocol compliance |

The SDK is a single `pip install mcp` and gives you `ClientSession`, `sse_client`, and `stdio_client` — exactly what we need.

**However**, we should wrap the SDK in our own abstraction layer so:
1. If the SDK API changes, only our wrapper needs updating
2. Our interface stays clean and Flexygent-specific
3. Users don't need to learn the SDK — they use `MCPClient`

---

## File Structure

```
flexygent/mcp/
├── __init__.py           # Re-exports MCPClient
├── client.py             # MCPClient — the main class users interact with
├── connection.py         # MCPConnection — manages a single server connection
├── adapter.py            # Converts MCP tool schemas → Flexygent Tool objects
├── config.py             # MCPServerConfig — configuration for connecting to servers
└── types.py              # MCP-specific Pydantic models (MCPTool, MCPToolResult)
```

---

## Step-by-Step Implementation

### Step 1: `flexygent/mcp/config.py`

Configuration for MCP server connections.

### Models to Define

**`MCPServerConfig`** — Configuration for one MCP server:
```python
class MCPServerConfig(BaseModel):
    name: str                          # Human-readable name ("github", "slack")
    transport: str                     # "sse" or "stdio"

    # For remote (SSE) servers:
    url: Optional[str] = None          # "https://mcp-server.example.com/sse"
    headers: Optional[dict] = None     # {"Authorization": "Bearer xxx"}

    # For local (stdio) servers:
    command: Optional[str] = None      # "npx" or "python"
    args: Optional[list[str]] = None   # ["@modelcontextprotocol/server-github"]
    env: Optional[dict] = None         # Extra environment variables for the subprocess
```

**`MCPConfig`** — Top-level config holding multiple servers:
```python
class MCPConfig(BaseModel):
    servers: list[MCPServerConfig] = []
```

**Usage example:**
```python
mcp_config = MCPConfig(servers=[
    MCPServerConfig(
        name="github",
        transport="sse",
        url="https://mcp.github.com/sse",
        headers={"Authorization": "Bearer ghp_xxxxx"}
    ),
    MCPServerConfig(
        name="local-db-tool",
        transport="stdio",
        command="python",
        args=["path/to/db_mcp_server.py"]
    )
])
```

---

### Step 2: `flexygent/mcp/types.py`

Pydantic models for MCP-specific data.

**`MCPToolSchema`** — Represents a tool discovered from an MCP server:
```python
class MCPToolSchema(BaseModel):
    name: str                    # "github_search"
    description: str             # "Search GitHub repositories"
    input_schema: dict           # JSON Schema for parameters (what MCP calls "inputSchema")
    server_name: str             # Which MCP server this came from ("github")
```

**`MCPToolResult`** — Result from calling an MCP tool:
```python
class MCPToolResult(BaseModel):
    content: list[dict]          # MCP returns content as a list of content blocks
    is_error: bool = False       # Whether the tool call resulted in an error
```

---

### Step 3: `flexygent/mcp/connection.py`

Manages a single connection to one MCP server.

### Imports
```python
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client         # For remote
from mcp.client.stdio import stdio_client     # For local
from mcp import StdioServerParameters
from flexygent.mcp.config import MCPServerConfig
```

### Class: `MCPConnection`

```python
class MCPConnection:
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session: ClientSession = None
        self._connected = False
```

### `connect()` Method — Async

This is the most important method. It establishes the connection based on transport type.

**For remote (SSE):**
```python
async def connect(self):
    if self.config.transport == "sse":
        # sse_client returns (read_stream, write_stream) context manager
        # You need to keep the context alive for the lifetime of the connection
        # This means storing the context manager and entering it
        self._transport_ctx = sse_client(
            self.config.url,
            headers=self.config.headers or {}
        )
        read, write = await self._transport_ctx.__aenter__()
        self._session_ctx = ClientSession(read, write)
        self.session = await self._session_ctx.__aenter__()
        await self.session.initialize()
        self._connected = True
```

**For local (stdio):**
```python
    elif self.config.transport == "stdio":
        server_params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args or [],
            env=self.config.env
        )
        self._transport_ctx = stdio_client(server_params)
        read, write = await self._transport_ctx.__aenter__()
        self._session_ctx = ClientSession(read, write)
        self.session = await self._session_ctx.__aenter__()
        await self.session.initialize()
        self._connected = True
```

> [!IMPORTANT]
> The `sse_client` and `stdio_client` are async context managers. You can't just `async with` them inside `connect()` because the connection would close when `connect()` returns. You need to manually enter the context and store it, then exit it in `disconnect()`.

### `list_tools()` Method — Async

```python
async def list_tools(self) -> list[dict]:
    """Discover available tools from this MCP server"""
    result = await self.session.list_tools()
    return result.tools  # List of tool objects with name, description, inputSchema
```

### `call_tool()` Method — Async

```python
async def call_tool(self, tool_name: str, arguments: dict) -> str:
    """Call a tool and return the result as a string"""
    result = await self.session.call_tool(tool_name, arguments=arguments)

    # MCP returns content as a list of content blocks
    # Each block has a "type" (usually "text") and the content
    # Concatenate all text blocks into a single string
    text_parts = []
    for block in result.content:
        if hasattr(block, 'text'):
            text_parts.append(block.text)
    return "\n".join(text_parts)
```

### `disconnect()` Method — Async

```python
async def disconnect(self):
    """Clean up the connection"""
    if self._connected:
        await self._session_ctx.__aexit__(None, None, None)
        await self._transport_ctx.__aexit__(None, None, None)
        self._connected = False
```

### Edge Cases
- If the server is unreachable, `connect()` should raise a clear error with the server name
- If a tool call fails, catch the MCP error and return a readable error string (same as how existing tools return `"Tool error: ..."`)
- If the connection drops mid-session, `call_tool` should raise an error (reconnection can be added later)

---

### Step 4: `flexygent/mcp/adapter.py`

**This is the key integration piece.** It converts MCP tools into Flexygent `Tool` objects so they can be registered in the existing `ToolRegistry`.

### Imports
```python
import asyncio
from flexygent.tools.base import Tool
from flexygent.mcp.connection import MCPConnection
```

### Function: `create_mcp_tool_caller(connection, tool_name)`

This creates a **callable function** that, when called by `ToolRegistry.call()`, sends the call to the MCP server.

**The problem:** Flexygent's tools are synchronous functions (`def func(params) -> str`). But MCP calls are async (`await session.call_tool()`). We need a bridge.

```python
def create_mcp_tool_caller(connection: MCPConnection, tool_name: str):
    """
    Returns a synchronous callable that wraps an async MCP tool call.
    This is what gets registered as the Tool's 'function'.
    """
    def caller(params: dict) -> str:
        # Bridge sync → async
        # If there's a running event loop (FastAPI), use it
        # If not (CLI), create one
        try:
            loop = asyncio.get_running_loop()
            # We're inside an async context (FastAPI)
            # Use asyncio.run_coroutine_threadsafe or similar
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(
                    asyncio.run,
                    connection.call_tool(tool_name, params)
                ).result()
            return result
        except RuntimeError:
            # No event loop running (CLI mode)
            return asyncio.run(connection.call_tool(tool_name, params))

    return caller
```

> [!NOTE]
> The sync/async bridge is the trickiest part of this integration. The approach above works but has limitations. A cleaner approach for FastAPI would be to make `agent_loop` itself async in the future. For now, the ThreadPoolExecutor bridge works.

### Function: `mcp_schema_to_flexygent_params(input_schema)`

Converts MCP's `inputSchema` (JSON Schema format) to Flexygent's `parameter_allowed` dict format.

**MCP format (JSON Schema):**
```json
{
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search query"},
        "limit": {"type": "integer", "description": "Max results"}
    },
    "required": ["query"]
}
```

**Flexygent format (parameter_allowed):**
```python
{
    "query": {"type": "string", "description": "Search query"},
    "limit": {"type": "integer", "description": "Max results"}
}
```

The conversion is straightforward — just extract the `properties` dict from the JSON Schema. They're nearly identical because Flexygent's `parameter_allowed` already uses JSON Schema-style property definitions.

```python
def mcp_schema_to_flexygent_params(input_schema: dict) -> dict:
    """Convert MCP inputSchema (JSON Schema) to Flexygent parameter_allowed format"""
    if not input_schema:
        return {}
    return input_schema.get("properties", {})
```

### Function: `adapt_mcp_tools(connection, server_name)`

The main function that discovers tools from an MCP server and creates Flexygent `Tool` objects.

```python
async def adapt_mcp_tools(connection: MCPConnection, server_name: str) -> list[Tool]:
    """
    Discover tools from an MCP connection and convert them
    to Flexygent Tool objects.
    """
    mcp_tools = await connection.list_tools()
    flexygent_tools = []

    for mcp_tool in mcp_tools:
        # Create a callable that forwards to the MCP server
        caller = create_mcp_tool_caller(connection, mcp_tool.name)

        # Convert the schema
        params = mcp_schema_to_flexygent_params(mcp_tool.inputSchema)

        # Create a Flexygent Tool object
        tool = Tool(
            name=f"{server_name}_{mcp_tool.name}",  # Prefix with server name to avoid collisions
            description=f"[MCP: {server_name}] {mcp_tool.description}",
            parameter_allowed=params,
            function=caller
        )
        flexygent_tools.append(tool)

    return flexygent_tools
```

**Important: Tool naming.** MCP tools are prefixed with the server name (e.g., `github_search_repos` instead of just `search_repos`) to avoid name collisions when multiple MCP servers are connected. The LLM sees the full name and description, so it knows which tool is which.

---

### Step 5: `flexygent/mcp/client.py`

**The main class users interact with.** This is the high-level interface.

### Imports
```python
import asyncio
from flexygent.mcp.config import MCPConfig, MCPServerConfig
from flexygent.mcp.connection import MCPConnection
from flexygent.mcp.adapter import adapt_mcp_tools
from flexygent.tools.base import Tool, ToolRegistry
```

### Class: `MCPClient`

```python
class MCPClient:
    def __init__(self):
        self.connections: dict[str, MCPConnection] = {}   # server_name → connection
        self.mcp_tools: list[Tool] = []                   # All discovered tools
```

### `connect_all(config)` — Async

Connect to all servers defined in config:

```python
async def connect_all(self, config: MCPConfig):
    """Connect to all MCP servers defined in the config"""
    for server_config in config.servers:
        await self.connect(server_config)
```

### `connect(server_config)` — Async

Connect to a single server and discover its tools:

```python
async def connect(self, server_config: MCPServerConfig):
    """Connect to one MCP server and discover its tools"""
    connection = MCPConnection(server_config)
    await connection.connect()
    self.connections[server_config.name] = connection

    # Discover and adapt tools
    tools = await adapt_mcp_tools(connection, server_config.name)
    self.mcp_tools.extend(tools)
```

### `register_tools(tool_registry)` — Sync

Register all discovered MCP tools into the existing ToolRegistry:

```python
def register_tools(self, tool_registry: ToolRegistry):
    """Register all MCP tools into a Flexygent ToolRegistry"""
    for tool in self.mcp_tools:
        tool_registry.add_tool(tool)
```

### `disconnect_all()` — Async

Clean up all connections:

```python
async def disconnect_all(self):
    """Disconnect from all MCP servers"""
    for name, connection in self.connections.items():
        await connection.disconnect()
    self.connections.clear()
    self.mcp_tools.clear()
```

### `list_connected_servers()` — Sync

```python
def list_connected_servers(self) -> list[str]:
    """Return names of all connected MCP servers"""
    return list(self.connections.keys())
```

---

### Step 6: `flexygent/mcp/__init__.py`

```python
try:
    from flexygent.mcp.client import MCPClient
    from flexygent.mcp.config import MCPConfig, MCPServerConfig
except ImportError:
    pass  # mcp SDK not installed
```

---

## How It All Comes Together

### In the CLI App

```python
import asyncio
from flexygent.mcp import MCPClient, MCPConfig, MCPServerConfig
from flexygent.tools import tool_registry

async def setup_mcp():
    mcp = MCPClient()
    await mcp.connect(MCPServerConfig(
        name="github",
        transport="sse",
        url="https://mcp.github.com/sse",
        headers={"Authorization": "Bearer ghp_xxxxx"}
    ))
    mcp.register_tools(tool_registry)  # MCP tools now in the registry
    return mcp

# After this, agent_loop works exactly as before
# It just has more tools available (github_search_repos, etc.)
```

### In the Flex Daemon

```python
# flex/app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Connect to MCP servers
    mcp = MCPClient()
    await mcp.connect_all(mcp_config)
    mcp.register_tools(tool_registry)
    app.state.mcp = mcp
    yield
    # SHUTDOWN: Disconnect
    await mcp.disconnect_all()
```

### What `agent_loop` Sees

**Nothing changes.** The agent loop calls `tool_registry.call("github_search_repos", {"query": "flexygent"})` the same way it calls `tool_registry.call("web_fetch", {"url": "..."})`. The tool registry dispatches to the right function — whether it's a local Python function or an MCP call wrapper.

---

## pyproject.toml Update

Add `mcp` to the server extras:

```toml
[project.optional-dependencies]
server = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "psycopg2-binary>=2.9.0",
    "PyJWT>=2.8.0",
    "mcp>=1.0.0",
]
```

Users install with: `pip install flexygent[server]`

---

## Implementation Order

```
Step 1: flexygent/mcp/config.py        — Config models (standalone, no deps)
Step 2: flexygent/mcp/types.py         — MCP type models (standalone)
Step 3: flexygent/mcp/connection.py    — Single server connection (uses mcp SDK)
Step 4: flexygent/mcp/adapter.py       — MCP → Flexygent tool conversion (uses connection + tools/base)
Step 5: flexygent/mcp/client.py        — High-level MCPClient (uses everything above)
Step 6: flexygent/mcp/__init__.py      — Re-exports
Step 7: pyproject.toml                 — Add mcp dependency
Step 8: Tests
```

---

## Tests

**`tests/test_mcp_config.py`:**
- Test MCPServerConfig creation (SSE and stdio)
- Test MCPConfig with multiple servers
- Test validation (SSE requires url, stdio requires command)

**`tests/test_mcp_adapter.py`:**
- Test `mcp_schema_to_flexygent_params` converts correctly
- Test that adapted tools have correct name prefixing
- Test that the generated caller function has correct signature

**`tests/test_mcp_client.py`:**
- Test `register_tools` adds tools to ToolRegistry
- Test `list_connected_servers` returns correct names
- Test `disconnect_all` clears state
- Mock the MCP SDK for unit tests (don't require real MCP servers)

---

## File Dependency Graph

```
mcp/config.py          ← pydantic only (standalone)
mcp/types.py           ← pydantic only (standalone)
    ↑
mcp/connection.py      ← uses config.py + mcp SDK
    ↑
mcp/adapter.py         ← uses connection.py + tools/base.py
    ↑
mcp/client.py          ← uses everything above
    ↑
mcp/__init__.py        ← re-exports client.py
```

---

## Quick Reference

| Question | Answer |
|----------|--------|
| Does agent_loop change? | **No.** Zero changes. MCP tools are registered in the same ToolRegistry. |
| Do built-in tools become MCP? | **No.** They stay as direct Python functions. |
| What SDK do we use? | Official `mcp` Python package |
| What transport for remote? | HTTP/SSE (`sse_client` from SDK) |
| What transport for local? | stdio (`stdio_client` from SDK) — lower priority |
| How are name collisions avoided? | Tool names prefixed with server name: `github_search_repos` |
| How does sync/async bridging work? | `ThreadPoolExecutor` wraps async MCP calls for sync ToolRegistry |
| Where does MCP config go? | In the app (Flex), not the framework. Framework just provides MCPClient. |
