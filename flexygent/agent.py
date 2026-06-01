from flexygent.types import Conversation,AgentConfig,Message,Role
from flexygent.tools.base import ToolRegistry

import json

def agent_loop(conversation:Conversation,input_message:str,tools:list,tool_registry:ToolRegistry,client,config:AgentConfig):


    conversation.add_user_message(input_message)

    response = client.chat.completions.create(model=config.model,messages=conversation.to_dict(),tools=tools)

    iter_no=1
    while iter_no<=config.max_iterations and response.choices[0].finish_reason !="stop":
        # inject warning 
        # if iter_no==config.max_iterations-1:
            # inject the warning message to llm
        conversation.add_assistant_message(content=response.choices[0].message.content,tool_calls=response.choices[0].message.tool_calls)


        for t in response.choices[0].message.tool_calls:
            params = json.loads(t.function.arguments)
            try:
                tool_call_res = tool_registry.call(t.function.name,params)
            except Exception as e:
                tool_call_res=f"Tool error : {str(e)}"
            conversation.add_tool_response(tool_call_id=t.id,content=tool_call_res)

        
        response = client.chat.completions.create(model=config.model,messages=conversation.to_dict(),tools=tools)
        iter_no=iter_no+1
        # or we could simply inject a warning messaging mention the ineration no left for the llm


    generated_response = response.choices[0].message.content
    conversation.add_assistant_message(content=generated_response)


    return generated_response



    

