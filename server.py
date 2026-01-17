"""
FastMCP quickstart example.
"""
import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import AppConfig
from core.files import FileService
from core.git import GitService
from core.graph import GraphService
from core.interpreter import GraphChangeApplier
from core.projects import ProjectManager
from globals import PROJECTS, ALLOWED_EXTENSIONS
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")
config = AppConfig.from_globals()
projects = ProjectManager(config)
files = FileService(config, projects)
graphs = GraphService(config)
interpreter = GraphChangeApplier(config, projects, files, graphs)
git = GitService(os.path.abspath(os.path.dirname(__file__)))


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
    return projects.make_dir(project, path)

@mcp.tool()
def rename_dir(project: str, old_path: str, new_path: str) -> bool:
    """Creates a folder at the specified path"""
    return projects.rename_dir(project, old_path, new_path)


@mcp.tool()
def get_project_scaffolding(project: str):
    """Retrieves the project scaffolding in a dict shape"""
    return projects.scaffolding(project=project)

@mcp.tool()
def get_files_inverted_index(project: str):
    """Retrieves the project scaffolding in a dict shape"""
    return projects.inverted_index(project=project)

@mcp.tool()
def build_code_graph(project: str):
    """Builds a code graph and stores it as JSON"""
    return graphs.build(project=project)

@mcp.tool()
def query_code_graph(project: str, term: str, kind: str | None = None):
    """Queries the code graph by name or file path"""
    return graphs.query(project=project, term=term, kind=kind)

@mcp.tool()
def save_graph_proposal(project: str, proposal: dict[str, object]):
    """Validates and stores a graph change proposal"""
    return graphs.save_proposal(project=project, proposal=proposal)

@mcp.tool()
def apply_graph_proposal(project: str, proposal_path: str):
    """Applies a graph proposal to code and updates the graph"""
    return interpreter.apply_proposal(project=project, proposal_path=proposal_path)

@mcp.tool()
def git_status() -> str:
    """Returns git status summary"""
    return git.status()

@mcp.tool()
def git_add_all() -> str:
    """Runs git add ."""
    return git.add_all()

@mcp.tool()
def git_commit(message: str) -> str:
    """Runs git commit -m <message>"""
    return git.commit(message)

@mcp.tool()
def git_push() -> str:
    """Pushes current branch to origin"""
    return git.push()


@mcp.tool()
def save_file(project: str, path: str, filename: str, extension: str, content: str) -> bool:
    """Creates or updates a file at the given path, with the given name, extension and content"""
    return files.save(project, path, filename, extension, content)

@mcp.tool()
def load_file(project: str, path: str) -> str:
    """loads a file at the given path"""
    return files.load(project, path)

@mcp.tool()
def execute_file(
        project: str = "test", path: str = "b/x.py", args: list[str] = ["a", "-v", "1"]
    ) -> dict[str, str]:
    """loads a file at the given path"""
    result = files.execute(project, path, args)
    return result

@mcp.tool()
def remove_file(project: str, path: str) -> bool:
    """removes a file at the given path"""
    return files.remove(project, path)
