from flexygent.skills import SkillRegistry
from flexygent.skills.presets.coding import coding_skill
from flexygent.skills.presets.ui_design import ui_design_skill
from flexygent.skills.presets.research import research_skill
from flexygent.skills.presets.devops import devops_skill

skill_registry = SkillRegistry()

skill_registry.register(coding_skill)
skill_registry.register(ui_design_skill)
skill_registry.register(research_skill)
skill_registry.register(devops_skill)


# per agent — just a list of names referencing the global registry

flex_skills= ["coding","ui_design"]
agent_2_skills=["research"]

