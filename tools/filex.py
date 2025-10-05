""" File manipulation tools. """
import io
import os
import sys
import subprocess
dirx =  __import__("mcp-coding-assistant.tools.dirx")
GLOBALS  = __import__("mcp-coding-assistant.globals", fromlist=[None])


def save(project: str, path: str, filename: str, extension: str, content: str) -> bool:
    """Creates or updates a file at the given path, with the given name, extension and content"""
    # Check If correct project and allowed extension
    if project in GLOBALS.PROJECTS and extension in GLOBALS.ALLOWED_EXTENSIONS:
        target_path = GLOBALS.BASE_PATH + project + "/" + path
        dirx.make(project, path)
        with open(target_path + "/" + filename + "." + extension, "w", encoding="UTF-8") as file:
            file.write(content)
        return True
    raise ValueError("Invalid project or extension")



def load(project: str, path: str) -> str:
    """loads a file at the given path"""
    # Check If correct project
    if project in GLOBALS.PROJECTS:
        file_path = GLOBALS.BASE_PATH + project + "/" + path
        # Check if the file exists
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="UTF-8") as file:
                content = file.read()
                return content
        raise ValueError("File doesn't exists")
    raise ValueError("Invalid project")

def remove(project: str, path: str) -> bool:
    """loads a file at the given path"""
    # Check If correct project
    if project in GLOBALS.PROJECTS:
        file_path = GLOBALS.BASE_PATH + project + "/" + path
        # Check if the file exists
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        raise ValueError("File doesn't exists")
    raise ValueError("Invalid project")


def execute(project: str, path: str, args: list[str], as_module: bool = False ) -> dict[str, str]:
    """Executes a python script with the specified params"""
    # TODO: popen always hangs when running any pyton program, it never exits, surrogat the call to a bash file that sets up
    # and runs a docker image with the actual script or code to run and wrap the call.
    # Check If correct project
    if project in GLOBALS.PROJECTS:
        file_path = GLOBALS.BASE_PATH + project + "/" + path
        # Check if the file exists
        if os.path.exists(file_path):
            command = [sys.executable, "-u"]
            if as_module:
                command.append("-m")
            command.append(file_path)
            command.extend(args)
            result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, text=True, creationflags = subprocess.CREATE_NEW_CONSOLE)
            for line in iter(result.stdout.readline, ""):
                return {"line": line}
            # return {
            #     "stdout": stdout,
            #     "stderr": stderr
            # }
        raise ValueError("File doesn't exists")
    raise ValueError("Invalid project")
