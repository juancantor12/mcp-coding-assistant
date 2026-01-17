"""Pytest fixtures for the MCP coding assistant tests."""
from __future__ import annotations

import os
import pathlib
from types import MethodType

import pytest

from core.config import AppConfig
from core.files import FileService
from core.graph import GraphService
from core.interpreter import GraphChangeApplier
from core.projects import ProjectManager


@pytest.fixture()
def project_name() -> str:
    return "demo"


@pytest.fixture()
def apps_root(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "apps"
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture()
def config(apps_root: pathlib.Path, project_name: str) -> AppConfig:
    return AppConfig(
        base_path=str(apps_root),
        projects={project_name},
        allowed_extensions={"py", "txt"},
    )


@pytest.fixture()
def project_root(apps_root: pathlib.Path, project_name: str) -> pathlib.Path:
    root = apps_root / project_name
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture()
def project_manager(config: AppConfig) -> ProjectManager:
    return ProjectManager(config)


@pytest.fixture()
def file_service(config: AppConfig, project_manager: ProjectManager) -> FileService:
    return FileService(config, project_manager)


@pytest.fixture()
def graph_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "graphs"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture()
def graph_service(config: AppConfig, graph_dir: pathlib.Path) -> GraphService:
    graphs = GraphService(config)
    graph_dir_str = str(graph_dir)

    def _graph_dir(self) -> str:
        os.makedirs(graph_dir_str, exist_ok=True)
        return graph_dir_str

    graphs._graph_dir = MethodType(_graph_dir, graphs)
    return graphs


@pytest.fixture()
def interpreter(
    config: AppConfig,
    project_manager: ProjectManager,
    file_service: FileService,
    graph_service: GraphService,
    graph_dir: pathlib.Path,
) -> GraphChangeApplier:
    interpreter = GraphChangeApplier(config, project_manager, file_service, graph_service)
    graph_dir_str = str(graph_dir)

    def _graph_path(self, project: str) -> str:
        return os.path.join(graph_dir_str, f"{project}.codegraph.json")

    interpreter._graph_path = MethodType(_graph_path, interpreter)
    return interpreter


@pytest.fixture()
def sample_python_file(project_root: pathlib.Path) -> pathlib.Path:
    content = "\n".join(
        [
            "import os",
            "",
            "class Greeter:",
            "    def greet(self):",
            "        return 'hi'",
            "",
            "def helper():",
            "    return 1",
            "",
        ]
    )
    path = project_root / "sample.py"
    path.write_text(content, encoding="utf-8")
    return path
