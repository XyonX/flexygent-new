
from flexygent.types import Conversation
from flexygent.types import Message
from flexygent.types import Role
from flexygent.tools import tool_registry, get_tools
from flexygent.client import client
from flexygent.agent import agent_loop
import json
from datetime import datetime
import glob

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


    conv = Conversation()
    conv.add_message(system_message)


    # make tools payload 
    tools= get_tools(tool_registry)


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
        
        # make a user message 
        user_message = Message(role=Role.USER,content = input_message,)

        # add it in conversation
        conv.add_message(user_message)


        response = client.chat.completions.create(model ="openrouter/owl-alpha",messages=conv.to_dict(),tools=tools)


        final_response = agent_loop(conv,response,tools,tool_registry,client)
        # print response 
        print("assistant: ",final_response)
        print("\n")

        # make llm message 

        llm_message = Message(role=Role.ASSISTANT, content=final_response)

        # add it in conversation
        conv.add_message(llm_message)
    
    return conv



if __name__ == "__main__":

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