"""Tests for flexygent.agent — the agent_loop function."""

import json
import pytest
from unittest.mock import MagicMock, patch
from flexygent.types import Conversation, Message, Role, AgentConfig
from flexygent.tools.base import Tool, ToolRegistry
from flexygent.agent import agent_loop


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_mock_response(content, finish_reason="stop", tool_calls=None):
    """Create a mock OpenAI chat completion response."""
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = finish_reason

    response = MagicMock()
    response.choices = [choice]
    return response


def _make_tool_call(call_id, name, arguments):
    """Create a mock tool call object."""
    tc = MagicMock()
    tc.id = call_id
    tc.function.name = name
    tc.function.arguments = json.dumps(arguments)
    return tc


def _make_echo_registry():
    """Create a registry with a simple echo tool."""
    registry = ToolRegistry()
    echo_tool = Tool(
        name="echo",
        description="Echo input",
        parameter_allowed={"text": {"type": "string", "description": "text"}},
        function=lambda params: f"echoed: {params.get('text', '')}",
    )
    registry.add_tool(echo_tool)
    return registry


# ── agent_loop tests ─────────────────────────────────────────────────────────

class TestAgentLoop:
    def test_simple_text_response(self):
        """LLM responds with finish_reason='stop', no tool calls."""
        conv = Conversation()
        conv.add_message(Message(role=Role.SYSTEM, content="You are helpful."))

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            content="Hello! How can I help?",
            finish_reason="stop",
        )

        config = AgentConfig(max_iterations=5)
        registry = ToolRegistry()

        result = agent_loop(conv, "hi", [], registry, mock_client, config)

        assert result == "Hello! How can I help?"
        mock_client.chat.completions.create.assert_called_once()

    def test_user_message_added_to_conversation(self):
        conv = Conversation()
        conv.add_message(Message(role=Role.SYSTEM, content="system"))

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response("ok")

        config = AgentConfig()
        registry = ToolRegistry()

        agent_loop(conv, "user input here", [], registry, mock_client, config)

        # the user message should be in the conversation
        user_msgs = [m for m in conv.messages if m.role == Role.USER]
        assert len(user_msgs) == 1
        assert user_msgs[0].content == "user input here"

    def test_assistant_response_added_to_conversation(self):
        conv = Conversation()
        conv.add_message(Message(role=Role.SYSTEM, content="system"))

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response("final answer")

        config = AgentConfig()
        registry = ToolRegistry()

        agent_loop(conv, "question", [], registry, mock_client, config)

        assistant_msgs = [m for m in conv.messages if m.role == Role.ASSISTANT]
        assert len(assistant_msgs) == 1
        assert assistant_msgs[0].content == "final answer"

    def test_single_tool_call_cycle(self):
        """LLM calls a tool once, then responds with stop."""
        conv = Conversation()
        conv.add_message(Message(role=Role.SYSTEM, content="system"))

        tc = _make_tool_call("tc_1", "echo", {"text": "hello"})
        tool_response = _make_mock_response(
            content=None,
            finish_reason="tool_calls",
            tool_calls=[tc],
        )
        final_response = _make_mock_response("Echoed result: hello", finish_reason="stop")

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [tool_response, final_response]

        config = AgentConfig(max_iterations=5)
        registry = _make_echo_registry()

        result = agent_loop(conv, "echo hello", [], registry, mock_client, config)

        assert result == "Echoed result: hello"
        assert mock_client.chat.completions.create.call_count == 2

        # verify tool response was added
        tool_msgs = [m for m in conv.messages if m.role == Role.TOOL]
        assert len(tool_msgs) == 1
        assert "echoed: hello" in tool_msgs[0].content

    def test_multiple_tool_calls_in_sequence(self):
        """LLM calls a tool twice before responding."""
        conv = Conversation()
        conv.add_message(Message(role=Role.SYSTEM, content="system"))

        tc1 = _make_tool_call("tc_1", "echo", {"text": "a"})
        tc2 = _make_tool_call("tc_2", "echo", {"text": "b"})
        resp1 = _make_mock_response(None, "tool_calls", [tc1])
        resp2 = _make_mock_response(None, "tool_calls", [tc2])
        final = _make_mock_response("done", "stop")

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [resp1, resp2, final]

        config = AgentConfig(max_iterations=5)
        registry = _make_echo_registry()

        result = agent_loop(conv, "do two things", [], registry, mock_client, config)

        assert result == "done"
        assert mock_client.chat.completions.create.call_count == 3

    def test_max_iterations_forces_stop(self):
        """When max_iterations is hit, a warning is injected and loop ends."""
        conv = Conversation()
        conv.add_message(Message(role=Role.SYSTEM, content="system"))

        tc = _make_tool_call("tc_1", "echo", {"text": "x"})
        tool_resp = _make_mock_response(None, "tool_calls", [tc])
        # on the warning round, LLM finally stops
        final = _make_mock_response("forced stop", "stop")

        mock_client = MagicMock()
        # max_iterations=1 → one tool round then forced stop
        mock_client.chat.completions.create.side_effect = [tool_resp, final]

        config = AgentConfig(max_iterations=1)
        registry = _make_echo_registry()

        result = agent_loop(conv, "keep going", [], registry, mock_client, config)

        assert result == "forced stop"

        # verify the warning was injected (check the messages_payload passed to create)
        second_call_args = mock_client.chat.completions.create.call_args_list[1]
        messages_payload = second_call_args[1]["messages"] if "messages" in second_call_args[1] else second_call_args[0][0]
        # the last message in payload should be the system warning
        has_warning = any(
            "maximum tool call limit" in str(m.get("content", ""))
            for m in messages_payload
            if isinstance(m, dict)
        )
        assert has_warning

    def test_tool_error_is_captured(self):
        """If a tool raises an exception, the error is passed as tool response."""
        conv = Conversation()
        conv.add_message(Message(role=Role.SYSTEM, content="system"))

        tc = _make_tool_call("tc_1", "failing_tool", {"x": 1})
        tool_resp = _make_mock_response(None, "tool_calls", [tc])
        final = _make_mock_response("handled error", "stop")

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [tool_resp, final]

        registry = ToolRegistry()
        registry.add_tool(Tool(
            name="failing_tool",
            description="Always fails",
            parameter_allowed={"x": {"type": "integer", "description": "x"}},
            function=lambda params: (_ for _ in ()).throw(ValueError("boom")),
        ))

        config = AgentConfig(max_iterations=5)
        result = agent_loop(conv, "use failing tool", [], registry, mock_client, config)

        assert result == "handled error"
        tool_msgs = [m for m in conv.messages if m.role == Role.TOOL]
        assert len(tool_msgs) == 1
        assert "Tool error" in tool_msgs[0].content

    def test_parallel_tool_calls(self):
        """LLM returns multiple tool calls in a single response."""
        conv = Conversation()
        conv.add_message(Message(role=Role.SYSTEM, content="system"))

        tc1 = _make_tool_call("tc_1", "echo", {"text": "first"})
        tc2 = _make_tool_call("tc_2", "echo", {"text": "second"})
        tool_resp = _make_mock_response(None, "tool_calls", [tc1, tc2])
        final = _make_mock_response("both done", "stop")

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [tool_resp, final]

        config = AgentConfig(max_iterations=5)
        registry = _make_echo_registry()

        result = agent_loop(conv, "do two things", [], registry, mock_client, config)

        assert result == "both done"
        tool_msgs = [m for m in conv.messages if m.role == Role.TOOL]
        assert len(tool_msgs) == 2
