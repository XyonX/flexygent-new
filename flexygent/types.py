from __future__ import annotations
from pydantic import BaseModel,Field
from enum import Enum
from typing import TYPE_CHECKING
from flexygent.prompts.builder import PromptBuilder

if TYPE_CHECKING:
    from flexygent.skills import Skill,SkillRegistry


class Role(str,Enum):
    SYSTEM="system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Message(BaseModel):
    role:Role
    content: str | None = None  # ✅ allow None for tool-call messages
    tool_calls:list | None = Field(default_factory=list)
    tool_call_id:str=""

    def to_dict(self):
        response ={"role":self.role.value,"content":self.content or ""}
        if self.tool_calls:
            response["tool_calls"]=self.tool_calls
        if self.tool_call_id:
            response["tool_call_id"]=self.tool_call_id
        return response
    
class Conversation(BaseModel):
    messages:list[Message]=Field(default_factory=list)

    def add_message(self,message:Message):
        self.messages.append(message)

    def add_user_message(self,content:str):
        m = Message(role=Role.USER,content=content)
        self.messages.append(m)

    def add_assistant_message(self,content:str,tool_calls:dict=None):
        m=Message(role=Role.ASSISTANT,content=content,tool_calls=tool_calls)
        self.messages.append(m)

    def add_tool_response(self,tool_call_id:str,content:str):
        m=Message(role=Role.TOOL,content=content,tool_call_id=tool_call_id)
        self.messages.append(m)
        


    def to_dict(self):
        ret=[]
        for message in self.messages:
            ret.append(message.to_dict())
        return ret
    


class AgentConfig(BaseModel):
    max_iterations:int =10
    model:str= "openrouter/owl-alpha"
    verbose:bool =False
    temperature:float = 0.7
    enable_rag :bool = False


class Agent(BaseModel):
    name:str
    builder : PromptBuilder=Field(default_factory = PromptBuilder)
    config:AgentConfig = Field(default_factory = AgentConfig)
    active_skills: list[str] = Field(default_factory=list)

    def apply_skill(self,skill_name:str,skill_registry:SkillRegistry):
        skill_registry.apply(skill_name,self.builder,self.config)
        self.active_skills.append(skill_name)

        skill_description = []

        for s_name in self.active_skills:
            skill = skill_registry.get(s_name)
            if skill is not None:
                skill_description.append(f"-{skill.name}: {skill.identity_intro} \n -read_file('{skill.doc_path}')")


        # update the builder for available_skills
        skill_str = f"""

## Available Skills

    You have the following skills loaded. When a query requires deep 
    expertise in a specific area, read the skill doc first:

    {'\n'.join(skill_description)}

    Always read the relevant skill doc before responding to domain-specific queries.

        """

        if "available_skills" in self.builder.data:
            self.builder.update("available_skills",skill_str)
        else:
            self.builder.add("available_skills",skill_str)

    
    def apply_skills(self,skills: list,skill_registry:SkillRegistry):
        for skill_name in skills:
            self.apply_skill(skill_name,skill_registry)



    def get_system_message(self):
        return Message(role=Role.SYSTEM,content=self.builder.build())
    
    def get_tool_filter(self,skill_registry:SkillRegistry):

        if not self.active_skills:
            return None
        tools = set()

        for skill_name in self.active_skills:
            skill = skill_registry.get(skill_name)
            skill_tools = skill.allowed_tools
            if skill_tools is None:
                return None
            tools.update(skill_tools)
        
        return list(tools)


