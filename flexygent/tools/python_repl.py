from pathlib import Path
from datetime import datetime
import subprocess
import shutil


def gen_temp_dir():

    base_path = Path("temp")

    d = datetime.now()

    sub_dir  = sub_dir = d.strftime("%Y-%m-%d-%H-%M-%S")

    sub_path = base_path / sub_dir

    sub_path.mkdir(parents=True)

    return str(sub_path)

def cleanup(working_dir):

    abs_dir = Path(working_dir).resolve()
    WORKSPACE_DIR =Path("temp").resolve()

    if abs_dir == WORKSPACE_DIR:
        return f"Error : you cant delete workspace direcoty"

    if WORKSPACE_DIR not in abs_dir.parents:
        return f"Error Deleting dir outside workspace is not allowed"
    
    if not abs_dir.exists():
        return f"Error : path '{abs_dir} doenst exist '"
    
    if not  abs_dir.is_dir():
        return f"Error : provided path '{abs_dir}' is not a  direfctory !!"

    
    
    shutil.rmtree(abs_dir)

    return f"Directory cleanup successfull for dir : '{str(abs_dir)}'"

def python_repl(params:dict):

    code = params.get("code")
    file_name = "run.py"

    if not code:
        return "Error : "
    
    working_dir = None

    try:

        # 01 generate working dir
        working_dir = gen_temp_dir()

        # 02 generate the file in the working dir
        file_path = Path(working_dir) / file_name

        # 03 scan the code 
        # block obviously dangerous imports at the code level
        BLOCKED = ["import os", "import subprocess", "import shutil", "__import__"]

        for blocked in BLOCKED:
            if blocked in code:
                return f"Error : code is unsafe to run"


        # 04 write the code in that file
        with open(file_path,"w")as f:
            f.write(code)

        # 05
        result = subprocess.run(["python",file_name],capture_output=True,text=True,timeout=10,cwd=working_dir)

        if result.returncode != 0:
            return f"Error : \n {result.stderr} "

        return result.stdout
    
    except subprocess.TimeoutExpired:
        return "Error : timed out after 10 seconds"
    
    except Exception as e:
        return f"Error : executing python file : '{str(e)}' "
    
    finally:
        if working_dir:
            cleanup(working_dir)

