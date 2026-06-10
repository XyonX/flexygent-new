from pathlib import Path

def read_file(params: dict):
    file_name = params.get("file_name")
    output_length = params.get("output_length", 8000)

    if not file_name:
        return "Error: no file name is provided"

    try:
        file_name = str(Path(file_name).expanduser())
        with open(file_name) as f:
            content = f.read()
        return content[:output_length]
    except FileNotFoundError:
        return f"Error: file '{file_name}' not found"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def replace(params: dict):
    file_name = params.get("file_name")
    old_string = params.get("old_string")
    new_string = params.get("new_string")

    try:
        file_name = str(Path(file_name).expanduser())
        with open(file_name, "r") as f:
            content = f.read()
        if old_string not in content:
            return f"Error: could not find the target string in {file_name}"
        if content.count(old_string) > 1:
            return f"Error: found multiple matches, be more specific"
        new_content = content.replace(old_string, new_string, 1)

        with open(file_name, "w") as f:
            f.write(new_content)

        return f"Successfully edited {file_name}"

    except FileNotFoundError:
        return f"Error: file '{file_name}' not found"
    except Exception as e:
        return f"Error editing file: {str(e)}"


def write_file(params: dict):
    file_name = params.get("file_name")
    content = params.get("content", "")

    if not file_name:
        return "Error: no file name is provided"

    try:
        file_name = str(Path(file_name).expanduser())
        Path(file_name).parent.mkdir(parents=True, exist_ok=True)
        with open(file_name, "w") as f:
            f.write(content)
        return f"Successfully wrote to '{file_name}'"

    except Exception as e:
        return f"Error writing file: {str(e)}"
