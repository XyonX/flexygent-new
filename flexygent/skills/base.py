# base.py
from pydantic import BaseModel,Field
from flexygent.prompts.builder import PromptBuilder
from flexygent.types import AgentConfig


class Skill(BaseModel):
    name:str
    description:str
    identity_intro:str
    doc_path:str
    allowed_tools:list[str] | None = None
    config_overrides : dict = Field(default_factory=dict)



class SkillRegistry(BaseModel):
    skills : dict[str,Skill] = Field(default_factory = dict)

    def register(self,skill:Skill):
        self.skills [skill.name] = skill

    def get(self,name:str):
        return self.skills[name]
    def apply(self,skill_name,builder:PromptBuilder,config:AgentConfig):

        skill = self.skills[skill_name]
        intro_section = builder.get_section("identity")

        skill_intro = skill.identity_intro

        # append the skill idnetity intro to the existing intro
        new_intro_section = f"{intro_section } \n \n {skill_intro}"

        builder.update("identity",new_intro_section)

        # update the agent config
        for k,v in skill.config_overrides.items():
            setattr(config,k,v)
            



