from pydantic import BaseModel,Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import AsyncOpenAI, OpenAI
from enum import Enum
from dotenv import load_dotenv
import os
from typing import Any, Callable

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
    def to_dict(self):
        return {"role":self.role.value,"content":self.content}
    
class Conversation(BaseModel):
    messages:list[Message]=Field(default_factory=list)

    def add_message(self,message:Message):
        self.messages.append(message)
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
    
    try:
        command = params.get("command")

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
    parameter_allowed:list
    function:Callable[...,Any]



class ToolRegistry(BaseModel):
    tools:dict=Field(default_factory=dict)

    def add_tool(self,tool:Tool):
        self.tools[tool.name]= tool

    def call(self,tool_name:str,params:dict):
        filtered = { k:v for k, v in params.items() if  k in self.tools[tool_name].parameter_allowed }
        return self.tools[tool_name].function(filtered)






tool_run_command = Tool(name="run_command",description="Execute shell command",parameter_allowed = ["command"],function=run_command)



# creating tool registry

tool_registry = ToolRegistry()

# addng run command tool

tool_registry.add_tool(tool_run_command)



output = tool_registry.call("run_command",{"command":"ls"})

print (output)



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


        response_message = response.choices[0].message.content
        # print response 
        print("assistant: ",response_message)
        print("\n")

        # make llm message 

        llm_message = Message(role=Role.ASSISTANT, content=response_message)

        # add it in conversation
        conv.add_message(llm_message)



# cli()


print(run_command("ls"))



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

