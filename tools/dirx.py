""" Dir manipulation tools"""
from collections import defaultdict
import os
GLOBALS  = __import__("mcp-coding-assistant.globals", fromlist=[None]) #import GLOBALS.BASE_PATH, GLOBALS.PROJECTS

def make(project: str, path: str) -> bool:
    """Creates a folder at the specified path"""
    if project in GLOBALS.PROJECTS:
        target_path = GLOBALS.BASE_PATH + project + "/" + path
        if not os.path.isdir(target_path):
            os.mkdir(target_path)
        return True
    raise ValueError("Invalid project")

def rename(project: str, old_path: str, new_path: str) -> bool:
    """Creates a folder at the specified path"""

    if project in GLOBALS.PROJECTS:
        path_to_rename = GLOBALS.BASE_PATH + project + "/" + old_path
        new_path = GLOBALS.BASE_PATH + project + "/" + new_path
        if os.path.isdir(path_to_rename):
            os.rename(path_to_rename, new_path)
        return True
    raise ValueError("Invalid project")

def scaffolding(project: str):
    """Retrieves the project scaffolding in a dict (json) shape"""
    if project in GLOBALS.PROJECTS:
        folder_dict = {
            "folder_name": project,
            "files": [],
            "subfolders": []
        }

        try:
            for entry in os.scandir(GLOBALS.BASE_PATH + "/" + project):
                if entry.is_file():
                    folder_dict["files"].append(entry.name)
                elif entry.is_dir():
                    subfolder_dict = scaffolding(entry.path)
                    folder_dict["subfolders"].append(subfolder_dict)
        except PermissionError:
            pass

        return folder_dict
    raise ValueError("Invalid project")

def inverted_index(project: str, path: str = None, pre_index: dict = None):
    """
    Generates a hashmap with partial paths, filenames and extensions as keys 
    and the associated full flat paths as values for searching
    """
    index = defaultdict(list) if not pre_index else pre_index
    if project in GLOBALS.PROJECTS:
        try:
            scan_path = project if not path else path
            for entry in os.scandir(GLOBALS.BASE_PATH + "/" + scan_path):
                if entry.is_file():
                    name, extension = entry.name.split(".")
                    index[extension].append(entry.path)
                    index[name].append(entry.path)
                elif entry.is_dir():
                    for segment in entry.path.split("/"):
                        index[segment].append(entry.path)
                    index = inverted_index(project, entry.path, index)
        except PermissionError:
            pass

        return index
    raise ValueError("Invalid project")

# def search(query: str):
#     """Searchs files by name, partial paths or extension"""
#     return 
