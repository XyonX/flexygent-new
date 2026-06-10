# flexygent/tools/user_input.py

import json

def collect_input(params: dict) -> str:
    """Ask the user for input dynamically and return JSON key-value pairs."""   
    res={}

    fields = params.get("fields",[])

    for input_configs in fields:
        key = input_configs.get("key")
        label =input_configs.get("label",key)
        val = input(label+": ")
        res[key]=val
    
    return json.dumps(res)
