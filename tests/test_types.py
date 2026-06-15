"""Tests for flexygent.types — Role, Message, Conversation, AgentConfig, Agent."""

import pytest
from flexygent.types import Role, Message, Conversation, AgentConfig, Agent
from flexygent.prompts.builder import PromptBuilder


# ── Role ─────────────────────────────────────────────────────────────────────

class TestRole:
    def test_role_values(self):
        assert Role.SYSTEM == "system"
        assert Role.USER == "user"
        assert Role.ASSISTANT == "assistant"
        assert Role.TOOL == "tool"

    def test_role_is_str_enum(self):
        assert isinstance(Role.SYSTEM, str)


# ── Message ──────────────────────────────────────────────────────────────────

class TestMessage:
    def test_basic_message(self):
        m = Message(role=Role.USER, content="hello")
        assert m.role == Role.USER
        assert m.content == "hello"

    def test_content_defaults_to_none(self):
        m = Message(role=Role.ASSISTANT)
        assert m.content is None

    def test_tool_calls_defaults_to_empty_list(self):
        m = Message(role=Role.ASSISTANT, content="hi")
        assert m.tool_calls == []

    def test_tool_call_id_defaults_to_empty_string(self):
        m = Message(role=Role.TOOL, content="result")
        assert m.tool_call_id == ""

    def test_to_dict_basic(self):
        m = Message(role=Role.USER, content="hello")
        d = m.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "hello"
        assert "tool_calls" not in d
        assert "tool_call_id" not in d

    def test_to_dict_with_tool_calls(self):
        fake_calls = [{"id": "tc_1", "function": {"name": "f", "arguments": "{}"}}]
        m = Message(role=Role.ASSISTANT, content=None, tool_calls=fake_calls)
        d = m.to_dict()
        assert d["tool_calls"] == fake_calls
        # content should be empty string when None
        assert d["content"] == ""

    def test_to_dict_with_tool_call_id(self):
        m = Message(role=Role.TOOL, content="result", tool_call_id="tc_1")
        d = m.to_dict()
        assert d["tool_call_id"] == "tc_1"

    def test_to_dict_no_tool_call_id_when_empty(self):
        m = Message(role=Role.USER, content="hi")
        d = m.to_dict()
        assert "tool_call_id" not in d


# ── Conversation ─────────────────────────────────────────────────────────────

class TestConversation:
    def test_empty_conversation(self):
        c = Conversation()
        assert c.messages == []
        assert c.to_dict() == []

    def test_add_message(self):
        c = Conversation()
        m = Message(role=Role.SYSTEM, content="you are helpful")
        c.add_message(m)
        assert len(c.messages) == 1
        assert c.messages[0].role == Role.SYSTEM

    def test_add_user_message(self):
        c = Conversation()
        c.add_user_message("hello")
        assert len(c.messages) == 1
        assert c.messages[0].role == Role.USER
        assert c.messages[0].content == "hello"

    def test_add_assistant_message_text_only(self):
        c = Conversation()
        c.add_assistant_message(content="hi there")
        assert c.messages[0].role == Role.ASSISTANT
        assert c.messages[0].content == "hi there"
        assert c.messages[0].tool_calls is None

    def test_add_assistant_message_with_tool_calls(self):
        c = Conversation()
        calls = [{"id": "tc_1"}]
        c.add_assistant_message(content=None, tool_calls=calls)
        assert c.messages[0].tool_calls == calls

    def test_add_tool_response(self):
        c = Conversation()
        c.add_tool_response(tool_call_id="tc_1", content="done")
        assert c.messages[0].role == Role.TOOL
        assert c.messages[0].tool_call_id == "tc_1"
        assert c.messages[0].content == "done"

    def test_to_dict_multi_message(self):
        c = Conversation()
        c.add_user_message("hi")
        c.add_assistant_message("hello")
        result = c.to_dict()
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_conversation_preserves_order(self):
        c = Conversation()
        c.add_user_message("1")
        c.add_assistant_message("2")
        c.add_user_message("3")
        contents = [m.content for m in c.messages]
        assert contents == ["1", "2", "3"]

    def test_serialization_roundtrip(self):
        """Conversation can be dumped and reloaded via pydantic."""
        c = Conversation()
        c.add_user_message("hello")
        c.add_assistant_message("hi")
        dump = c.model_dump()
        restored = Conversation.model_validate(dump)
        assert len(restored.messages) == 2
        assert restored.messages[0].content == "hello"
        assert restored.messages[1].content == "hi"


# ── AgentConfig ──────────────────────────────────────────────────────────────

class TestAgentConfig:
    def test_defaults(self):
        cfg = AgentConfig()
        assert cfg.max_iterations == 10
        assert cfg.verbose is False
        assert cfg.temperature == 0.7
        assert cfg.enable_rag is False

    def test_custom_values(self):
        cfg = AgentConfig(max_iterations=5, model="gpt-4", temperature=0.2, verbose=True, enable_rag=True)
        assert cfg.max_iterations == 5
        assert cfg.model == "gpt-4"
        assert cfg.temperature == 0.2
        assert cfg.verbose is True
        assert cfg.enable_rag is True


# ── Agent ────────────────────────────────────────────────────────────────────

class TestAgent:
    def test_agent_creation(self):
        a = Agent(name="test_agent")
        assert a.name == "test_agent"
        assert isinstance(a.builder, PromptBuilder)
        assert isinstance(a.config, AgentConfig)
        assert a.active_skills == []

    def test_get_system_message(self):
        a = Agent(name="test")
        msg = a.get_system_message()
        assert msg.role == Role.SYSTEM
        assert isinstance(msg.content, str)
        assert len(msg.content) > 0

    def test_get_system_message_contains_prompt_sections(self):
        a = Agent(name="test")
        msg = a.get_system_message()
        # should contain identity and behavior sections at minimum
        assert "Flex" in msg.content or "flex" in msg.content.lower()

    def test_get_tool_filter_no_skills(self):
        """With no active skills, tool filter returns None (all tools allowed)."""
        from flexygent.skills.base import SkillRegistry
        a = Agent(name="test")
        sr = SkillRegistry()
        assert a.get_tool_filter(sr) is None
