from pydantic import BaseModel,Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import AsyncOpenAI, OpenAI
from enum import Enum
from dotenv import load_dotenv
import os
from typing import Any, Callable

import json

# loaidng env variable and injecting them in the process 
load_dotenv()

class Role(str,Enum):
    SYSTEM="system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Message(BaseModel):
    role:Role
    content:str
    tool_calls:list = Field(default_factory=list)
    tool_call_id:str=""

    def to_dict(self):
        response ={"role":self.role.value,"content":self.content}
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
        

    
# m1 = Message(role=Role.USER, content="How are you ? ")
# m2 = Message(role=Role.ASSISTANT, content="Hello! I'm doing well, thank you for asking! How can I help you today?")
# m3 = Message(role=Role.USER, content="great, anything exciting happening in the field of computer science ")

# conv = Conversation()

# conv.add_message(m1)
# conv.add_message(m2)
# conv.add_message(m3)

# # history = conv.to_dict()

# # print(history)



# api_key = os.getenv("API")
# base_url = os.getenv("ENDPOINT")

# client = OpenAI(api_key=api_key,base_url=base_url)

# response = client.chat.completions.create(model="openrouter/owl-alpha",messages = conv.to_dict())

# output_message = response.choices[0].message.content

# m4 = Message(role=Role.ASSISTANT,content=output_message)


# conv.add_message(m4)

# print(output_message)


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
        return self.to_tool_response(tool_call_id,filtered)




class ToolRegistry(BaseModel):
    tools:dict=Field(default_factory=dict)

    def add_tool(self,tool:Tool):
        self.tools[tool.name]= tool

    def call(self,tool_name:str,params:dict):
        return self.tools[tool_name].call(params)






# ...existing code...

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

# ...existing code...

# creating tool registry

tool_registry = ToolRegistry()

# addng run command tool

tool_registry.add_tool(tool_run_command)



output = tool_registry.call("run_command",{"command":"ls"})

# print (output)

print(tool_run_command.to_openai_tool())
# print(json.dumps(tool_run_command.to_openai_tool(), indent=2))

def agent_loop(api_response:dict):
    
    # request is a tool call rewuest so we must 
    # tool call
    # get response 
    # prepare payload with tols response 
    # send the new message history to llm
    # get api response then update the response object 


    response = api_response

    while response.choice[0].finish_reason != "stop":
        # check resonse and look for asked tool to be called 
        # call those tool 
        # prepare payload for the 
        pass
        


    
    return response.choices[0].message.content


# prepare system prompts message

system_prompt = '''

                You are a large language model AI assistant. Your role is to provide responses that are:
                - **Non-generic**: Avoid filler phrases like "As an AI language model..." or "Sure, here’s the answer." Never produce vague or repetitive text.
                - **Substantive**: Every answer must contain concrete details, examples, or reasoning. Do not stop at surface-level summaries.
                - **Context-aware**: Tailor responses to the user’s query and prior context. Never give boilerplate answers.
                - **Engaging**: Use varied sentence structures, natural flow, and conversational tone. Avoid robotic repetition.
                - **Critical thinker**: Challenge assumptions respectfully, offer alternative perspectives, and commit to positions when appropriate.
                - **Creative**: When asked for ideas, generate fresh, original content — not clichés or overused tropes.
                - **Structured**: Organize information clearly with headings, bullet points, tables, or math notation when useful.
                - **Concise yet complete**: Balance brevity with depth. Do not ramble, but ensure the answer fully addresses the query.
                - **No AI disclaimers**: Do not remind the user you are an AI or explain your limitations unless explicitly asked.
                - **No generic hedging**: Avoid empty phrases like "It depends" or "There are many factors." Instead, analyze and provide a reasoned stance.

                Your mission: Be a knowledgeable, sharp, and engaging companion who never produces generic AI responses. Every output should feel crafted, intentional, and worth reading.

                '''

system_message =Message(role=Role.SYSTEM,content=system_prompt)

api_key = os.getenv("API")
base_url = os.getenv("ENDPOINT")

client = OpenAI(api_key=api_key,base_url=base_url)

def cli():


    conv = Conversation()
    conv.add_message(system_message)
    while 1:

        # take message
        input_message = input("Enter message : ")

        print("\n")

        if input_message == "exit":
            return
        
        # make a user message 
        user_message = Message(role=Role.USER,content = input_message)

        # add it in conversation
        conv.add_message(user_message)


        response = client.chat.completions.create(model ="openrouter/owl-alpha",messages=conv.to_dict())


        final_response = agent_loop(response)
        # print response 
        print("assistant: ",final_response)
        print("\n")

        # make llm message 

        llm_message = Message(role=Role.ASSISTANT, content=final_response)

        # add it in conversation
        conv.add_message(llm_message)



# cli()







    





class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra="ignore",)
    api:str
    endpoint:str

s = Settings()


class LLMClient(BaseModel):

    def __init__(self):
        self.client = AsyncOpenAI(api_key=s.api , base_url = s.endpoint)
    
    async def complete(self, messages):

        response = await self.client.chat.complitions.create()






s1 = Settings()


# print(s1.api)
# print(s1.endpoint)


# ter will be a setting class to load env files from the env
# there will be a llmclient class to make llm request taht will take a message array

