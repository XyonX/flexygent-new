
from flexygent.types import Conversation
from flexygent.types import Message
from flexygent.types import Role
from flexygent.tools import tool_registry, get_tools
from flexygent.client import client
from flexygent.agent import agent_loop


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


    
    while 1:

        # take message
        input_message = input("Enter message : ")

        print("\n")

        if input_message == "exit":
            return
        
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



if __name__ == "__main__":
    cli()