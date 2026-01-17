"""Project-level directory management."""
from __future__ import annotations

from collections import defaultdict
import os

from core.config import AppConfig


class ProjectManager:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def _project_root(self, project: str) -> str:
        return os.path.join(self._config.base_path, project)

    def _validate_project(self, project: str) -> None:
        if project not in self._config.projects:
            raise ValueError("Invalid project")

    def make_dir(self, project: str, path: str) -> bool:
        """Creates a folder at the specified path."""
        self._validate_project(project)
        target_path = os.path.join(self._project_root(project), path)
        if not os.path.isdir(target_path):
            os.makedirs(target_path, exist_ok=True)
        return True

    def rename_dir(self, project: str, old_path: str, new_path: str) -> bool:
        """Renames a folder at the specified path."""
        self._validate_project(project)
        path_to_rename = os.path.join(self._project_root(project), old_path)
        new_path_full = os.path.join(self._project_root(project), new_path)
        if os.path.isdir(path_to_rename):
            os.rename(path_to_rename, new_path_full)
        return True

    def scaffolding(self, project: str, sub_path: str | None = None) -> dict:
        """Retrieves the project scaffolding in a dict (json) shape."""
        self._validate_project(project)
        root = self._project_root(project)
        path = root if not sub_path else sub_path

        folder_dict = {
            "folder_name": project if not sub_path else os.path.basename(sub_path),
            "files": [],
            "subfolders": [],
        }

        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    folder_dict["files"].append(entry.name)
                elif entry.is_dir():
                    subfolder_dict = self.scaffolding(project=project, sub_path=entry.path)
                    folder_dict["subfolders"].append(subfolder_dict)
        except PermissionError:
            pass

        return folder_dict

    def inverted_index(
        self, project: str, sub_path: str | None = None, pre_index: dict | None = None
    ) -> dict:
        """
        Generates a hashmap with partial paths, filenames and extensions as keys
        and the associated full flat paths as values for searching.
        """
        self._validate_project(project)
        index = defaultdict(list) if pre_index is None else pre_index
        root = self._project_root(project)
        path = root if not sub_path else sub_path

        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    name, extension = entry.name.split(".")
                    index[extension].append(entry.path)
                    index[name].append(entry.path)
                elif entry.is_dir():
                    for segment in entry.path.split("\\"):
                        index[segment].append(entry.path)
                    index = self.inverted_index(
                        project=project, sub_path=entry.path, pre_index=index
                    )
        except PermissionError:
            pass

        return index
