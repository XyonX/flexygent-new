
from pydantic import BaseModel,Field
from typing import Any, Callable  # ← add this line


# tool setup

class Tool(BaseModel):
    name:str
    description:str
    parameter_allowed:dict
    function:Callable[...,Any]

    # TODO FINISH IMPLEMENTING 
    def to_openai_tool(self):
        tool_json = {
            "type":"function",
            "function":{
                "name":self.name,
                "description":self.description,
                "parameters":{
                    "type":"object",
                    "properties":{k:  {kn:vn for kn,vn  in v.items() } for k,v in self.parameter_allowed.items()},
                    "required":[p for  p in self.parameter_allowed.keys() ]

                }

            }
        }
        return tool_json
    
    def to_tool_response(self,tool_call_id,params):

        tool_output = self.function(params)

        
        response = {
            "role":"tool",
            "tool_call_id":tool_call_id,
            "content":tool_output
        }
        return response
    
    def call(self,params,tool_call_id=None):
        filtered = { k:v for k, v in params.items() if  k in self.parameter_allowed.keys() }
        # return self.to_tool_response(tool_call_id,filtered)
        return self.function(filtered)


Tool.model_rebuild()  # ← move it here, right after Tool class


class ToolRegistry(BaseModel):
    tools:dict=Field(default_factory=dict)

    def add_tool(self,tool:Tool):
        self.tools[tool.name]= tool

    def call(self,tool_name:str,params:dict):
        return self.tools[tool_name].call(params)

def get_tools(tool_registry:ToolRegistry,allowed:list):

    response =[]


    if allowed is None:
        for tool in tool_registry.tools.values():
            response.append(tool.to_openai_tool())
    else:

        for tool_name in allowed:
            tool=tool_registry.tools.get(tool_name,None)
            if tool is not None:
                response.append(tool.to_openai_tool())

    return response


