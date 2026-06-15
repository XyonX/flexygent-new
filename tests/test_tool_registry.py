"""Tests for the global tool registry — flexygent.tools.registry."""

import pytest
from flexygent.tools.registry import tool_registry
from flexygent.tools.base import ToolRegistry


class TestGlobalToolRegistry:
    def test_is_tool_registry_instance(self):
        assert isinstance(tool_registry, ToolRegistry)

    def test_has_run_command(self):
        assert "run_command" in tool_registry.tools

    def test_has_get_weather(self):
        assert "get_weather" in tool_registry.tools

    def test_has_read_file(self):
        assert "read_file" in tool_registry.tools

    def test_has_write_file(self):
        assert "write_file" in tool_registry.tools

    def test_has_replace(self):
        assert "replace" in tool_registry.tools

    def test_has_web_fetch(self):
        assert "web_fetch" in tool_registry.tools

    def test_has_python_repl(self):
        assert "python_repl" in tool_registry.tools

    def test_has_collect_input(self):
        assert "collect_input" in tool_registry.tools

    def test_total_tool_count(self):
        assert len(tool_registry.tools) == 8

    def test_all_tools_produce_valid_openai_schema(self):
        for name, tool in tool_registry.tools.items():
            schema = tool.to_openai_tool()
            assert schema["type"] == "function", f"{name} schema missing 'type'"
            assert "name" in schema["function"], f"{name} schema missing 'name'"
            assert "description" in schema["function"], f"{name} schema missing 'description'"
            assert "parameters" in schema["function"], f"{name} schema missing 'parameters'"

    def test_all_tools_have_descriptions(self):
        for name, tool in tool_registry.tools.items():
            assert len(tool.description) > 0, f"Tool '{name}' has empty description"

    def test_all_tools_have_functions(self):
        for name, tool in tool_registry.tools.items():
            assert callable(tool.function), f"Tool '{name}' function is not callable"
