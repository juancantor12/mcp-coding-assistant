"""File manipulation tools."""
from core.config import AppConfig
from core.files import FileService as CoreFileService
from core.projects import ProjectManager

FileService = CoreFileService
_CONFIG = AppConfig.from_globals()
_PROJECTS = ProjectManager(_CONFIG)
_DEFAULT_FILES = FileService(_CONFIG, _PROJECTS)


def save(project: str, path: str, filename: str, extension: str, content: str) -> bool:
    """Creates or updates a file at the given path, with the given name, extension and content."""
    return _DEFAULT_FILES.save(project, path, filename, extension, content)


def load(project: str, path: str) -> str:
    """Loads a file at the given path."""
    return _DEFAULT_FILES.load(project, path)


def remove(project: str, path: str) -> bool:
    """Removes a file at the given path."""
    return _DEFAULT_FILES.remove(project, path)


def execute(project: str, path: str, args: list[str]) -> dict[str, object]:
    """Executes a python script with the specified params."""
    return _DEFAULT_FILES.execute(project, path, args)
