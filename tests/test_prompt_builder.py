"""Tests for flexygent.prompts — PromptBuilder and prompt constants."""

import pytest
from flexygent.prompts.builder import PromptBuilder
from flexygent.prompts.identity import IDENTITY
from flexygent.prompts.behavior import BEHAVIOR
from flexygent.prompts.guardrails import GUARDRAILS
from flexygent.prompts.react import REACT
from flexygent.prompts.user_data import USER_DATA


# ── Prompt constants ─────────────────────────────────────────────────────────

class TestPromptConstants:
    def test_identity_is_non_empty_string(self):
        assert isinstance(IDENTITY, str)
        assert len(IDENTITY.strip()) > 0

    def test_behavior_is_non_empty_string(self):
        assert isinstance(BEHAVIOR, str)
        assert len(BEHAVIOR.strip()) > 0

    def test_guardrails_is_non_empty_string(self):
        assert isinstance(GUARDRAILS, str)
        assert len(GUARDRAILS.strip()) > 0

    def test_react_is_non_empty_string(self):
        assert isinstance(REACT, str)
        assert len(REACT.strip()) > 0

    def test_user_data_is_non_empty_string(self):
        assert isinstance(USER_DATA, str)
        assert len(USER_DATA.strip()) > 0


# ── PromptBuilder ────────────────────────────────────────────────────────────

class TestPromptBuilder:
    def test_default_sections(self):
        pb = PromptBuilder()
        assert "identity" in pb.data
        assert "behavior" in pb.data
        assert "user_data" in pb.data
        assert "react" in pb.data
        assert "guardrails" in pb.data

    def test_default_section_values(self):
        pb = PromptBuilder()
        assert pb.data["identity"] == IDENTITY
        assert pb.data["behavior"] == BEHAVIOR
        assert pb.data["guardrails"] == GUARDRAILS

    def test_build_joins_all_sections(self):
        pb = PromptBuilder()
        result = pb.build()
        assert isinstance(result, str)
        # build joins with double newlines
        assert IDENTITY in result
        assert BEHAVIOR in result
        assert GUARDRAILS in result

    def test_add_section(self):
        pb = PromptBuilder()
        pb.add("custom", "Custom section content")
        assert "custom" in pb.data
        assert pb.data["custom"] == "Custom section content"
        assert "Custom section content" in pb.build()

    def test_update_existing_section(self):
        pb = PromptBuilder()
        pb.update("identity", "New identity")
        assert pb.data["identity"] == "New identity"

    def test_update_nonexistent_section_raises(self):
        pb = PromptBuilder()
        with pytest.raises(ValueError, match="not found"):
            pb.update("nonexistent_key", "some value")

    def test_remove_section(self):
        pb = PromptBuilder()
        pb.remove("guardrails")
        assert "guardrails" not in pb.data
        assert GUARDRAILS not in pb.build()

    def test_remove_nonexistent_is_noop(self):
        pb = PromptBuilder()
        pb.remove("does_not_exist")  # should not raise

    def test_get_section(self):
        pb = PromptBuilder()
        assert pb.get_section("identity") == IDENTITY

    def test_get_section_missing_returns_empty(self):
        pb = PromptBuilder()
        assert pb.get_section("nonexistent") == ""

    def test_build_order_is_deterministic(self):
        """Sections should appear in insertion order."""
        pb = PromptBuilder()
        result = pb.build()
        identity_pos = result.index(IDENTITY)
        behavior_pos = result.index(BEHAVIOR)
        guardrails_pos = result.index(GUARDRAILS)
        assert identity_pos < behavior_pos < guardrails_pos

    def test_multiple_builders_are_independent(self):
        pb1 = PromptBuilder()
        pb2 = PromptBuilder()
        pb1.add("extra", "only in pb1")
        assert "extra" not in pb2.data
