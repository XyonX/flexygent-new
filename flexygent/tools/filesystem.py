

def read_file(params:dict):

    filename = params.get("file_name")
    output_length = params.get("output_length",8000)

    if not filename:
        return "Error : no file name is provided"

    try:

        with open(filename) as f:
            content = f.read()
        return content[:8000]
    except FileNotFoundError :
        return f"Error : file '{filename} not found"
    except Exception as e:
        return f"Error : reading file '{str(e)}"
        

def replace(params:dict):

    filename =params.get("filename")
    old_string=params.get("old_string")
    new_string=params.get(new_string)

    try:
        with open(filename,"r") as f:
            content = f.read()
        if old_string not in content:
            return f"Error: could not find the target string in {filename}"
        if content.count(old_string)>1:
            return f"Error: found multiple matches, be more specific"
        new_content = content.replace(old_string,new_string,1)

        with open(filename,"w") as f:
            f.write(new_content)
    
        return f"Successfully edited {filename}"

    except FileNotFoundError:
        return f"Error : file '{filename} not found"
    except Exception as e:
        return f"Error : editing file '{filename}"
    





def write_file(params:dict):

    filename = params.get("filename")
    content = params.get("content", "")

    if not filename :
        return f"Error : no file name is provided"
    
    try:
        with open(filename,"w") as f:
            f.write(content)
            return f"succesfully wrote to '{filename}"
    
    except Exception as e:
        return f"Error writing file : '{str(e)}"

