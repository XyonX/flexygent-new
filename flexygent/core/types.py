from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT ="assistant"
    TOOL="tool_result"
    


# the base class for message 
#  it stores waht role this message belongs to and waht conent the message has 
class Message(BaseModel):
    role:Role
    content:str

    def to_dict(self)->dict[str,Any]:
        return {"role":self.role.value,"content":self.content}
    

class SystemMessage(Message):
    role:Role=Role.SYSTEM

class UserMessage(Message):
    role:Role=Role.USER

class AssistantMessage(Message):
    role:Role=Role.ASSISTANT

class MessageHistory(BaseModel):
    messages:list[Message] = Field(default_factory = list)

    def add(self, message:Message):
        self.messages.append(message)
    def to_list(self)->list[dict[str,Any]]:
        return[m.to_dict() for m in self.messages]
    
    def last(self)->Message | None:
        return self.messages[-1] if self.messages else None
    def __len__(self):
        return len(self.messages)



    