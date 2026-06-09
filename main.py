
from flexygent.types import Conversation,Message,Role,AgentConfig
from flexygent.tools import tool_registry, get_tools
from flexygent.client import client
from flexygent.agent import agent_loop
import json
from datetime import datetime
import glob
from flexygent.prompts import PromptBuilder
from flexygent.types import Agent
from flexygent.skills import skill_registry,flex_skills
import json



def gen_file_name():
    now = datetime.now()

    formatted_string ="conversation-"+now.strftime('%Y-%m-%d_%H-%M-%S')+".json"
    return formatted_string


def get_saved_files():
    files = glob.glob("conversation-*.json")
    return  sorted(files,reverse=True)


def save_conversation(conversation:Conversation,file_name):
    print("saving conversation ... ")
    # create pydantic dump
    conversation_dump =  conversation.model_dump()


    # save it in a json file u
    with open(file_name,"w") as file:
        json.dump(conversation_dump,file,indent =4)

    print("conversation save done !")

def load_conversation(file_name:str):

    print("Loading conversation")

    # loiad the json data form the file 
    with open(file_name,"r") as file:
        data = json.load(file)
    

    print("Loading conversation done ! ")
    return Conversation.model_validate(data)



def cli():

    config  = AgentConfig(model="deepseek-v4-flash")

    flex = Agent(name="flex",config=config)
    flex.apply_skills(flex_skills,skill_registry)

    system_message = flex.get_system_message()

    conv = Conversation()
    conv.add_message(system_message)


    # # make tools payload 
    tool_filter= flex.get_tool_filter(skill_registry)
    tools= get_tools(tool_registry,tool_filter)


    saved_conversation_files = get_saved_files()

    if(len(saved_conversation_files) !=0):
        print("Saved file detected , would you like to load the latest one ? ")
        input_value = input()
        no_val = ["no","n","nahi"]
        if input_value in no_val:
            pass
        else:
            conv=load_conversation(saved_conversation_files[0])

            
    
    while 1:

        # take message
        input_message = input("Enter message : ")

        print("\n")

        if input_message == "exit":
            return conv
        
        output_message = agent_loop(conv,input_message,tools,tool_registry,client,flex.config)

        # print response 
        print("assistant: ",output_message)
        print("\n")
    
    return conv



if __name__ == "__main__":

    conv = None
    try:
        conv = cli()
    except KeyboardInterrupt:
        print("\nUser pressed Ctrl+C, stopping gracefully")
    except Exception as e:
        print("unexpected errpr:",e)
    finally:
        if conv is not None:
            file_name = gen_file_name()
            save_conversation(conv,file_name)
            print("Conversation saved before exit to the file : ", file_name)