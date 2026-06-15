"""Tests for flexygent.tools.base — Tool, ToolRegistry, get_tools."""

import pytest
from flexygent.tools.base import Tool, ToolRegistry, get_tools


# ── helpers ──────────────────────────────────────────────────────────────────

def _echo_tool():
    """A simple tool that echoes back its input."""
    return Tool(
        name="echo",
        description="Echo the input back",
        parameter_allowed={
            "text": {"type": "string", "description": "Text to echo"},
        },
        function=lambda params: params.get("text", ""),
    )


def _add_tool():
    """A simple tool that adds two numbers."""
    return Tool(
        name="add",
        description="Add two numbers",
        parameter_allowed={
            "a": {"type": "integer", "description": "First number"},
            "b": {"type": "integer", "description": "Second number"},
        },
        function=lambda params: str(params.get("a", 0) + params.get("b", 0)),
    )


# ── Tool ─────────────────────────────────────────────────────────────────────

class TestTool:
    def test_tool_creation(self):
        t = _echo_tool()
        assert t.name == "echo"
        assert t.description == "Echo the input back"

    def test_to_openai_tool_structure(self):
        t = _echo_tool()
        schema = t.to_openai_tool()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "echo"
        assert schema["function"]["description"] == "Echo the input back"
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "text" in params["properties"]
        assert "text" in params["required"]

    def test_to_openai_tool_multiple_params(self):
        t = _add_tool()
        schema = t.to_openai_tool()
        props = schema["function"]["parameters"]["properties"]
        assert "a" in props
        assert "b" in props
        required = schema["function"]["parameters"]["required"]
        assert "a" in required
        assert "b" in required

    def test_call_basic(self):
        t = _echo_tool()
        result = t.call({"text": "hello"})
        assert result == "hello"

    def test_call_filters_extra_params(self):
        t = _echo_tool()
        result = t.call({"text": "hello", "extra": "should be ignored"})
        assert result == "hello"

    def test_call_missing_param(self):
        t = _echo_tool()
        result = t.call({})
        assert result == ""

    def test_call_add_tool(self):
        t = _add_tool()
        result = t.call({"a": 3, "b": 7})
        assert result == "10"


# ── ToolRegistry ─────────────────────────────────────────────────────────────

class TestToolRegistry:
    def test_add_and_call(self):
        reg = ToolRegistry()
        reg.add_tool(_echo_tool())
        result = reg.call("echo", {"text": "hi"})
        assert result == "hi"

    def test_add_multiple_tools(self):
        reg = ToolRegistry()
        reg.add_tool(_echo_tool())
        reg.add_tool(_add_tool())
        assert len(reg.tools) == 2

    def test_call_nonexistent_tool_raises(self):
        reg = ToolRegistry()
        with pytest.raises(KeyError):
            reg.call("nonexistent", {})

    def test_overwrite_tool(self):
        reg = ToolRegistry()
        reg.add_tool(_echo_tool())
        new_echo = Tool(
            name="echo",
            description="New echo",
            parameter_allowed={"text": {"type": "string", "description": "t"}},
            function=lambda params: "new_" + params.get("text", ""),
        )
        reg.add_tool(new_echo)
        assert reg.call("echo", {"text": "x"}) == "new_x"


# ── get_tools ────────────────────────────────────────────────────────────────

class TestGetTools:
    def _make_registry(self):
        reg = ToolRegistry()
        reg.add_tool(_echo_tool())
        reg.add_tool(_add_tool())
        return reg

    def test_get_all_tools_when_allowed_is_none(self):
        reg = self._make_registry()
        tools = get_tools(reg, allowed=None)
        assert len(tools) == 2
        names = {t["function"]["name"] for t in tools}
        assert names == {"echo", "add"}

    def test_get_filtered_tools(self):
        reg = self._make_registry()
        tools = get_tools(reg, allowed=["echo"])
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "echo"

    def test_get_tools_empty_allowed(self):
        reg = self._make_registry()
        tools = get_tools(reg, allowed=[])
        assert tools == []

    def test_get_tools_nonexistent_in_allowed_is_skipped(self):
        reg = self._make_registry()
        tools = get_tools(reg, allowed=["echo", "nonexistent"])
        assert len(tools) == 1

    def test_get_tools_returns_valid_openai_schema(self):
        reg = self._make_registry()
        tools = get_tools(reg, allowed=None)
        for t in tools:
            assert t["type"] == "function"
            assert "name" in t["function"]
            assert "parameters" in t["function"]
