
def run_command(params:dict):

    import subprocess

    BLOCKED = {
        "rm", "shutdown", "reboot", "mkfs", "dd", "halt", "poweroff",
        "init", "telinit", "kill", "killall", "pkill", "rmdir",
        "mv", "cp", "chmod", "chown", "chgrp", "passwd",
        "iptables", "ufw", "systemctl", "service", "mount", "umount",
        "echo" 
    }


    command = params.get("command")

    if not command:
        return "No command provided"

    # Split to check the first word (the actual command)
    cmd_name = command.split()[0]

    if cmd_name in BLOCKED:
        return f"Blocked: '{cmd_name}' is not allowed"
    
    try:

        result =subprocess.run(command,
                       shell=True,
                       check=True,
                       capture_output=True,
                       text=True)
        return result.stdout.strip()
    except Exception as e:
        return f" Error running command:{str(e)}"

def get_weather(params: dict):
    """Mock weather tool that always returns 25°C"""
    location = params.get("location", "unknown")
    return f"The weather in {location} is 25°C and sunny."
