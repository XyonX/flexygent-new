from flexygent.types import Conversation
from flexygent.tools.base import ToolRegistry
import json

def agent_loop(conversation:Conversation, api_response:dict,tools:list,tool_registry:ToolRegistry,client):
    
    # request is a tool call rewuest so we must 
    # tool call
    # get response 
    # prepare payload with tols response 
    # send the new message history to llm
    # get api response then update the response object 

    response = api_response


    iter_no=1

    while response.choices[0].finish_reason != "stop":

        print("iteration no :",iter_no)
        # check resonse and look for asked tool to be called 
        # call those tool 
        # prepare payload for the 

        # 01 as this is nto a final resposne it must be a tool call request 
        # we are gonna add this to our converation hiosoty
        conversation.add_assistant_message(content=response.choices[0].message.content,tool_calls=response.choices[0].message.tool_calls)


        # 02 now we added the toool call request to the conversation
        # next step is to call each mentioned tools 

        for t in response.choices[0].message.tool_calls:
            params = json.loads(t.function.arguments)
            tool_call_res = tool_registry.call(t.function.name,params)
            conversation.add_tool_response(tool_call_id=t.id,content=tool_call_res)

        # 02 now as we have called all the tools and appended response as message in the conversation

        # 03 now can send a reqeust to the llm again or for the second pass

        second_response = client.chat.completions.create(model="openrouter/owl-alpha",messages=conversation.to_dict(),tools=tools)


        iter_no=iter_no+1

        response = second_response

    return response.choices[0].message.content
