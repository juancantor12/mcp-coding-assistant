"""Dir manipulation tools."""
from core.config import AppConfig
from core.projects import ProjectManager as CoreProjectManager

ProjectManager = CoreProjectManager
_DEFAULT_MANAGER = ProjectManager(AppConfig.from_globals())


def make(project: str, path: str) -> bool:
    """Creates a folder at the specified path."""
    return _DEFAULT_MANAGER.make_dir(project, path)


def rename(project: str, old_path: str, new_path: str) -> bool:
    """Renames a folder at the specified path."""
    return _DEFAULT_MANAGER.rename_dir(project, old_path, new_path)


def scaffolding(project: str, sub_path: str | None = None):
    """Retrieves the project scaffolding in a dict (json) shape."""
    return _DEFAULT_MANAGER.scaffolding(project, sub_path=sub_path)


def inverted_index(project: str, sub_path: str | None = None, pre_index: dict | None = None):
    """
    Generates a hashmap with partial paths, filenames and extensions as keys
    and the associated full flat paths as values for searching.
    """
    return _DEFAULT_MANAGER.inverted_index(
        project, sub_path=sub_path, pre_index=pre_index
    )
