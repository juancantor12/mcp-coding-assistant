"""Project registry stored in JSON for persistence."""
from __future__ import annotations

import json
import os
from typing import Set


class ProjectRegistry:
    def __init__(self, repo_root: str) -> None:
        self._repo_root = repo_root

    def _path(self) -> str:
        return os.path.join(self._repo_root, "projects.json")

    def load(self) -> Set[str]:
        path = self._path()
        if not os.path.exists(path):
            return set()
        with open(path, "r", encoding="UTF-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return {str(item) for item in data}
        return set()

    def save(self, projects: Set[str]) -> None:
        path = self._path()
        with open(path, "w", encoding="UTF-8") as handle:
            json.dump(sorted(projects), handle, indent=2, ensure_ascii=True)

    def add(self, project: str) -> Set[str]:
        projects = self.load()
        projects.add(project)
        self.save(projects)
        return projects
