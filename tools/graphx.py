"""Code graph generation and querying."""
from core.config import AppConfig
from core.graph import GraphService as CoreGraphService

GraphService = CoreGraphService
_DEFAULT_GRAPH = GraphService(AppConfig.from_globals())


def build(project: str) -> dict[str, object]:
    """Builds a code graph for a project and writes it to disk."""
    return _DEFAULT_GRAPH.build(project)


def query(project: str, term: str, kind: str | None = None) -> dict[str, object]:
    """Query nodes by name/file and return matching nodes with related edges."""
    return _DEFAULT_GRAPH.query(project, term, kind=kind)


def save_proposal(project: str, proposal: dict[str, object]) -> dict[str, object]:
    """Validates and stores a graph change proposal."""
    return _DEFAULT_GRAPH.save_proposal(project, proposal)
