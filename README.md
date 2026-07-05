# Flexygent

A minimal, flexible, from-scratch AI agent framework in Python.

Build agentic AI systems that can reason, use tools, remember conversations, and adapt their personality through skills — all with a clean, composable API.

---

## Features

- **ReAct Agent Loop** — Agents think before they act. Built-in reasoning → action → observation cycle.
- **Tool System** — 8 built-in tools + easy custom tool creation. OpenAI-compatible schemas auto-generated.
- **Skill System** — Plug-in skill modules that reshape agent identity, unlock specific tools, and override configs.
- **Prompt Engineering** — Composable `PromptBuilder` with ordered sections. Full control over every piece of the system prompt.
- **User Data System** — Persistent personal context (profile, bio, memory, data logs) so the agent remembers who you are.
- **Conversation Memory** — Save, load, and resume conversations. Pluggable storage backends.
- **I/O Abstraction** — Swap between CLI, API, or any platform by implementing a simple interface.
- **Provider Agnostic** — Works with any OpenAI-compatible API (OpenAI, Anthropic via proxy, DeepSeek, local models, OpenRouter, etc.)

---

## Installation

```bash
# Clone the repo
git clone https://github.com/XyonX/flexygent-new.git
cd flexygent-new

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with all dependencies
pip install -e ".[dev]"
```

### Environment Setup

Create a `.env` file in the project root:

```env
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://your-llm-provider-endpoint
```

**Provider examples:**

| Provider | LLM_BASE_URL |
|----------|----------|
| OpenAI | `https://api.openai.com/v1` |
| OpenRouter | `https://openrouter.ai/api/v1` |
| DeepSeek | `https://api.deepseek.com/v1` |
| Local (Ollama) | `http://localhost:11434/v1` |
| Local (LM Studio) | `http://localhost:1234/v1` |
| Groq | `https://api.groq.com/openai/v1` |

Flexygent uses the OpenAI client library under the hood, so **any provider that exposes an OpenAI-compatible API works out of the box** — just change `LLM_API_KEY` and `LLM_BASE_URL`.

---

## Quick Start

### Minimal Agent (5 lines)

```python
from flexygent.types import Conversation, AgentConfig, Agent
from flexygent.tools import tool_registry, get_tools
from flexygent.client import client
from flexygent.agent import agent_loop

# 1. Create an agent with a config
config = AgentConfig(model="gpt-4o-mini")
agent = Agent(name="assistant", config=config)

# 2. Set up conversation with the system prompt
conv = Conversation()
conv.add_message(agent.get_system_message())

# 3. Prepare tools
tools = get_tools(tool_registry, allowed=None)  # None = all tools

# 4. Run the agent
response = agent_loop(conv, "What files are in the current directory?", tools, tool_registry, client, config)
print(response)
```

That's it. The agent will reason about the question, call the `run_command` tool with `ls`, and give you a natural language answer.

### Interactive CLI App

```python
from flexygent.types import Conversation, AgentConfig, Agent
from flexygent.tools import tool_registry, get_tools
from flexygent.skills import skill_registry
from flexygent.client import client
from flexygent.agent import agent_loop
from flexygent.adapters.cli import CliUserIO
from flexygent.memory.file_store import FileStore

# Setup
io = CliUserIO()
config = AgentConfig(model="gpt-4o-mini")
agent = Agent(name="flex", config=config)

# Apply skills — this agent gets coding + research abilities
agent.apply_skills(["coding", "research"], skill_registry)

# Conversation + tools
conv = Conversation()
conv.add_message(agent.get_system_message())
tools = get_tools(tool_registry, agent.get_tool_filter(skill_registry))

# Memory for saving/loading conversations
memory = FileStore()

# Chat loop
while True:
    user_input = io.get_input("You: ")
    if user_input == "exit":
        break

    response = agent_loop(conv, user_input, tools, tool_registry, client, config)
    io.show_output(f"Agent: {response}")

# Save conversation on exit
memory.save(conv, memory.gen_file_name())
```

---

## Architecture

```
flexygent/
├── agent.py              # ReAct agent loop (the brain)
├── types.py              # Core types — Message, Conversation, Agent, AgentConfig
├── client.py             # LLM client (OpenAI-compatible)
├── interfaces.py         # Abstract UserIO interface
│
├── prompts/              # System prompt engineering
│   ├── builder.py        # PromptBuilder — composable prompt sections
│   ├── identity.py       # Who the agent is
│   ├── behavior.py       # How the agent behaves
│   ├── react.py          # ReAct reasoning instructions
│   ├── guardrails.py     # Safety rules and boundaries
│   └── user_data.py      # User data system instructions
│
├── tools/                # Tool system
│   ├── base.py           # Tool + ToolRegistry base classes
│   ├── registry.py       # Pre-built tool instances
│   ├── filesystem.py     # read_file, write_file, replace
│   ├── system.py         # run_command, get_weather
│   ├── web.py            # web_fetch
│   ├── python_repl.py    # Sandboxed Python execution
│   └── user_input.py     # collect_input (structured user data gathering)
│
├── skills/               # Skill system
│   ├── base.py           # Skill + SkillRegistry
│   ├── registry.py       # Pre-registered skill presets
│   ├── presets/           # Built-in skills (coding, research, ui_design, devops)
│   └── docs/             # Skill documentation (loaded by agent on demand)
│
├── memory/               # Conversation persistence
│   ├── base.py           # Abstract ConversationMemory
│   └── file_store.py     # JSON file-based implementation
│
├── adapters/             # I/O adapters
│   └── cli.py            # Terminal input/output
│
└── examples/             # Example applications
    ├── cli_app.py         # Full CLI agent app
    └── fast_api.py        # FastAPI server (WIP)
```

---

## Core Concepts

### 1. Agent

The `Agent` is your AI entity. It has a name, a configuration, and an optional set of skills.

```python
from flexygent.types import Agent, AgentConfig

# Basic agent
agent = Agent(name="helper", config=AgentConfig(model="gpt-4o-mini"))

# Agent with custom config
config = AgentConfig(
    model="deepseek-v4-flash",
    max_iterations=15,       # Max tool-call rounds (default: 10)
    temperature=0.5,         # LLM temperature (default: 0.7)
    verbose=False,           # Debug output (default: False)
    enable_rag=False,        # RAG support (default: False, coming in future release)
)
agent = Agent(name="researcher", config=config)
```

### 2. Conversation

The `Conversation` holds the full message history. It's a Pydantic model you can serialize, save, and restore.

```python
from flexygent.types import Conversation

conv = Conversation()

# The agent's system message sets up its personality
conv.add_message(agent.get_system_message())

# After running agent_loop, the conversation contains the full history
# including tool calls, tool responses, and assistant messages
```

### 3. Agent Loop

The `agent_loop` is the core reasoning engine. It implements the ReAct pattern:

```
User message → LLM → (Tool call → Tool result → LLM)* → Final response
```

The loop continues calling tools until the LLM decides to stop or hits `max_iterations`. If it reaches the limit, a warning is injected telling the LLM to give a final answer without more tool calls.

```python
from flexygent.agent import agent_loop

response = agent_loop(
    conversation,       # Conversation object (modified in place)
    "user's message",   # The user's input
    tools,              # List of tool schemas (OpenAI format)
    tool_registry,      # ToolRegistry instance (for executing tool calls)
    client,             # OpenAI-compatible client
    config              # AgentConfig
)
```

---

## Swapping LLM Providers

Flexygent works with **any OpenAI-compatible API**. Switching providers is just changing your `.env`:

### OpenAI

```env
LLM_API_KEY=sk-your-openai-key
LLM_BASE_URL=https://api.openai.com/v1
```
```python
config = AgentConfig(model="gpt-4o-mini")
```

### DeepSeek

```env
LLM_API_KEY=your-deepseek-key
LLM_BASE_URL=https://api.deepseek.com/v1
```
```python
config = AgentConfig(model="deepseek-v4-flash")
```

### OpenRouter (access to 100+ models)

```env
LLM_API_KEY=your-openrouter-key
LLM_BASE_URL=https://openrouter.ai/api/v1
```
```python
config = AgentConfig(model="anthropic/claude-opus-4.7")
# or
config = AgentConfig(model="google/gemini-2.5-pro")
# or
config = AgentConfig(model="meta-llama/llama-4-maverick")
```

### Local Models (Ollama)

```env
LLM_API_KEY=not-needed
LLM_BASE_URL=http://localhost:11434/v1
```
```python
config = AgentConfig(model="llama3.2")
```

### Local Models (LM Studio)

```env
LLM_API_KEY=lm-studio
LLM_BASE_URL=http://localhost:1234/v1
```
```python
config = AgentConfig(model="local-model")
```

**The key point:** You never change framework code to switch providers. Just update the env vars and the model name in `AgentConfig`.

---

## Tools

### Built-in Tools

| Tool | What It Does |
|------|-------------|
| `run_command` | Execute shell commands (with a safety blocklist) |
| `read_file` | Read file contents (with truncation) |
| `write_file` | Create or overwrite files |
| `replace` | Surgical string replacement in files |
| `web_fetch` | Fetch and clean web page content |
| `python_repl` | Run Python code in a sandboxed subprocess |
| `collect_input` | Gather structured data from the user |
| `get_weather` | Get weather for a location (placeholder) |

### Creating Custom Tools

```python
from flexygent.tools.base import Tool, ToolRegistry

# 1. Define the function
def calculate_bmi(params: dict):
    height = params.get("height")  # in meters
    weight = params.get("weight")  # in kg
    bmi = weight / (height ** 2)
    return f"BMI: {bmi:.1f}"

# 2. Wrap it as a Tool
bmi_tool = Tool(
    name="calculate_bmi",
    description="Calculate Body Mass Index from height (meters) and weight (kg)",
    parameter_allowed={
        "height": {
            "type": "number",
            "description": "Height in meters (e.g., 1.75)"
        },
        "weight": {
            "type": "number",
            "description": "Weight in kilograms (e.g., 70)"
        }
    },
    function=calculate_bmi,
)

# 3. Register it
from flexygent.tools import tool_registry
tool_registry.add_tool(bmi_tool)
```

That's it. The framework auto-generates the OpenAI-compatible JSON schema from your `parameter_allowed` dict. The agent will discover and use the tool when relevant.

### Using a Custom Tool Registry

If you don't want to modify the global registry, create your own:

```python
from flexygent.tools.base import Tool, ToolRegistry, get_tools

my_registry = ToolRegistry()
my_registry.add_tool(bmi_tool)
my_registry.add_tool(some_other_tool)

tools = get_tools(my_registry, allowed=None)

# Use my_registry instead of the default tool_registry in agent_loop
response = agent_loop(conv, message, tools, my_registry, client, config)
```

---

## Skills

Skills are **plug-in modules that transform what your agent is**. A skill can:

- **Inject identity** — Add expertise to the agent's persona (e.g., "You are also a world-class software engineer")
- **Filter tools** — Restrict which tools the agent can use (a research skill doesn't need `write_file`)
- **Override config** — Change temperature, max iterations, etc. (coding needs low temp, research needs higher)

### Built-in Skills

| Skill | Identity | Tools Unlocked | Config Overrides |
|-------|----------|---------------|------------------|
| `coding` | Software engineer — clean code, debugging | read_file, write_file, replace, python_repl, run_command, web_fetch, collect_input | temp: 0.3, max_iter: 20 |
| `research` | Research analyst — gather, synthesize, cite | web_fetch, read_file, python_repl | temp: 0.8, max_iter: 15 |
| `ui_design` | UI/UX designer — visual hierarchy, accessibility | read_file, write_file, replace, web_fetch, run_command | temp: 0.6 |
| `devops` | DevOps engineer — infrastructure, CI/CD, cloud | run_command, read_file, write_file, replace, web_fetch | temp: 0.3, max_iter: 25 |

### Applying Skills

```python
from flexygent.skills import skill_registry

agent = Agent(name="coder", config=config)

# Apply one skill
agent.apply_skill("coding", skill_registry)

# Or apply multiple
agent.apply_skills(["coding", "devops"], skill_registry)

# The agent's system prompt now includes coding + devops expertise
# Tool filtering now only allows tools that both skills use
# Config has been overridden (last skill wins for conflicts)
```

### Creating Custom Skills

```python
from flexygent.skills import Skill, SkillRegistry

# 1. Define the skill
data_science_skill = Skill(
    name="data_science",
    description="Data analysis, visualization, and machine learning",
    identity_intro=(
        "You are also an expert data scientist. "
        "You excel at exploratory data analysis, statistical modeling, "
        "and building ML pipelines. You use pandas, numpy, scikit-learn, "
        "and matplotlib fluently. You always start with understanding "
        "the data before jumping to models."
    ),
    doc_path="skills/docs/data_science.md",  # Optional detailed docs
    allowed_tools=["python_repl", "read_file", "write_file", "web_fetch"],
    config_overrides={
        "temperature": 0.4,
        "max_iterations": 20,
    },
)

# 2. Register it
from flexygent.skills import skill_registry
skill_registry.register(data_science_skill)

# 3. Use it
agent.apply_skill("data_science", skill_registry)
```

### How Skills Compose

When you apply multiple skills:

- **Identity**: Each skill's `identity_intro` is appended to the agent's identity section
- **Tools**: The agent can only use tools that appear in **any** active skill's `allowed_tools`. If any skill has `allowed_tools=None`, all tools are available
- **Config**: Each skill's `config_overrides` are applied in order. Last skill wins for conflicting keys
- **Docs**: Available skill docs are listed in the prompt so the agent can `read_file` them on demand

---

## Prompt System

The `PromptBuilder` lets you compose the system prompt from named, ordered sections.

### Default Sections (in order)

| Section | What It Contains |
|---------|-----------------|
| `identity` | Who the agent is ("You are Flex, an autonomous AI assistant") |
| `behavior` | How to behave (be direct, no filler, match user's tone) |
| `user_data` | Instructions for the user data system (profile, bio, memory, data logs) |
| `react` | ReAct reasoning pattern (Thought → Action → Observation → Final Answer) |
| `guardrails` | Safety rules (no prompt injection, no destructive ops) |

### Customizing the Prompt

```python
from flexygent.prompts.builder import PromptBuilder

builder = PromptBuilder()

# Modify the identity
builder.update("identity", "You are Atlas, a senior backend engineer who speaks concisely.")

# Add a new section
builder.add("domain_knowledge", """
## Domain Knowledge
You specialize in financial systems and trading platforms.
Always consider regulatory compliance in your suggestions.
""")

# Remove a section
builder.remove("guardrails")  # Not recommended, but you can

# Build the final prompt string
system_prompt = builder.build()

# Or use it with an Agent
agent = Agent(name="atlas")
agent.builder = builder
system_message = agent.get_system_message()  # Message(role=SYSTEM, content=built_prompt)
```

### Using Custom Builders with Agents

```python
agent = Agent(name="custom_agent", config=config)

# The agent has its own PromptBuilder you can modify directly
agent.builder.update("identity", "You are Nova, a creative writing assistant.")
agent.builder.add("style_guide", """
## Writing Style
- Use vivid, sensory language
- Prefer active voice
- Keep paragraphs under 4 sentences
""")
```

---

## I/O Adapters

The `UserIO` interface abstracts how the agent communicates with users. This makes the same agent work across different platforms.

### The Interface

```python
from abc import ABC, abstractmethod

class UserIO(ABC):
    @abstractmethod
    def get_input(self, prompt: str = "") -> str:
        ...

    @abstractmethod
    def show_output(self, message: str):
        ...
```

### Built-in: CLI Adapter

```python
from flexygent.adapters.cli import CliUserIO

io = CliUserIO()
message = io.get_input("You: ")    # Uses input()
io.show_output("Hello!")            # Uses print()
```

### Creating Your Own Adapter

To run your agent on any platform, implement `UserIO`:

```python
from flexygent.interfaces import UserIO

# Example: A simple logging adapter
class LoggingUserIO(UserIO):
    def __init__(self):
        self.log = []

    def get_input(self, prompt: str = ""):
        user_msg = input(prompt)
        self.log.append({"role": "user", "content": user_msg})
        return user_msg

    def show_output(self, message: str):
        self.log.append({"role": "assistant", "content": message})
        print(f"🤖 {message}")
```

```python
# Example: FastAPI adapter (request/response based)
class FastApiUserIO(UserIO):
    def __init__(self):
        self.pending_input = None
        self.last_output = None

    def get_input(self, prompt: str = ""):
        # In a web context, input comes from the HTTP request
        return self.pending_input

    def show_output(self, message: str):
        # In a web context, output goes to the HTTP response
        self.last_output = message
```

The adapter pattern means your agent code never changes — only the I/O layer does.

---

## Conversation Memory

Save and restore conversations so users can pick up where they left off.

### Using FileStore

```python
from flexygent.memory.file_store import FileStore

memory = FileStore(base_dir="conversations")  # Default directory

# Save a conversation
file_name = memory.gen_file_name()  # "conversation-2025-07-05_14-30-00.json"
memory.save(conv, file_name)

# List saved conversations
saved = memory.list_saved()  # ["conversation-2025-07-05_14-30-00.json", ...]

# Load a conversation
conv = memory.load(saved[0])

# Check if a conversation exists
memory.exists("conversation-2025-07-05_14-30-00.json")

# Delete a conversation
memory.delete("conversation-2025-07-05_14-30-00.json")
```

### Custom Memory Backend

Implement `ConversationMemory` for your own storage:

```python
from flexygent.memory.base import ConversationMemory
from flexygent.types import Conversation

class RedisMemory(ConversationMemory):
    def __init__(self, redis_client):
        self.redis = redis_client

    def save(self, conversation: Conversation, name: str):
        self.redis.set(name, conversation.model_dump_json())

    def load(self, name: str) -> Conversation:
        data = self.redis.get(name)
        return Conversation.model_validate_json(data)

    def list_saved(self) -> list[str]:
        return self.redis.keys("conversation-*")

    def delete(self, name: str):
        self.redis.delete(name)

    def exists(self, name: str) -> bool:
        return self.redis.exists(name)
```

---

## User Data System

The agent has a built-in system for remembering who the user is, their preferences, and their ongoing activities.

### Data Types

| Type | File | Loaded | Purpose |
|------|------|--------|---------|
| **Profile** | `~/.flexygent/user/profile.md` | Always (every request) | Quick identity snapshot — name, age, location, occupation |
| **Bio** | `~/.flexygent/user/bio.md` | On demand | Detailed life narrative — journey, goals, deeper context |
| **Memory** | `~/.flexygent/user/memory.json` | Always (summary) | LLM-inferred traits, patterns, preferences. Auto-updated after conversations |
| **Data Logs** | `~/.flexygent/user/data/**/*.json` | On demand | Structured logs — DSA progress, projects, skills, reading lists, etc. |

### How It Works

The agent knows about these files through the `user_data` prompt section. It will:

1. **First conversation**: Offer to build a profile using `collect_input`
2. **Every conversation**: Automatically reference profile and memory data
3. **On-topic queries**: Proactively fetch relevant data logs (e.g., ask about DSA → reads `data/dsa/progress.json`)
4. **Post-conversation**: The memory system updates `memory.json` with observed patterns

You don't need to code anything — the prompt engineering handles it. The agent uses its existing `read_file` and `write_file` tools to manage the data.

---

## Full Example: Building a Personal Assistant

Here's a complete, production-ready CLI assistant:

```python
"""my_assistant.py — A personal AI assistant built with Flexygent"""

from flexygent.types import Conversation, AgentConfig, Agent
from flexygent.tools import tool_registry, get_tools
from flexygent.tools.base import Tool
from flexygent.skills import skill_registry, Skill
from flexygent.client import client
from flexygent.agent import agent_loop
from flexygent.adapters.cli import CliUserIO
from flexygent.memory.file_store import FileStore


# --- Custom Tool ---
def search_notes(params: dict):
    """Search personal notes directory."""
    import glob
    query = params.get("query", "").lower()
    results = []
    for f in glob.glob("notes/**/*.md", recursive=True):
        with open(f) as fh:
            content = fh.read()
        if query in content.lower():
            results.append(f"{f}: ...{content[content.lower().index(query)-50:content.lower().index(query)+100]}...")
    return "\n".join(results) if results else "No notes found matching query."

tool_registry.add_tool(Tool(
    name="search_notes",
    description="Search through personal notes for a keyword or topic",
    parameter_allowed={
        "query": {"type": "string", "description": "Search term to find in notes"}
    },
    function=search_notes,
))


# --- Custom Skill ---
skill_registry.register(Skill(
    name="personal_assistant",
    description="Personal productivity and life management",
    identity_intro=(
        "You are also a proactive personal assistant. "
        "You help manage tasks, track goals, organize information, "
        "and provide thoughtful suggestions. You remember context "
        "from previous conversations and connect dots across topics."
    ),
    doc_path="skills/docs/assistant.md",
    allowed_tools=None,  # None = can use ALL tools
    config_overrides={"temperature": 0.5},
))


# --- Main App ---
def main():
    io = CliUserIO()
    config = AgentConfig(model="gpt-4o-mini", max_iterations=15)

    # Create agent with multiple skills
    agent = Agent(name="jarvis", config=config)
    agent.apply_skills(["coding", "research", "personal_assistant"], skill_registry)

    # Customize the identity
    agent.builder.update("identity", "You are Jarvis, a personal AI assistant.")

    # Setup
    conv = Conversation()
    conv.add_message(agent.get_system_message())
    tools = get_tools(tool_registry, agent.get_tool_filter(skill_registry))
    memory = FileStore()

    # Resume last conversation if available
    saved = memory.list_saved()
    if saved:
        io.show_output(f"Found {len(saved)} saved conversation(s). Loading most recent...")
        conv = memory.load(saved[0])

    # Chat loop
    io.show_output("Jarvis ready. Type 'exit' to quit.\n")
    try:
        while True:
            user_input = io.get_input("You: ")
            if user_input.strip().lower() == "exit":
                break

            response = agent_loop(conv, user_input, tools, tool_registry, client, config)
            io.show_output(f"\nJarvis: {response}\n")

    except KeyboardInterrupt:
        io.show_output("\nShutting down...")
    finally:
        memory.save(conv, memory.gen_file_name())
        io.show_output("Conversation saved.")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python my_assistant.py
```

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| **OpenAI client library** | It's the de facto standard. Every provider supports it. Zero lock-in. |
| **Pydantic everywhere** | Type safety, serialization, and validation for free. Models are the data layer. |
| **Functions over classes for tools** | Tools are just functions with metadata. No inheritance ceremony needed. |
| **Skills are data, not code** | A skill is a Pydantic model with strings and lists. No subclassing. Easy to create and share. |
| **Prompt sections are ordered** | The order of system prompt sections matters for LLM attention. `PromptBuilder` preserves insertion order. |
| **I/O is an interface, not a base class** | `UserIO` has exactly 2 methods. Implementing it for any platform takes 5 minutes. |
| **Local-first storage** | JSON files on disk. No database required. Works offline. Easy to inspect and debug. |

---

## What's Coming

See [docs/RELEASE_PLAN.md](docs/RELEASE_PLAN.md) for the full roadmap. Highlights:

- **v0.2.0** — FastAPI example + server deployment
- **v0.3.0** — Agent task system (short + long-running autonomous tasks)
- **v0.4.0** — User task management (to-dos, roadmaps, progress tracking)
- **v0.5.0** — RAG system (ChromaDB integration)
- **v0.6.0** — User data as MCP server (universal personal context)
- **v0.7.0** — Database backends (SQLite, PostgreSQL)
- **v0.8.0** — Platform adapters (Blender, Discord, Telegram) + example apps

---

## License

MIT
