# cli_app.py

from flexygent.types import Conversation,Message,Role,AgentConfig
from flexygent.types import Agent
from flexygent.skills import skill_registry,flex_skills
from flexygent.tools import tool_registry, get_tools
from flexygent.agent import agent_loop
from flexygent.client import client
from flexygent.memory.file_store import FileStore
from flexygent.adapters.cli import CliUserIO

def app():

    io=CliUserIO()
    # use the framrwork and make the cli app
    
    config  = AgentConfig(model="deepseek-v4-flash")

    flex = Agent(name="flex",config=config)
    flex.apply_skills(flex_skills,skill_registry)

    system_message = flex.get_system_message()

    conv = Conversation()
    conv.add_message(system_message)

        # # make tools payload 
    tool_filter= flex.get_tool_filter(skill_registry)
    tools= get_tools(tool_registry,tool_filter)


    memory =FileStore()


    # saved_conversation_files = get_saved_files()
    saved_conversation_files = memory.list_saved()

    if(len(saved_conversation_files) !=0):
        print("Saved file detected , would you like to load the latest one ? ")
        input_value = input()
        no_val = ["no","n","nahi"]
        if input_value in no_val:
            pass
        else:
            # conv=load_conversation(saved_conversation_files[0])
            conv=memory.load(saved_conversation_files[0])


    try:

        while 1:

            # take message
            input_message = io.get_input("Enter message : ")

            print("\n")

            if input_message == "exit":
                return conv
            
            output_message = agent_loop(conv,input_message,tools,tool_registry,client,flex.config)

            # print response 
            io.show_output(output_message)

    except KeyboardInterrupt:
        print("\nUser pressed Ctrl+C, stopping gracefully")
    except Exception as e:
        print("unexpected errpr:",e)
    finally:
        if conv is not None:
            file_name = memory.gen_file_name()
            memory.save(conv,file_name)
            print("Conversation saved before exit to the file : ", file_name)


    


if __name__ == "__main__":
    app()