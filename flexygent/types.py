from pydantic import BaseModel,Field
from enum import Enum

class Role(str,Enum):
    SYSTEM="system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Message(BaseModel):
    role:Role
    content: str | None = None  # ✅ allow None for tool-call messages
    tool_calls:list = Field(default_factory=list)
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