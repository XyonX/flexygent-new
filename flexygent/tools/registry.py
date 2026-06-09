from flexygent.tools.base import Tool,ToolRegistry
from flexygent.tools.filesystem import read_file,write_file,replace
from flexygent.tools.system import run_command,get_weather
from flexygent.tools.web import web_fetch
from flexygent.tools.python_repl import python_repl


tool_run_command = Tool(
    name="run_command",
    description="Execute shell command",
    parameter_allowed={
        "command": {
            "type": "string",
            "description": "Shell command to execute (e.g., 'ls', 'pwd')."
        }
    },
    function=run_command,
)

tool_get_weather = Tool(
    name="get_weather",
    description="Get the current weather for a location",
    parameter_allowed={
        "location": {
            "type": "string",
            "description": "The city or location to get weather for (e.g., 'London', 'New York')."
        }
    },
    function=get_weather,
)


tool_read_file = Tool(
    name="read_file",
    description="Read the contents of a file at a given path. Returns the text content, truncated to output_length characters.",
    parameter_allowed={
        "file_name": {
            "type": "string",
            "description": "Path to the file to read (e.g., 'main.py', 'flexygent/agent.py')"
        },
        "output_length": {
            "type": "integer",
            "description": "Max characters to return. Defaults to 8000."
        }
    },
    function=read_file,
)

tool_write_file = Tool(
    name="write_file",
    description="Create a new file or overwrite an existing file with the given content. Use for creating new files only — use replace for editing existing files.",
    parameter_allowed={
        "file_name": {
            "type": "string",
            "description": "Path to the file to write (e.g., 'output.txt', 'scripts/run.py')"
        },
        "content": {
            "type": "string",
            "description": "The full text content to write into the file"
        }
    },
    function=write_file,
)

tool_replace = Tool(
    name="replace",
    description="Edit an existing file by replacing a specific string with a new string. Always read_file first to get the exact current content before using this.",
    parameter_allowed={
        "file_name": {
            "type": "string",
            "description": "Path to the file to edit"
        },
        "old_string": {
            "type": "string",
            "description": "The exact string to find and replace. Must be unique in the file."
        },
        "new_string": {
            "type": "string",
            "description": "The string to replace it with"
        }
    },
    function=replace,
)


tool_web_fetch = Tool(
    name="web_fetch",
    description="Fetch and read content from a URL. Strips HTML tags and returns clean readable text. Use this to read documentation, articles, or any web page. Always provide the full URL including https://",
    parameter_allowed={
        "url": {
            "type": "string",
            "description": "The full URL to fetch (e.g., 'https://docs.python.org/3/library/json.html')"
        }
    },
    function=web_fetch,
)

tool_python_repl = Tool(
    name="python_repl",
    description="Execute Python code in an isolated subprocess and return the output. Use this for calculations, data processing, testing logic, or anything that needs actual code execution rather than guessing. Always use print() to output results — return values alone won't show. Do not use for file operations, use read_file/write_file instead.",
    parameter_allowed={
        "code": {
            "type": "string",
            "description": "Valid Python code to execute. Use print() for any output you want returned. Example: 'print(2 ** 100)'"
        }
    },
    function=python_repl,
)

tool_registry = ToolRegistry()

tool_registry.add_tool(tool_run_command)
tool_registry.add_tool(tool_get_weather)
tool_registry.add_tool(tool_read_file)
tool_registry.add_tool(tool_write_file)
tool_registry.add_tool(tool_replace)
tool_registry.add_tool(tool_web_fetch)
tool_registry.add_tool(tool_python_repl)
