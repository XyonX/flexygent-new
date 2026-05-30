
from pydantic import BaseModel,Field
from typing import Any, Callable  # ← add this line



# run command tool
def run_command(params:dict):

    import subprocess

    BLOCKED = {
        "rm", "shutdown", "reboot", "mkfs", "dd", "halt", "poweroff",
        "init", "telinit", "kill", "killall", "pkill", "rmdir",
        "mv", "cp", "chmod", "chown", "chgrp", "passwd",
        "iptables", "ufw", "systemctl", "service", "mount", "umount",
        "echo" 
    }


    command = params.get("command")

    if not command:
        return "No command provided"

    # Split to check the first word (the actual command)
    cmd_name = command.split()[0]

    if cmd_name in BLOCKED:
        return f"Blocked: '{cmd_name}' is not allowed"
    
    try:

        result =subprocess.run(command,
                       shell=True,
                       check=True,
                       capture_output=True,
                       text=True)
        return result.stdout.strip()
    except Exception as e:
        return " error running command"

def get_weather(params: dict):
    """Mock weather tool that always returns 25°C"""
    location = params.get("location", "unknown")
    return f"The weather in {location} is 25°C and sunny."

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


tool_run_command = Tool(
    name="run_command",
    description="Execute shell command",
    parameter_allowed={
        "command": {
            "type": "string",
            "description": "Shell command to execute (e.g., 'ls', 'pwd')."
        }
    },
    function=run_command,
)


tool_get_weather = Tool(
    name="get_weather",
    description="Get the current weather for a location",
    parameter_allowed={
        "location": {
            "type": "string",
            "description": "The city or location to get weather for (e.g., 'London', 'New York')."
        }
    },
    function=get_weather,
)

def get_tools(tool_registry):
    response =[]
    for tool in tool_registry.tools.values():
        response.append(tool.to_openai_tool())
    return response



tool_registry = ToolRegistry()

# addng run command tool

tool_registry.add_tool(tool_run_command)
tool_registry.add_tool(tool_get_weather)