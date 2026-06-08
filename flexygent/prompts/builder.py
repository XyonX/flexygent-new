from pydantic import BaseModel, Field
from flexygent.prompts.behavior import BEHAVIOR
from flexygent.prompts.guardrails import GUARDRAILS
from flexygent.prompts.identity import IDENTITY
from flexygent.prompts.react import REACT


# ibrg ordered 

class PromptBuilder(BaseModel):
    data:dict=Field(default_factory=lambda:{"identity":IDENTITY,"behavior":BEHAVIOR,"react":REACT,"guardrails":GUARDRAILS})

    def add(self,key:str,prompt:str):
        self.data[key]=prompt
    def update(self, key,prompt:str):
        if key not in self.data:
            raise ValueError(f" Section in not found with key '{key}' use add() to add new  section !")
        self.data[key]=prompt

    def remove(self,key):
        self.data.pop(key,None)
    def build(self):
        return "\n\n".join(self.data.values())
    def get_section(self,section_name:str):
        return self.data.get(section_name,"")
    



