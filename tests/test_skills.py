"""Tests for flexygent.skills — Skill, SkillRegistry, presets."""

import pytest
from flexygent.skills.base import Skill, SkillRegistry
from flexygent.prompts.builder import PromptBuilder
from flexygent.types import AgentConfig, Agent


# ── Skill model ──────────────────────────────────────────────────────────────

class TestSkill:
    def test_skill_creation(self):
        s = Skill(
            name="test",
            description="A test skill",
            identity_intro="You are a tester.",
            doc_path="skills/docs/test.md",
        )
        assert s.name == "test"
        assert s.allowed_tools is None
        assert s.config_overrides == {}

    def test_skill_with_tools_and_overrides(self):
        s = Skill(
            name="coding",
            description="Coding skill",
            identity_intro="You code.",
            doc_path="skills/docs/coding.md",
            allowed_tools=["read_file", "write_file"],
            config_overrides={"max_iterations": 20},
        )
        assert s.allowed_tools == ["read_file", "write_file"]
        assert s.config_overrides["max_iterations"] == 20


# ── SkillRegistry ────────────────────────────────────────────────────────────

class TestSkillRegistry:
    def _make_skill(self, name="test", tools=None, overrides=None):
        return Skill(
            name=name,
            description=f"{name} skill",
            identity_intro=f"You are {name}.",
            doc_path=f"skills/docs/{name}.md",
            allowed_tools=tools,
            config_overrides=overrides or {},
        )

    def test_register_and_get(self):
        sr = SkillRegistry()
        s = self._make_skill("coding")
        sr.register(s)
        assert sr.get("coding") is s

    def test_get_nonexistent_raises(self):
        sr = SkillRegistry()
        with pytest.raises(KeyError):
            sr.get("nonexistent")

    def test_register_multiple(self):
        sr = SkillRegistry()
        sr.register(self._make_skill("a"))
        sr.register(self._make_skill("b"))
        assert len(sr.skills) == 2

    def test_apply_injects_identity(self):
        sr = SkillRegistry()
        s = self._make_skill("coding")
        sr.register(s)

        builder = PromptBuilder()
        config = AgentConfig()
        original_identity = builder.get_section("identity")

        sr.apply("coding", builder, config)

        new_identity = builder.get_section("identity")
        assert s.identity_intro in new_identity
        assert original_identity in new_identity

    def test_apply_updates_config(self):
        sr = SkillRegistry()
        s = self._make_skill("coding", overrides={"max_iterations": 25, "temperature": 0.1})
        sr.register(s)

        builder = PromptBuilder()
        config = AgentConfig()

        sr.apply("coding", builder, config)

        assert config.max_iterations == 25
        assert config.temperature == 0.1

    def test_apply_no_overrides(self):
        sr = SkillRegistry()
        s = self._make_skill("basic")
        sr.register(s)

        builder = PromptBuilder()
        config = AgentConfig()
        original_max = config.max_iterations

        sr.apply("basic", builder, config)

        assert config.max_iterations == original_max


# ── Agent + Skills integration ───────────────────────────────────────────────

class TestAgentSkillIntegration:
    def _make_registry_with_skills(self):
        sr = SkillRegistry()
        sr.register(Skill(
            name="coding",
            description="Coding skill",
            identity_intro="You are a coder.",
            doc_path="skills/docs/coding.md",
            allowed_tools=["read_file", "write_file", "replace"],
            config_overrides={"max_iterations": 20},
        ))
        sr.register(Skill(
            name="research",
            description="Research skill",
            identity_intro="You are a researcher.",
            doc_path="skills/docs/research.md",
            allowed_tools=["web_fetch", "read_file"],
            config_overrides={"temperature": 0.5},
        ))
        return sr

    def test_apply_single_skill(self):
        sr = self._make_registry_with_skills()
        agent = Agent(name="test")
        agent.apply_skill("coding", sr)
        assert "coding" in agent.active_skills
        assert agent.config.max_iterations == 20

    def test_apply_multiple_skills(self):
        sr = self._make_registry_with_skills()
        agent = Agent(name="test")
        agent.apply_skills(["coding", "research"], sr)
        assert len(agent.active_skills) == 2
        assert "coding" in agent.active_skills
        assert "research" in agent.active_skills

    def test_system_message_contains_skill_identity(self):
        sr = self._make_registry_with_skills()
        agent = Agent(name="test")
        agent.apply_skill("coding", sr)
        msg = agent.get_system_message()
        assert "coder" in msg.content

    def test_tool_filter_with_skills(self):
        sr = self._make_registry_with_skills()
        agent = Agent(name="test")
        agent.apply_skills(["coding", "research"], sr)
        tools = agent.get_tool_filter(sr)
        assert isinstance(tools, list)
        # union of both skills' tools
        assert "read_file" in tools
        assert "write_file" in tools
        assert "web_fetch" in tools
        assert "replace" in tools

    def test_tool_filter_with_none_allowed_tools(self):
        """If any skill has allowed_tools=None, filter returns None (all tools)."""
        sr = SkillRegistry()
        sr.register(Skill(
            name="wildcard",
            description="Wildcard",
            identity_intro="You can do anything.",
            doc_path="skills/docs/wild.md",
            allowed_tools=None,
        ))
        agent = Agent(name="test")
        agent.apply_skill("wildcard", sr)
        assert agent.get_tool_filter(sr) is None

    def test_available_skills_in_prompt(self):
        sr = self._make_registry_with_skills()
        agent = Agent(name="test")
        agent.apply_skill("coding", sr)
        msg = agent.get_system_message()
        assert "Available Skills" in msg.content


# ── Preset skills loading ────────────────────────────────────────────────────

class TestPresetSkills:
    def test_coding_skill_loads(self):
        from flexygent.skills.presets.coding import coding_skill
        assert coding_skill.name == "coding"
        assert "read_file" in coding_skill.allowed_tools

    def test_ui_design_skill_loads(self):
        from flexygent.skills.presets.ui_design import ui_design_skill
        assert ui_design_skill.name == "ui_design"

    def test_research_skill_loads(self):
        from flexygent.skills.presets.research import research_skill
        assert research_skill.name == "research"

    def test_devops_skill_loads(self):
        from flexygent.skills.presets.devops import devops_skill
        assert devops_skill.name == "devops"

    def test_global_registry_has_all_presets(self):
        from flexygent.skills.registry import skill_registry
        assert "coding" in skill_registry.skills
        assert "ui_design" in skill_registry.skills
        assert "research" in skill_registry.skills
        assert "devops" in skill_registry.skills

    def test_flex_skills_list(self):
        from flexygent.skills.registry import flex_skills
        assert "coding" in flex_skills
        assert "ui_design" in flex_skills

    def test_agent_2_skills_list(self):
        from flexygent.skills.registry import agent_2_skills
        assert "research" in agent_2_skills
