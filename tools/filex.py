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


def execute(project: str, path: str, args: list[str]) -> dict[str, any]:
    """Executes a python script with the specified params"""
    # Check If correct project
    if project in GLOBALS.PROJECTS:
        file_path = GLOBALS.BASE_PATH + project + "/" + path
        # Check if the file exists
        if os.path.exists(file_path):
            command = [sys.executable, file_path] + args
            with subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as process:
                outs, errs = process.communicate()
                return { "outs":outs, "errs":errs}
        raise ValueError("File doesn't exists")
    raise ValueError("Invalid project")
