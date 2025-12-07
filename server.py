"""
FastMCP quickstart example.
"""
import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools import dirx, filex
from globals import PROJECTS, ALLOWED_EXTENSIONS
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")


@mcp.resource("resource://listx_available_projects")
def list_available_projects() -> str:
    """Return the list of available build paths"""
    return PROJECTS


@mcp.resource("resource://list_available_extensions")
def list_available_extensions() -> str:
    """Return the list of available file extensions"""
    return ALLOWED_EXTENSIONS

@mcp.tool()
def make_dir(project: str, path: str) -> bool:
    """Creates a folder at the specified path"""
    return dirx.make(project, path)

@mcp.tool()
def rename_dir(project: str, old_path: str, new_path: str) -> bool:
    """Creates a folder at the specified path"""
    return dirx.rename(project, old_path, new_path)


@mcp.tool()
def get_project_scaffolding(project: str):
    """Retrieves the project scaffolding in a dict shape"""
    return dirx.scaffolding(project=project)

@mcp.tool()
def get_files_inverted_index(project: str):
    """Retrieves the project scaffolding in a dict shape"""
    return dirx.inverted_index(project=project)


@mcp.tool()
def save_file(project: str, path: str, filename: str, extension: str, content: str) -> bool:
    """Creates or updates a file at the given path, with the given name, extension and content"""
    return filex.save(project, path, filename, extension, content)

@mcp.tool()
def load_file(project: str, path: str) -> str:
    """loads a file at the given path"""
    return filex.load(project, path)

@mcp.tool()
def execute_file(
        project: str = "test", path: str = "b/x.py", args: list[str] = ["a", "-v", "1"]
    ) -> dict[str, str]:
    """loads a file at the given path"""
    result = filex.execute(project, path, args)
    return result

@mcp.tool()
def remove_file(project: str, path: str) -> bool:
    """removes a file at the given path"""
    return filex.remove(project, path)
