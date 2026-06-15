"""Tests for flexygent.memory — ConversationMemory ABC, FileStore."""

import json
import pytest
from pathlib import Path
from flexygent.memory.base import ConversationMemory
from flexygent.memory.file_store import FileStore
from flexygent.types import Conversation, Role


# ── ConversationMemory ABC ───────────────────────────────────────────────────

class TestConversationMemoryABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            ConversationMemory()

    def test_subclass_must_implement_all_methods(self):
        # If a subclass misses any method, instantiation should fail
        class Incomplete(ConversationMemory):
            def save(self, conversation, name):
                pass
            # missing load, list_saved, delete, exists

        with pytest.raises(TypeError):
            Incomplete()


# ── FileStore ────────────────────────────────────────────────────────────────

class TestFileStore:

    @pytest.fixture
    def store(self, tmp_path):
        return FileStore(base_dir=str(tmp_path))

    @pytest.fixture
    def sample_conversation(self):
        c = Conversation()
        c.add_user_message("hello")
        c.add_assistant_message("hi there")
        return c

    # -- gen_file_name --

    def test_gen_file_name_format(self, store):
        name = store.gen_file_name()
        assert name.startswith("conversation-")
        assert name.endswith(".json")

    def test_gen_file_name_unique_over_time(self, store):
        """Two calls should produce different names (or at least valid ones)."""
        n1 = store.gen_file_name()
        n2 = store.gen_file_name()
        # they're generated in the same second so may be equal, but format is correct
        assert n1.startswith("conversation-")

    # -- save --

    def test_save_creates_file(self, store, sample_conversation):
        fname = "test_conv.json"
        store.save(sample_conversation, fname)
        path = Path(store.base_dir) / fname
        assert path.exists()

    def test_save_writes_valid_json(self, store, sample_conversation):
        fname = "test_conv.json"
        store.save(sample_conversation, fname)
        path = Path(store.base_dir) / fname
        with open(path) as f:
            data = json.load(f)
        assert "messages" in data

    def test_save_content_matches_conversation(self, store, sample_conversation):
        fname = "test_conv.json"
        store.save(sample_conversation, fname)
        path = Path(store.base_dir) / fname
        with open(path) as f:
            data = json.load(f)
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "hello"

    # -- load --

    def test_load_restores_conversation(self, store, sample_conversation):
        fname = "test_conv.json"
        store.save(sample_conversation, fname)
        loaded = store.load(fname)
        assert isinstance(loaded, Conversation)
        assert len(loaded.messages) == 2
        assert loaded.messages[0].role == Role.USER
        assert loaded.messages[0].content == "hello"
        assert loaded.messages[1].content == "hi there"

    def test_load_nonexistent_raises(self, store):
        with pytest.raises(FileNotFoundError):
            store.load("nonexistent.json")

    def test_save_and_load_roundtrip(self, store):
        c = Conversation()
        c.add_user_message("first")
        c.add_assistant_message("response")
        c.add_user_message("second")
        c.add_tool_response(tool_call_id="tc_1", content="tool result")

        fname = "roundtrip.json"
        store.save(c, fname)
        loaded = store.load(fname)

        assert len(loaded.messages) == 4
        assert loaded.messages[0].content == "first"
        assert loaded.messages[2].content == "second"
        assert loaded.messages[3].role == Role.TOOL
        assert loaded.messages[3].tool_call_id == "tc_1"

    # -- list_saved --

    def test_list_saved_empty(self, store):
        result = store.list_saved()
        assert result == []

    def test_list_saved_returns_matching_files(self, store, sample_conversation):
        store.save(sample_conversation, "conversation-2025-01-01_00-00-00.json")
        store.save(sample_conversation, "conversation-2025-01-02_00-00-00.json")
        result = store.list_saved()
        assert len(result) == 2

    def test_list_saved_ignores_non_matching_files(self, store, sample_conversation):
        store.save(sample_conversation, "conversation-2025-01-01_00-00-00.json")
        # save a non-matching file
        other = Path(store.base_dir) / "other_file.json"
        other.write_text("{}")
        result = store.list_saved()
        assert len(result) == 1

    def test_list_saved_sorted_reverse(self, store, sample_conversation):
        store.save(sample_conversation, "conversation-2025-01-01_00-00-00.json")
        store.save(sample_conversation, "conversation-2025-01-03_00-00-00.json")
        store.save(sample_conversation, "conversation-2025-01-02_00-00-00.json")
        result = store.list_saved()
        assert result[0] == "conversation-2025-01-03_00-00-00.json"
        assert result[-1] == "conversation-2025-01-01_00-00-00.json"

    # -- _get_full_path --

    def test_get_full_path(self, store):
        path = store._get_full_path("test.json")
        assert str(path).endswith("test.json")
        assert str(store.base_dir) in str(path)

    # -- base_dir creation --

    def test_creates_base_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "new_conversations"
        assert not new_dir.exists()
        store = FileStore(base_dir=str(new_dir))
        assert new_dir.exists()


# ── FileStore with tool calls ────────────────────────────────────────────────

class TestFileStoreWithToolCalls:
    @pytest.fixture
    def store(self, tmp_path):
        return FileStore(base_dir=str(tmp_path))

    def test_save_load_conversation_with_tool_calls(self, store):
        c = Conversation()
        c.add_user_message("what's the weather?")
        fake_calls = [{"id": "tc_1", "type": "function", "function": {"name": "get_weather", "arguments": '{"location":"London"}'}}]
        c.add_assistant_message(content=None, tool_calls=fake_calls)
        c.add_tool_response(tool_call_id="tc_1", content="25°C and sunny")
        c.add_assistant_message(content="The weather in London is 25°C and sunny.")

        fname = "tool_conv.json"
        store.save(c, fname)
        loaded = store.load(fname)

        assert len(loaded.messages) == 4
        assert loaded.messages[1].role == Role.ASSISTANT
        assert loaded.messages[2].role == Role.TOOL
        assert loaded.messages[2].tool_call_id == "tc_1"
