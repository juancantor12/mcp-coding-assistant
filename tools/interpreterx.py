"""Graph change interpreter tools."""
from core.config import AppConfig
from core.files import FileService
from core.graph import GraphService
from core.interpreter import GraphChangeApplier
from core.projects import ProjectManager

GraphInterpreter = GraphChangeApplier
_CONFIG = AppConfig.from_globals()
_PROJECTS = ProjectManager(_CONFIG)
_FILES = FileService(_CONFIG, _PROJECTS)
_GRAPHS = GraphService(_CONFIG)
_DEFAULT_INTERPRETER = GraphInterpreter(_CONFIG, _PROJECTS, _FILES, _GRAPHS)


def apply_proposal(project: str, proposal_path: str) -> dict[str, object]:
    """Applies a graph proposal to code and updates the graph."""
    return _DEFAULT_INTERPRETER.apply_proposal(project, proposal_path)
