"""Core services for the MCP coding assistant."""

from core.config import AppConfig
from core.files import FileService
from core.git import GitService
from core.graph import GraphService
from core.interpreter import GraphChangeApplier
from core.projects import ProjectManager
from core.registry import ProjectRegistry

__all__ = [
    "AppConfig",
    "ProjectManager",
    "FileService",
    "GraphService",
    "GitService",
    "ProjectRegistry",
    "GraphChangeApplier",
]
