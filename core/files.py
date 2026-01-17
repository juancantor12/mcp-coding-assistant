"""File management operations."""
from __future__ import annotations

import os
import subprocess
import sys

from core.config import AppConfig
from core.projects import ProjectManager


class FileService:
    def __init__(self, config: AppConfig, projects: ProjectManager) -> None:
        self._config = config
        self._projects = projects

    def _project_root(self, project: str) -> str:
        return os.path.join(self._config.base_path, project)

    def _validate_project(self, project: str) -> None:
        if project not in self._config.projects:
            raise ValueError("Invalid project")

    def save(self, project: str, path: str, filename: str, extension: str, content: str) -> bool:
        """Creates or updates a file at the given path, with the given name, extension and content."""
        if project not in self._config.projects or extension not in self._config.allowed_extensions:
            raise ValueError("Invalid project or extension")
        target_path = os.path.join(self._project_root(project), path)
        self._projects.make_dir(project, path)
        file_path = os.path.join(target_path, f"{filename}.{extension}")
        with open(file_path, "w", encoding="UTF-8") as handle:
            handle.write(content)
        return True

    def load(self, project: str, path: str) -> str:
        """Loads a file at the given path."""
        self._validate_project(project)
        file_path = os.path.join(self._project_root(project), path)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="UTF-8") as handle:
                return handle.read()
        raise ValueError("File doesn't exists")

    def remove(self, project: str, path: str) -> bool:
        """Removes a file at the given path."""
        self._validate_project(project)
        file_path = os.path.join(self._project_root(project), path)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        raise ValueError("File doesn't exists")

    def execute(self, project: str, path: str, args: list[str]) -> dict[str, object]:
        """Executes a python script with the specified params."""
        self._validate_project(project)
        file_path = os.path.join(self._project_root(project), path)
        if os.path.exists(file_path):
            command = [sys.executable, file_path] + args
            with subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as process:
                outs, errs = process.communicate()
                return {"outs": outs, "errs": errs}
        raise ValueError("File doesn't exists")
