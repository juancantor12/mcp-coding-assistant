""" File manipulation tools. """
import json
import os
import subprocess
from localmcp.tools.dirx import make as make_dir
from localmcp.globals import BASE_PATH, PROJECTS, ALLOWED_EXTENSIONS

def save(project: str, path: str, filename: str, extension: str, content: str) -> bool:
    """Creates or updates a file at the given path, with the given name, extension and content"""
    # Check If correct project and allowed extension
    if project in PROJECTS and extension in ALLOWED_EXTENSIONS:
        target_path = BASE_PATH + project + "/" + path
        make_dir(project, path)
        with open(target_path + "/" + filename + "." + extension, "w", encoding="UTF-8") as file:
            file.write(content)
        return True
    raise ValueError("Invalid project or extension")



def load(project: str, path: str) -> str:
    """loads a file at the given path"""
    # Check If correct project
    if project in PROJECTS:
        file_path = BASE_PATH + project + "/" + path
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
    if project in PROJECTS:
        file_path = BASE_PATH + project + "/" + path
        # Check if the file exists
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        raise ValueError("File doesn't exists")
    raise ValueError("Invalid project")


def execute(project: str, path: str, args: list[str], as_module: bool = False ) -> dict[str, str]:
    """Executes a python script with the specified params"""
    # Check If correct project
    if project in PROJECTS:
        file_path = BASE_PATH + project + "/" + path
        # Check if the file exists
        if os.path.exists(file_path):
            command = ["python"]
            if as_module:
                command.append("-m")
            command.append(file_path)
            command.extend(args)
            result = subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True
            )
            return {
                "args": result.args, 
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        raise ValueError("File doesn't exists")
    raise ValueError("Invalid project")
